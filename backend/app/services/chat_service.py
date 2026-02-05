"""
RAG (Retrieval Augmented Generation) chatbot service.
Uses search results as context for Ollama LLM-powered Q&A.

100% free & local — no API keys needed.
"""

import requests
from app.core.config import settings
from app.services.search_service import semantic_search


def check_ollama_available() -> bool:
    """Check if Ollama server is running."""
    try:
        resp = requests.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=3)
        return resp.status_code == 200
    except requests.ConnectionError:
        return False


def chat_with_documents(question: str, top_k: int = 5) -> dict:
    """
    Answer a question using retrieved document context (RAG).
    Pipeline: semantic search → build context → Ollama LLM → return answer + sources.
    """
    # Check Ollama is running
    if not check_ollama_available():
        return {
            "answer": (
                "⚠️ Ollama is not running. Start it with:\n\n"
                "  1. `ollama serve`  (in a separate terminal)\n"
                "  2. `ollama pull mistral`  (download model if not already)\n\n"
                "Ollama is free and runs 100% locally."
            ),
            "sources": [],
        }

    # 1. Retrieve relevant chunks
    search_results = semantic_search(question, top_k=top_k)

    if not search_results:
        return {
            "answer": "I couldn't find any relevant documents to answer your question. Please upload some PDFs first.",
            "sources": [],
        }

    # 2. Build context from search results
    context_parts = []
    for i, result in enumerate(search_results):
        context_parts.append(
            f"[Source {i+1}: {result['filename']}, Page {result['page_number']}]\n{result['chunk_text']}"
        )
    context = "\n\n---\n\n".join(context_parts)

    # 3. Generate answer with Ollama
    system_prompt = """You are a helpful document assistant. Answer the user's question based ONLY on the provided document context. 
    - If the answer is found in the documents, cite which source it came from (e.g., Source 1, Source 2).
    - If the context doesn't contain enough information, say so honestly.
    - Be concise and accurate."""

    user_prompt = f"""Context from documents:
{context}

Question: {question}

Answer based on the documents above:"""

    try:
        response = requests.post(
            f"{settings.OLLAMA_BASE_URL}/api/chat",
            json={
                "model": settings.OLLAMA_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_predict": 1000,
                },
            },
            timeout=120,
        )
        response.raise_for_status()
        answer = response.json()["message"]["content"]
    except requests.Timeout:
        answer = "⚠️ Ollama took too long to respond. The model may still be loading — try again in a moment."
    except requests.RequestException as e:
        answer = f"⚠️ Error communicating with Ollama: {str(e)}"
    except (KeyError, ValueError):
        answer = "⚠️ Unexpected response from Ollama. Make sure the model is downloaded: `ollama pull mistral`"

    return {
        "answer": answer,
        "sources": search_results,
    }
