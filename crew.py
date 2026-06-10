import os
import time
import re
from datetime import date
from typing import Optional
from dotenv import load_dotenv

from crewai import Crew, Process

from agents.triage_agent import get_triage_agent
from agents.policy_retriever_agent import get_policy_retriever_agent
from agents.resolution_writer_agent import get_resolution_writer_agent
from agents.compliance_agent import get_compliance_agent
from agents.escalation_agent import get_escalation_agent
from tasks import build_tasks, build_rewrite_tasks, build_escalation_task
from models import ResolutionResult
from config.config import cfg

load_dotenv()

# --- API Key Rotation ---
_groq_keys = [
    k for k in [
        os.getenv("GROQ_API_KEY_1"),
        os.getenv("GROQ_API_KEY_2"),
        os.getenv("GROQ_API_KEY_3"),
        os.getenv("GROQ_API_KEY"),  # fallback to single key
    ]
    if k
]

if not _groq_keys:
    raise RuntimeError("No Groq API key found. Set GROQ_API_KEY or GROQ_API_KEY_1 in .env")

_key_index = 0

def get_next_key() -> str:
    """Rotate to the next available API key."""
    global _key_index
    key = _groq_keys[_key_index % len(_groq_keys)]
    _key_index += 1
    return key

def get_llm() -> str:
    """Return LLM string with current API key set in environment."""
    key = get_next_key()
    os.environ["GROQ_API_KEY"] = key
    print(f"[Bazario] Using API key ending in ...{key[-6:]}")
    return cfg.llm_model


def validate_order_dates(order: dict) -> list:
    """Check for future dates in order. Returns list of problems found."""
    problems = []
    today = date.today()

    for field in ["order_date", "delivery_date"]:
        val = order.get(field)
        if not val:
            continue
        try:
            parsed = date.fromisoformat(str(val))
            if parsed > today:
                problems.append(
                    f"{field} is {val}, which is in the future — order details appear invalid."
                )
        except ValueError:
            problems.append(f"{field} has an unrecognisable format: {val}")

    return problems


def parse_compliance_verdict(compliance_output: str) -> str:
    """Extract verdict from compliance output."""
    for line in compliance_output.splitlines():
        line_upper = line.strip().upper()
        if line_upper.startswith("VERDICT:"):
            verdict = line_upper.replace("VERDICT:", "").strip()
            if "ESCALATE" in verdict:
                return "ESCALATE"
            if "REWRITE" in verdict:
                return "NEEDS REWRITE"
            if "APPROVED" in verdict:
                return "APPROVED"

    upper = compliance_output.upper()
    if "ESCALATE TO HUMAN AGENT" in upper or "ESCALATION REPORT" in upper:
        return "ESCALATE"
    if "NEEDS REWRITE" in upper:
        return "NEEDS REWRITE"
    return "APPROVED"


def extract_customer_response(text: str) -> Optional[str]:
    match = re.search(
        r"##\s*Customer Response Draft\s*\n(.*?)(?=\n##|\Z)",
        text, re.DOTALL | re.IGNORECASE
    )
    return match.group(1).strip() if match else None


def extract_decision(text: str) -> Optional[str]:
    match = re.search(
        r"##\s*Decision\s*\n(.*?)(?=\n##|\Z)",
        text, re.DOTALL | re.IGNORECASE
    )
    return match.group(1).strip() if match else None


def run_with_retry(crew: Crew, max_attempts: int = 5) -> str:
    """Run a crew with rate-limit retry and automatic key rotation."""
    for attempt in range(max_attempts):
        try:
            return str(crew.kickoff())
        except Exception as e:
            err = str(e).lower()
            if "rate_limit" in err or "429" in err:
                # Rotate to next key before retrying
                new_key = get_next_key()
                os.environ["GROQ_API_KEY"] = new_key
                print(f"[Bazario] Rate limit hit. Rotating to key ...{new_key[-6:]}")
                wait = 30 * (attempt + 1)  # shorter wait since we're rotating keys
                print(f"[Bazario] Waiting {wait}s before retry {attempt + 1}/{max_attempts}...")
                time.sleep(wait)
            else:
                raise e
    raise RuntimeError("Failed after 5 attempts — all keys exhausted or rate limited.")


def resolve_ticket(ticket: str, order: dict, vectorstore, verbose: bool = True) -> ResolutionResult:
    llm = get_llm()

    # --- Validate order dates ---
    date_problems = validate_order_dates(order)
    if date_problems:
        problem_str = "; ".join(date_problems)
        print(f"[Bazario] Date validation failed: {problem_str}")
        return ResolutionResult(
            status="needs_info",
            message=f"Order date validation failed: {problem_str}. Please verify your order ID and try again.",
            missing_fields=["valid_dates"],
            result=None
        )

    # --- Build agents ---
    triage       = get_triage_agent(llm)
    retriever, _ = get_policy_retriever_agent(llm, vectorstore)
    writer       = get_resolution_writer_agent(llm)
    compliance   = get_compliance_agent(llm)
    escalation   = get_escalation_agent(llm)

    # --- Run 4-task pipeline ---
    t1, t2, t3, t4 = build_tasks(ticket, order, triage, retriever, writer, compliance)

    main_crew = Crew(
        agents=[triage, retriever, writer, compliance],
        tasks=[t1, t2, t3, t4],
        process=Process.sequential,
        verbose=verbose
    )

    compliance_result = run_with_retry(main_crew)
    verdict = parse_compliance_verdict(compliance_result)
    print(f"\n[Bazario] Compliance verdict: {verdict}")

    # --- APPROVED ---
    if verdict == "APPROVED":
        return ResolutionResult(
            status="resolved",
            verdict="APPROVED",
            result=compliance_result,
            customer_response=extract_customer_response(compliance_result),
            decision=extract_decision(compliance_result),
            message="Ticket resolved successfully."
        )

    # --- NEEDS REWRITE ---
    if verdict == "NEEDS REWRITE":
        print("[Bazario] Rerunning writer with compliance feedback...")

        rt3, rt4 = build_rewrite_tasks(
            ticket, order, writer, compliance,
            prior_compliance_output=compliance_result,
            t1=t1, t2=t2
        )

        rewrite_crew = Crew(
            agents=[writer, compliance],
            tasks=[rt3, rt4],
            process=Process.sequential,
            verbose=verbose
        )

        rewrite_result = run_with_retry(rewrite_crew)
        rewrite_verdict = parse_compliance_verdict(rewrite_result)

        if rewrite_verdict == "APPROVED":
            return ResolutionResult(
                status="resolved",
                verdict="APPROVED",
                result=rewrite_result,
                customer_response=extract_customer_response(rewrite_result),
                decision=extract_decision(rewrite_result),
                message="Ticket resolved after revision."
            )

        print("[Bazario] Still not approved after rewrite — escalating.")
        compliance_result = rewrite_result

    # --- ESCALATE ---
    print("[Bazario] Running escalation agent...")

    t5 = build_escalation_task(ticket, order, escalation, t1, t2, t4)

    escalation_crew = Crew(
        agents=[escalation],
        tasks=[t5],
        process=Process.sequential,
        verbose=verbose
    )

    escalation_result = run_with_retry(escalation_crew)

    return ResolutionResult(
        status="escalated",
        verdict="ESCALATE",
        result=escalation_result,
        customer_response=extract_customer_response(escalation_result),
        decision=None,
        message="Ticket escalated to human agent."
    )