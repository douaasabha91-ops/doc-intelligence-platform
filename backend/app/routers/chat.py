"""
RAG Chatbot endpoints (Optional feature).
"""

from fastapi import APIRouter

from app.models.schemas import ChatRequest, ChatResponse, SearchResult
from app.services.chat_service import chat_with_documents

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/", response_model=ChatResponse)
async def ask_question(request: ChatRequest):
    """
    Ask a question and get an answer grounded in uploaded documents.
    Optionally filter to a specific document by providing document_id.
    """
    result = chat_with_documents(
        request.question, 
        top_k=request.top_k,
        document_id=getattr(request, 'document_id', None)
    )

    # Filter sources by relevance score (only show sources with score > 0.3)
    # This ensures we only display truly relevant documents to the user
    RELEVANCE_THRESHOLD = 0.3
    filtered_sources = [s for s in result["sources"] if s.get("score", 0) > RELEVANCE_THRESHOLD]

    return ChatResponse(
        answer=result["answer"],
        sources=[SearchResult(**s) for s in filtered_sources],
    )