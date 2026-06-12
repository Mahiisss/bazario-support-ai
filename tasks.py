import json
from crewai import Task

COMPLIANCE_CHECKS = (
    "Review the resolution draft. Check for:\n"
    "- Any claim not backed by a citation → mark UNSUPPORTED\n"
    "- Decision made without evidence → mark MISSING CITATION\n"
    "- Anything contradicting retrieved policy → mark POLICY VIOLATION\n\n"
    "Return VERDICT: ESCALATE when ANY of the following are true:\n"
    "- Customer threatens legal action\n"
    "- Customer requests compensation beyond documented policy\n"
    "- Multiple previous support attempts have failed\n"
    "- Policy excerpts conflict with each other\n"
    "- No policy coverage exists for the requested action\n"
    "- A marketplace seller is actively refusing a valid customer claim\n"
    "- Human judgment is required to make a decision\n"
    "- Customer explicitly requests management or senior support review\n\n"
    "Return VERDICT: NEEDS REWRITE when:\n"
    "- A factual policy claim has no citation\n"
    "- An invented policy or number not in retrieved chunks\n"
    "- Decision directly contradicts cited policy\n\n"
    "Return VERDICT: APPROVED when the resolution is factually grounded "
    "and policy-aligned, even if not perfect.\n\n"
    "Your output MUST start with exactly one of these on the first line:\n"
    "VERDICT: APPROVED\n"
    "VERDICT: NEEDS REWRITE\n"
    "VERDICT: ESCALATE\n\n"
    "Then continue with:\n"
    "## Compliance Verdict\n"
    "[APPROVED / NEEDS REWRITE / ESCALATE]\n\n"
    "## Issues Found\n"
    "[list each issue, or 'None']\n\n"
    "## Final Resolution\n"
    "[paste approved resolution, corrected version, "
    "or 'ESCALATE TO HUMAN AGENT: [reason]']"
)

COMPLIANCE_EXPECTED = (
    "First line must be VERDICT: [APPROVED/NEEDS REWRITE/ESCALATE], "
    "followed by compliance verdict, issues found, and final resolution."
)


def build_tasks(ticket: str, order: dict, triage, retriever, writer, compliance):
    order_str = json.dumps(order, indent=2)

    t1 = Task(
        description=(
            f"Ticket:\n{ticket}\n\n"
            f"Order Context:\n{order_str}\n\n"
            "Provide:\n"
            "1. Classification: [issue type] | Confidence: [High/Med/Low]\n"
            "2. Missing Info: [any gaps that affect resolution]\n"
            "3. Clarifying Questions: [max 3, or 'None needed']\n"
            "4. Key Facts: [brief summary of what we know]"
        ),
        expected_output=(
            "Triage report with classification, confidence, missing info, "
            "clarifying questions, and key facts."
        ),
        agent=triage,
    )

    t2 = Task(
        description=(
            f"Ticket:\n{ticket}\n\n"
            f"Order:\n{order_str}\n\n"
            "Search for all relevant policy sections using policy_search. "
            "Run a MAXIMUM of 3 searches only — cover "
            "shipping delays, regional rules, marketplace rules, dispute process. "
            "Return every excerpt with source file + chunk ID. "
            "If nothing is found, return: NO_POLICY_FOUND."
        ),
        expected_output=(
            "All relevant policy excerpts with citations (source file + chunk ID)."
        ),
        agent=retriever,
        context=[t1],
    )

    t3 = Task(
        description=(
            f"Ticket:\n{ticket}\n\n"
            f"Order:\n{order_str}\n\n"
            "Using ONLY the retrieved policy excerpts, write the resolution "
            "in this exact format:\n\n"
            "## Classification\n"
            "## Clarifying Questions\n"
            "## Decision\n"
            "## Rationale\n"
            "## Citations\n"
            "## Customer Response Draft\n"
            "## Next Steps / Internal Notes\n\n"
            "Hard rules:\n"
            "- Every factual claim in Rationale must appear in Citations.\n"
            "- If something is not covered by policy, write: "
            "'Not in available policy — recommend escalation to human agent.'\n"
            "- Do not invent, assume, or paraphrase policy from memory."
        ),
        expected_output=(
            "Complete 7-section resolution with a citation for every factual claim."
        ),
        agent=writer,
        context=[t1, t2],
    )

    t4 = Task(
        description=COMPLIANCE_CHECKS,
        expected_output=COMPLIANCE_EXPECTED,
        agent=compliance,
        context=[t2, t3],
    )

    return t1, t2, t3, t4


def build_rewrite_tasks(ticket: str, order: dict, writer, compliance,
                        prior_compliance_output: str, t1, t2):
    order_str = json.dumps(order, indent=2)

    rt3 = Task(
        description=(
            f"Ticket:\n{ticket}\n\n"
            f"Order:\n{order_str}\n\n"
            "The compliance agent reviewed your previous draft and found issues. "
            "Here is their feedback:\n\n"
            f"{prior_compliance_output}\n\n"
            "Rewrite the resolution fixing ALL issues listed above. "
            "Use the same 7-section format:\n\n"
            "## Classification\n"
            "## Clarifying Questions\n"
            "## Decision\n"
            "## Rationale\n"
            "## Citations\n"
            "## Customer Response Draft\n"
            "## Next Steps / Internal Notes\n\n"
            "Every factual claim MUST have a citation. Do not add new information."
        ),
        expected_output="Corrected 7-section resolution addressing all compliance issues.",
        agent=writer,
        context=[t1, t2],
    )

    rt4 = Task(
        description=COMPLIANCE_CHECKS,
        expected_output=COMPLIANCE_EXPECTED,
        agent=compliance,
        context=[t1, t2, rt3],
    )

    return rt3, rt4


def build_escalation_task(ticket: str, order: dict, escalation, t1, t2, t4) -> Task:
    order_str = json.dumps(order, indent=2)

    return Task(
        description=(
            f"Ticket:\n{ticket}\n\n"
            f"Order:\n{order_str}\n\n"
            "The compliance agent has flagged this ticket for escalation. "
            "Prepare a full escalation report for the human support team:\n"
            "- Why this ticket is being escalated\n"
            "- What was attempted and why it failed\n"
            "- What policy gaps or conflicts exist\n"
            "- Recommended next steps for the human agent\n"
            "- A draft message to send the customer explaining the delay"
        ),
        expected_output=(
            "Escalation report with reason, attempted steps, policy gaps, "
            "next steps, and customer message draft."
        ),
        agent=escalation,
        context=[t1, t2, t4],
    )