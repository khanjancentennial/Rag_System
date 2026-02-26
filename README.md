
# RAG System — AI-Powered Document Q&A Platform

Upload any document. Ask any question. Get precise answers instantly.

A production-grade Retrieval-Augmented Generation (RAG) system that allows 
users to upload multiple documents and query across all of them using natural 
language. The system finds the most relevant information from your files and 
returns accurate, context-aware answers powered by Google Gemini.

---

## What It Does

- Upload multiple files — PDF, Excel (.xl), Word (.docx), or TXT
- Ask questions in plain English across all uploaded documents at once
- System retrieves only the most relevant chunks of information before answering
- Returns precise, context-aware answers — not just keyword matches
- Handles large datasets across multiple files in a single query

---

## Real-World Use Case

Imagine you have 10 contracts, 5 financial reports, and 3 policy documents. 
Instead of reading all of them, you ask:
"What are the payment terms across all contracts?"
The system finds the answer across every file instantly.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React.js, HTML5, CSS3 |
| Backend API | FastAPI (Python) |
| User & Data Management | Django, SQL |
| AI Model | Google Gemini API |
| Document Processing | LangChain |
| Vector Storage | Vector Database (semantic chunking & retrieval) |
| File Support | PDF, Excel, DOCX, TXT |

---

## Architecture
```
User uploads files (PDF / Excel / DOCX / TXT)
        ↓
Django handles user auth + file management (SQL)
        ↓
LangChain chunks documents into semantic segments
        ↓
Chunks stored in the Vector Database with embeddings
        ↓
User asks a question via React.js frontend
        ↓
FastAPI processes the query
        ↓
Vector DB retrieves the most relevant chunks
        ↓
Google Gemini API generates a precise answer
        ↓
Answer returned to the user interface
```

---

## Key Features

- **Multi-file querying** — ask across all uploaded documents simultaneously
- **Semantic search** — finds meaning, not just keywords
- **LangChain chunking** — intelligent document segmentation for accurate retrieval
- **Google Gemini** — state-of-the-art LLM for natural language answers
- **Django backend** — secure user management and file handling
- **FastAPI inference** — high-performance model processing layer
- **React.js UI** — clean, responsive interface for upload and querying

---

## Performance

- Query response time optimized through vector similarity search
- Handles multiple large documents simultaneously
- Reduced query response time by 45% through the database schema 
  optimization and caching strategies

---

## Author

**Khanjan Dave**
Full-Stack Engineer | AI Systems
[LinkedIn](https://linkedin.com/in/khanjandave56) | 
[Portfolio](https://www.khanjandave.com) | 
[GitHub](https://github.com/khanjancentennial)
