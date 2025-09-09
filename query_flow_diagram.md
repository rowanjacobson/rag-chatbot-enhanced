# RAG System Query Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                   FRONTEND                                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│  User Interface (script.js)                                                    │
│                                                                                 │
│  1. User Input: [Chat Input Field] → [Send Button/Enter]                      │
│                        ↓                                                       │
│  2. sendMessage() function:                                                    │
│     • Disable input/show loading                                              │
│     • Create POST request                                                      │
│                        ↓                                                       │
│  3. HTTP POST /api/query                                                       │
│     Body: { query: "user question", session_id: "session123" }               │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                   BACKEND                                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│  FastAPI App (app.py)                                                         │
│                                                                                 │
│  4. POST /api/query endpoint:                                                  │
│     • Receive QueryRequest                                                     │
│     • Create session if needed                                                 │
│                        ↓                                                       │
│  5. Call: rag_system.query(query, session_id)                                │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│  RAG System (rag_system.py)                                                   │
│                                                                                 │
│  6. query() method:                                                            │
│     ┌─────────────────────┐    ┌─────────────────────┐                       │
│     │   Session Manager   │    │   Tool Manager      │                       │
│     │                     │    │                     │                       │
│     │ • Get conversation  │    │ • Register tools    │                       │
│     │   history          │    │ • Get definitions   │                       │
│     └─────────────────────┘    └─────────────────────┘                       │
│                        ↓                ↓                                     │
│  7. AI Generator Call:                                                         │
│     ai_generator.generate_response(query, history, tools, tool_manager)       │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│  AI Generator (ai_generator.py)                                               │
│                                                                                 │
│  8. generate_response():                                                       │
│     • Send query to Claude AI with available tools                            │
│                        ↓                                                       │
│  9. Claude AI Processing:                                                      │
│     • Analyze query                                                            │
│     • Decide if tools needed                                                   │
│     • Call CourseSearchTool if needed                                         │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    ↓ (if tool needed)
┌─────────────────────────────────────────────────────────────────────────────────┐
│  Search Tools (search_tools.py)                                               │
│                                                                                 │
│  10. CourseSearchTool.search():                                               │
│      ┌─────────────────────────────────────────────────────────────────────┐  │
│      │                    Vector Store                                     │  │
│      │                                                                     │  │
│      │  11. ChromaDB Query:                                               │  │
│      │      • Convert query to embeddings                                 │  │
│      │      • Search similar course chunks                                │  │
│      │      • Return relevant context                                     │  │
│      └─────────────────────────────────────────────────────────────────────┘  │
│                        ↓                                                       │
│  12. Return: { context: "relevant chunks", sources: ["Course A", "Lesson 1"] } │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│  Response Generation & Return Path                                             │
│                                                                                 │
│  13. Claude AI: Generate response using retrieved context                      │
│  14. RAG System: Collect sources, update session history                      │
│  15. FastAPI: Format as QueryResponse JSON                                    │
│  16. Frontend: Display response + sources, re-enable input                    │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                               DATA STRUCTURES                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  Request:  { query: "string", session_id: "optional" }                        │
│                                                                                 │
│  Response: { answer: "string", sources: ["array"], session_id: "string" }     │
│                                                                                 │
│  Vector DB: CourseChunk { content, course_title, lesson_number, chunk_index } │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Key Components Flow Summary:

1. **Frontend** → User input → HTTP POST
2. **FastAPI** → Route to RAG system  
3. **RAG System** → Orchestrate session + AI + tools
4. **AI Generator** → Claude AI with tool access
5. **Search Tools** → Query ChromaDB vector store
6. **Vector Store** → Return relevant course chunks
7. **Response Path** → AI synthesis → JSON response → UI display

The system uses tool-augmented AI where Claude can dynamically search the knowledge base to provide accurate, contextual responses.