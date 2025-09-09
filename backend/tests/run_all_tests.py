#!/usr/bin/env python3
"""
Comprehensive test runner for RAG system debugging
"""
import unittest
import sys
import os
import traceback
from io import StringIO

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_tests_with_detailed_output():
    """Run all tests and capture detailed output"""

    print("=" * 80)
    print("RAG SYSTEM COMPREHENSIVE TEST SUITE")
    print("=" * 80)

    # Test modules to run
    test_modules = ["test_course_search_tool", "test_ai_generator", "test_rag_system"]

    results = {}

    for module_name in test_modules:
        print(f"\n{'='*50}")
        print(f"TESTING MODULE: {module_name}")
        print(f"{'='*50}")

        try:
            # Import the test module
            test_module = __import__(module_name)

            # Create test suite
            loader = unittest.TestLoader()
            suite = loader.loadTestsFromModule(test_module)

            # Run tests with detailed output
            stream = StringIO()
            runner = unittest.TextTestRunner(
                stream=stream, verbosity=2, failfast=False, buffer=False
            )

            result = runner.run(suite)

            # Capture results
            output = stream.getvalue()

            results[module_name] = {
                "result": result,
                "output": output,
                "tests_run": result.testsRun,
                "failures": len(result.failures),
                "errors": len(result.errors),
                "success": result.wasSuccessful(),
            }

            print(output)

            if result.failures:
                print(f"\nFAILURES in {module_name}:")
                for test, traceback_str in result.failures:
                    print(f"  FAILED: {test}")
                    print(f"  {traceback_str}")

            if result.errors:
                print(f"\nERRORS in {module_name}:")
                for test, traceback_str in result.errors:
                    print(f"  ERROR: {test}")
                    print(f"  {traceback_str}")

        except Exception as e:
            print(f"CRITICAL ERROR importing/running {module_name}: {e}")
            traceback.print_exc()
            results[module_name] = {
                "result": None,
                "output": "",
                "tests_run": 0,
                "failures": 0,
                "errors": 1,
                "success": False,
                "import_error": str(e),
            }

    # Summary report
    print(f"\n{'='*80}")
    print("COMPREHENSIVE TEST SUMMARY")
    print(f"{'='*80}")

    total_tests = 0
    total_failures = 0
    total_errors = 0
    successful_modules = 0

    for module_name, module_results in results.items():
        total_tests += module_results["tests_run"]
        total_failures += module_results["failures"]
        total_errors += module_results["errors"]

        if module_results["success"]:
            successful_modules += 1
            status = "✅ PASSED"
        else:
            status = "❌ FAILED"

        print(
            f"{module_name:30} {status:10} Tests:{module_results['tests_run']:3} Failures:{module_results['failures']:2} Errors:{module_results['errors']:2}"
        )

        if "import_error" in module_results:
            print(f"  └─ Import Error: {module_results['import_error']}")

    print(f"\n{'='*50}")
    print(f"OVERALL RESULTS:")
    print(f"  Modules: {successful_modules}/{len(test_modules)} passed")
    print(
        f"  Tests:   {total_tests - total_failures - total_errors}/{total_tests} passed"
    )
    print(f"  Failures: {total_failures}")
    print(f"  Errors:   {total_errors}")

    if total_failures + total_errors == 0:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("🚨 SOME TESTS FAILED - See details above")

    print(f"{'='*50}")

    return results


if __name__ == "__main__":
    results = run_tests_with_detailed_output()
