"""
Search service combining semantic (vector) search and keyword (BM25) search.
Runs NER on returned snippets so entities are visible in search results.
"""

from rank_bm25 import BM25Okapi

from app.services.embedding_service import generate_single_embedding
from app.services.vector_store import search_similar, get_collection
from app.services.ner_service import extract_entities


def _enrich_with_entities(results: list[dict]) -> list[dict]:
    """Run NER on each result snippet and attach entities."""
    for result in results:
        try:
            ents = extract_entities(result["chunk_text"][:2000])
            result["entities"] = ents[:10]  # Keep top 10 to avoid bloat
        except Exception:
            result["entities"] = []
    return results


def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """Perform semantic search using vector similarity."""
    query_embedding = generate_single_embedding(query)
    results = search_similar(query_embedding, top_k=top_k)

    search_results = []
    if results and results["documents"] and results["documents"][0]:
        for i in range(len(results["documents"][0])):
            meta = results["metadatas"][0][i] if results["metadatas"] else {}
            distance = results["distances"][0][i] if results["distances"] else 0

            # Convert cosine distance to similarity score (0-1)
            score = 1 - distance

            search_results.append({
                "document_id": meta.get("document_id", ""),
                "filename": meta.get("filename", ""),
                "chunk_text": results["documents"][0][i],
                "page_number": meta.get("page_number", 0),
                "score": round(score, 4),
                "extraction_method": meta.get("extraction_method", ""),
                "entities": [],
            })

    return _enrich_with_entities(search_results)


def keyword_search(query: str, top_k: int = 10) -> list[dict]:
    """Perform keyword search using BM25."""
    collection = get_collection()

    # Get all documents from collection
    all_docs = collection.get(include=["documents", "metadatas"])

    if not all_docs["documents"]:
        return []

    # Tokenize documents for BM25
    tokenized_docs = [doc.lower().split() for doc in all_docs["documents"]]
    bm25 = BM25Okapi(tokenized_docs)

    # Search
    tokenized_query = query.lower().split()
    scores = bm25.get_scores(tokenized_query)

    # Get top-k results
    top_indices = scores.argsort()[-top_k:][::-1]

    search_results = []
    for idx in top_indices:
        if scores[idx] > 0:
            meta = all_docs["metadatas"][idx] if all_docs["metadatas"] else {}
            search_results.append({
                "document_id": meta.get("document_id", ""),
                "filename": meta.get("filename", ""),
                "chunk_text": all_docs["documents"][idx],
                "page_number": meta.get("page_number", 0),
                "score": round(float(scores[idx]), 4),
                "extraction_method": meta.get("extraction_method", ""),
                "entities": [],
            })

    return _enrich_with_entities(search_results)


def hybrid_search(query: str, top_k: int = 10, semantic_weight: float = 0.7) -> list[dict]:
    """
    Combine semantic and keyword search with weighted scoring.
    semantic_weight: 0.0 = pure keyword, 1.0 = pure semantic.
    """
    semantic_results = semantic_search(query, top_k=top_k * 2)
    keyword_results = keyword_search(query, top_k=top_k * 2)

    # Merge results by chunk text (deduplicate)
    combined = {}

    for result in semantic_results:
        key = result["chunk_text"][:100]
        combined[key] = {
            **result,
            "score": result["score"] * semantic_weight,
        }

    for result in keyword_results:
        key = result["chunk_text"][:100]
        if key in combined:
            combined[key]["score"] += result["score"] * (1 - semantic_weight)
        else:
            combined[key] = {
                **result,
                "score": result["score"] * (1 - semantic_weight),
            }

    # Sort by combined score
    results = sorted(combined.values(), key=lambda x: x["score"], reverse=True)
    return results[:top_k]
