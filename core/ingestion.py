from pathlib import Path
from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document


POLICIES_DIR = Path("data/policies")


def load_policies(policies_dir: Path = POLICIES_DIR) -> list[Document]:
    if not policies_dir.exists():
        raise FileNotFoundError(f"Policies directory not found: {policies_dir}")
    docs = []
    for txt_file in sorted(policies_dir.glob("*.txt")):
        loader = TextLoader(str(txt_file), encoding="utf-8")
        loaded = loader.load()
        for doc in loaded:
            doc.metadata["source_file"] = txt_file.name
            doc.metadata["policy_name"] = txt_file.stem.replace("_", " ").title()
            docs.append(doc)
    print(f"Loaded {len(docs)} policy document(s) from {policies_dir}")
    return docs


def load_single_policy(filename: str, policies_dir: Path = POLICIES_DIR) -> Document:
    path = policies_dir / filename
    if not path.exists():
        raise FileNotFoundError(f"Policy file not found: {path}")
    loader = TextLoader(str(path), encoding="utf-8")
    docs = loader.load()
    docs[0].metadata["source"] = filename
    docs[0].metadata["policy_name"] = path.stem.replace("_", " ").title()
    return docs[0]


if __name__ == "__main__":
    docs = load_policies()
    for doc in docs:
        print(doc.metadata["source_file"], len(doc.page_content.split()), "words")
