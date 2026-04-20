from crewai import Agent


# issue types the triage agent can classify into
ISSUE_TYPES = [
    "refund",
    "shipping",
    "payment",
    "promo",
    "fraud",
    "dispute",
    "cancellation",
    "other",
]


def get_triage_agent(llm) -> Agent:
    """
    First agent in the pipeline.
    Reads the ticket + order context, figures out what's going on,
    and flags anything missing before the other agents start working.
    """
    return Agent(
        role="Triage Agent",
        goal=(
            f"Classify the support ticket into one of: {', '.join(ISSUE_TYPES)}. "
            "Extract key facts from the order context. "
            "If critical information is missing, list up to 3 clarifying questions — "
            "but only ask what actually matters for resolving the ticket."
        ),
        backstory=(
            "You've handled thousands of support tickets and you're fast at cutting "
            "through the noise. You know what info matters and what's just filler. "
            "You never jump to conclusions — if something's unclear, you say so."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )
