"""
Test fixtures and configuration for RAG system tests.
"""
import pytest
from unittest.mock import Mock, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
from typing import Dict, List, Any
import os
import tempfile
import shutil

# Import the models from app for test app
from app import QueryRequest, QueryResponse, CourseStats


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    config = Mock()
    config.CHUNK_SIZE = 800
    config.CHUNK_OVERLAP = 100
    config.MAX_RESULTS = 5
    config.MODEL_NAME = "claude-sonnet-4-20250514"
    config.EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    config.CHROMA_DB_PATH = ":memory:"
    config.MAX_HISTORY = 2
    return config


@pytest.fixture
def mock_rag_system():
    """Mock RAG system for testing."""
    rag_system = Mock()
    rag_system.query.return_value = (
        "This is a test answer about machine learning concepts.",
        [
            {"text": "Machine learning is a subset of AI", "link": "course1/lesson1"},
            {"text": "Deep learning uses neural networks", "link": "course1/lesson2"}
        ]
    )
    rag_system.get_course_analytics.return_value = {
        "total_courses": 2,
        "course_titles": ["Introduction to ML", "Advanced Deep Learning"]
    }
    rag_system.session_manager.create_session.return_value = "test-session-123"
    return rag_system


@pytest.fixture
def mock_session_manager():
    """Mock session manager for testing."""
    session_manager = Mock()
    session_manager.create_session.return_value = "test-session-123"
    session_manager.get_session_history.return_value = []
    session_manager.add_message.return_value = None
    return session_manager


@pytest.fixture
def sample_query_request():
    """Sample query request for testing."""
    return QueryRequest(
        query="What is machine learning?",
        session_id="test-session-123"
    )


@pytest.fixture
def sample_query_response():
    """Sample query response for testing."""
    return QueryResponse(
        answer="Machine learning is a subset of artificial intelligence.",
        sources=[
            {"text": "ML definition", "link": "course1/lesson1"},
            {"text": "AI overview", "link": "course1/lesson2"}
        ],
        session_id="test-session-123"
    )


@pytest.fixture
def sample_course_stats():
    """Sample course statistics for testing."""
    return CourseStats(
        total_courses=2,
        course_titles=["Course 1", "Course 2"]
    )


@pytest.fixture
def test_app(mock_rag_system):
    """Create test FastAPI app without static file mounting to avoid import issues."""
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.middleware.trustedhost import TrustedHostMiddleware
    
    # Create a test-specific FastAPI app
    app = FastAPI(title="Test Course Materials RAG System", root_path="")
    
    # Add middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
    
    # Use the mocked RAG system
    rag_system = mock_rag_system
    
    # Define API endpoints inline to avoid import issues
    @app.post("/api/query", response_model=QueryResponse)
    async def query_documents(request: QueryRequest):
        """Process a query and return response with sources"""
        try:
            # Create session if not provided
            session_id = request.session_id
            if not session_id:
                session_id = rag_system.session_manager.create_session()
            
            # Process query using RAG system
            answer, sources = rag_system.query(request.query, session_id)
            
            return QueryResponse(
                answer=answer,
                sources=sources,
                session_id=session_id
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")

    @app.get("/api/courses", response_model=CourseStats)
    async def get_course_stats():
        """Get course analytics and statistics"""
        try:
            analytics = rag_system.get_course_analytics()
            return CourseStats(
                total_courses=analytics["total_courses"],
                course_titles=analytics["course_titles"]
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/")
    async def read_root():
        """Root endpoint for health check"""
        return {"message": "RAG System API is running"}
    
    return app


@pytest.fixture
def test_client(test_app):
    """Create test client for API testing."""
    return TestClient(test_app)


@pytest.fixture
def temp_docs_dir():
    """Create temporary documents directory for testing."""
    temp_dir = tempfile.mkdtemp()
    
    # Create sample documents
    sample_doc1 = """
Course Title: Introduction to Machine Learning
Course Instructor: Dr. John Smith
Course Link: https://example.com/ml-course

Lesson 1: What is Machine Learning?
Machine learning is a subset of artificial intelligence that enables computers to learn and make decisions from data without being explicitly programmed.

Lesson 2: Types of Machine Learning
There are three main types: supervised learning, unsupervised learning, and reinforcement learning.
"""
    
    sample_doc2 = """
Course Title: Deep Learning Fundamentals
Course Instructor: Dr. Jane Doe
Course Link: https://example.com/dl-course

Lesson 1: Introduction to Neural Networks
Neural networks are computing systems inspired by biological neural networks.

Lesson 2: Backpropagation Algorithm
Backpropagation is the standard method for training neural networks.
"""
    
    with open(os.path.join(temp_dir, "ml_course.txt"), "w") as f:
        f.write(sample_doc1)
    
    with open(os.path.join(temp_dir, "dl_course.txt"), "w") as f:
        f.write(sample_doc2)
    
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_vector_store():
    """Mock vector store for testing."""
    vector_store = Mock()
    vector_store.search.return_value = [
        {
            "content": "Machine learning is a subset of AI",
            "course_title": "Introduction to ML",
            "lesson_title": "What is ML?",
            "course_link": "https://example.com/ml",
            "distance": 0.1
        }
    ]
    vector_store.get_course_titles.return_value = ["Course 1", "Course 2"]
    vector_store.get_course_count.return_value = 2
    return vector_store


@pytest.fixture
def mock_ai_generator():
    """Mock AI generator for testing."""
    ai_generator = Mock()
    ai_generator.generate_response.return_value = "This is a mock AI response about machine learning."
    return ai_generator


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "api: mark test as an API test"
    )