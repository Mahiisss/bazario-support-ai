from crewai import Agent
import yaml
from pathlib import Path


def load_compliance_config():
    path = Path("config/prompts.yaml")
    if path.exists():
        with open(path) as f:
            return yaml.safe_load(f).get("compliance", {})
    return {}


def get_compliance_agent(llm) -> Agent:
    cfg = load_compliance_config()
    system_prompt = cfg.get("system", "")
    verdicts = cfg.get("verdicts", ["APPROVED", "NEEDS REWRITE", "ESCALATE"])

    return Agent(
        role="Compliance Agent",
        goal=(
            f"{system_prompt}\n\n"
            f"Valid verdicts: {', '.join(verdicts)}\n"
            "Output MUST start with exactly one of:\n"
            "VERDICT: APPROVED\n"
            "VERDICT: NEEDS REWRITE\n"
            "VERDICT: ESCALATE"
        ),
        backstory=(
            "You are a pragmatic compliance reviewer for Bazario. "
            "You approve resolutions that are factually grounded and policy-aligned. "
            "You only block resolutions with genuine policy violations — invented facts, "
            "uncited policy claims, or direct contradictions with retrieved policy. "
            "Order IDs and order details in internal notes are normal and expected. "
            "You do not flag minor wording issues or polite phrases without citations."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )