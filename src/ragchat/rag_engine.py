import hashlib
import logging

from ragchat.cache import TTLCache, cache_key, normalize_query
from ragchat.constants import (
    CHROMA_DIR,
    CHUNKING,
    COLLECTION_NAME,
    EMBED_MODEL_NAME,
    RETRIEVAL_CACHE_TTL,
    TOP_K,
)
from ragchat.doc_loader import load_documents

logger = logging.getLogger(__name__)

_client = None
_embed = None
_index = None
_retrieval_cache = TTLCache(ttl_seconds=RETRIEVAL_CACHE_TTL)


def _documents_hash(documents: list[dict[str, str]]) -> str:
    digest = hashlib.sha256()
    for item in documents:
        digest.update(item["source"].encode("utf-8"))
        digest.update(b"\0")
        digest.update(item["text"].encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def _get_chroma_client():
    global _client
    if _client is None:
        import chromadb

        CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return _client


def _get_embed_model():
    global _embed
    if _embed is None:
        from ragchat.embeddings import ProfileHuggingFaceEmbedding

        _embed = ProfileHuggingFaceEmbedding(model_name=EMBED_MODEL_NAME)
    return _embed


def _reset_index() -> None:
    global _index
    _index = None
    _retrieval_cache.clear()


def _build_index_from_collection():
    from llama_index.core import Settings, VectorStoreIndex
    from llama_index.vector_stores.chroma import ChromaVectorStore

    client = _get_chroma_client()
    try:
        collection = client.get_collection(COLLECTION_NAME)
    except Exception:
        return None
    if collection.count() == 0:
        return None
    embed = _get_embed_model()
    Settings.embed_model = embed
    vector_store = ChromaVectorStore(chroma_collection=collection)
    return VectorStoreIndex.from_vector_store(vector_store, embed_model=embed)


def _get_index():
    global _index
    if _index is None:
        _index = _build_index_from_collection()
    return _index


def _ingest(documents: list[dict[str, str]], docs_hash: str) -> None:
    from llama_index.core import Document, Settings, StorageContext, VectorStoreIndex
    from llama_index.core.node_parser import SemanticSplitterNodeParser, SentenceSplitter
    from llama_index.vector_stores.chroma import ChromaVectorStore

    client = _get_chroma_client()
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={
            "embed_model": EMBED_MODEL_NAME,
            "chunking": CHUNKING,
            "docs_hash": docs_hash,
        },
    )
    embed = _get_embed_model()
    Settings.embed_model = embed

    llama_docs = [
        Document(text=item["text"], metadata={"source": item["source"], "url": item["url"]})
        for item in documents
    ]
    sentence = SentenceSplitter(chunk_size=1024, chunk_overlap=50)
    try:
        semantic = SemanticSplitterNodeParser(
            buffer_size=1,
            breakpoint_percentile_threshold=95,
            embed_model=embed,
        )
        nodes = semantic.get_nodes_from_documents(llama_docs)
        if not nodes:
            nodes = sentence.get_nodes_from_documents(llama_docs)
        else:
            split_nodes = []
            for node in nodes:
                split_nodes.extend(
                    sentence.get_nodes_from_documents(
                        [Document(text=node.get_content(), metadata=dict(node.metadata))]
                    )
                )
            nodes = split_nodes or nodes
    except Exception as exc:
        logger.warning("Semantic split failed, using sentence splitter: %s", exc)
        nodes = sentence.get_nodes_from_documents(llama_docs)

    vector_store = ChromaVectorStore(chroma_collection=collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    global _index
    _index = VectorStoreIndex(nodes, storage_context=storage_context, embed_model=embed)
    _retrieval_cache.clear()
    logger.info("Ingested %s nodes into %s", len(nodes), COLLECTION_NAME)


def ensure_index() -> None:
    documents = load_documents()
    if not documents:
        logger.warning("No markdown in data/; skip ingest. Add profile.md then reingest.")
        return

    docs_hash = _documents_hash(documents)
    client = _get_chroma_client()
    try:
        collection = client.get_collection(COLLECTION_NAME)
        metadata = collection.metadata or {}
        if (
            metadata.get("embed_model") == EMBED_MODEL_NAME
            and metadata.get("chunking") == CHUNKING
            and metadata.get("docs_hash") == docs_hash
        ):
            logger.info("Collection %s is up to date", COLLECTION_NAME)
            return
    except Exception:
        pass

    _ingest(documents, docs_hash)


def reingest() -> dict[str, str]:
    documents = load_documents()
    if not documents:
        logger.warning("No markdown in data/; reingest skipped")
        return {"status": "skipped", "reason": "no markdown in data/"}
    _reset_index()
    _ingest(documents, _documents_hash(documents))
    return {"status": "ok", "collection": COLLECTION_NAME}


def retrieve(query: str, top_k: int = TOP_K) -> list[dict[str, str]]:
    key = cache_key("retrieve", normalize_query(query), str(top_k))
    cached = _retrieval_cache.get(key)
    if cached is not None:
        return cached

    index = _get_index()
    if index is None:
        return []

    nodes = index.as_retriever(similarity_top_k=top_k).retrieve(query)
    chunks: list[dict[str, str]] = []
    for node in nodes:
        metadata = node.metadata or {}
        chunks.append(
            {
                "text": node.get_content(),
                "source": str(metadata.get("source") or ""),
                "url": str(metadata.get("url") or ""),
            }
        )
    _retrieval_cache.set(key, chunks)
    return chunks


def clear_retrieval_cache() -> None:
    _retrieval_cache.clear()
