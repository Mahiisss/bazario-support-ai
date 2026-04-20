from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


# 500/100 is the sweet spot for policy docs —
# big enough to capture a full rule, small enough to stay focused
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100


def chunk_documents(docs: List[Document]) -> List[Document]:
    """
    Splits policy docs into overlapping chunks for vector indexing.
    Tries to split on section breaks first, then sentences, then words.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", "SECTION", ". ", " "],
    )

    chunks = splitter.split_documents(docs)

    # tag each chunk with an id so citations are traceable
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_id"] = f"chunk_{i:04d}"

    print(f"Chunked {len(docs)} docs → {len(chunks)} chunks "
          f"(size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    return chunks


def preview_chunks(chunks: List[Document], n: int = 3) -> None:
    """Print first n chunks — good for sanity checking before indexing."""
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
