from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config.config import cfg


def chunk_documents(docs: List[Document]) -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=cfg.chunk_size,
        chunk_overlap=cfg.chunk_overlap,
        separators=["\n\n", "\n", "SECTION", ". ", " "],
    )

    chunks = splitter.split_documents(docs)

    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_id"] = f"chunk_{i:04d}"

    print(f"Chunked {len(docs)} docs → {len(chunks)} chunks "
          f"(size={cfg.chunk_size}, overlap={cfg.chunk_overlap})")
    return chunks


def preview_chunks(chunks: List[Document], n: int = 3) -> None:
    print(f"\nShowing first {n} chunks:\n")
    for chunk in chunks[:n]:
        src = chunk.metadata.get("source_file", "?")
        cid = chunk.metadata.get("chunk_id", "?")
        print(f"[{cid}] {src}")
        print(chunk.page_content[:300])
        print("---")


if __name__ == "__main__":
    from core.ingestion import load_policies
    docs = load_policies()
    chunks = chunk_documents(docs)
    preview_chunks(chunks, n=5)