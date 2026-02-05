from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Document Intelligence Platform"
    DEBUG: bool = True

    # Paths
    UPLOAD_DIR: str = "./data/uploads"
    SAMPLE_PDF_DIR: str = "./data/sample_pdfs"

    # ChromaDB
    CHROMA_PERSIST_DIR: str = "./data/chroma_db"
    CHROMA_COLLECTION_NAME: str = "documents"

    # Embedding Model
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # OCR
    TESSERACT_CMD: str = "tesseract"  # Path to tesseract binary

    # spaCy NER Model
    SPACY_MODEL: str = "en_core_web_sm"

    # Ollama (Free & Local LLM for RAG chatbot)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "tinyllama"  # lightweight model (~1.5GB RAM)

    # Search
    TOP_K_RESULTS: int = 10
    CHUNK_SIZE: int = 500       # Characters per text chunk
    CHUNK_OVERLAP: int = 50     # Overlap between chunks

    class Config:
        env_file = ".env"


settings = Settings()

# Ensure directories exist
Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.CHROMA_PERSIST_DIR).mkdir(parents=True, exist_ok=True)
