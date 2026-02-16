# DocuMind

**DocuMind** is a production‑ready document question‑answering system built on Retrieval‑Augmented Generation (RAG). It enables users to upload PDF documents and interact with them through a conversational interface powered by Groq’s high‑speed inference and semantic vector retrieval.

The platform is designed with a clean, modern interface and a scalable backend architecture suitable for both experimentation and deployment.

---

## Overview

DocuMind converts static documents into interactive knowledge sources. After uploading a document, users can ask natural language questions and receive contextual answers grounded strictly in the document content.

The system performs the following pipeline:

1. Document ingestion and parsing
2. Text chunking and embedding generation
3. Vector indexing (FAISS)
4. Semantic retrieval
5. LLM response generation using retrieved context

---

## Architecture

### Backend (FastAPI – Python)

* Handles file uploads and session management
* Generates embeddings using HuggingFace models
* Stores vectors in FAISS
* Retrieves relevant chunks using similarity search
* Generates responses using Groq LLM via LangChain

### Frontend (Next.js – React + TypeScript)

* Modern chat interface
* Real‑time conversation flow
* Session‑based interaction with uploaded documents
* Responsive UI using Tailwind CSS

---

## Technology Stack

**Backend**

* FastAPI
* LangChain
* Groq LLM API
* FAISS Vector Store
* HuggingFace Sentence Transformers

**Frontend**

* Next.js 14
* React 18
* TypeScript
* Tailwind CSS

---

## Prerequisites

* Python 3.11 or higher
* Node.js 18 or higher
* Groq API Key ([https://console.groq.com](https://console.groq.com))

---

## Installation and Setup

### 1. Backend Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Create environment file:

```
GROQ_API_KEY=your_groq_api_key_here
```

Run backend server:

```bash
uvicorn backend:app --reload --port 8000
```

Backend URL:

```
http://localhost:8000
```

---

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend URL:

```
http://localhost:3000
```

---

## Project Structure

```
document-chat-rag/
├── backend.py
├── app.py
├── requirements.txt
├── .env
├── docs/
└── frontend/
    ├── app/
    │   ├── page.tsx
    │   ├── layout.tsx
    │   └── globals.css
    ├── package.json
    └── tailwind.config.js
```

---

## API Endpoints

### Upload Document

`POST /upload`

Uploads and indexes a PDF document for chat interaction.

**Request**: multipart/form‑data with `file`

**Response**

```json
{
  "session_id": "uuid",
  "file_name": "document.pdf",
  "message": "Document indexed successfully"
}
```

---

### Chat with Document

`POST /chat`

**Request**

```json
{
  "session_id": "uuid",
  "message": "What is this document about?"
}
```

**Response**

```json
{
  "answer": "Generated response grounded in document context"
}
```

---

### Health Check

`GET /health`

Returns service availability status.

---

## Configuration

### Backend Parameters

* Model name configurable inside `backend.py`
* Chunk size and overlap adjustable in text splitter
* Retrieval top‑k configurable in retriever settings

### Frontend Parameters

* Update `BACKEND_URL` in `frontend/app/page.tsx` if backend port changes
* Customize UI theme in `tailwind.config.js`

---

## Features

* PDF document ingestion and indexing
* Context‑aware conversational Q&A
* Semantic search using vector embeddings
* Session‑based conversations
* Clean and responsive UI
* Modular and extensible architecture

---

## Production Notes

* Current session storage is in‑memory; replace with Redis or database for scaling
* GPU acceleration recommended for faster embedding generation
* Persistent vector storage recommended for large deployments

---

## License

This project is licensed under the MIT License.

---

## Author

DocuMind – Document Intelligence through Retrieval‑Augmented Generation
