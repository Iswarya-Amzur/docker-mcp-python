"""
Quick debug test to see what's happening with E2E testing.
Run this directly to test without MCP layer.
"""
import asyncio
import logging
import sys
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Add docker-mcp directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
docker_mcp_dir = os.path.join(current_dir, 'docker-mcp')
sys.path.insert(0, docker_mcp_dir)

from docker_tools.e2e_tester_async import run_interactive_tests_async, launch_and_test_async

async def test_direct():
    """Test the E2E tester directly without MCP"""
    print("\n" + "="*100)
    print("🔍 DIRECT TEST OF E2E FUNCTIONALITY")
    print("="*100 + "\n")
    
    # Use the currently running containers (test-app)
    project_root = r"C:\Users\IswaryaK\dockermcp-python\docker-mcp"
    frontend_url = "http://localhost:3000"
    backend_url = "http://localhost:8000"
    
    print(f"📂 Project Root: {project_root}")
    print(f"🌐 Frontend URL: {frontend_url}")
    print(f"🔗 Backend URL: {backend_url}")
    print(f"🎬 Starting test...\n")
    
    try:
        # Test the core function directly
        results = await run_interactive_tests_async(
            project_root=project_root,
            frontend_url=frontend_url,
            backend_url=backend_url,
            headless=False,
            perform_interactions=True
        )
        
        print("\n" + "="*100)
        print("📊 TEST RESULTS")
        print("="*100)
        print(f"Status: {results.get('status', 'unknown')}")
        print(f"Total Tests: {results.get('total', 0)}")
        print(f"Passed: {results.get('passed', 0)}")
        print(f"Failed: {results.get('failed', 0)}")
        print(f"Screenshots: {len([k for k in results.keys() if 'screenshot' in k])}")
        print(f"Interactions: {len(results.get('interactions', []))}")
        
        if results.get('screenshot_initial'):
            print(f"\n✅ Initial screenshot captured: {len(results['screenshot_initial'])} chars")
        else:
            print("\n❌ No initial screenshot")
            
        if results.get('screenshot_after'):
            print(f"✅ After screenshot captured: {len(results['screenshot_after'])} chars")
        else:
            print("❌ No after screenshot")
        
        print("\n📝 Test Details:")
        for test in results.get('tests', []):
            status_emoji = "✅" if test.get('status') == 'passed' else "❌"
            print(f"  {status_emoji} {test.get('name', 'Unknown')}: {test.get('status', 'unknown')}")
        
        if results.get('interactions'):
            print("\n🎯 Interactions Performed:")
            for interaction in results['interactions'][:10]:  # Show first 10
                print(f"  • {interaction}")
        
        print("\n" + "="*100)
        
        return results
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_full_workflow():
    """Test the full workflow including container management"""
    print("\n" + "="*100)
    print("🔍 FULL WORKFLOW TEST (with container management)")
    print("="*100 + "\n")
    
    project_root = r"C:\Users\IswaryaK\dockermcp-python\docker-mcp"
    
    try:
        results = await launch_and_test_async(
            project_root=project_root,
            backend_port=8000,
            frontend_port=3000,
            cleanup=False,
            headless=False,
            show_browser=True
        )
        
        print("\n" + "="*100)
        print("📊 WORKFLOW RESULTS")
        print("="*100)
        print(f"Status: {results.get('status', 'unknown')}")
        
        print("\n📝 Steps:")
        for step in results.get('steps', []):
            status_emoji = "✅" if step.get('status') == 'success' else "❌"
            print(f"  {status_emoji} {step.get('name', 'Unknown')}: {step.get('status', 'unknown')}")
        
        print(f"\nTests: {len(results.get('tests', []))}")
        print(f"Screenshots: {len(results.get('screenshots', {}))}")
        
        print("\n" + "="*100)
        
        return results
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("\n🚀 E2E Testing Debug Script")
    print("This will test the browser automation directly\n")
    
    print("Choose test mode:")
    print("1. Direct test (run_interactive_tests_async)")
    print("2. Full workflow test (launch_and_test_async)")
    print("3. Both")
    
    choice = input("\nEnter choice (1/2/3) or press Enter for option 1: ").strip() or "1"
    
    if choice == "1":
        asyncio.run(test_direct())
    elif choice == "2":
        asyncio.run(test_full_workflow())
    elif choice == "3":
        asyncio.run(test_direct())
        print("\n\n")
        asyncio.run(test_full_workflow())
    else:
        print("Invalid choice")
