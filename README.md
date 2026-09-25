# ARES — AI Retrieval Engine System

ARES is a privacy-first local Retrieval-Augmented Generation (RAG) application for searching and chatting with private PDF, CSV and Excel files. It was reconstructed from the original project design after the local source was lost.

## What ARES does

- Runs locally with **Ollama** (default LLM: `mistral`, embeddings: `nomic-embed-text`).
- Uploads and indexes **PDF, CSV, XLSX and XLS** files.
- Uses **ChromaDB PersistentClient** for local vector search.
- Uses filename/metadata routing to shortlist relevant documents when the user has not explicitly selected files.
- Supports explicit **multi-file selection**.
- Produces **file-wise answers** so information from different sources stays separated.
- Persists users, roles, chats, messages and document metadata in **SQLite**.
- Provides **Admin** and **User** roles.
- Includes lightweight in-memory caching and safe Chroma ingestion batches.
- Includes a React/Vite frontend and optional Tauri desktop shell.

## Repository layout

```text
ARES/
├── backend/
│   ├── app/
│   │   ├── routers/
│   │   └── services/
│   ├── scripts/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   └── src-tauri/
├── .env.example
└── README.md
```

## Prerequisites

1. Python 3.10+ (3.11 recommended)
2. Node.js 18+ / npm
3. Ollama installed and running
4. Pull the local models:

```bash
ollama pull mistral
ollama pull nomic-embed-text
```

## 1. Backend setup

```bash
cd backend
python -m venv .venv
```

Activate the environment:

**Windows PowerShell**
```powershell
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux**
```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Copy the environment file:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Create the first admin account:

```bash
python scripts/create_admin.py
```

Start the API:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API health check: `http://localhost:8000/health`

## 2. Frontend setup

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

## Optional: run as a Tauri desktop app

Install Rust and the platform prerequisites required by Tauri, then:

```bash
cd frontend
npm install
npm run tauri:dev
```

To build a desktop bundle:

```bash
npm run tauri:build
```

The FastAPI backend still needs to be running locally. A production packaging step can later bundle/launch the backend as a sidecar.

## Environment variables

Backend variables live in `backend/.env`.

```env
ARES_DB_PATH=data/ares.db
ARES_CHROMA_PATH=data/chroma_db
ARES_UPLOAD_DIR=data/uploads
ARES_OLLAMA_HOST=http://localhost:11434
ARES_LLM_MODEL=mistral
ARES_EMBED_MODEL=nomic-embed-text
ARES_JWT_SECRET=replace-this-with-a-long-random-secret
ARES_TOKEN_EXPIRE_MINUTES=720
ARES_TOP_K=6
ARES_MAX_ROUTED_FILES=3
ARES_CHROMA_BATCH_SIZE=250
ARES_CACHE_TTL_SECONDS=300
```

Frontend variables can be set in `frontend/.env`:

```env
VITE_API_URL=http://localhost:8000
```

## Roles

### User
- Log in
- Start and rename chats
- Select available documents
- Ask questions
- Receive file-separated answers

### Admin
Everything a user can do, plus:
- Upload/index documents
- Delete documents and their Chroma vectors
- Create users
- Change user roles
- Delete non-self users

## Retrieval flow

1. Query enters the FastAPI chat endpoint.
2. If the user chose documents, ARES searches only those files.
3. Otherwise, metadata routing scores filenames/metadata against the query and chooses a small file shortlist.
4. Chroma retrieves the most relevant chunks independently for each chosen file.
5. Mistral generates an answer for each file using only that file's retrieved context.
6. Answers are returned as separate file sections and saved to the chat history.

## Notes

- The ingestion batch size is deliberately kept below the historical Chroma max-batch issue encountered in the original project.
- PDF extraction uses PyMuPDF. Scanned PDFs without embedded text need an OCR extension; a hook is left in the ingestion layer for adding one later.
- This repo intentionally contains no API keys, passwords, private ONGC files or proprietary documents.

## Suggested GitHub first commit

```bash
git init
git add .
git commit -m "Reconstruct ARES local RAG system"
git branch -M main
git remote add origin <YOUR_GITHUB_REPO_URL>
git push -u origin main
```
