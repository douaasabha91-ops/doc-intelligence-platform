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
| Chatbot LLM         | Ollama + TinyLlama 1.1B (CPU)              | Local LLM for RAG Q&A                     | MIT / Apache | Free |
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

### Docker (Recommended)

```bash
# 1. Install Ollama on your host machine
#    Linux:   curl -fsSL https://ollama.com/install.sh | sh
#    macOS:   brew install ollama
#    Windows: download from https://ollama.com/download

# 2. Pull the model and start Ollama
ollama pull tinyllama
ollama serve

# 3. Start the platform
docker-compose up --build
```

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`

### Manual Setup (without Docker)

#### Prerequisites

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
ollama pull tinyllama
```

#### Backend

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

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

UI available at: `http://localhost:5173`

#### Ollama (separate terminal)

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
│   ├── Dockerfile
│   ├── .dockerignore
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
│   ├── Dockerfile
│   ├── .dockerignore
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
| 4GB | TinyLlama 1.1B ⭐ | `ollama pull tinyllama` | ~637MB |
| 8GB+ | Mistral 7B | `ollama pull mistral` | ~4.1GB |
| 16GB+ | Llama 3 8B | `ollama pull llama3` | ~4.7GB |

The default model is **TinyLlama** (CPU-only, `num_gpu: 0`), which runs on any machine without a GPU.

### Verify Setup

```bash
# Start Ollama server
ollama serve

# In another terminal:
curl http://localhost:11434/api/tags    # Should return model list

# Test a completion:
curl http://localhost:11434/api/chat -d '{
  "model": "tinyllama",
  "messages": [{"role": "user", "content": "Hello!"}],
  "stream": false
}'
```

### Configuration

Edit `backend/.env` to change the model:

```env
OLLAMA_BASE_URL=http://host.docker.internal:11434   # Docker
# OLLAMA_BASE_URL=http://localhost:11434             # Local (without Docker)
OLLAMA_MODEL=tinyllama
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
5. Ollama (TinyLlama) generates an answer constrained to only cite the provided context
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
