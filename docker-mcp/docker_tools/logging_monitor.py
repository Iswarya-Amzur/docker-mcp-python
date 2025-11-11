import subprocess
import os
import json
import logging
import time
import webbrowser
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


def generate_monitoring_compose(project_root: str, services: Dict) -> str:
    """
    Generate docker-compose configuration with Grafana, Loki, and Promtail.
    
    Args:
        project_root: Root directory of the project
        services: Dictionary of detected services
        
    Returns:
        Path to the generated monitoring compose file
    """
    monitoring_compose = """version: '3.8'

services:
  # Grafana for visualization
  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana-storage:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
    networks:
      - monitoring
    restart: unless-stopped

  # Loki for log aggregation
  loki:
    image: grafana/loki:latest
    container_name: loki
    ports:
      - "3100:3100"
    command: -config.file=/etc/loki/local-config.yaml
    volumes:
      - loki-storage:/loki
    networks:
      - monitoring
    restart: unless-stopped

  # Promtail for log collection
  promtail:
    image: grafana/promtail:latest
    container_name: promtail
    volumes:
      - /var/log:/var/log
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - ./promtail-config.yml:/etc/promtail/config.yml
    command: -config.file=/etc/promtail/config.yml
    networks:
      - monitoring
    restart: unless-stopped
    depends_on:
      - loki

networks:
  monitoring:
    driver: bridge

volumes:
  grafana-storage:
  loki-storage:
"""
    
    compose_path = os.path.join(project_root, "docker-compose.monitoring.yml")
    with open(compose_path, 'w') as f:
        f.write(monitoring_compose)
    
    return compose_path


def generate_promtail_config(project_root: str) -> str:
    """
    Generate Promtail configuration for log collection.
    
    Args:
        project_root: Root directory of the project
        
    Returns:
        Path to the generated promtail config
    """
    promtail_config = """server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: docker
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
        refresh_interval: 5s
    relabel_configs:
      - source_labels: ['__meta_docker_container_name']
        regex: '/(.*)'
        target_label: 'container'
      - source_labels: ['__meta_docker_container_log_stream']
        target_label: 'stream'
      - source_labels: ['__meta_docker_container_label_com_docker_compose_service']
        target_label: 'service'
"""
    
    config_path = os.path.join(project_root, "promtail-config.yml")
    with open(config_path, 'w') as f:
        f.write(promtail_config)
    
    return config_path


def generate_grafana_datasource(project_root: str) -> str:
    """
    Generate Grafana datasource configuration for Loki.
    
    Args:
        project_root: Root directory of the project
        
    Returns:
        Path to the generated datasource config
    """
    provisioning_dir = os.path.join(project_root, "grafana", "provisioning", "datasources")
    os.makedirs(provisioning_dir, exist_ok=True)
    
    datasource_config = """apiVersion: 1

datasources:
  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
    isDefault: true
    jsonData:
      maxLines: 1000
"""
    
    config_path = os.path.join(provisioning_dir, "loki.yml")
    with open(config_path, 'w') as f:
        f.write(datasource_config)
    
    return config_path


def generate_grafana_dashboard(project_root: str, services: List[str]) -> str:
    """
    Generate pre-configured Grafana dashboard for application logs.
    
    Args:
        project_root: Root directory of the project
        services: List of service names
        
    Returns:
        Path to the generated dashboard
    """
    dashboard_dir = os.path.join(project_root, "grafana", "provisioning", "dashboards")
    os.makedirs(dashboard_dir, exist_ok=True)
    
    # Dashboard provider config
    provider_config = """apiVersion: 1

providers:
  - name: 'Default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    options:
      path: /etc/grafana/provisioning/dashboards
"""
    
    provider_path = os.path.join(dashboard_dir, "provider.yml")
    with open(provider_path, 'w') as f:
        f.write(provider_config)
    
    # Create dashboard JSON
    dashboard = {
        "dashboard": {
            "title": "Application Logs",
            "tags": ["docker", "logs"],
            "timezone": "browser",
            "panels": [],
            "schemaVersion": 16,
            "version": 0,
            "refresh": "5s"
        },
        "overwrite": true
    }
    
    # Add panel for each service
    panel_y = 0
    for idx, service in enumerate(services):
        panel = {
            "id": idx + 1,
            "gridPos": {"h": 8, "w": 24, "x": 0, "y": panel_y},
            "type": "logs",
            "title": f"{service.capitalize()} Logs",
            "datasource": "Loki",
            "targets": [{
                "expr": f'{{container=~".*{service}.*"}}',
                "refId": "A"
            }],
            "options": {
                "showTime": True,
                "showLabels": True,
                "sortOrder": "Descending"
            }
        }
        dashboard["dashboard"]["panels"].append(panel)
        panel_y += 8
    
    dashboard_path = os.path.join(dashboard_dir, "app-logs.json")
    with open(dashboard_path, 'w') as f:
        json.dump(dashboard, f, indent=2)
    
    return dashboard_path


def start_monitoring_stack(project_root: str) -> Dict:
    """
    Start Grafana, Loki, and Promtail services.
    
    Args:
        project_root: Root directory of the project
        
    Returns:
        Dictionary with status and URLs
    """
    try:
        logger.info("Starting monitoring stack")
        result = subprocess.run(
            ["docker-compose", "-f", "docker-compose.monitoring.yml", "up", "-d"],
            cwd=project_root,
            capture_output=True,
            encoding='utf-8',
            errors='replace',
            timeout=120
        )
        
        if result.returncode == 0:
            # Wait for Grafana to be ready
            time.sleep(5)
            return {
                "status": "success",
                "grafana_url": "http://localhost:3001",
                "loki_url": "http://localhost:3100",
                "credentials": {"username": "admin", "password": "admin"},
                "output": result.stdout
            }
        else:
            return {
                "status": "error",
                "message": "Failed to start monitoring stack",
                "error": result.stderr
            }
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "message": "Monitoring stack startup timeout"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error starting monitoring stack: {str(e)}"
        }


def fetch_logs_from_loki(loki_url: str, query: str, limit: int = 100) -> Dict:
    """
    Fetch logs from Loki.
    
    Args:
        loki_url: URL of Loki service
        query: LogQL query
        limit: Maximum number of log lines
        
    Returns:
        Dictionary with logs
    """
    import requests
    
    try:
        params = {
            "query": query,
            "limit": limit,
            "direction": "backward"
        }
        
        response = requests.get(
            f"{loki_url}/loki/api/v1/query_range",
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            logs = []
            
            if "data" in data and "result" in data["data"]:
                for stream in data["data"]["result"]:
                    for entry in stream.get("values", []):
                        timestamp, log_line = entry
                        logs.append({
                            "timestamp": timestamp,
                            "log": log_line,
                            "labels": stream.get("stream", {})
                        })
            
            return {
                "status": "success",
                "logs": logs,
                "count": len(logs)
            }
        else:
            return {
                "status": "error",
                "message": f"Loki returned status {response.status_code}"
            }
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error fetching logs: {str(e)}"
        }


def analyze_logs_for_errors(logs: List[Dict]) -> Dict:
    """
    Analyze logs to identify errors, exceptions, and patterns.
    
    Args:
        logs: List of log entries
        
    Returns:
        Dictionary with analysis results
    """
    import re
    
    analysis = {
        "total_logs": len(logs),
        "errors": [],
        "warnings": [],
        "exceptions": [],
        "patterns": {}
    }
    
    # Error patterns
    error_patterns = [
        r"ERROR",
        r"Exception",
        r"CRITICAL",
        r"FATAL",
        r"Traceback",
        r"\d{3} (4\d{2}|5\d{2})",  # 4xx and 5xx HTTP codes
        r"failed",
        r"failure",
        r"not found",
        r"denied"
    ]
    
    warning_patterns = [
        r"WARNING",
        r"WARN",
        r"deprecated"
    ]
    
    for log_entry in logs:
        log_line = log_entry.get("log", "")
        
        # Check for errors
        for pattern in error_patterns:
            if re.search(pattern, log_line, re.IGNORECASE):
                analysis["errors"].append({
                    "timestamp": log_entry.get("timestamp"),
                    "log": log_line,
                    "pattern": pattern
                })
                break
        
        # Check for warnings
        for pattern in warning_patterns:
            if re.search(pattern, log_line, re.IGNORECASE):
                analysis["warnings"].append({
                    "timestamp": log_entry.get("timestamp"),
                    "log": log_line
                })
                break
        
        # Extract exceptions
        if "Exception" in log_line or "Traceback" in log_line:
            analysis["exceptions"].append({
                "timestamp": log_entry.get("timestamp"),
                "log": log_line
            })
    
    return analysis


def suggest_fixes_for_errors(analysis: Dict) -> List[Dict]:
    """
    Analyze errors and suggest potential code fixes.
    
    Args:
        analysis: Log analysis results
        
    Returns:
        List of suggested fixes
    """
    suggestions = []
    
    # Common error patterns and fixes
    fix_patterns = {
        r"connection.*refused": {
            "issue": "Connection Refused",
            "possible_causes": [
                "Service not running",
                "Wrong port configuration",
                "Firewall blocking connection"
            ],
            "fixes": [
                "Check if the service is running: docker ps",
                "Verify port mappings in docker-compose.yml",
                "Check network connectivity between containers",
                "Ensure service dependencies are started first"
            ]
        },
        r"module.*not found|import.*error": {
            "issue": "Module Not Found / Import Error",
            "possible_causes": [
                "Missing dependency",
                "Incorrect Python path",
                "Package not installed in Docker image"
            ],
            "fixes": [
                "Add missing package to requirements.txt",
                "Rebuild Docker image: docker-compose build",
                "Check PYTHONPATH environment variable",
                "Verify package is installed: pip list"
            ]
        },
        r"permission denied": {
            "issue": "Permission Denied",
            "possible_causes": [
                "Incorrect file permissions",
                "User doesn't have access",
                "Docker volume mount permissions"
            ],
            "fixes": [
                "Add chmod command in Dockerfile: RUN chmod +x /app/script.sh",
                "Run container with appropriate user",
                "Check volume mount permissions",
                "Use Docker USER directive"
            ]
        },
        r"out of memory|oom": {
            "issue": "Out of Memory",
            "possible_causes": [
                "Memory leak",
                "Insufficient memory allocation",
                "Large dataset processing"
            ],
            "fixes": [
                "Increase memory limit in docker-compose.yml: mem_limit: 2g",
                "Optimize code to reduce memory usage",
                "Use pagination for large datasets",
                "Check for memory leaks"
            ]
        },
        r"database.*error|sql.*error": {
            "issue": "Database Error",
            "possible_causes": [
                "Database not ready",
                "Wrong credentials",
                "Connection pool exhausted"
            ],
            "fixes": [
                "Add healthcheck and depends_on in docker-compose.yml",
                "Verify DATABASE_URL environment variable",
                "Check database credentials",
                "Implement connection retry logic"
            ]
        },
        r"404|not found": {
            "issue": "Resource Not Found (404)",
            "possible_causes": [
                "Incorrect URL/endpoint",
                "Route not registered",
                "File missing"
            ],
            "fixes": [
                "Check API route definitions",
                "Verify URL path is correct",
                "Check if static files are copied in Dockerfile",
                "Review reverse proxy configuration"
            ]
        },
        r"500|internal server error": {
            "issue": "Internal Server Error (500)",
            "possible_causes": [
                "Unhandled exception",
                "Code error",
                "Configuration issue"
            ],
            "fixes": [
                "Check application logs for stack traces",
                "Add error handling and logging",
                "Verify environment variables are set",
                "Test code locally before deploying"
            ]
        }
    }
    
    # Analyze errors and match with patterns
    for error in analysis.get("errors", []):
        log_line = error.get("log", "")
        
        for pattern, fix_info in fix_patterns.items():
            if re.search(pattern, log_line, re.IGNORECASE):
                suggestions.append({
                    "error_log": log_line,
                    "timestamp": error.get("timestamp"),
                    "issue": fix_info["issue"],
                    "possible_causes": fix_info["possible_causes"],
                    "suggested_fixes": fix_info["fixes"]
                })
                break
    
    return suggestions


def setup_complete_monitoring(project_root: str, services: List[str]) -> str:
    """
    Complete setup: Generate configs, start monitoring stack, configure dashboards.
    
    Args:
        project_root: Root directory of the project
        services: List of service names to monitor
        
    Returns:
        Setup report
    """
    report = "🔍 **Monitoring Setup Report**\n\n"
    report += f"**Project:** {project_root}\n\n"
    
    # Step 1: Generate Promtail config
    report += "**Step 1: Generating log collection configuration...**\n"
    try:
        promtail_path = generate_promtail_config(project_root)
        report += f"✅ Promtail config: {promtail_path}\n\n"
    except Exception as e:
        report += f"❌ Error: {str(e)}\n\n"
        return report
    
    # Step 2: Generate Grafana datasource
    report += "**Step 2: Configuring Grafana datasource...**\n"
    try:
        datasource_path = generate_grafana_datasource(project_root)
        report += f"✅ Grafana datasource: {datasource_path}\n\n"
    except Exception as e:
        report += f"❌ Error: {str(e)}\n\n"
        return report
    
    # Step 3: Generate dashboard
    report += "**Step 3: Creating Grafana dashboard...**\n"
    try:
        dashboard_path = generate_grafana_dashboard(project_root, services)
        report += f"✅ Dashboard config: {dashboard_path}\n\n"
    except Exception as e:
        report += f"❌ Error: {str(e)}\n\n"
        return report
    
    # Step 4: Generate monitoring compose
    report += "**Step 4: Generating monitoring docker-compose...**\n"
    try:
        compose_path = generate_monitoring_compose(project_root, {})
        report += f"✅ Monitoring compose: {compose_path}\n\n"
    except Exception as e:
        report += f"❌ Error: {str(e)}\n\n"
        return report
    
    # Step 5: Start monitoring stack
    report += "**Step 5: Starting monitoring services...**\n"
    start_result = start_monitoring_stack(project_root)
    
    if start_result["status"] == "success":
        report += "✅ Monitoring stack started\n\n"
        report += "=" * 60 + "\n"
        report += "📊 **GRAFANA DASHBOARD READY!**\n"
        report += "=" * 60 + "\n\n"
        report += f"🌐 Grafana URL: {start_result['grafana_url']}\n"
        report += f"👤 Username: {start_result['credentials']['username']}\n"
        report += f"🔑 Password: {start_result['credentials']['password']}\n\n"
        report += f"📡 Loki URL: {start_result['loki_url']}\n\n"
        report += "**Next Steps:**\n"
        report += "1. Open Grafana in your browser\n"
        report += "2. Login with the credentials above\n"
        report += "3. Navigate to Dashboards → Application Logs\n"
        report += "4. View real-time logs from your services\n\n"
        report += "**Services Monitored:**\n"
        for service in services:
            report += f"  - {service}\n"
    else:
        report += f"❌ {start_result.get('message')}\n"
        if 'error' in start_result:
            report += f"Error: {start_result['error']}\n"
    
    return report


def launch_grafana_dashboard(grafana_url: str = "http://localhost:3001") -> str:
    """
    Open Grafana dashboard in the default browser.
    
    Args:
        grafana_url: URL of Grafana
        
    Returns:
        Status message
    """
    try:
        webbrowser.open(grafana_url)
        return f"✅ Grafana dashboard opened in browser: {grafana_url}"
    except Exception as e:
        return f"❌ Error opening browser: {str(e)}\nPlease open manually: {grafana_url}"
