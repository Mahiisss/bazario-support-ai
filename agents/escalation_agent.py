from crewai import Agent


# reasons that should always trigger escalation
ESCALATION_TRIGGERS = [
    "conflicting regional and seller policies",
    "no policy coverage found",
    "potential fraud detected",
    "customer threatening legal action",
    "high value order requiring manual review",
    "compliance agent flagged unresolvable issues",
]


def get_escalation_agent(llm) -> Agent:
    """
    Steps in when the compliance agent returns ESCALATE
    or when the resolution writer hits a dead end.
    Writes a clear internal handoff note for the human agent
    so they're not starting from scratch.
    """
    return Agent(
        role="Escalation Agent",
        goal=(
            "When a ticket cannot be resolved through policy alone, "
            "prepare a clear escalation report for the human support team. "
            "The report must include:\n"
            "- Why this ticket is being escalated\n"
            "- What was already tried and why it failed\n"
            "- What policy gaps or conflicts exist\n"
            "- Recommended next steps for the human agent\n"
            "- A draft message to send the customer explaining the delay\n\n"
            f"Common escalation triggers: {', '.join(ESCALATION_TRIGGERS)}."
        ),
        backstory=(
            "You handle the cases that fall through the cracks — "
            "the ones where policy is silent, rules conflict, or the stakes are too high "
            "to risk an automated response. "
            "Your job isn't to resolve the ticket yourself, it's to make sure "
            "the human agent who picks it up has everything they need to close it fast. "
            "A good handoff saves everyone time."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )
