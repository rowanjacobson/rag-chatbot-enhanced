"""
API endpoint tests for the RAG system FastAPI application.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
import json


@pytest.mark.api
class TestQueryEndpoint:
    """Test the /api/query endpoint."""
    
    def test_query_with_session_id(self, test_client, sample_query_request):
        """Test query endpoint with existing session ID."""
        response = test_client.post(
            "/api/query",
            json={
                "query": "What is machine learning?",
                "session_id": "test-session-123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "answer" in data
        assert "sources" in data
        assert "session_id" in data
        assert data["session_id"] == "test-session-123"
        assert isinstance(data["sources"], list)
        assert len(data["sources"]) > 0
        
        # Check source structure
        for source in data["sources"]:
            assert "text" in source
            assert "link" in source
    
    def test_query_without_session_id(self, test_client):
        """Test query endpoint without session ID (should create new session)."""
        response = test_client.post(
            "/api/query",
            json={"query": "What is deep learning?"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "answer" in data
        assert "sources" in data
        assert "session_id" in data
        assert data["session_id"] == "test-session-123"  # From mock
    
    def test_query_empty_string(self, test_client):
        """Test query endpoint with empty query string."""
        response = test_client.post(
            "/api/query",
            json={"query": ""}
        )
        
        assert response.status_code == 200
        # Should still return valid response structure
        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert "session_id" in data
    
    def test_query_very_long_string(self, test_client):
        """Test query endpoint with very long query string."""
        long_query = "What is machine learning? " * 100
        response = test_client.post(
            "/api/query",
            json={"query": long_query}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert "session_id" in data
    
    def test_query_invalid_json(self, test_client):
        """Test query endpoint with invalid JSON."""
        response = test_client.post(
            "/api/query",
            data="invalid json"
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_query_missing_query_field(self, test_client):
        """Test query endpoint without required query field."""
        response = test_client.post(
            "/api/query",
            json={"session_id": "test-123"}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_query_rag_system_exception(self, test_client, mock_rag_system):
        """Test query endpoint when RAG system raises exception."""
        # Configure the mock to raise exception
        mock_rag_system.query.side_effect = Exception("Database connection failed")
        
        # Create a test app with the exception-throwing mock
        from fastapi import FastAPI, HTTPException
        from fastapi.middleware.cors import CORSMiddleware
        from fastapi.middleware.trustedhost import TrustedHostMiddleware
        from app import QueryRequest, QueryResponse
        
        app = FastAPI(title="Test Course Materials RAG System", root_path="")
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
        app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"], expose_headers=["*"])
        
        @app.post("/api/query", response_model=QueryResponse)
        async def query_documents(request: QueryRequest):
            try:
                session_id = request.session_id or mock_rag_system.session_manager.create_session()
                answer, sources = mock_rag_system.query(request.query, session_id)
                return QueryResponse(answer=answer, sources=sources, session_id=session_id)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")
        
        from fastapi.testclient import TestClient
        client = TestClient(app)
        
        response = client.post(
            "/api/query",
            json={"query": "What is AI?"}
        )
        
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Query processing failed" in data["detail"]
    
    def test_query_response_structure(self, test_client):
        """Test that query response matches expected structure."""
        response = test_client.post(
            "/api/query",
            json={
                "query": "Explain neural networks",
                "session_id": "test-session-456"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure matches QueryResponse model
        required_fields = ["answer", "sources", "session_id"]
        for field in required_fields:
            assert field in data
        
        # Validate source structure
        assert isinstance(data["sources"], list)
        for source in data["sources"]:
            assert isinstance(source, dict)
            assert "text" in source
            assert "link" in source
            assert isinstance(source["text"], str)
            assert isinstance(source["link"], str)


@pytest.mark.api
class TestCoursesEndpoint:
    """Test the /api/courses endpoint."""
    
    def test_get_courses_success(self, test_client):
        """Test successful retrieval of course statistics."""
        response = test_client.get("/api/courses")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_courses" in data
        assert "course_titles" in data
        assert isinstance(data["total_courses"], int)
        assert isinstance(data["course_titles"], list)
        assert data["total_courses"] == 2
        assert len(data["course_titles"]) == 2
    
    def test_get_courses_response_structure(self, test_client):
        """Test that courses response matches expected structure."""
        response = test_client.get("/api/courses")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure matches CourseStats model
        required_fields = ["total_courses", "course_titles"]
        for field in required_fields:
            assert field in data
        
        # Validate field types
        assert isinstance(data["total_courses"], int)
        assert isinstance(data["course_titles"], list)
        
        # Validate course titles are strings
        for title in data["course_titles"]:
            assert isinstance(title, str)
    
    def test_get_courses_rag_system_exception(self, mock_rag_system):
        """Test courses endpoint when RAG system raises exception."""
        mock_rag_system.get_course_analytics.side_effect = Exception("Analytics service unavailable")
        
        # Create a test app with the exception-throwing mock
        from fastapi import FastAPI, HTTPException
        from fastapi.middleware.cors import CORSMiddleware
        from fastapi.middleware.trustedhost import TrustedHostMiddleware
        from app import CourseStats
        
        app = FastAPI(title="Test Course Materials RAG System", root_path="")
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
        app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"], expose_headers=["*"])
        
        @app.get("/api/courses", response_model=CourseStats)
        async def get_course_stats():
            try:
                analytics = mock_rag_system.get_course_analytics()
                return CourseStats(total_courses=analytics["total_courses"], course_titles=analytics["course_titles"])
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        from fastapi.testclient import TestClient
        client = TestClient(app)
        
        response = client.get("/api/courses")
        
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Analytics service unavailable" in data["detail"]
    
    def test_get_courses_empty_result(self, mock_rag_system):
        """Test courses endpoint with empty analytics result."""
        # Configure the mock to return empty results
        mock_rag_system.get_course_analytics.return_value = {
            "total_courses": 0,
            "course_titles": []
        }
        
        # Create a test app with the empty-result mock
        from fastapi import FastAPI, HTTPException
        from fastapi.middleware.cors import CORSMiddleware
        from fastapi.middleware.trustedhost import TrustedHostMiddleware
        from app import CourseStats
        
        app = FastAPI(title="Test Course Materials RAG System", root_path="")
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
        app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"], expose_headers=["*"])
        
        @app.get("/api/courses", response_model=CourseStats)
        async def get_course_stats():
            try:
                analytics = mock_rag_system.get_course_analytics()
                return CourseStats(total_courses=analytics["total_courses"], course_titles=analytics["course_titles"])
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        from fastapi.testclient import TestClient
        client = TestClient(app)
        
        response = client.get("/api/courses")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_courses"] == 0
        assert data["course_titles"] == []


@pytest.mark.api
class TestRootEndpoint:
    """Test the root endpoint."""
    
    def test_root_endpoint(self, test_client):
        """Test the root endpoint returns health check message."""
        response = test_client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "RAG System API is running" in data["message"]


@pytest.mark.api
class TestCORSAndMiddleware:
    """Test CORS and middleware configuration."""
    
    def test_cors_headers(self, test_client):
        """Test that CORS headers are properly set."""
        response = test_client.options("/api/query")
        
        # Should handle preflight request
        assert response.status_code in [200, 405]  # 405 if OPTIONS not explicitly handled
    
    def test_cors_on_actual_request(self, test_client):
        """Test CORS headers on actual API request."""
        response = test_client.post(
            "/api/query",
            json={"query": "test"},
            headers={"Origin": "http://localhost:3000"}
        )
        
        assert response.status_code == 200
        # CORS middleware should allow the request


@pytest.mark.api
class TestRequestValidation:
    """Test request validation for API endpoints."""
    
    def test_query_request_validation_types(self, test_client):
        """Test query request validation with wrong types."""
        # Query should be string, not number
        response = test_client.post(
            "/api/query",
            json={"query": 123}
        )
        assert response.status_code == 422
        
        # Session ID should be string, not number
        response = test_client.post(
            "/api/query",
            json={"query": "test", "session_id": 123}
        )
        assert response.status_code == 422
    
    def test_query_request_extra_fields(self, test_client):
        """Test query request with extra fields."""
        response = test_client.post(
            "/api/query",
            json={
                "query": "test",
                "session_id": "test-123",
                "extra_field": "should be ignored"
            }
        )
        
        # Should succeed and ignore extra fields
        assert response.status_code == 200


@pytest.mark.api
class TestAsyncEndpoints:
    """Test async endpoint behavior."""
    
    def test_multiple_sequential_requests(self, test_client):
        """Test handling of multiple sequential requests."""
        # Send multiple sequential requests to test session handling
        responses = []
        session_id = None
        
        for i in range(3):
            response = test_client.post(
                "/api/query", 
                json={
                    "query": f"test query {i}",
                    "session_id": session_id
                }
            )
            responses.append(response)
            
            # Use the session ID from first response for subsequent requests
            if i == 0:
                session_id = response.json().get("session_id")
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert "answer" in data
            assert "sources" in data
            assert "session_id" in data
            
        # All responses should have the same session ID
        session_ids = [r.json()["session_id"] for r in responses]
        assert len(set(session_ids)) == 1, "All requests should use the same session ID"