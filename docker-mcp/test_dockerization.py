#!/usr/bin/env python3
"""
Test dockerization on the Express app
"""

import sys
import os
import asyncio

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from docker_tools.comprehensive_workflow_async import comprehensive_dockerize_and_test_async

async def test_dockerization():
    express_app_path = r"c:\Users\IswaryaK\dockermcp-python\docker-mcp\test-express-app"
    
    print("="*60)
    print("Testing Full Dockerization Workflow")
    print("="*60)
    
    print(f"\nDockerizing Express App: {express_app_path}")
    
    try:
        result = await comprehensive_dockerize_and_test_async(
            express_app_path,
            test_e2e=True,
            monitor_logs=False,
            auto_fix_errors=True
        )
        
        print("\n" + "="*60)
        print("DOCKERIZATION RESULT:")
        print("="*60)
        print(result.get("report", "No report available"))
        
        if "screenshots" in result:
            screenshots = result["screenshots"]
            if screenshots.get("initial"):
                print(f"\n📸 Initial screenshot captured: {len(screenshots['initial'])} characters")
            if screenshots.get("after"):
                print(f"📸 After screenshot captured: {len(screenshots['after'])} characters")
        
        return result
        
    except Exception as e:
        print(f"❌ Error during dockerization: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    asyncio.run(test_dockerization())