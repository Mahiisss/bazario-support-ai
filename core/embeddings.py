from langchain_huggingface import HuggingFaceEmbeddings


# all-MiniLM-L6-v2 is fast, lightweight, and good enough for policy retrieval
# no need for a heavier model here — these are structured text docs, not complex semantics
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def get_embeddings() -> HuggingFaceEmbeddings:
    """
    Returns the embedding model instance.
    Runs locally — no API key needed, no rate limits.
    First call downloads the model (~80MB), subsequent calls load from cache.
    """
    print(f"Loading embedding model: {EMBED_MODEL}")
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBED_MODEL,
        model_kwargs={"device": "cpu"},      # swap to "cuda" if you have a GPU
        encode_kwargs={"normalize_embeddings": True},
    )
    return embeddings


if __name__ == "__main__":
    # quick smoke test
    emb = get_embeddings()
    test = emb.embed_query("What is the return window for electronics?")
    print(f"Embedding dim: {len(test)}")
    print(f"First 5 values: {test[:5]}")
