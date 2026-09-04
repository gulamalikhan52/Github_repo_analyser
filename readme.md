🤖 AI Repository Intelligence
AI-powered repository analysis and codebase question-answering system.

AI Repository Intelligence allows you to provide a GitHub repository URL, automatically process the repository, create a semantic vector index, and ask natural-language questions about the codebase.

The system combines GitHub repository ingestion, code chunking, Sentence Transformers, FAISS, semantic retrieval, LangGraph, Groq LLM, FastAPI, and Streamlit into an end-to-end RAG pipeline.

✨ Features
🔗 Analyze any accessible GitHub repository using its URL

📦 Automatically download and process repository files

🧹 Filter irrelevant and generated files

✂️ Split repository content into semantic chunks

🧠 Generate vector embeddings using Sentence Transformers

⚡ Store and search embeddings using FAISS

🔎 Retrieve relevant repository context for user questions

💬 Generate grounded answers using an LLM through Groq

🔄 Orchestrate the RAG workflow with LangGraph

🚀 Expose backend functionality through FastAPI

🎨 Interactive Streamlit frontend

💾 Save repository indexes locally for reuse

📚 Display retrieved source files with answers

🏗️ System Architecture
┌──────────────────────┐
│ Streamlit │
│ Frontend │
└──────────┬───────────┘
│
│ HTTP
▼
┌──────────────────────┐
│ FastAPI │
│ Backend │
└──────────┬───────────┘
│
▼
┌──────────────────────┐
│ LangGraph Flow │
└──────────┬───────────┘
│
┌──────────────┴──────────────┐
│ │
▼ ▼
┌──────────────────┐ ┌──────────────────┐
│ Repository │ │ RAG / Retrieval │
│ Collection │ │ Pipeline │
└────────┬─────────┘ └────────┬─────────┘
│ │
▼ ▼
┌──────────────────┐ ┌──────────────────┐
│ File Filtering │ │ Sentence │
│ & Chunking │ │ Transformers │
└──────────────────┘ └────────┬─────────┘
│
▼
┌──────────────────┐
│ FAISS │
│ Vector Index │
└────────┬─────────┘
│
▼
┌──────────────────┐
│ Context Builder │
└────────┬─────────┘
│
▼
┌──────────────────┐
│ Groq LLM │
│ Answer Generation│
└──────────────────┘
🔄 Workflow
Repository Preparation
GitHub URL
↓
Repository ZIP Download
↓
File Filtering
↓
Content Extraction
↓
Chunking
↓
Sentence Transformer Embeddings
↓
FAISS Index
↓
Local Index Storage
Question Answering
User Question
↓
Query Embedding
↓
FAISS Similarity Search
↓
Top-K Relevant Chunks
↓
Context Builder
↓
Groq LLM
↓
Grounded Answer + Sources
🛠️ Technology Stack
Layer Technology
Frontend Streamlit
Backend FastAPI
Workflow LangGraph
LLM Groq
Embeddings Sentence Transformers
Embedding Model all-MiniLM-L6-v2
Vector Database FAISS
Repository Source GitHub
Language Python
API Communication REST / HTTP
📁 Project Structure
ai-repository-intelligence/
│
├── backend/
│ ├── graph/
│ │ ├── graph.py
│ │ ├── nodes.py
│ │ └── state.py
│ │
│ ├── rag/
│ │ ├── chunker.py
│ │ ├── embeddings.py
│ │ ├── indexer.py
│ │ └── vector_store.py
│ │
│ ├── services/
│ │ ├── github_service.py
│ │ ├── llm_service.py
│ │ ├── rag_service.py
│ │ ├── repository_manager.py
│ │ └── repository_service.py
│ │
│ ├── utils/
│ │ └── file_filter.py
│ │
│ └── main.py
│
├── frontend/
│ └── app.py
│
├── data/
│ └── indexes/
│
├── .env
├── .gitignore
├── requirements.txt
└── README.md
⚙️ Installation

1. Clone the project
   git clone <YOUR_REPOSITORY_URL>
   cd ai-repository-intelligence
2. Create a virtual environment
   Windows PowerShell:

python -m venv venv
Activate it:

.\venv\Scripts\Activate.ps1 3. Install dependencies
python -m pip install -r requirements.txt
🔐 Environment Variables
Create a .env file in the project root:

GITHUB_TOKEN=your_github_token
GROQ_API_KEY=your_groq_api_key
Important
Never commit .env to GitHub.

Make sure .gitignore contains:

.env
.env.\*
venv/
.venv/
**pycache**/
data/indexes/
🚀 Running the Application
The application uses two services:

Start FastAPI Backend
From the project root:

python -m uvicorn backend.main:app
The backend will run on:

http://127.0.0.1:8000
Health check:

GET /health
Start Streamlit Frontend
Open another PowerShell terminal, activate the same virtual environment, and run:

streamlit run frontend/app.py
Streamlit will provide a local URL similar to:

http://localhost:8501
🔌 API Endpoints
Health Check
GET /health
Checks whether the backend is running.

Prepare Repository
POST /prepare
Example request:

{
"repository_url": "https://github.com/owner/repository"
}
The endpoint starts repository preparation and returns the repository status.

Preparation Status
GET /prepare/status/{repository_key}
Used by the frontend to monitor repository preparation.

Ask a Question
POST /ask
Example:

{
"repository_url": "https://github.com/owner/repository",
"question": "What is the main purpose of this repository?",
"top_k": 5
}
Example response:

{
"answer": "The repository ...",
"sources": [
{
"file_path": "src/main.py"
}
],
"retrieved_chunks": 5
}
🧠 RAG Pipeline
The retrieval-augmented generation pipeline works in three major stages.

1. Indexing
   Repository files are:

Downloaded from GitHub

Filtered according to supported file types

Split into manageable chunks

Converted into vector embeddings

Stored in a FAISS index

2. Retrieval
   When a user asks a question:

The question is converted into an embedding

FAISS performs similarity search

The most relevant chunks are retrieved

The retrieved chunks are passed to the context builder

3. Generation
   The LLM receives:

User Question

- Retrieved Repository Context
  and generates a grounded response based on the available repository information.

📄 Supported File Types
The repository processing pipeline currently supports common source-code and configuration formats, including:

.py
.js
.jsx
.ts
.tsx
.java
.cpp
.c
.h
.hpp
.go
.rs
.php
.rb
.cs
.html
.css
.scss
.json
.yaml
.yml
.toml
.md
Common generated or irrelevant directories are ignored, including:

.git
node_modules
venv
.venv
**pycache**
dist
build
coverage
.idea
.vscode
Environment files such as .env are excluded to avoid processing secrets.

💾 Repository Indexing
Each repository receives a deterministic repository key generated from its URL.

Indexes are stored under:

data/indexes/
This allows an already-indexed repository to be loaded instead of rebuilding the complete FAISS index every time.

💬 Example Questions
After analyzing a repository, you can ask:

What is the main purpose of this repository?
Where is the main application defined?
Explain the project architecture.
Where is authentication implemented?
What are the main dependencies?
Which files contain the API implementation?
How does this project handle database operations?
🖥️ User Interface
The Streamlit interface provides:

GitHub repository input

Repository analysis workflow

Preparation status

Repository statistics

Interactive chat

Retrieved source information

New repository workflow

The interface is designed to make repository exploration feel like an AI-powered development workspace.

🔒 Security Considerations
API credentials are stored in environment variables.

.env files are excluded from repository processing.

API keys should never be hardcoded into source files.

Do not commit GitHub or Groq credentials to version control.

If credentials are accidentally exposed, revoke and regenerate them immediately.

🧪 Testing
A small repository can be used for quick end-to-end testing.

Example:

https://github.com/neubig/starter-repo
Paste the repository URL into the Streamlit interface and click:

🚀 Analyze
After indexing completes, ask questions about the repository.

📌 Current Project Status
Completed
GitHub repository URL processing

Repository ZIP collection

File filtering

Repository chunking

Sentence Transformer embeddings

FAISS vector indexing

Semantic search

Context building

Groq LLM integration

LangGraph workflow

FastAPI backend

Background repository preparation

Local index persistence

Streamlit frontend

Interactive repository chat

Retrieved source display

🎯 Project Goal
The goal of AI Repository Intelligence is to make large software repositories easier to understand by allowing developers to interact with a codebase using natural language.

Instead of manually searching through hundreds or thousands of files, users can ask questions and receive answers based on the repository's own content.

👨‍💻 Project
AI Repository Intelligence

An AI-powered RAG system for semantic GitHub repository understanding and codebase exploration.
