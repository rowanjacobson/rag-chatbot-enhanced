# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
- Quick start: `./run.sh` (creates docs dir, starts backend server)
- Manual start: `cd backend && uv run uvicorn app:app --reload --port 8000`
- Access: http://localhost:8000 (web UI) or http://localhost:8000/docs (API docs)

### Environment Setup
- Dependencies: `uv sync`
- Environment: Copy `.env.example` to `.env` and add `ANTHROPIC_API_KEY=your_key`
- Prerequisites: Python 3.13+, uv package manager, Anthropic API key

## Architecture Overview

### Core System Design
This is a **RAG (Retrieval-Augmented Generation) chatbot** that answers questions about course materials using semantic search and AI-powered responses.

**Data Flow Architecture:**
1. **Document Ingestion**: Course documents → DocumentProcessor → text chunks → ChromaDB vector storage
2. **Query Processing**: User query → RAGSystem → AI Generator (Claude) → CourseSearchTool → vector search → response synthesis
3. **Session Management**: Conversation history maintained server-side for context continuity

### Component Relationships

**RAGSystem** (`backend/rag_system.py`) - Main orchestrator that coordinates:
- **DocumentProcessor** - Parses course documents with structured format (Course Title/Link/Instructor, then Lessons)
- **VectorStore** - ChromaDB wrapper with course metadata and content collections  
- **AIGenerator** - Claude API integration with tool-based search capabilities
- **SessionManager** - Conversation history management
- **ToolManager** - Manages CourseSearchTool for dynamic knowledge base access

**Key Integration Points:**
- Tools are registered with ToolManager and passed to Claude for dynamic search
- CourseSearchTool bridges AI requests to VectorStore queries
- Session continuity maintained through conversation history injection
- Document structure expects `Course Title:`, `Course Instructor:`, `Lesson N:` format

### Configuration System
Central config in `backend/config.py`:
- Chunking: 800 chars with 100 char overlap
- Model: claude-sonnet-4-20250514
- Embeddings: all-MiniLM-L6-v2
- Vector DB: ./chroma_db (persistent)
- Context: 5 max results, 2 conversation messages

### Frontend-Backend Communication
- REST API endpoints: `/api/query` (POST) and `/api/courses` (GET)
- Session-based conversation state maintained server-side
- Frontend sends query + session_id, receives answer + sources + session_id
- Static file serving for HTML/CSS/JS frontend

### Document Processing Pipeline
1. **Structure Recognition**: Parses course metadata from first 3-4 lines
2. **Lesson Segmentation**: Identifies `Lesson N: Title` patterns  
3. **Text Chunking**: Sentence-based chunking with configurable overlap
4. **Context Enrichment**: Prefixes chunks with course/lesson context for better retrieval
5. **Vector Storage**: Creates CourseChunk objects with metadata in ChromaDB

### Startup Behavior
- Application auto-loads documents from `../docs/` folder on startup
- Supports .pdf, .docx, .txt files
- Avoids duplicate processing by checking existing course titles
- Creates welcome session and loads course statistics for frontend display

## Important Implementation Details

### Tool-Augmented AI Pattern
The system uses Claude's tool calling to dynamically search the knowledge base rather than pre-retrieving context. This allows the AI to make informed decisions about when and what to search for.

### Vector Store Collections
ChromaDB maintains two collections:
- **course_metadata**: Course and lesson information for title matching
- **course_content**: Text chunks with embeddings for semantic search

### Session Management
Sessions are ephemeral (in-memory) and maintain limited conversation history (configurable via MAX_HISTORY) for context without token bloat.

### Error Handling Strategy
- Graceful degradation at each layer (document processing, vector search, API calls)
- Frontend loading states with fallback error messages
- Backend exception handling with HTTP status codes
- always use uv to run the server do not use pip directly
- make sure to use uv yo manage all dependencies
- use uv to run Python files
- dont run the server using ./run.sh I will start it myself