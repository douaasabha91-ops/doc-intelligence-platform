"""
Document management endpoints: upload, list, view, delete.
Accepts both PDF and image files (JPG, PNG, TIFF, BMP).
"""

import uuid
import shutil
from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, HTTPException

from app.core.config import settings
from app.models.schemas import DocumentUploadResponse, DocumentInfo, PageExtractionDetail
from app.services.ocr_service import (
    extract_text_from_file, get_file_metadata, chunk_text,
)
from app.services.embedding_service import generate_embeddings
from app.services.vector_store import add_document_chunks, get_all_documents, delete_document, get_collection_count
from app.services.ner_service import extract_entities_summary

router = APIRouter(prefix="/documents", tags=["Documents"])


ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp", ".webp"}


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a document (PDF or image) and run the full pipeline:
    1. Save file
    2. Extract text (digital for PDFs / full OCR for images)
    3. Image preprocessing (grayscale → denoise → CLAHE → deskew → binarize)
    4. Preserve layout info (text blocks with bounding boxes)
    5. Chunk text with sentence-aware overlap
    6. Generate sentence-transformer embeddings
    7. Store chunks + embeddings + metadata in ChromaDB
    8. Run spaCy NER to extract named entities

    Supported formats: PDF, JPG, JPEG, PNG, TIFF, BMP, WebP
    """

    # Validate file extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Accepted: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    # Save uploaded file
    doc_id = str(uuid.uuid4())[:8]
    upload_path = Path(settings.UPLOAD_DIR) / f"{doc_id}_{file.filename}"

    with open(upload_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        # 1. Extract text (auto-detects PDF vs image)
        pages = extract_text_from_file(str(upload_path))
        full_text = "\n\n".join([p["text"] for p in pages if p["text"]])
        file_meta = get_file_metadata(str(upload_path))

        # 2. Chunk text
        chunks = []
        chunk_metadatas = []
        for page_data in pages:
            page_chunks = chunk_text(
                page_data["text"],
                chunk_size=settings.CHUNK_SIZE,
                overlap=settings.CHUNK_OVERLAP,
            )
            for chunk in page_chunks:
                chunks.append(chunk)
                chunk_metadatas.append({
                    "document_id": doc_id,
                    "filename": file.filename,
                    "page_number": page_data["page_number"],
                    "page_count": file_meta["page_count"],
                    "extraction_method": page_data["method"],
                    "file_type": file_meta["file_type"],
                    "upload_date": datetime.now().isoformat(),
                })

        # 3. Generate embeddings + store in ChromaDB
        stored_count = 0
        if chunks:
            embeddings = generate_embeddings(chunks)
            stored_count = add_document_chunks(doc_id, chunks, embeddings, chunk_metadatas)

        # 4. Extract entities (NER)
        entities = []
        try:
            entity_summary = extract_entities_summary(full_text[:10000])
            entities = [{"label": k, "values": v} for k, v in entity_summary.items()]
        except Exception:
            pass

        # 5. Build per-page extraction details
        extraction_details = []
        for page_data in pages:
            text_blocks = page_data.get("text_blocks") or []
            detail = PageExtractionDetail(
                page=page_data["page_number"],
                primary_method=page_data["method"],
                has_digital=page_data.get("digital_text") is not None,
                has_ocr=page_data.get("ocr_text") is not None,
                digital_preview=(page_data.get("digital_text") or "")[:300],
                ocr_preview=(page_data.get("ocr_text") or "")[:300],
                block_count=len(text_blocks),
                preprocessing_steps=page_data.get("preprocessing_steps"),
            )
            extraction_details.append(detail)

        file_type_label = file_meta["file_type"].upper()
        return DocumentUploadResponse(
            id=doc_id,
            filename=file.filename,
            page_count=file_meta["page_count"],
            total_chunks=stored_count,
            status="processed",
            extracted_text_preview=full_text[:500] + "..." if len(full_text) > 500 else full_text,
            entities=entities,
            extraction_details=extraction_details,
            message=f"[{file_type_label}] Processed {file_meta['page_count']} page(s) → {stored_count} chunks embedded and stored.",
        )

    except Exception as e:
        upload_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.get("/", response_model=list[DocumentInfo])
async def list_documents():
    """List all uploaded documents."""
    docs = get_all_documents()
    return [
        DocumentInfo(
            id=d["id"],
            filename=d["filename"],
            page_count=d.get("page_count", 0),
            upload_date=d.get("upload_date", ""),
            chunk_count=0,
        )
        for d in docs
    ]


@router.get("/stats")
async def get_stats():
    """Get collection statistics."""
    return {
        "total_chunks": get_collection_count(),
        "total_documents": len(get_all_documents()),
    }


@router.delete("/{doc_id}")
async def remove_document(doc_id: str):
    """Delete a document and its chunks from the vector store."""
    delete_document(doc_id)
    return {"message": f"Document {doc_id} deleted."}
