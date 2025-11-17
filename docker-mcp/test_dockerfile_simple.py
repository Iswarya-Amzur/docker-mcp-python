#!/usr/bin/env python3
"""
Simple test to isolate dockerfile generation issues
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from docker_tools.multi_service_handler_enhanced import detect_services, dockerize_full_project

def test_dockerfile_generation():
    express_app_path = r"c:\Users\IswaryaK\dockermcp-python\docker-mcp\test-express-app"
    
    print("="*60)
    print("Testing Dockerfile Generation")
    print("="*60)
    
    print(f"\nTesting on Express App: {express_app_path}")
    
    try:
        # Test service detection
        print("\n1. Detecting Services:")
        services = detect_services(express_app_path)
        print(f"   Detection result type: {type(services)}")
        print(f"   Detection result keys: {list(services.keys()) if isinstance(services, dict) else 'Not a dict'}")
        
        if isinstance(services, dict) and 'application_services' in services:
            app_services = services['application_services']
            print(f"   Application services: {list(app_services.keys()) if isinstance(app_services, dict) else 'Not a dict'}")
            
            for name, info in app_services.items():
                print(f"\n   Service: {name}")
                print(f"     Type: {type(info)}")
                if isinstance(info, dict):
                    for key in ['type', 'framework', 'language', 'path']:
                        if key in info:
                            print(f"     {key}: {info[key]}")
        
        print(f"\n2. Testing dockerize_full_project:")
        try:
            result = dockerize_full_project(express_app_path, auto_start=False)
            print(f"   Result: {result[:200]}..." if len(str(result)) > 200 else f"   Result: {result}")
        except Exception as e:
            print(f"   ❌ Error in dockerize_full_project: {e}")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_dockerfile_generation()