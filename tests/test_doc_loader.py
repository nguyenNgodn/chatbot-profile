from pathlib import Path

from ragchat.doc_loader import load_documents


def test_load_documents_skips_empty_dir(tmp_path: Path):
    assert load_documents(tmp_path) == []


def test_load_documents_reads_markdown(tmp_path: Path):
    (tmp_path / "profile.md").write_text("# Hello\nI am the owner.", encoding="utf-8")
    (tmp_path / "empty.md").write_text("   \n", encoding="utf-8")
    docs = load_documents(tmp_path)
    assert len(docs) == 1
    assert docs[0]["source"] == "profile"
    assert "owner" in docs[0]["text"]
