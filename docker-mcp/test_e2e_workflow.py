#!/usr/bin/env python3
"""
Test the complete E2E workflow with browser automation
"""

import sys
import os
import asyncio

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from docker_tools.e2e_tester_async import run_interactive_tests_async

async def test_e2e_workflow():
    express_app_path = r"c:\Users\IswaryaK\dockermcp-python\docker-mcp\test-express-app"
    
    print("="*60)
    print("Testing E2E Workflow with Browser Automation")
    print("="*60)
    
    try:
        print(f"\nTesting browser automation on: http://localhost:3000")
        
        # Run E2E tests with browser automation
        result = await run_interactive_tests_async(
            express_app_path,
            frontend_url="http://localhost:3000",
            backend_url="http://localhost:3000",
            headless=True,  # Use headless for this test
            perform_interactions=True
        )
        
        print("\n" + "="*60)
        print("E2E TEST RESULTS:")
        print("="*60)
        
        print(f"Status: {result.get('status', 'unknown')}")
        print(f"Tests passed: {result.get('passed', 0)}")
        print(f"Tests failed: {result.get('failed', 0)}")
        print(f"Total tests: {result.get('total', 0)}")
        
        # Check screenshots
        screenshots = result.get('screenshots', {})
        if screenshots.get('screenshot_initial'):
            print(f"\n📸 Initial screenshot: {len(screenshots['screenshot_initial'])} characters")
            print(f"   Starts with: {screenshots['screenshot_initial'][:50]}...")
        
        if screenshots.get('screenshot_after'):
            print(f"\n📸 After screenshot: {len(screenshots['screenshot_after'])} characters")
            print(f"   Starts with: {screenshots['screenshot_after'][:50]}...")
        
        # Show test results
        if 'tests' in result:
            print(f"\nTest Details:")
            for test in result['tests']:
                status = test.get('status', 'unknown')
                name = test.get('name', 'Unknown')
                icon = "✅" if status == 'passed' else "❌" if status == 'failed' else "⚠️"
                print(f"  {icon} {name}")
                if test.get('error'):
                    print(f"      Error: {test['error']}")
        
        # Show interactions
        if 'interactions' in result:
            print(f"\nInteractions Performed:")
            for interaction in result['interactions']:
                print(f"  - {interaction}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    asyncio.run(test_e2e_workflow())