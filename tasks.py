import json
from crewai import Task
from crewai import Agent


def build_tasks(ticket: str, order: dict, triage, retriever, writer, compliance, escalation) -> list[Task]:
    """
    Defines the 5 tasks in order — each one feeds context into the next.
    The escalation task only matters if compliance returns ESCALATE,
    but we define it here so the crew has it ready.
    """
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
            "All relevant policy excerpts with citations (source file + chunk ID) for each."
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
        description=(
            "Review the resolution draft. Check for:\n"
            "- Any claim not backed by a citation → mark UNSUPPORTED\n"
            "- Decision made without evidence → mark MISSING CITATION\n"
            "- Anything contradicting retrieved policy → mark POLICY VIOLATION\n"
            "- Customer PII or sensitive data visible → mark DATA LEAK\n\n"
            "Output:\n"
            "## Compliance Verdict\n"
            "[APPROVED / NEEDS REWRITE / ESCALATE]\n\n"
            "## Issues Found\n"
            "[list each issue, or 'None']\n\n"
            "## Final Resolution\n"
            "[paste approved resolution, corrected version, "
            "or 'ESCALATE TO HUMAN AGENT: [reason]']"
        ),
        expected_output=(
            "Compliance verdict, list of issues, and the final resolution or escalation note."
        ),
        agent=compliance,
        context=[t2, t3],
    )

    t5 = Task(
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

    return [t1, t2, t3, t4, t5]
