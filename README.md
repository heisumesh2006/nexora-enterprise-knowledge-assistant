# RAG Document Assistant

An end-to-end Retrieval-Augmented Generation (RAG) application built incrementally using Python, LangChain, ChromaDB, NVIDIA NeMoTron, and Streamlit.

## Project Goal

Build a document-based AI assistant that can:

- Ingest multiple document formats
- Split documents into meaningful chunks
- Generate embeddings
- Store and retrieve documents using a vector database
- Answer questions using retrieved document context
- Provide source citations
- Persist the knowledge base
- Provide a Streamlit web interface

## Current Progress

### Module 1 — Environment Setup

Status: **Completed**

The development environment has been configured and the NVIDIA NeMoTron API has been successfully tested.

### Verified Components

- Python virtual environment
- LangChain
- ChromaDB
- OpenAI Python SDK
- python-dotenv
- PyPDF
- Docx2txt
- NVIDIA API
- NVIDIA NeMoTron 3 Ultra 550B
- Git

### NVIDIA Model

```text
nvidia/nemotron-3-ultra-550b-a55b
```

### API Configuration

The application uses NVIDIA's OpenAI-compatible API endpoint.

API credentials are stored in `.env` and are intentionally excluded from version control.

## Project Roadmap

- [x] Module 1 — Environment Setup
- [ ] Module 2 — Document Ingestion
- [ ] Module 3 — Text Chunking
- [ ] Module 4 — Embeddings
- [ ] Module 5 — Vector Database
- [ ] Module 6 — Basic RAG Chain
- [ ] Module 7 — Citations
- [ ] Module 8 — Streamlit UI
- [ ] Module 9 — Multi-Document & Persistence
- [ ] Module 10 — Polish & Robustness

## Running the Project

Activate the virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Run the Module 1 NVIDIA test:

```powershell
python src\main.py
```

## Security

API keys are stored in `.env`.

Never commit `.env` to GitHub.
