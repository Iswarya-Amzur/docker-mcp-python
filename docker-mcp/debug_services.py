#!/usr/bin/env python3
"""
Debug service detection
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from docker_tools.multi_service_handler_enhanced import detect_services
from docker_tools.comprehensive_workflow_async import detect_database_services

def debug_service_detection():
    express_app_path = r"c:\Users\IswaryaK\dockermcp-python\docker-mcp\test-express-app"
    
    print("="*60)
    print("Debugging Service Detection")
    print("="*60)
    
    print(f"\nTesting on Express App: {express_app_path}")
    
    try:
        # Test service detection
        print("\n1. Detecting Application Services:")
        services = detect_services(express_app_path)
        print(f"   Found {len(services)} services:")
        
        for name, info in services.items():
            print(f"\n   Service: {name}")
            for key, value in info.items():
                if isinstance(value, dict) and len(str(value)) > 100:
                    print(f"     {key}: {type(value).__name__} (truncated)")
                else:
                    print(f"     {key}: {value}")
        
        # Test database detection
        print(f"\n2. Detecting Database Services:")
        databases = detect_database_services(express_app_path)
        print(f"   Found {len(databases)} databases:")
        
        for name, info in databases.items():
            print(f"\n   Database: {name}")
            for key, value in info.items():
                print(f"     {key}: {value}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_service_detection()