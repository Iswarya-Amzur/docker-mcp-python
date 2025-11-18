#!/usr/bin/env python3
"""
Regenerate monitoring configurations with correct labels.

This script regenerates:
- promtail-config.yml (with explicit job="docker" label)
- Grafana dashboard (with correct id labels for metrics and job labels for logs)
- docker-compose.monitoring.yml (if needed)

Usage:
    python regenerate_configs.py <project_root>
    
Example:
    python regenerate_configs.py ./test-multi-app
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'docker-mcp'))

from docker_tools.logging_monitor import (
    generate_promtail_config,
    generate_grafana_dashboard,
    generate_grafana_datasource,
    setup_complete_monitoring
)
from docker_tools.multi_service_handler import detect_services


def regenerate_monitoring_configs(project_root: str):
    """Regenerate all monitoring configuration files."""
    
    print("=" * 60)
    print("REGENERATING MONITORING CONFIGURATIONS")
    print("=" * 60)
    print()
    
    # Make paths absolute
    project_root = os.path.abspath(project_root)
    
    if not os.path.exists(project_root):
        print(f"❌ Error: Project root not found: {project_root}")
        return False
    
    print(f"📁 Project root: {project_root}")
    print()
    
    # Step 1: Detect services
    print("🔍 Detecting services...")
    detected = detect_services(project_root)
    
    if detected:
        service_list = list(detected.keys())
        print(f"✅ Detected {len(service_list)} service(s): {', '.join(service_list)}")
    else:
        service_list = ["app"]
        print(f"⚠️  No services detected, using default: 'app'")
    print()
    
    # Step 2: Generate Promtail config
    print("📝 Generating Promtail configuration...")
    promtail_path = generate_promtail_config(project_root)
    print(f"✅ Created: {promtail_path}")
    
    # Verify job label is in config
    with open(promtail_path, 'r') as f:
        content = f.read()
        if "target_label: 'job'" in content:
            print("   ✓ Job label configured correctly")
        else:
            print("   ⚠️  Warning: Job label may not be set")
    print()
    
    # Step 3: Generate Grafana datasource
    print("📝 Generating Grafana datasource configuration...")
    datasource_path = generate_grafana_datasource(project_root)
    print(f"✅ Created: {datasource_path}")
    print()
    
    # Step 4: Generate Grafana dashboard
    print("📝 Generating Grafana dashboard...")
    dashboard_path = generate_grafana_dashboard(project_root, service_list)
    print(f"✅ Created: {dashboard_path}")
    
    # Verify queries use correct labels
    import json
    with open(dashboard_path, 'r') as f:
        dashboard_data = json.load(f)
        
    # Check metric panels
    metric_panels = [p for p in dashboard_data.get("panels", []) if p.get("datasource", {}).get("type") == "prometheus"]
    log_panels = [p for p in dashboard_data.get("panels", []) if p.get("datasource", {}).get("type") == "loki"]
    
    print()
    print(f"   📊 {len(metric_panels)} metric panels (should use 'id' label)")
    for panel in metric_panels:
        expr = panel.get("targets", [{}])[0].get("expr", "")
        if 'id=~"/docker/.+"' in expr or 'id=~"/docker/' in expr:
            print(f"   ✓ {panel.get('title')}: Uses correct 'id' label")
        else:
            print(f"   ⚠️  {panel.get('title')}: May use incorrect label")
    
    print()
    print(f"   📋 {len(log_panels)} log panels (should use 'job=\"docker\"')")
    for panel in log_panels:
        expr = panel.get("targets", [{}])[0].get("expr", "")
        if 'job="docker"' in expr:
            print(f"   ✓ {panel.get('title')}: Uses correct 'job' label")
        else:
            print(f"   ⚠️  {panel.get('title')}: May use incorrect label")
    print()
    
    # Step 5: Setup complete monitoring stack (docker-compose, prometheus, etc.)
    print("📝 Setting up complete monitoring stack...")
    result = setup_complete_monitoring(project_root, service_list)
    print(f"✅ Monitoring stack configured")
    print()
    
    # Summary
    print("=" * 60)
    print("✅ CONFIGURATION REGENERATION COMPLETE")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Restart monitoring containers:")
    print(f"   cd {project_root}")
    print("   docker-compose -f docker-compose.monitoring.yml down")
    print("   docker-compose -f docker-compose.monitoring.yml up -d")
    print()
    print("2. Wait 30-45 seconds for services to fully initialize")
    print()
    print("3. Access Grafana:")
    print("   http://localhost:3001")
    print("   Username: admin")
    print("   Password: admin")
    print()
    print("4. Verify in Grafana dashboard:")
    print("   - Metric panels show container CPU/Memory/Network/Disk")
    print("   - Log panels show container logs")
    print()
    print("5. Check labels in Loki:")
    print("   curl http://localhost:3100/loki/api/v1/labels")
    print("   (Should include 'job' in the list)")
    print()
    
    return True


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python regenerate_configs.py <project_root>")
        print()
        print("Example:")
        print("  python regenerate_configs.py ./test-multi-app")
        print("  python regenerate_configs.py C:\\Projects\\my-app")
        sys.exit(1)
    
    project_root = sys.argv[1]
    success = regenerate_monitoring_configs(project_root)
    
    sys.exit(0 if success else 1)
