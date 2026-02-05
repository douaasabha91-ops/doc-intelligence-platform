"""
RAG Chatbot endpoints (Optional feature).
"""

from fastapi import APIRouter

from app.models.schemas import ChatRequest, ChatResponse, SearchResult
from app.services.chat_service import chat_with_documents

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/", response_model=ChatResponse)
async def ask_question(request: ChatRequest):
    """Ask a question and get an answer grounded in uploaded documents."""
    result = chat_with_documents(request.question, top_k=request.top_k)

    return ChatResponse(
        answer=result["answer"],
        sources=[SearchResult(**s) for s in result["sources"]],
    )
