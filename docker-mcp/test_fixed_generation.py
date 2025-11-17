#!/usr/bin/env python3
"""
Test the fixed dockerfile generation
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from docker_tools.multi_service_handler_enhanced import dockerize_full_project
from docker_tools.analyzer import analyze_application
from docker_tools.dockerfile_generator import generate_dockerfile

def test_fixed_generation():
    express_app_path = r"c:\Users\IswaryaK\dockermcp-python\docker-mcp\test-express-app"
    
    print("="*60)
    print("Testing Fixed Dockerfile Generation")
    print("="*60)
    
    try:
        # Test analysis first
        print("\n1. Testing Analysis:")
        analysis = analyze_application(express_app_path)
        print(f"   App Type: {analysis.get('app_type')}")
        print(f"   Framework: {analysis.get('framework')}")
        print(f"   Entry Point: {analysis.get('entry_point')}")
        print(f"   Port: {analysis.get('port')}")
        
        # Test dockerfile generation
        print(f"\n2. Testing Dockerfile Generation:")
        dockerfile_content = generate_dockerfile(express_app_path, analysis)
        print(f"   Generated Dockerfile ({len(dockerfile_content)} chars)")
        
        # Check if CMD is correct
        if 'CMD ["node", "index.js"]' in dockerfile_content:
            print("   ✅ CMD is correct: node index.js")
        elif 'CMD ["node", "None"]' in dockerfile_content:
            print("   ❌ CMD is wrong: node None")
        else:
            print(f"   ⚠️  CMD not found in expected format")
            
        # Test full dockerization
        print(f"\n3. Testing Full Dockerization:")
        result = dockerize_full_project(express_app_path, auto_start=False)
        print(f"   Result length: {len(result)} chars")
        print(f"   First 300 chars: {result[:300]}...")
        
        if "✅" in result:
            print("   ✅ Dockerization appears successful")
        else:
            print("   ⚠️  Check result for issues")
        
        print(f"\n4. Checking Generated Files:")
        dockerfile_exists = os.path.exists(os.path.join(express_app_path, 'Dockerfile'))
        compose_exists = os.path.exists(os.path.join(express_app_path, 'docker-compose.yml'))
        
        print(f"   Dockerfile exists: {dockerfile_exists}")
        print(f"   docker-compose.yml exists: {compose_exists}")
        
        if compose_exists:
            with open(os.path.join(express_app_path, 'docker-compose.yml'), 'r') as f:
                compose_content = f.read()
                if '- .:/app' in compose_content:
                    print("   ✅ Volume mapping is correct: .:/app")
                elif '- ./app:/app' in compose_content:
                    print("   ❌ Volume mapping is wrong: ./app:/app")
                else:
                    print("   ⚠️  Volume mapping format unexpected")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fixed_generation()