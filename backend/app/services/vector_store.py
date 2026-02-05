"""
Vector store service using ChromaDB.
Handles storage and retrieval of document embeddings.
"""

import chromadb
from chromadb.config import Settings as ChromaSettings
from app.core.config import settings

# Singleton client
_client = None
_collection = None


def get_client():
    """Get or create ChromaDB client."""
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
    return _client


def get_collection():
    """Get or create the documents collection."""
    global _collection
    if _collection is None:
        client = get_client()
        _collection = client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def add_document_chunks(
    doc_id: str,
    chunks: list[str],
    embeddings: list[list[float]],
    metadatas: list[dict],
):
    """Add document chunks with embeddings to the vector store."""
    collection = get_collection()

    ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]

    collection.add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    return len(ids)


def search_similar(
    query_embedding: list[float],
    top_k: int = 10,
) -> dict:
    """Search for similar document chunks by embedding."""
    collection = get_collection()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    return results


def get_all_documents() -> list[dict]:
    """Get metadata of all stored documents."""
    collection = get_collection()
    results = collection.get(include=["metadatas"])

    # Extract unique documents
    docs = {}
    for meta in results["metadatas"]:
        doc_id = meta.get("document_id", "unknown")
        if doc_id not in docs:
            docs[doc_id] = {
                "id": doc_id,
                "filename": meta.get("filename", "unknown"),
                "page_count": meta.get("page_count", 0),
                "upload_date": meta.get("upload_date", ""),
            }

    return list(docs.values())


def get_collection_count() -> int:
    """Get total number of chunks in the collection."""
    collection = get_collection()
    return collection.count()


def delete_document(doc_id: str):
    """Delete all chunks for a document."""
    collection = get_collection()
    # Get all IDs that belong to this document
    results = collection.get(
        where={"document_id": doc_id},
        include=[],
    )
    if results["ids"]:
        collection.delete(ids=results["ids"])
