# 📄 Document Intelligence & Semantic Search Platform

*Inspired by IntelArchive*

A system capable of ingesting **scanned document images and PDFs**, extracting structured information using OCR with image enhancement, and enabling semantic search and question answering over the document collection.

> **100% Free & Open Source** — No paid APIs, no subscriptions, no cloud dependencies. Everything runs locally.

---

## 🏗️ System Architecture

```
                          ┌──────────────────────────────┐
                          │       React Frontend          │
                          │  Upload · Search · Chat UI    │
                          └──────────────┬───────────────┘
                                         │ REST API
                          ┌──────────────▼───────────────┐
                          │       FastAPI Backend          │
                          │  /api/documents · /api/search  │
                          │  /api/chat                     │
                          └──────────────┬───────────────┘
                                         │
          ┌──────────────────────────────┼──────────────────────────────┐
          ▼                              ▼                              ▼
 ┌─────────────────┐          ┌─────────────────┐           ┌─────────────────┐
 │  Document Input  │          │  AI / ML Models  │           │    Storage       │
 │                  │          │                  │           │                  │
 │  JPG/PNG/TIFF ──┐│          │  Tesseract OCR   │           │  ChromaDB        │
 │  PDF ───────────┘│          │  spaCy NER       │           │  (vector store)  │
 │                  │          │  sentence-trans.  │           │                  │
 └────────┬────────┘          │  Ollama LLM      │           └────────┬────────┘
          │                   └────────┬─────────┘                    │
          ▼                            ▼                              ▼
 ┌──────────────────────────────────────────────────────────────────────────┐
 │                        Processing Pipeline                               │
 │                                                                          │
 │  1. Image Enhancement (OpenCV)                                           │
 │     grayscale → denoise → CLAHE contrast → deskew → adaptive binarize   │
 │                                                                          │
 │  2. OCR + Layout Extraction                                              │
 │     Tesseract OCR with bounding-box layout blocks (images)               │
 │     PyMuPDF dict extraction with text blocks + font sizes (PDFs)         │
 │                                                                          │
 │  3. Named Entity Recognition (spaCy)                                     │
 │     PERSON · ORG · DATE · GPE · MONEY                                    │
 │                                                                          │
 │  4. Text Chunking → Embedding → Vector Storage                           │
 │     sentence-aware splits → all-MiniLM-L6-v2 → ChromaDB                 │
 │                                                                          │
 │  5. Search Engine                                                        │
 │     Semantic (cosine) · Keyword (BM25) · Hybrid (weighted merge)        │
 │                                                                          │
 │  6. RAG Chatbot                                                          │
 │     retrieve top-k → assemble context → Ollama LLM → grounded answer   │
 └──────────────────────────────────────────────────────────────────────────┘
```

### Design Decisions

- **OCR-first architecture**: Since our primary data is scanned invoice images (`.jpg`), every document passes through the full image preprocessing → Tesseract pipeline. For PDFs with embedded text, digital extraction is used as primary with OCR comparison available for demo.
- **Preprocessing visualization**: Each OCR step (original → grayscale → denoised → contrast → deskewed → binarized) is captured as a base64 thumbnail and returned to the frontend, so the evaluator can visually inspect the image enhancement pipeline.
- **Layout preservation**: For images, Tesseract's `image_to_data()` groups words by block number with bounding boxes. For PDFs, PyMuPDF's dict mode extracts text blocks with coordinates and font sizes.
- **Hybrid search**: Combining semantic similarity (captures meaning) with BM25 keyword search (captures exact terms) gives more robust results than either alone, weighted 70/30.

---

## 📦 Tech Stack (All Free & Open Source)

| Layer               | Technology                                 | Purpose                                   | License    | Cost |
|---------------------|--------------------------------------------|-------------------------------------------|------------|------|
| Frontend            | React 18 + Tailwind CSS                    | Upload UI, search, chat interface          | MIT        | Free |
| Backend API         | Python 3.11 + FastAPI                      | REST endpoints, pipeline orchestration     | MIT        | Free |
| Image Preprocessing | OpenCV (`cv2`) + Pillow                    | Denoise, CLAHE, deskew, binarize          | Apache 2.0 | Free |
| OCR Engine          | Tesseract OCR (`pytesseract`)              | Text extraction from images                | Apache 2.0 | Free |
| PDF Parsing         | PyMuPDF (`fitz`)                           | Digital text + layout from PDFs            | AGPL-3.0   | Free |
| NER                 | spaCy (`en_core_web_sm`)                   | Named entity recognition                   | MIT        | Free |
| Embeddings          | sentence-transformers (`all-MiniLM-L6-v2`) | 384-dim text vectors                       | Apache 2.0 | Free |
| Vector Database     | ChromaDB                                   | Persistent vector storage + cosine search  | Apache 2.0 | Free |
| Keyword Search      | rank_bm25                                  | BM25Okapi scoring for keyword search       | Apache 2.0 | Free |
| Chatbot LLM         | Ollama + Mistral 7B                        | Local LLM for RAG Q&A                     | MIT / Apache | Free |
| Containerization    | Docker + Docker Compose                    | Reproducible deployment                    | Apache 2.0 | Free |

### Why These Choices?

| Decision | Reasoning |
|----------|-----------|
| **Tesseract** over cloud OCR | Free, offline, Apache-licensed, most mature open-source OCR engine |
| **OpenCV preprocessing** | Significantly improves OCR accuracy on noisy/skewed scans (demonstrated with before/after in UI) |
| **ChromaDB** over Pinecone/Weaviate | Zero-config, embedded Python, persistent, perfect for prototypes |
| **all-MiniLM-L6-v2** over larger models | 5x faster than `mpnet-base`, 384-dim is sufficient for document search at this scale |
| **Ollama** over OpenAI API | 100% free, 100% local, no API keys, data never leaves the machine |
| **BM25 + semantic hybrid** | BM25 catches exact terms (invoice numbers, names); semantic catches meaning ("payment documents") |

---

## 📚 Data Sources

### Primary: Invoice Image Dataset (Google Drive)

Our demo data consists of **scanned invoice images (`.jpg`)** from a shared Google Drive folder. These are ideal because:
- Every image **must** go through the full OCR pipeline (no digital text layer to shortcut)
- Invoices contain **rich structured entities**: seller/client names, addresses, dates, tax IDs, monetary amounts
- Table layouts test Tesseract's ability to handle structured data
- Real-world use case that evaluators can relate to

### Additional Free Data Sources

| Source | Type | Format | License |
|--------|------|--------|---------|
| [arXiv Open Access](https://arxiv.org/) | Research papers | PDF | CC-BY / arXiv non-exclusive |
| [PubMed Central](https://pmc.ncbi.nlm.nih.gov/tools/openftlist/) | Biomedical papers | PDF | CC licenses |
| [Sample PDF Invoices (GitHub)](https://github.com/femstac/Sample-Pdf-invoices) | Business invoices | PDF | Public |
| [Mendeley Invoice Dataset](https://data.mendeley.com/datasets/tnj49gpmtz/2) | 1000 invoices | PDF | CC BY 4.0 |
| [OCR Document Dataset (HuggingFace)](https://huggingface.co/datasets/TrainingDataPro/ocr-text-detection-in-the-documents) | Mixed documents | Image | CC BY-NC-ND 4.0 |
| [US Gov Reports](https://www.govinfo.gov/) | Government docs | PDF | Public domain |

---

## 🚀 Quick Start

### Prerequisites

```bash
# Python 3.11+
python --version

# Node.js 18+
node --version

# Tesseract OCR
# sudo apt install tesseract-ocr              # Ubuntu/Debian
# brew install tesseract                     # macOS
choco install tesseract                    # Windows

# Ollama (for RAG chatbot)
curl -fsSL https://ollama.com/install.sh | sh
ollama pull mistral                          # ~4.1GB download
```

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # macOS: source venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

API docs available at: `http://localhost:8000/docs`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

UI available at: `http://localhost:5173`

### Ollama (separate terminal)

```bash
ollama serve      # Starts at http://localhost:11434
```

---

## 📁 Project Structure

```
doc-intelligence-platform/
├── README.md
├── .gitignore
├── docker-compose.yml
│
├── backend/
│   ├── .env.example
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py                    # FastAPI entry point + CORS
│   │   ├── core/
│   │   │   └── config.py              # Pydantic settings (models, paths, chunk size)
│   │   ├── models/
│   │   │   └── schemas.py             # Request/response Pydantic models
│   │   ├── routers/
│   │   │   ├── documents.py           # POST /upload (PDF+images), GET /, DELETE /{id}
│   │   │   ├── search.py              # POST /search (semantic/keyword/hybrid)
│   │   │   └── chat.py                # POST /chat (RAG Q&A with Ollama)
│   │   └── services/
│   │       ├── preprocessing.py       # OpenCV pipeline: grayscale→denoise→CLAHE→deskew→binarize
│   │       ├── ocr_service.py         # Image OCR + PDF extraction + layout blocks + chunk_text
│   │       ├── ner_service.py         # spaCy NER: PERSON, ORG, DATE, GPE, MONEY
│   │       ├── embedding_service.py   # sentence-transformers (all-MiniLM-L6-v2)
│   │       ├── vector_store.py        # ChromaDB persistent client + CRUD
│   │       ├── search_service.py      # Semantic + BM25 keyword + hybrid merge
│   │       └── chat_service.py        # RAG: search → context → Ollama → grounded answer
│   └── data/
│       ├── uploads/                   # Uploaded files stored here
│       └── chroma_db/                 # ChromaDB persistent storage
│
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── index.html
│   └── src/
│       ├── App.jsx                    # React Router + navigation bar
│       ├── main.jsx                   # Entry point
│       ├── index.css                  # Tailwind imports
│       ├── pages/
│       │   ├── UploadPage.jsx         # Drag-drop upload + results + preprocessing visualization
│       │   ├── SearchPage.jsx         # Search bar + type selector + chat mode toggle
│       │   └── DocumentView.jsx       # Single document detail view
│       └── services/
│           └── api.js                 # Axios client for all API endpoints
```

### Supported Input Formats

| Format | Extension(s) | Processing |
|--------|-------------|------------|
| PDF (digital) | `.pdf` | PyMuPDF text + layout extraction (OCR also run on first 3 pages for comparison) |
| PDF (scanned) | `.pdf` | Full OCR pipeline (automatic when digital text < 50 chars) |
| JPEG | `.jpg`, `.jpeg` | Full OCR pipeline (always) |
| PNG | `.png` | Full OCR pipeline (always) |
| TIFF | `.tiff`, `.tif` | Full OCR pipeline (always) |
| BMP | `.bmp` | Full OCR pipeline (always) |
| WebP | `.webp` | Full OCR pipeline (always) |

---

## 🗺️ ROADMAP — 6-Day Implementation Plan

---

### 📅 Day 1 — Project Setup + Document Ingestion

**Goal:** Backend running, React shell ready, files uploading and basic text extracting.

| Time | Task | Details |
|------|------|---------|
| 1.0h | Environment setup | Create venv, `pip install -r requirements.txt`, verify Tesseract installed (`tesseract --version`), `npm install` frontend |
| 0.5h | Prepare test data | Copy 10-15 invoice `.jpg` files from Google Drive into `data/uploads/` for testing |
| 1.0h | FastAPI scaffold | Run `main.py`, verify `/docs` Swagger UI, test CORS with React dev server |
| 1.5h | File upload endpoint | `POST /api/documents/upload` — accept PDF and images, save file, validate extension, return metadata |
| 1.0h | Basic OCR | Load image with Pillow → `pytesseract.image_to_string()` → return extracted text |
| 0.5h | React upload page | Wire `UploadPage.jsx` to upload endpoint with react-dropzone, show filename + text preview |
| 0.5h | Test end-to-end | Upload 2-3 invoice JPGs, verify text shows up in browser |

**✅ Day 1 Deliverable:** Upload an invoice image → see OCR-extracted text in the browser.

---

### 📅 Day 2 — Image Enhancement + Layout Extraction

**Goal:** Full OpenCV preprocessing pipeline improving OCR quality, layout blocks preserved.

| Time | Task | Details |
|------|------|---------|
| 1.5h | OpenCV preprocessing | `preprocessing.py` — implement grayscale → non-local means denoise → CLAHE contrast → deskew → adaptive binarize |
| 0.5h | Preprocessing visualization | Capture base64 thumbnail of each step, return in API response for UI display |
| 1.0h | Tesseract with preprocessing | Wire preprocessed image into `image_to_string()`, compare OCR quality before/after |
| 0.5h | Layout extraction | Use `image_to_data()` to get word bounding boxes, group by block_num to form text blocks |
| 0.5h | PDF support | Add PyMuPDF path: `get_text("dict")` for digital PDFs with block/line/span layout |
| 1.0h | Text chunking | `chunk_text()` — sentence-aware splitting, 500 chars, 50 char overlap |
| 0.5h | UI: preprocessing pipeline | Show 3×2 grid of preprocessing step images per page in upload results |
| 0.5h | Test + compare | Upload invoice JPGs, expand preprocessing view, verify quality improvement |

**✅ Day 2 Deliverable:** Upload image → see preprocessing pipeline visually → improved OCR text + layout blocks.

---

### 📅 Day 3 — Embeddings + Vector Database Storage

**Goal:** All text chunks stored as searchable vectors in ChromaDB.

| Time | Task | Details |
|------|------|---------|
| 0.5h | Test sentence-transformers | Load `all-MiniLM-L6-v2`, verify 384-dim embeddings generate correctly |
| 1.0h | Embedding service | `embedding_service.py` — lazy model loading, batch + single embedding generation |
| 1.0h | ChromaDB vector store | `vector_store.py` — PersistentClient, add/query/delete, cosine distance |
| 1.0h | Wire into upload | After chunking → generate embeddings → store with metadata (doc_id, filename, page, method, date) |
| 0.5h | Stats endpoint | `GET /api/documents/stats` — total chunks + total documents |
| 0.5h | List + delete endpoints | `GET /api/documents/` and `DELETE /api/documents/{id}` |
| 1.0h | Test persistence | Upload 10+ invoice images, restart server, verify data survives |
| 0.5h | UI: document list | Show uploaded docs with chunk counts on UploadPage |

**✅ Day 3 Deliverable:** Invoices auto-embedded and stored — data persists across restarts.

---

### 📅 Day 4 — Search Engine (Semantic + Keyword + Hybrid)

**Goal:** 3 working search modes with ranked results in the UI.

| Time | Task | Details |
|------|------|---------|
| 1.5h | Semantic search | Embed query → `collection.query()` → cosine similarity → top-k results |
| 1.0h | Keyword search (BM25) | Load all docs → tokenize → `BM25Okapi` → score + rank |
| 1.0h | Hybrid search | Weighted merge (70% semantic + 30% keyword), deduplicate by chunk prefix, sort |
| 0.5h | Search router | `POST /api/search/` — accept query + search_type + top_k |
| 1.0h | Search UI | SearchPage with search bar, type dropdown (semantic/keyword/hybrid), result cards |
| 0.5h | Enrich results | Run NER on returned snippets, show extraction_method badge (digital/ocr) per result |
| 0.5h | Test all 3 modes | Search "Garrett Gonzales" (keyword), "wine purchase invoice" (semantic), compare |

**✅ Day 4 Deliverable:** Type a query → get ranked results with scores, entities, and source info.

---

### 📅 Day 5 — NER + RAG Chatbot with Ollama

**Goal:** Entity extraction on upload + conversational Q&A grounded in documents.

| Time | Task | Details |
|------|------|---------|
| 0.5h | spaCy NER setup | `python -m spacy download en_core_web_sm`, test on invoice text |
| 1.0h | NER service | `ner_service.py` — extract PERSON, ORG, DATE, GPE, MONEY + deduplicate + group by type |
| 0.5h | Wire into upload | Run NER on first 10K chars of extracted text, return grouped entities |
| 0.5h | Wire into search | Run NER on each search result snippet, display entity tags on result cards |
| 0.5h | UI: entity display | Expandable entity list with colored labels in upload results |
| 0.5h | Ollama setup | `ollama pull mistral`, verify `curl localhost:11434/api/tags` |
| 1.5h | RAG chatbot service | `chat_service.py` — semantic search top-5 → context assembly → Ollama → answer + source citations |
| 0.5h | Chat router | `POST /api/chat/` |
| 1.0h | Chat UI | Chat mode toggle on SearchPage — message bubbles, source file + page references |

**✅ Day 5 Deliverable:** Entities extracted from invoices + ask "What did Garrett Gonzales sell?" → grounded answer.

---

### 📅 Day 6 — Polish + Presentation + Demo Rehearsal

**Goal:** Stable demo, clean slides, confident delivery.

| Time | Task | Details |
|------|------|---------|
| 1.0h | Bug fixes | Handle: corrupt images, large files, empty OCR, special chars, timeout errors |
| 0.5h | Error handling UI | Loading spinners, error toasts, empty state messages |
| 0.5h | Pre-load demo data | Upload all invoice images, verify ChromaDB populated, test searches |
| 1.0h | Write demo script | Exact steps: (1) upload invoice JPGs, (2) show preprocessing pipeline + text + entities, (3) run 3 search types, (4) chatbot Q&A |
| 2.0h | Build presentation | Architecture diagram, tech justification with tradeoff analysis, pipeline flow with screenshots, limitations slide |
| 1.0h | Demo rehearsal | Run through 2-3 times end-to-end, time each section, prepare backup screenshots |
| 0.5h | Prepare Q&A answers | Why ChromaDB? Why Tesseract? OCR vs cloud APIs? How to scale? What are failure cases? |

**✅ Day 6 Deliverable:** Polished demo + slides ready + answers to expected questions.

---

## 📊 Effort Summary

| Day | Focus | Hours | Deliverable |
|-----|-------|-------|-------------|
| 1 | Setup + Document Ingestion | ~6h | Upload image → see OCR text |
| 2 | Image Enhancement + Layout | ~6h | Preprocessing pipeline visible in UI |
| 3 | Embeddings + Vector DB | ~6h | Chunks stored in ChromaDB |
| 4 | Search Engine | ~6h | 3 search modes with NER + method badges |
| 5 | NER + RAG Chatbot | ~6h | Entities + Ollama-powered Q&A |
| 6 | Polish + Presentation | ~6h | Stable demo + slides |
| **Total** | | **~36h** | **Complete working prototype** |

---

## 🎯 Demo Script (10-15 minutes)

### Step 1: Document Upload (3 min)
1. Open the app at `http://localhost:5173`
2. Drag-drop 3-5 invoice `.jpg` files into the upload area
3. **Show:** Processing status → "[IMAGE] Processed 1 page → N chunks embedded"
4. **Expand:** "View extracted text preview" → show OCR-extracted invoice content
5. **Expand:** "Named entities" → show PERSON, ORG, DATE, GPE, MONEY extracted
6. **Expand:** "Extraction details per page" → show method badge ("OCR"), block count
7. **Expand:** "View image preprocessing pipeline" → **show 6-step grid**: original → grayscale → denoised → contrast enhanced → deskewed → binarized

### Step 2: Search (3 min)
8. Navigate to **Search** tab
9. **Semantic search:** "wine purchase" → results ranked by meaning similarity
10. **Keyword search:** "Garrett Gonzales" → results with exact name match
11. **Hybrid search:** "invoice from Connecticut" → combines both approaches
12. **Point out:** Score values, extraction method badge, entity tags on results

### Step 3: Chatbot (3 min)
13. Toggle **Chat Mode ON**
14. Ask: "What items were purchased in the Garrett Gonzales invoice?"
15. **Show:** Grounded answer with source citations (filename, page, score)
16. Ask: "Which invoices have the highest total amount?"
17. **Show:** Answer references specific documents

### Step 4: Architecture (2 min)
18. Show architecture slide with pipeline flow
19. Explain technology choices with tradeoff reasoning
20. Discuss limitations honestly

---

## ⚠️ Known Limitations (Discuss in Presentation)

| # | Limitation | Impact | Possible Improvement |
|---|-----------|--------|---------------------|
| 1 | **Tesseract OCR accuracy** | Struggles with complex table layouts, handwriting, very low-res scans | Use EasyOCR or PaddleOCR; combine multiple engines |
| 2 | **Fixed-size chunking** | May split mid-sentence or mid-table row | Use semantic chunking based on paragraph/section boundaries |
| 3 | **Embedding model size** | `all-MiniLM-L6-v2` (384-dim) trades quality for speed | Upgrade to `all-mpnet-base-v2` (768-dim) for better retrieval |
| 4 | **Single-node ChromaDB** | Not suitable for millions of documents | Migrate to Qdrant, Milvus, or Weaviate for distributed search |
| 5 | **RAG hallucination** | Local LLMs may fabricate information despite grounding | Add confidence scoring, enforce stricter prompts, use larger models |
| 6 | **No authentication** | Prototype has no access control | Add JWT auth or integrate with OAuth provider |
| 7 | **English only** | OCR and NER configured for English | Add `lang` parameter for Tesseract, use multilingual spaCy/NER model |
| 8 | **Image-only = 1 page** | Each `.jpg` is treated as 1 page; no multi-page image support | Support multi-page TIFF or batch upload grouping |

---

## 🔧 Ollama Setup Guide

### Installation

```bash
# Linux
curl -fsSL https://ollama.com/install.sh | sh

# macOS
brew install ollama

# Windows — download from https://ollama.com/download
```

### Recommended Models

| RAM Available | Model | Command | Size |
|---------------|-------|---------|------|
| 4GB | Phi-3 Mini 3.8B | `ollama pull phi3:mini` | ~2.3GB |
| 8GB+ | Mistral 7B ⭐ | `ollama pull mistral` | ~4.1GB |
| 16GB+ | Llama 3 8B | `ollama pull llama3` | ~4.7GB |

### Verify Setup

```bash
# Start Ollama server
ollama serve

# In another terminal:
curl http://localhost:11434/api/tags    # Should return model list

# Test a completion:
curl http://localhost:11434/api/chat -d '{
  "model": "mistral",
  "messages": [{"role": "user", "content": "Hello!"}],
  "stream": false
}'
```

### Configuration

Edit `backend/.env` to change the model:

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral
```

---

## 🔬 Technical Explanations (For Q&A)

### How does the image preprocessing pipeline work?

Each image passes through 5 OpenCV transformations before OCR:

1. **Grayscale** (`cvtColor`) — Reduces 3-channel RGB to 1-channel, removing color noise
2. **Denoising** (`fastNlMeansDenoising`) — Non-local means algorithm removes salt-and-pepper noise while preserving edges
3. **CLAHE** (`createCLAHE`) — Contrast Limited Adaptive Histogram Equalization enhances local contrast without over-amplifying noise
4. **Deskew** (`minAreaRect + warpAffine`) — Detects rotation angle from text coordinates and corrects skew up to ±15°
5. **Binarization** (`adaptiveThreshold`) — Adaptive Gaussian thresholding converts to pure black/white, handling uneven lighting

### How does RAG (Retrieval Augmented Generation) work?

1. User asks a question (e.g., "What did Garrett Gonzales sell?")
2. The question is embedded using `all-MiniLM-L6-v2` → 384-dim vector
3. ChromaDB finds the top-5 most similar document chunks (cosine similarity)
4. Those chunks are assembled into a context prompt with source labels
5. Ollama (Mistral 7B) generates an answer constrained to only cite the provided context
6. The answer is returned with source references (filename + page + similarity score)

### Why hybrid search instead of just semantic?

- **Semantic search** understands meaning: "payment document" matches "invoice" even without the exact word
- **Keyword search (BM25)** catches exact matches: searching "932-75-6582" (a tax ID) won't work semantically but BM25 finds it instantly
- **Hybrid (70/30)** combines both: semantic similarity drives relevance, keyword matching ensures precision on specific terms like names, dates, and IDs

### How are embeddings stored?

Each text chunk is stored in ChromaDB with:
- **Vector**: 384-dimensional float array from sentence-transformers
- **Document**: The raw chunk text
- **Metadata**: `document_id`, `filename`, `page_number`, `extraction_method`, `file_type`, `upload_date`

ChromaDB uses HNSW (Hierarchical Navigable Small World) indexing for approximate nearest neighbor search with cosine distance.
