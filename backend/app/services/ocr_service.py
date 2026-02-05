"""
OCR service: Extracts text from documents (PDFs and images).

Supports two input types:
  - PDF files  → PyMuPDF digital extraction + OCR fallback
  - Image files (.jpg, .png, .tiff, .bmp) → Full OCR pipeline (always)

OCR Pipeline (for images and scanned PDFs):
  1. Load image
  2. OpenCV preprocessing (grayscale → denoise → CLAHE → deskew → binarize)
  3. Tesseract OCR with layout-aware extraction
  4. Return text + preprocessing step thumbnails for visualization

For digital PDFs: PyMuPDF get_text("dict") preserves layout blocks with bounding boxes.
OCR is also run on the first N pages of digital PDFs for demo comparison purposes.
"""

import fitz  # PyMuPDF
import pytesseract
import numpy as np
import cv2
import base64
import io
from PIL import Image
from pathlib import Path

from app.services.preprocessing import (
    preprocess_image, pil_to_cv2, cv2_to_pil,
    to_grayscale, denoise, enhance_contrast, deskew, binarize,
)


# File type constants
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp", ".webp"}
PDF_EXTENSIONS = {".pdf"}
SUPPORTED_EXTENSIONS = IMAGE_EXTENSIONS | PDF_EXTENSIONS

# How many pages to force-OCR even on digital PDFs (for demo purposes)
DEMO_OCR_PAGES = 3


def is_image_file(file_path: str) -> bool:
    return Path(file_path).suffix.lower() in IMAGE_EXTENSIONS


def is_pdf_file(file_path: str) -> bool:
    return Path(file_path).suffix.lower() in PDF_EXTENSIONS


def is_supported_file(file_path: str) -> bool:
    return Path(file_path).suffix.lower() in SUPPORTED_EXTENSIONS


# ──────────────────────────────────────────────────────────────────
# Main entry point: handles both PDFs and images
# ──────────────────────────────────────────────────────────────────

def extract_text_from_file(file_path: str) -> list[dict]:
    """
    Extract text from any supported file (PDF or image).
    Dispatches to the appropriate handler.

    Returns list of page dicts (images always return 1 page):
      {
        page_number, text, method, ocr_text, digital_text,
        text_blocks, preprocessing_steps
      }
    """
    if is_image_file(file_path):
        return extract_text_from_image(file_path)
    elif is_pdf_file(file_path):
        return extract_text_from_pdf(file_path)
    else:
        raise ValueError(f"Unsupported file type: {Path(file_path).suffix}")


# ──────────────────────────────────────────────────────────────────
# Image extraction (JPG, PNG, TIFF, etc.)
# ──────────────────────────────────────────────────────────────────

def extract_text_from_image(image_path: str) -> list[dict]:
    """
    Extract text from an image file using the full OCR pipeline.
    Always runs: load → preprocess → Tesseract OCR.
    Also extracts layout blocks via Tesseract's bounding box data.

    Returns a single-element list (one "page") for consistency with PDF output.
    """
    # Load image
    img = Image.open(image_path).convert("RGB")
    cv2_img = pil_to_cv2(img)

    # Run OCR with preprocessing steps
    ocr_text, preprocessing_steps = ocr_image_with_steps(cv2_img)

    # Extract layout blocks via Tesseract's bounding box output
    text_blocks = extract_layout_from_image(cv2_img)

    return [{
        "page_number": 1,
        "text": ocr_text,
        "method": "ocr",
        "ocr_text": ocr_text,
        "digital_text": None,
        "text_blocks": text_blocks,
        "preprocessing_steps": preprocessing_steps,
    }]


def extract_layout_from_image(cv2_img: np.ndarray) -> list[dict]:
    """
    Extract layout blocks from an image using Tesseract's bounding box data.
    Groups text by block_num to preserve spatial layout.
    """
    # Preprocess for better Tesseract results
    processed = preprocess_image(cv2_img.copy())
    processed_pil = cv2_to_pil(processed)

    try:
        data = pytesseract.image_to_data(
            processed_pil, lang="eng", output_type=pytesseract.Output.DICT
        )
    except Exception:
        return []

    # Group words by block number
    blocks_map = {}
    n = len(data["text"])
    for i in range(n):
        text = data["text"][i].strip()
        conf = int(data["conf"][i]) if data["conf"][i] != "-1" else -1
        if not text or conf < 30:
            continue

        block_num = data["block_num"][i]
        if block_num not in blocks_map:
            blocks_map[block_num] = {
                "words": [],
                "x0": data["left"][i],
                "y0": data["top"][i],
                "x1": data["left"][i] + data["width"][i],
                "y1": data["top"][i] + data["height"][i],
            }

        block = blocks_map[block_num]
        block["words"].append(text)
        block["x0"] = min(block["x0"], data["left"][i])
        block["y0"] = min(block["y0"], data["top"][i])
        block["x1"] = max(block["x1"], data["left"][i] + data["width"][i])
        block["y1"] = max(block["y1"], data["top"][i] + data["height"][i])

    text_blocks = []
    for block_num, block in sorted(blocks_map.items()):
        block_text = " ".join(block["words"])
        if block_text.strip():
            text_blocks.append({
                "block_index": block_num,
                "type": "text",
                "bbox": [block["x0"], block["y0"], block["x1"], block["y1"]],
                "lines": [{"text": block_text, "bbox": [block["x0"], block["y0"], block["x1"], block["y1"]], "font_size": 0}],
            })

    return text_blocks


# ──────────────────────────────────────────────────────────────────
# PDF extraction
# ──────────────────────────────────────────────────────────────────

def extract_text_from_pdf(pdf_path: str, force_ocr_pages: int = DEMO_OCR_PAGES) -> list[dict]:
    """
    Extract text from PDF, page by page.

    Digital PDFs: PyMuPDF text + layout blocks. OCR also run on first N pages for demo.
    Scanned PDFs: Full OCR pipeline as primary extraction.
    """
    doc = fitz.open(pdf_path)
    pages = []

    for page_num in range(len(doc)):
        page = doc[page_num]

        # Step 1: Try digital extraction with layout
        digital_text, text_blocks = extract_page_with_layout(page)
        has_text_layer = len(digital_text) > 50

        # Step 2: Decide whether to run OCR
        should_ocr = (not has_text_layer) or (page_num < force_ocr_pages)

        ocr_text = None
        preprocessing_steps = None
        if should_ocr:
            ocr_text, preprocessing_steps = ocr_pdf_page_with_steps(page)

        # Step 3: Pick primary text
        if has_text_layer:
            primary_text = digital_text
            method = "digital"
        else:
            primary_text = ocr_text or ""
            method = "ocr"

        pages.append({
            "page_number": page_num + 1,
            "text": primary_text,
            "method": method,
            "ocr_text": ocr_text,
            "digital_text": digital_text if has_text_layer else None,
            "text_blocks": text_blocks if has_text_layer else None,
            "preprocessing_steps": preprocessing_steps,
        })

    doc.close()
    return pages


def extract_page_with_layout(page: fitz.Page) -> tuple[str, list[dict]]:
    """
    Extract text from a PDF page preserving layout structure.
    Uses PyMuPDF's dict extraction for text blocks with bounding boxes.
    """
    page_dict = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)
    blocks = page_dict.get("blocks", [])

    text_blocks = []
    plain_parts = []

    for i, block in enumerate(blocks):
        block_type = "image" if block.get("type") == 1 else "text"
        bbox = list(block.get("bbox", [0, 0, 0, 0]))

        if block_type == "text":
            lines_data = []
            for line in block.get("lines", []):
                line_text_parts = []
                font_sizes = []
                for span in line.get("spans", []):
                    line_text_parts.append(span.get("text", ""))
                    font_sizes.append(span.get("size", 0))

                line_text = "".join(line_text_parts).strip()
                if line_text:
                    avg_font = sum(font_sizes) / len(font_sizes) if font_sizes else 0
                    lines_data.append({
                        "text": line_text,
                        "bbox": list(line.get("bbox", [0, 0, 0, 0])),
                        "font_size": round(avg_font, 1),
                    })
                    plain_parts.append(line_text)

            if lines_data:
                text_blocks.append({
                    "block_index": i,
                    "type": block_type,
                    "bbox": [round(b, 1) for b in bbox],
                    "lines": lines_data,
                })
        else:
            text_blocks.append({
                "block_index": i,
                "type": "image",
                "bbox": [round(b, 1) for b in bbox],
                "lines": [],
            })

    plain_text = "\n".join(plain_parts)
    return plain_text, text_blocks


# ──────────────────────────────────────────────────────────────────
# OCR with preprocessing step capture
# ──────────────────────────────────────────────────────────────────

def ocr_image_with_steps(cv2_img: np.ndarray) -> tuple[str, dict]:
    """
    Run OCR on a CV2 image with full preprocessing pipeline.
    Returns (ocr_text, preprocessing_steps_as_base64_thumbnails).
    """
    steps = {}
    steps["original"] = _img_to_base64_thumb(cv2_img, max_width=400)

    gray = to_grayscale(cv2_img)
    steps["grayscale"] = _img_to_base64_thumb(gray, max_width=400)

    denoised_img = denoise(gray)
    steps["denoised"] = _img_to_base64_thumb(denoised_img, max_width=400)

    contrast = enhance_contrast(denoised_img)
    steps["contrast_enhanced"] = _img_to_base64_thumb(contrast, max_width=400)

    deskewed = deskew(contrast)
    steps["deskewed"] = _img_to_base64_thumb(deskewed, max_width=400)

    binarized = binarize(deskewed)
    steps["binarized"] = _img_to_base64_thumb(binarized, max_width=400)

    # Final OCR
    processed_pil = cv2_to_pil(binarized)
    text = pytesseract.image_to_string(processed_pil, lang="eng")

    return text.strip(), steps


def ocr_pdf_page_with_steps(page: fitz.Page, dpi: int = 300) -> tuple[str, dict]:
    """OCR a PDF page by rendering to image first, then running the full pipeline."""
    pix = page.get_pixmap(dpi=dpi)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    cv2_img = pil_to_cv2(img)
    return ocr_image_with_steps(cv2_img)


# ──────────────────────────────────────────────────────────────────
# Utilities
# ──────────────────────────────────────────────────────────────────

def _img_to_base64_thumb(img: np.ndarray, max_width: int = 400) -> str:
    """Convert a CV2 image to a small base64 JPEG thumbnail."""
    pil_img = cv2_to_pil(img)
    w, h = pil_img.size
    if w > max_width:
        ratio = max_width / w
        pil_img = pil_img.resize((max_width, int(h * ratio)), Image.LANCZOS)

    buffer = io.BytesIO()
    pil_img.save(buffer, format="JPEG", quality=60)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def get_file_metadata(file_path: str) -> dict:
    """Extract metadata from any supported file."""
    path = Path(file_path)

    if is_pdf_file(file_path):
        doc = fitz.open(file_path)
        metadata = {
            "filename": path.name,
            "page_count": len(doc),
            "file_type": "pdf",
            "metadata": doc.metadata,
        }
        doc.close()
    else:
        # Image file — always 1 page
        img = Image.open(file_path)
        metadata = {
            "filename": path.name,
            "page_count": 1,
            "file_type": "image",
            "metadata": {
                "format": img.format,
                "size": f"{img.width}x{img.height}",
                "mode": img.mode,
            },
        }
        img.close()

    return metadata


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """
    Split text into overlapping chunks for embedding.
    Uses sentence-aware splitting to avoid cutting mid-sentence.
    """
    if not text:
        return []

    sentences = text.replace("\n", " ").split(". ")
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            words = current_chunk.split()
            overlap_text = " ".join(words[-overlap // 5:]) if len(words) > overlap // 5 else ""
            current_chunk = overlap_text + " " + sentence + ". "
        else:
            current_chunk += sentence + ". "

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks
