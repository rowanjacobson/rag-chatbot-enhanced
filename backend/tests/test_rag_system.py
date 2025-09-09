import unittest
import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag_system import RAGSystem
from config import Config

class TestRAGSystem(unittest.TestCase):
    """Test complete RAG system functionality"""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        cls.config = Config()
        
        # Check if we have a valid API key
        if not cls.config.ANTHROPIC_API_KEY or cls.config.ANTHROPIC_API_KEY.startswith('your-'):
            cls.skipTest = True
            return
            
        cls.skipTest = False
        cls.rag_system = RAGSystem(cls.config)

    def setUp(self):
        """Set up for each test"""
        if self.skipTest:
            self.skipTest("No valid Anthropic API key configured")

    def test_system_initialization(self):
        """Test that RAG system initializes correctly"""
        self.assertIsNotNone(self.rag_system.document_processor)
        self.assertIsNotNone(self.rag_system.vector_store)
        self.assertIsNotNone(self.rag_system.ai_generator)
        self.assertIsNotNone(self.rag_system.session_manager)
        self.assertIsNotNone(self.rag_system.tool_manager)
        
        # Check that both tools are registered
        tool_definitions = self.rag_system.tool_manager.get_tool_definitions()
        tool_names = [tool['name'] for tool in tool_definitions]
        
        print(f"Registered tools: {tool_names}")
        self.assertIn('search_course_content', tool_names)
        self.assertIn('get_course_outline', tool_names)

    def test_course_analytics(self):
        """Test course analytics functionality"""
        analytics = self.rag_system.get_course_analytics()
        
        self.assertIsInstance(analytics, dict)
        self.assertIn('total_courses', analytics)
        self.assertIn('course_titles', analytics)
        
        print(f"Course analytics: {analytics}")
        
        # Should have some courses loaded
        self.assertGreater(analytics['total_courses'], 0, 
                          "RAG system should have courses loaded")

    def test_simple_content_query(self):
        """Test a simple content-related query"""
        try:
            response, sources = self.rag_system.query("What is retrieval augmented generation?")
            
            print(f"Simple query response: {response[:200]}...")
            print(f"Sources: {sources}")
            
            self.assertIsInstance(response, str)
            self.assertGreater(len(response), 0)
            self.assertNotIn("query failed", response.lower())
            self.assertNotIn("error", response.lower())
            
        except Exception as e:
            print(f"Exception during simple query: {e}")
            self.fail(f"Simple query failed with exception: {e}")

    def test_course_specific_query(self):
        """Test a course-specific content query"""
        # Get available courses first
        analytics = self.rag_system.get_course_analytics()
        if not analytics['course_titles']:
            self.skipTest("No courses available for testing")
            
        course_title = analytics['course_titles'][0]
        query = f"Tell me about embeddings in {course_title}"
        
        try:
            response, sources = self.rag_system.query(query)
            
            print(f"Course-specific query response: {response[:200]}...")
            print(f"Sources: {sources}")
            
            self.assertIsInstance(response, str)
            self.assertGreater(len(response), 0)
            self.assertNotIn("query failed", response.lower())
            
        except Exception as e:
            print(f"Exception during course-specific query: {e}")
            self.fail(f"Course-specific query failed: {e}")

    def test_course_outline_query(self):
        """Test a course outline query"""
        # Get available courses first
        analytics = self.rag_system.get_course_analytics()
        if not analytics['course_titles']:
            self.skipTest("No courses available for testing")
            
        course_title = analytics['course_titles'][0]
        query = f"What are the lessons in {course_title}?"
        
        try:
            response, sources = self.rag_system.query(query)
            
            print(f"Outline query response: {response[:300]}...")
            print(f"Sources: {sources}")
            
            self.assertIsInstance(response, str)
            self.assertGreater(len(response), 0)
            self.assertNotIn("query failed", response.lower())
            
            # Should contain course structure information
            self.assertIn("Course:", response)
            
        except Exception as e:
            print(f"Exception during outline query: {e}")
            self.fail(f"Outline query failed: {e}")

    def test_session_management(self):
        """Test session-based conversation"""
        session_id = "test_session_123"
        
        try:
            # First query
            response1, sources1 = self.rag_system.query(
                "What is vector search?", 
                session_id=session_id
            )
            
            print(f"First response: {response1[:100]}...")
            
            # Follow-up query (should use context)
            response2, sources2 = self.rag_system.query(
                "How does it work?", 
                session_id=session_id
            )
            
            print(f"Follow-up response: {response2[:100]}...")
            
            self.assertIsInstance(response1, str)
            self.assertIsInstance(response2, str)
            self.assertNotIn("query failed", response1.lower())
            self.assertNotIn("query failed", response2.lower())
            
        except Exception as e:
            print(f"Exception during session test: {e}")
            self.fail(f"Session management test failed: {e}")

    def test_tool_execution_debugging(self):
        """Detailed debugging of tool execution"""
        # Test individual tool execution
        search_result = self.rag_system.tool_manager.execute_tool(
            "search_course_content", 
            query="retrieval"
        )
        
        print(f"Direct tool execution result: {search_result[:200]}...")
        
        self.assertIsInstance(search_result, str)
        self.assertNotIn("Tool 'search_course_content' not found", search_result)
        
        # Test outline tool if available
        if "get_course_outline" in [t['name'] for t in self.rag_system.tool_manager.get_tool_definitions()]:
            analytics = self.rag_system.get_course_analytics()
            if analytics['course_titles']:
                course_title = analytics['course_titles'][0]
                outline_result = self.rag_system.tool_manager.execute_tool(
                    "get_course_outline",
                    course_name=course_title
                )
                
                print(f"Direct outline tool result: {outline_result[:200]}...")
                self.assertIsInstance(outline_result, str)

    def test_vector_store_data_availability(self):
        """Test that vector store has data available"""
        # Check course count
        course_count = self.rag_system.vector_store.get_course_count()
        print(f"Vector store course count: {course_count}")
        self.assertGreater(course_count, 0)
        
        # Try direct search on vector store
        search_results = self.rag_system.vector_store.search("retrieval")
        print(f"Direct vector search results: {len(search_results.documents)} documents")
        print(f"Search error: {search_results.error}")
        
        if search_results.error:
            self.fail(f"Vector store search failed: {search_results.error}")
            
        # Should have some results for common terms
        if search_results.is_empty():
            print("Warning: Vector store search returned no results for 'retrieval'")

    def test_error_handling_with_invalid_input(self):
        """Test error handling with various invalid inputs"""
        # Empty query
        try:
            response, sources = self.rag_system.query("")
            print(f"Empty query response: {response}")
            self.assertIsInstance(response, str)
        except Exception as e:
            print(f"Empty query exception: {e}")
            
        # Very long query
        try:
            long_query = "retrieval " * 100
            response, sources = self.rag_system.query(long_query)
            print(f"Long query response length: {len(response)}")
            self.assertIsInstance(response, str)
        except Exception as e:
            print(f"Long query exception: {e}")

if __name__ == '__main__':
    unittest.main(verbosity=2)