from pathlib import Path
from typing import List, Optional

from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS

from core.embeddings import get_embeddings


FAISS_PATH = "data/faiss_index"


def build_index(chunks: List[Document], save_path: str = FAISS_PATH) -> FAISS:
    embeddings = get_embeddings()
    print(f"Indexing {len(chunks)} chunks...")
    vs = FAISS.from_documents(chunks, embeddings)
    Path(save_path).mkdir(parents=True, exist_ok=True)
    vs.save_local(save_path)
    print(f"Index saved to {save_path}")
    return vs


def load_index(save_path: str = FAISS_PATH) -> FAISS:
    if not Path(save_path).exists():
        raise FileNotFoundError(f"No index found at {save_path}. Run build_index() first.")
    embeddings = get_embeddings()
    print(f"Loading index from {save_path}...")
    vs = FAISS.load_local(save_path, embeddings, allow_dangerous_deserialization=True)
    print("Index loaded.")
    return vs


def get_or_build_index(chunks: Optional[List[Document]] = None, rebuild: bool = False) -> FAISS:
    if not rebuild and Path(FAISS_PATH).exists():
        return load_index()
    if chunks is None:
        raise ValueError("No existing index found and no chunks provided to build one.")
    return build_index(chunks)


if __name__ == "__main__":
    from core.ingestion import load_policies
    from core.chunker import chunk_documents
    docs = load_policies()
    chunks = chunk_documents(docs)
    vs = build_index(chunks)
    results = vs.similarity_search("return policy for perishable items", k=3)
    for r in results:
        print(f"  [{r.metadata.get('chunk_id')}] {r.metadata.get('source')}")
        print(f"  {r.page_content[:150]}\n")
