import unittest
import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from search_tools import CourseSearchTool
from vector_store import VectorStore
from config import Config


class TestCourseSearchTool(unittest.TestCase):
    """Test CourseSearchTool functionality"""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures using real vector store"""
        cls.config = Config()
        cls.vector_store = VectorStore(
            cls.config.CHROMA_PATH, cls.config.EMBEDDING_MODEL, cls.config.MAX_RESULTS
        )
        cls.search_tool = CourseSearchTool(cls.vector_store)

        # Get available courses for testing
        cls.available_courses = cls.vector_store.get_existing_course_titles()
        print(f"Available courses for testing: {cls.available_courses}")

    def test_tool_definition(self):
        """Test that tool definition is properly formatted"""
        definition = self.search_tool.get_tool_definition()

        self.assertIsInstance(definition, dict)
        self.assertEqual(definition["name"], "search_course_content")
        self.assertIn("description", definition)
        self.assertIn("input_schema", definition)

        # Check required parameters
        schema = definition["input_schema"]
        self.assertEqual(schema["properties"]["query"]["type"], "string")
        self.assertEqual(schema["required"], ["query"])

    def test_execute_with_valid_query_no_course_filter(self):
        """Test execute with a general query (no course filter)"""
        if not self.available_courses:
            self.skipTest("No courses available in vector store")

        result = self.search_tool.execute("retrieval")
        print(f"General query result: {result[:200]}...")

        # Should not return error messages
        self.assertNotIn("No course found", result)
        self.assertNotIn("Error", result)
        self.assertNotIn("query failed", result.lower())

    def test_execute_with_course_filter(self):
        """Test execute with course name filter"""
        if not self.available_courses:
            self.skipTest("No courses available in vector store")

        # Use the first available course
        course_name = self.available_courses[0]
        result = self.search_tool.execute("retrieval", course_name=course_name)
        print(f"Course-filtered query result: {result[:200]}...")

        # Should not return error messages
        self.assertNotIn("No course found", result)
        self.assertNotIn("Error", result)
        self.assertNotIn("query failed", result.lower())

    def test_execute_with_invalid_course(self):
        """Test execute with non-existent course name"""
        result = self.search_tool.execute(
            "retrieval", course_name="NonExistentCourse123"
        )
        print(f"Invalid course result: {result}")

        # Should return appropriate error message
        self.assertIn("No course found matching", result)

    def test_execute_with_empty_query(self):
        """Test execute with empty query"""
        result = self.search_tool.execute("")
        print(f"Empty query result: {result}")

        # Should handle gracefully, not crash
        self.assertIsInstance(result, str)

    def test_source_tracking(self):
        """Test that sources are properly tracked"""
        if not self.available_courses:
            self.skipTest("No courses available in vector store")

        # Clear any existing sources
        self.search_tool.last_sources = []

        # Execute a search
        result = self.search_tool.execute("retrieval")

        # Check that sources were tracked
        self.assertIsInstance(self.search_tool.last_sources, list)
        print(f"Tracked sources: {self.search_tool.last_sources}")

        # If we got results, we should have sources
        if not result.startswith("No relevant content"):
            self.assertGreater(len(self.search_tool.last_sources), 0)

    def test_vector_store_connection(self):
        """Test that vector store is properly connected and has data"""
        # Check if courses exist
        course_count = self.vector_store.get_course_count()
        print(f"Course count in vector store: {course_count}")
        self.assertGreater(course_count, 0, "Vector store should contain courses")

        # Check if content exists by trying direct search
        try:
            results = self.vector_store.search("retrieval")
            print(f"Direct vector store search results count: {len(results.documents)}")
            print(f"Search error: {results.error}")

            if results.error:
                self.fail(f"Vector store search failed with error: {results.error}")

        except Exception as e:
            self.fail(f"Vector store search raised exception: {e}")

    def test_course_name_resolution(self):
        """Test course name resolution functionality"""
        if not self.available_courses:
            self.skipTest("No courses available in vector store")

        # Test with exact course name
        course_name = self.available_courses[0]
        resolved = self.vector_store._resolve_course_name(course_name)
        print(f"Exact name resolution: '{course_name}' -> '{resolved}'")
        self.assertEqual(resolved, course_name)

        # Test with partial course name (first few chars)
        if len(course_name) > 3:
            partial_name = course_name[:5]
            resolved_partial = self.vector_store._resolve_course_name(partial_name)
            print(f"Partial name resolution: '{partial_name}' -> '{resolved_partial}'")
            self.assertIsNotNone(resolved_partial)


if __name__ == "__main__":
    # Run with verbose output
    unittest.main(verbosity=2)
