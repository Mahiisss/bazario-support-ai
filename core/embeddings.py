from langchain_huggingface import HuggingFaceEmbeddings
from config.config import cfg


def get_embeddings() -> HuggingFaceEmbeddings:
    print(f"Loading embedding model: {cfg.embedding_model}")
    embeddings = HuggingFaceEmbeddings(
        model_name=cfg.embedding_model,
        model_kwargs={"device": cfg.embedding_device},
        encode_kwargs={"normalize_embeddings": cfg.embedding_normalize},
    )
    return embeddings


if __name__ == "__main__":
    emb = get_embeddings()
    test = emb.embed_query("What is the return window for electronics?")
    print(f"Embedding dim: {len(test)}")
    print(f"First 5 values: {test[:5]}")