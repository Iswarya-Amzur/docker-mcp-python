#!/usr/bin/env python3
"""
Test script to verify dynamic port detection functionality
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from docker_tools.port_detector import detect_port_with_fallback, detect_ports_in_code
from docker_tools.analyzer import analyze_application

def test_port_detection():
    # Test on the Express app
    express_app_path = r"c:\Users\IswaryaK\dockermcp-python\docker-mcp\test-express-app"
    
    print("="*60)
    print("Testing Port Detection")
    print("="*60)
    
    print(f"\nTesting on Express App: {express_app_path}")
    
    # Test direct port detection
    print("\n1. Direct Port Detection:")
    port_result = detect_ports_in_code(express_app_path, "express")
    print(f"   Result: {port_result}")
    
    # Test with fallback
    print("\n2. Port Detection with Fallback:")
    final_port = detect_port_with_fallback(express_app_path, "express")
    print(f"   Final Port: {final_port}")
    
    # Test full analysis
    print("\n3. Full Application Analysis:")
    analysis = analyze_application(express_app_path)
    print(f"   App Type: {analysis.get('app_type')}")
    print(f"   Framework: {analysis.get('framework')}")
    print(f"   Detected Port: {analysis.get('port')}")
    print(f"   Start Command: {analysis.get('start_command')}")
    
    print("\n" + "="*60)
    print("Port Detection Test Complete")
    print("="*60)

if __name__ == "__main__":
    test_port_detection()