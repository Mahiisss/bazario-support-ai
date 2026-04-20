from typing import List
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS


# top 5 is enough for most tickets — going higher adds noise
TOP_K = 5


def retrieve(vectorstore: FAISS, query: str, k: int = TOP_K) -> List[Document]:
    """
    Runs similarity search against the FAISS index.
    Returns top-k chunks ranked by relevance.
    """
    results = vectorstore.similarity_search(query, k=k)

    if not results:
        print(f"No results found for query: '{query}'")

    return results


def format_results(results: List[Document]) -> str:
    """
    Formats retrieved chunks into a clean string for agent consumption.
    Each chunk includes source file + chunk_id for citation traceability.
    """
    if not results:
        return "NO_POLICY_FOUND: nothing relevant in the knowledge base."

    out = []
    for i, doc in enumerate(results):
        src = doc.metadata.get("source_file", "unknown")
        cid = doc.metadata.get("chunk_id", f"chunk_{i}")
        out.append(
            f"[{i+1}] Source: {src} | ID: {cid}\n{doc.page_content.strip()}"
        )

    return "\n---\n".join(out)


def retrieve_and_format(vectorstore: FAISS, query: str, k: int = TOP_K) -> str:
    """
    Convenience wrapper — retrieve + format in one call.
    This is what the PolicySearchTool uses internally.
    """
    results = retrieve(vectorstore, query, k=k)
    return format_results(results)


if __name__ == "__main__":
    from ingestion import load_policies
    from chunker import chunk_documents
    from vectorstore import get_or_build_index

    docs = load_policies()
    chunks = chunk_documents(docs)
    vs = get_or_build_index(chunks)

    # test a few realistic queries
    test_queries = [
        "refund policy for perishable food items",
        "return window for electronics",
        "what happens if the package is lost in transit",
        "can I return a final sale item",
    ]

    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 50)
        output = retrieve_and_format(vs, query, k=3)
        print(output[:500])  # trim for readability
        print()
