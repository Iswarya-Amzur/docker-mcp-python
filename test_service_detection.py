"""
Test service detection improvements.
Verifies that only real services are detected, not utility folders.
"""
import sys
import os
from pathlib import Path

# Add docker-mcp directory to path
current_dir = Path(__file__).parent
docker_mcp_dir = current_dir / 'docker-mcp'
sys.path.insert(0, str(docker_mcp_dir))

from docker_tools.multi_service_handler_enhanced import detect_services

def test_service_detection(project_root: str):
    """Test service detection on a project."""
    print(f"\n{'='*100}")
    print(f"🔍 TESTING SERVICE DETECTION")
    print(f"{'='*100}\n")
    print(f"📂 Project Root: {project_root}\n")
    
    # Run detection
    result = detect_services(project_root)
    
    # Display results
    app_services = result.get('application_services', {})
    db_services = result.get('database_services', {})
    
    print(f"📊 DETECTION RESULTS:")
    print(f"{'='*100}\n")
    
    print(f"🎯 Application Services Found: {len(app_services)}")
    if app_services:
        for service_name, service_info in app_services.items():
            print(f"\n  ✅ Service: {service_name}")
            print(f"     Path: {service_info.get('path', 'unknown')}")
            print(f"     Type: {service_info.get('language', 'unknown')}")
            print(f"     Framework: {service_info.get('framework', 'unknown')}")
            print(f"     Category: {service_info.get('category', 'unknown')}")
            print(f"     Detection Method: {service_info.get('detection_method', 'unknown')}")
    else:
        print("  ⚠️  No application services detected")
    
    print(f"\n🗄️  Database Services Found: {len(db_services)}")
    if db_services:
        for db_name, db_info in db_services.items():
            print(f"  ✅ {db_name}: {db_info.get('type', 'unknown')}")
    else:
        print("  ℹ️  No database services detected")
    
    print(f"\n{'='*100}")
    print(f"🎯 VALIDATION CHECKS:")
    print(f"{'='*100}\n")
    
    # Validation checks
    checks = []
    
    # Check 1: No docs/tests folders detected as services
    invalid_services = [name for name in app_services.keys() 
                       if any(x in name.lower() for x in ['docs', 'doc', 'test', 'tests'])]
    if invalid_services:
        checks.append(f"❌ FAIL: Found docs/tests as services: {invalid_services}")
    else:
        checks.append("✅ PASS: No docs/tests folders detected as services")
    
    # Check 2: No config/scripts folders detected as services
    invalid_services = [name for name in app_services.keys() 
                       if any(x in name.lower() for x in ['config', 'script', 'utils', 'helpers'])]
    if invalid_services:
        checks.append(f"❌ FAIL: Found config/utility folders as services: {invalid_services}")
    else:
        checks.append("✅ PASS: No config/utility folders detected as services")
    
    # Check 3: docker-mcp itself not detected
    invalid_services = [name for name in app_services.keys() 
                       if 'docker-mcp' in name.lower() or 'docker_mcp' in name.lower()]
    if invalid_services:
        checks.append(f"❌ FAIL: docker-mcp detected as service: {invalid_services}")
    else:
        checks.append("✅ PASS: docker-mcp not detected as service")
    
    # Check 4: Only services with dependency files
    for service_name, service_info in app_services.items():
        service_path = Path(service_info['path'])
        has_deps = any([
            (service_path / 'package.json').exists(),
            (service_path / 'requirements.txt').exists(),
            (service_path / 'pyproject.toml').exists(),
            (service_path / 'pom.xml').exists(),
            (service_path / 'go.mod').exists(),
            (service_path / 'Cargo.toml').exists()
        ])
        if not has_deps:
            checks.append(f"❌ FAIL: Service '{service_name}' has no dependency file")
    
    if not any('FAIL' in check for check in checks):
        checks.append("\n✅ PASS: All services have dependency files")
    
    for check in checks:
        print(check)
    
    print(f"\n{'='*100}")
    
    # Summary
    total_checks = len(checks)
    passed = sum(1 for c in checks if '✅' in c)
    failed = sum(1 for c in checks if '❌' in c)
    
    print(f"\n📊 SUMMARY: {passed}/{total_checks} checks passed")
    if failed > 0:
        print(f"⚠️  {failed} validation failures detected")
    else:
        print("✅ All validations passed!")
    
    print(f"\n{'='*100}\n")
    
    return result, passed == total_checks

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        # Default to current workspace
        project_root = str(Path(__file__).parent)
        print(f"No project root specified, using: {project_root}")
    
    result, success = test_service_detection(project_root)
    
    if success:
        print("✅ Service detection is working correctly!")
        sys.exit(0)
    else:
        print("❌ Service detection has issues that need fixing")
        sys.exit(1)
