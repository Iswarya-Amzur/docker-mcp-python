#!/usr/bin/env python3
"""
Test script to verify automatic container health fix functionality.

This script tests the auto-fix feature that detects and fixes container health issues
like missing Python packages.
"""

import sys
import os

# Add docker-mcp to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'docker-mcp'))

from docker_tools.logging_monitor import check_and_fix_container_health
import json

def test_auto_fix():
    """Test the auto-fix functionality for container health issues."""
    
    print("=" * 70)
    print("Testing Automatic Container Health Fix")
    print("=" * 70)
    print()
    
    print("🔍 Checking container health and applying auto-fixes...")
    print()
    
    # Run health check with auto-fix
    result = check_and_fix_container_health()
    
    # Display results
    print(f"📊 Status: {result['status']}")
    print(f"📦 Containers checked: {len(result['containers_checked'])}")
    
    if result['containers_checked']:
        print(f"   Containers: {', '.join(result['containers_checked'])}")
    print()
    
    if result['unhealthy_containers']:
        print(f"⚠️  Unhealthy containers detected: {len(result['unhealthy_containers'])}")
        for container in result['unhealthy_containers']:
            print(f"   • {container}")
        print()
    else:
        print("✅ All containers are healthy!")
        print()
    
    if result['fixes_applied']:
        print(f"🔧 Auto-fixes applied: {len(result['fixes_applied'])}")
        for fix in result['fixes_applied']:
            print(f"   ✅ {fix}")
        print()
    else:
        print("ℹ️  No fixes needed")
        print()
    
    if result['errors']:
        print(f"⚠️  Issues encountered: {len(result['errors'])}")
        for error in result['errors']:
            print(f"   • {error}")
        print()
    
    print("=" * 70)
    print("Test Complete!")
    print("=" * 70)
    print()
    
    # Print JSON for debugging
    print("Full result (JSON):")
    print(json.dumps(result, indent=2))
    
    return result


if __name__ == "__main__":
    result = test_auto_fix()
    
    # Exit with appropriate code
    if result['status'] in ['healthy', 'success']:
        sys.exit(0)
    elif result['status'] == 'partial':
        sys.exit(1)
    else:
        sys.exit(2)
