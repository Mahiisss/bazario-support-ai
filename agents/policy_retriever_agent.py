from crewai import Agent
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Any

from langchain_community.vectorstores import FAISS


TOP_K = 3


class PolicySearchInput(BaseModel):
    query: str = Field(description="what to search for in the policy docs")


class PolicySearchTool(BaseTool):
    """
    Wraps the FAISS retriever as a CrewAI tool.
    Every result includes source file + chunk_id so citations are always traceable.
    """
    name: str = "policy_search"
    description: str = (
        "Searches Bazario policy documents and returns relevant excerpts with citations. "
        "Use this for anything related to returns, refunds, shipping, promos, disputes, "
        "cancellations, or regional/marketplace rules. Always cite source + chunk ID."
    )
    args_schema: type[BaseModel] = PolicySearchInput
    vectorstore: Any = None

    class Config:
        arbitrary_types_allowed = True

    def _run(self, query: str) -> str:
        results = self.vectorstore.similarity_search(query, k=TOP_K)

        if not results:
            return "NO_POLICY_FOUND: nothing relevant found in the knowledge base."

        out = []
        for i, doc in enumerate(results):
            src = doc.metadata.get("source_file", "unknown")
            cid = doc.metadata.get("chunk_id", f"chunk_{i}")
            out.append(
                f"[{i+1}] Source: {src} | ID: {cid}\n{doc.page_content.strip()}"
            )

        return "\n---\n".join(out)


def get_policy_retriever_agent(llm, vectorstore: FAISS) -> tuple[Agent, PolicySearchTool]:
    """
    Returns the retriever agent + its search tool.
    Both are returned so the tool can be reused or inspected elsewhere.
    """
    tool = PolicySearchTool(vectorstore=vectorstore)

    agent = Agent(
        role="Policy Retriever Agent",
        goal=(
            "Use the policy_search tool to find every relevant policy section for this ticket. "
            "Search multiple times if needed — cover returns, refunds, item categories, "
            "regional rules, and marketplace rules where applicable. "
            "Never state a policy rule from memory. Always cite source file and chunk ID."
        ),
        backstory=(
            "You're the policy lookup specialist. You have one rule: "
            "if it's not in the docs, it doesn't exist. "
            "You search thoroughly and return everything relevant — "
            "the writer agent depends on you getting this right."
        ),
        tools=[tool],
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    return agent, tool
