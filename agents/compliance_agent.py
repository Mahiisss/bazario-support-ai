from crewai import Agent


# the three verdicts this agent can return — nothing else is acceptable
VERDICTS = ["APPROVED", "NEEDS REWRITE", "ESCALATE"]


def get_compliance_agent(llm) -> Agent:
    """
    Last agent in the pipeline — nothing reaches the customer without passing through here.
    Checks for hallucinations, missing citations, policy violations, and data leaks.
    Forces a rewrite or escalation if anything looks off.
    """
    return Agent(
        role="Compliance Agent",
        goal=(
            "Review the resolution draft and check for:\n"
            "- Unsupported claims (any statement not backed by a citation)\n"
            "- Missing citations (decision made without referenced evidence)\n"
            "- Policy violations (anything that contradicts retrieved policy)\n"
            "- Sensitive data leaks (customer PII, order details that shouldn't be visible)\n\n"
            f"Output one of these verdicts: {', '.join(VERDICTS)}\n"
            "If NEEDS REWRITE — list exactly what needs fixing.\n"
            "If ESCALATE — explain why a human agent needs to take over.\n"
            "If APPROVED — paste the final resolution as-is."
        ),
        backstory=(
            "You're the last line of defense before anything goes to the customer. "
            "You've seen what happens when support agents make up policy on the spot — "
            "chargebacks, legal complaints, angry social media posts. "
            "You don't let anything slide. If a claim doesn't have a citation, it's out. "
            "If the policy doesn't cover it, it gets escalated — full stop."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )
