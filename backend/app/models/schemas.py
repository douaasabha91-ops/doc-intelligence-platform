from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# ── Document Models ──

class TextBlock(BaseModel):
    """A text block with layout position from PyMuPDF dict extraction."""
    block_index: int
    type: str                    # "text" or "image"
    bbox: list[float]            # [x0, y0, x1, y1] position on page
    lines: list[dict] = []       # [{text, bbox, font_size}, ...]


class PageExtractionDetail(BaseModel):
    """Per-page extraction info showing both methods."""
    page: int
    primary_method: str          # "digital" or "ocr"
    has_digital: bool
    has_ocr: bool
    digital_preview: str = ""
    ocr_preview: str = ""
    block_count: int = 0         # Number of text blocks (layout info)
    preprocessing_steps: Optional[dict] = None  # Base64 thumbnails of each step


class DocumentUploadResponse(BaseModel):
    id: str
    filename: str
    page_count: int
    total_chunks: int
    status: str
    extracted_text_preview: str
    entities: list[dict] = []
    extraction_details: list[PageExtractionDetail] = []
    message: str


class DocumentInfo(BaseModel):
    id: str
    filename: str
    page_count: int
    upload_date: str
    chunk_count: int


# ── Search Models ──

class SearchRequest(BaseModel):
    query: str
    search_type: str = "semantic"   # "semantic", "keyword", "hybrid"
    top_k: int = 10


class SearchResult(BaseModel):
    document_id: str
    filename: str
    chunk_text: str
    page_number: int
    score: float
    extraction_method: str = ""     # "digital" or "ocr"
    entities: list[dict] = []


class SearchResponse(BaseModel):
    query: str
    search_type: str
    results: list[SearchResult]
    total_results: int


# ── NER Models ──

class Entity(BaseModel):
    text: str
    label: str       # PERSON, ORG, DATE, GPE, etc.
    start: int
    end: int


# ── Chat Models (RAG with Ollama) ──

class ChatRequest(BaseModel):
    question: str
    top_k: int = 20  # Also changed from 5 to 20 to match your frontend
    document_id: Optional[str] = None  # ADD THIS LINE


class ChatResponse(BaseModel):
    answer: str
    sources: list[SearchResult]
