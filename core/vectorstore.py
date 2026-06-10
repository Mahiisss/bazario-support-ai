from pathlib import Path
from typing import List, Optional

from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS

from core.embeddings import get_embeddings
from config.config import cfg


def build_index(chunks: List[Document], save_path: Optional[str] = None) -> FAISS:
    path = save_path if save_path is not None else cfg.index_path
    embeddings = get_embeddings()
    print(f"Indexing {len(chunks)} chunks...")
    vs = FAISS.from_documents(chunks, embeddings)
    Path(path).mkdir(parents=True, exist_ok=True)
    vs.save_local(path)
    print(f"Index saved to {path}")
    return vs


def load_index(save_path: Optional[str] = None) -> FAISS:
    path = save_path if save_path is not None else cfg.index_path
    if not Path(path).exists():
        raise FileNotFoundError(f"No index found at {path}. Run build_index() first.")
    embeddings = get_embeddings()
    print(f"Loading index from {path}...")
    vs = FAISS.load_local(path, embeddings, allow_dangerous_deserialization=True)
    print("Index loaded.")
    return vs


def get_or_build_index(chunks: Optional[List[Document]] = None, rebuild: bool = False) -> FAISS:
    index_path: str = cfg.index_path
    if not rebuild and Path(index_path).exists():
        return load_index(index_path)
    if chunks is None:
        raise ValueError("No existing index found and no chunks provided to build one.")
    return build_index(chunks, index_path)


if __name__ == "__main__":
    from core.ingestion import load_policies
    from core.chunker import chunk_documents
    docs = load_policies()
    chunks = chunk_documents(docs)
    vs = build_index(chunks)
    results = vs.similarity_search("return policy for perishable items", k=cfg.top_k)
    for r in results:
        print(f"  [{r.metadata.get('chunk_id')}] {r.metadata.get('source')}")
        print(f"  {r.page_content[:150]}\n")