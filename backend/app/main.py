"""
Document Intelligence & Semantic Search Platform
Main FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import documents, search, chat
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered document ingestion, OCR, semantic search, and Q&A platform.",
    version="1.0.0",
)

# CORS - allow React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(documents.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(chat.router, prefix="/api")


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "upload": "POST /api/documents/upload",
            "list_docs": "GET /api/documents/",
            "search": "POST /api/search/",
            "chat": "POST /api/chat/",
            "stats": "GET /api/documents/stats",
        },
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
