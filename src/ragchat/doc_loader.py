from pathlib import Path

from ragchat.constants import DATA_DIR


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def load_documents(data_dir: Path | None = None) -> list[dict[str, str]]:
    root = data_dir or DATA_DIR
    if not root.exists():
        return []
    documents: list[dict[str, str]] = []
    for path in sorted(root.glob("*.md")):
        text = load_text(path)
        if not text:
            continue
        documents.append({"source": path.stem, "url": "", "text": text})
    return documents
