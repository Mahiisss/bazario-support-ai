import os
import time
from dotenv import load_dotenv


from crewai import Crew, Process


from agents.triage_agent import get_triage_agent
from agents.policy_retriever_agent import get_policy_retriever_agent
from agents.resolution_writer_agent import get_resolution_writer_agent
from agents.compliance_agent import get_compliance_agent
from agents.escalation_agent import get_escalation_agent
from tasks import build_tasks


load_dotenv()




def get_llm():
    return "groq/llama-3.3-70b-versatile"




def build_crew(ticket: str, order: dict, vectorstore, verbose: bool = True):
    llm = get_llm()


    triage = get_triage_agent(llm)
    retriever, _ = get_policy_retriever_agent(llm, vectorstore)
    writer = get_resolution_writer_agent(llm)
    compliance = get_compliance_agent(llm)
    escalation = get_escalation_agent(llm)


    tasks = build_tasks(ticket, order, triage, retriever, writer, compliance, escalation)


    crew = Crew(
        agents=[triage, retriever, writer, compliance, escalation],
        tasks=tasks,
        process=Process.sequential,
        verbose=verbose
    )


    return crew




def resolve_ticket(ticket: str, order: dict, vectorstore, verbose: bool = True):
    crew = build_crew(ticket, order, vectorstore, verbose=verbose)


    for attempt in range(5):
        try:
            time.sleep(60)  # let Groq token window reset before each attempt
            result = crew.kickoff()
            return str(result)
        except Exception as e:
            if "rate_limit" in str(e).lower() or "429" in str(e):
                print(f"\nRate limit hit. Waiting 60s before retry {attempt + 1}/5...")
                time.sleep(60)
            else:
                raise e


    raise RuntimeError("Failed after 5 attempts due to rate limits.")