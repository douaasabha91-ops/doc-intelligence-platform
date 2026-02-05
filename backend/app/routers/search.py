"""
Search endpoints: semantic, keyword, and hybrid search.
"""

from fastapi import APIRouter

from app.models.schemas import SearchRequest, SearchResponse, SearchResult
from app.services.search_service import semantic_search, keyword_search, hybrid_search

router = APIRouter(prefix="/search", tags=["Search"])


@router.post("/", response_model=SearchResponse)
async def search_documents(request: SearchRequest):
    """Search across all documents using semantic, keyword, or hybrid search."""

    if request.search_type == "semantic":
        results = semantic_search(request.query, top_k=request.top_k)
    elif request.search_type == "keyword":
        results = keyword_search(request.query, top_k=request.top_k)
    elif request.search_type == "hybrid":
        results = hybrid_search(request.query, top_k=request.top_k)
    else:
        results = semantic_search(request.query, top_k=request.top_k)

    return SearchResponse(
        query=request.query,
        search_type=request.search_type,
        results=[SearchResult(**r) for r in results],
        total_results=len(results),
    )
