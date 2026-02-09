"""
Vector store service using ChromaDB.
Handles storage and retrieval of document embeddings.

FIXED VERSION with:
1. Debug logging to track filtering
2. Proper ChromaDB $eq operator for filtering
3. Metadata validation
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

    # IMPORTANT: Ensure document_id is in ALL metadata entries
    for meta in metadatas:
        if "document_id" not in meta:
            print(f"⚠️  WARNING: Adding missing document_id to metadata")
            meta["document_id"] = doc_id

    collection.add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    print(f"✅ Added {len(ids)} chunks for document {doc_id}")
    return len(ids)


def search_similar(
    query_embedding: list[float],
    top_k: int = 10,
    document_id: str = None,
) -> dict:
    """Search for similar document chunks by embedding."""
    collection = get_collection()

    # ============ DEBUG LOGGING START ============
    print("\n" + "="*80)
    print("🔍 SEARCH_SIMILAR DEBUG")
    print("="*80)
    print(f"📌 Requested top_k: {top_k}")
    print(f"📌 Filter document_id: {document_id}")
    # ============ DEBUG LOGGING END ============

    query_params = {
        "query_embeddings": [query_embedding],
        "n_results": top_k,
        "include": ["documents", "metadatas", "distances"],
    }
    
    # Add document filter if specified
    if document_id:
        # ============ DEBUG LOGGING START ============
        print(f"🔧 Adding where filter for document_id: {document_id}")
        # ============ DEBUG LOGGING END ============
        
        # Use ChromaDB's $eq operator for exact string matching
        query_params["where"] = {"document_id": {"$eq": document_id}}
        
        # ============ DEBUG LOGGING START ============
        print(f"🔧 Where clause: {query_params['where']}")
        # ============ DEBUG LOGGING END ============

    # ============ DEBUG LOGGING START ============
    print(f"📤 Executing ChromaDB query...")
    # ============ DEBUG LOGGING END ============
    
    results = collection.query(**query_params)
    
    # ============ DEBUG LOGGING START ============
    if results and results.get("documents") and results["documents"][0]:
        print(f"✅ Retrieved {len(results['documents'][0])} results")
        print("\n📋 Document IDs in results:")
        for i, meta in enumerate(results["metadatas"][0][:5]):  # Show first 5
            doc_id = meta.get("document_id", "NO_ID")
            filename = meta.get("filename", "NO_FILENAME")
            print(f"   {i+1}. doc_id={doc_id}, file={filename}")
        if len(results["metadatas"][0]) > 5:
            print(f"   ... and {len(results['metadatas'][0]) - 5} more")
    else:
        print("❌ No results returned from ChromaDB")
    print("="*80 + "\n")
    # ============ DEBUG LOGGING END ============

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
        where={"document_id": {"$eq": doc_id}},  # Use $eq here too
        include=[],
    )
    if results["ids"]:
        collection.delete(ids=results["ids"])
        print(f"✅ Deleted {len(results['ids'])} chunks for document {doc_id}")