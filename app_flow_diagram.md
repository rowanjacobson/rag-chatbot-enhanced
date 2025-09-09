# RAG Chatbot Application Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              APPLICATION STARTUP                               │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│  1. System Initialization                                                      │
│                                                                                 │
│  ./run.sh OR uv run uvicorn app:app                                           │
│                        ↓                                                       │
│  FastAPI App (app.py):                                                        │
│  ┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐│
│  │   Load Config       │    │  Initialize RAG     │    │  Setup Middleware   ││
│  │   (.env vars)       │    │  System Components  │    │  (CORS, Static)     ││
│  └─────────────────────┘    └─────────────────────┘    └─────────────────────┘│
│                        ↓                                                       │
│  RAG System Initialization:                                                   │
│  ┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐│
│  │ Document Processor  │    │   Vector Store      │    │   AI Generator      ││
│  │ (chunk config)      │    │   (ChromaDB)        │    │   (Claude API)      ││
│  └─────────────────────┘    └─────────────────────┘    └─────────────────────┘│
│                        ↓                                                       │
│  ┌─────────────────────┐    ┌─────────────────────┐                          │
│  │ Session Manager     │    │   Search Tools      │                          │
│  │ (conversation hist) │    │ (CourseSearchTool)  │                          │
│  └─────────────────────┘    └─────────────────────┘                          │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│  2. Document Loading (startup_event)                                          │
│                                                                                 │
│  Check ../docs folder exists                                                   │
│                        ↓                                                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │                     Document Processing Pipeline                        │  │
│  │                                                                         │  │
│  │  For each file (.pdf, .docx, .txt):                                   │  │
│  │                                                                         │  │
│  │  File Reader → Document Parser → Course/Lesson Extractor →            │  │
│  │                                                                         │  │
│  │  Text Chunker → Embedding Generator → ChromaDB Storage                │  │
│  │                                                                         │  │
│  │  Result: CourseChunk objects with metadata stored in vector DB        │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
│                        ↓                                                       │
│  Output: "Loaded N courses with M chunks"                                     │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            FRONTEND INITIALIZATION                             │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│  3. Browser Loads Application                                                  │
│                                                                                 │
│  GET http://localhost:8000                                                     │
│                        ↓                                                       │
│  Static Files Served:                                                         │
│  ┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐│
│  │   index.html        │    │    style.css        │    │    script.js        ││
│  │   (UI structure)    │    │   (styling)         │    │  (functionality)    ││
│  └─────────────────────┘    └─────────────────────┘    └─────────────────────┘│
│                        ↓                                                       │
│  DOM Content Loaded Event:                                                    │
│  • Initialize UI elements                                                     │
│  • Setup event listeners                                                      │
│  • Create welcome session                                                     │
│  • Load course statistics                                                     │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│  4. Initial Data Loading                                                       │
│                                                                                 │
│  GET /api/courses                                                              │
│                        ↓                                                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │                     Course Analytics                                    │  │
│  │                                                                         │  │
│  │  Vector Store Query → Count courses → Get course titles →              │  │
│  │                                                                         │  │
│  │  Return: { total_courses: N, course_titles: ["Course A", ...] }       │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
│                        ↓                                                       │
│  Frontend Updates:                                                             │
│  • Display course count in sidebar                                            │
│  • Show list of available courses                                             │
│  • Show welcome message                                                       │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            USER INTERACTION CYCLE                              │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│  5. User Query Cycle (Repeating)                                              │
│                                                                                 │
│  User Input → Send Message → Loading State                                    │
│                        ↓                                                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │                        Query Processing                                 │  │
│  │                                                                         │  │
│  │  POST /api/query → Session Management → AI Processing →                │  │
│  │                                                                         │  │
│  │  Tool-Based Search → Vector Retrieval → Response Generation →          │  │
│  │                                                                         │  │
│  │  Source Collection → History Update → JSON Response                    │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
│                        ↓                                                       │
│  Response Display:                                                             │
│  • Remove loading animation                                                   │
│  • Render markdown response                                                   │
│  • Show collapsible sources                                                   │
│  • Re-enable input for next query                                            │
│                        ↓                                                       │
│  Session Continuity:                                                          │
│  • Maintain conversation history                                              │
│  • Context-aware responses                                                    │
│  • Persistent session ID                                                      │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              SYSTEM STATES                                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  Backend State:                        Frontend State:                         │
│  • Vector database (persistent)       • Current session ID                    │
│  • Session histories (in-memory)      • Chat message history (DOM)            │
│  • Course metadata cache              • UI interaction states                 │
│  • Tool manager state                 • Loading states                        │
│                                                                                 │
│  Error Handling:                       Features:                               │
│  • Graceful degradation               • Suggested questions                   │
│  • Loading fallbacks                  • Markdown rendering                    │
│  • Session recovery                   • Source attribution                    │
│  • API error responses                • Responsive design                     │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                                TECHNOLOGY STACK                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  Backend:                          Frontend:                                   │
│  • FastAPI (web framework)        • Vanilla JavaScript                        │
│  • ChromaDB (vector database)     • HTML5 + CSS3                             │
│  • Anthropic Claude (AI)          • Marked.js (markdown)                     │
│  • Sentence Transformers          • Fetch API (HTTP)                         │
│                                                                                 │
│  Data Flow:                        Security:                                   │
│  • HTTP REST APIs                 • CORS middleware                          │
│  • JSON serialization             • Trusted host middleware                  │
│  • Vector embeddings              • Input sanitization                       │
│  • Session management             • Error boundaries                         │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Application Flow Summary:

**Startup Phase:**
1. **System Init** → RAG components + middleware setup
2. **Document Loading** → Parse docs → Generate embeddings → Store in ChromaDB
3. **Frontend Init** → Load UI → Fetch course stats → Display welcome

**Runtime Phase:**
4. **User Interaction** → Query processing → AI + vector search → Response display
5. **Session Management** → Conversation continuity → Context preservation

**Key Characteristics:**
- **Persistent Knowledge**: Vector database survives restarts
- **Stateful Sessions**: Conversation history maintained
- **Real-time Processing**: Immediate responses with loading states
- **Tool-Augmented AI**: Dynamic knowledge base access