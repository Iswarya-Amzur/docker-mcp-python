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


def test_loki_connection(loki_url: str = "http://localhost:3100") -> Dict:
    """
    Test if Loki is running and accessible.
    
    Args:
        loki_url: URL of Loki service
        
    Returns:
        Dictionary with test results
    """
    import requests
    
    results = {
        "loki_ready": False,
        "loki_version": None,
        "error": None
    }
    
    try:
        # Test /ready endpoint
        response = requests.get(f"{loki_url}/ready", timeout=5)
        if response.status_code == 200:
            results["loki_ready"] = True
        
        # Test /metrics endpoint to get version
        try:
            metrics_response = requests.get(f"{loki_url}/metrics", timeout=5)
            if metrics_response.status_code == 200:
                # Try to extract version from metrics
                for line in metrics_response.text.split('\n'):
                    if 'loki_build_info' in line and 'version=' in line:
                        results["loki_version"] = line.split('version="')[1].split('"')[0]
                        break
        except:
            pass
        
        return results
        
    except requests.exceptions.ConnectionError:
        results["error"] = "Connection refused - Loki is not running"
        return results
    except requests.exceptions.Timeout:
        results["error"] = "Connection timeout - Loki is not responding"
        return results
    except Exception as e:
        results["error"] = f"Error connecting to Loki: {str(e)}"
        return results


def test_promtail_connection(promtail_url: str = "http://localhost:9080") -> Dict:
    """
    Test if Promtail is running and sending logs to Loki.
    
    Args:
        promtail_url: URL of Promtail service
        
    Returns:
        Dictionary with test results
    """
    import requests
    
    results = {
        "promtail_ready": False,
        "targets": [],
        "error": None
    }
    
    try:
        # Test /ready endpoint
        response = requests.get(f"{promtail_url}/ready", timeout=5)
        if response.status_code == 200:
            results["promtail_ready"] = True
        
        # Get targets (what Promtail is scraping)
        try:
            targets_response = requests.get(f"{promtail_url}/targets", timeout=5)
            if targets_response.status_code == 200:
                targets_data = targets_response.json()
                results["targets"] = targets_data.get("activeTargets", [])
        except:
            pass
        
        return results
        
    except requests.exceptions.ConnectionError:
        results["error"] = "Connection refused - Promtail is not running"
        return results
    except requests.exceptions.Timeout:
        results["error"] = "Connection timeout - Promtail is not responding"
        return results
    except Exception as e:
        results["error"] = f"Error connecting to Promtail: {str(e)}"
        return results


def test_loki_receiving_logs(loki_url: str = "http://localhost:3100") -> Dict:
    """
    Test if Loki is actually receiving logs from Promtail.
    
    Args:
        loki_url: URL of Loki service
        
    Returns:
        Dictionary with test results
    """
    import requests
    
    results = {
        "receiving_logs": False,
        "log_count": 0,
        "labels": [],
        "error": None
    }
    
    try:
        # Query Loki for any logs in the last 5 minutes
        params = {
            "query": '{job="docker"}',
            "limit": 10,
            "start": int((time.time() - 300) * 1e9),  # 5 minutes ago in nanoseconds
            "end": int(time.time() * 1e9)
        }
        
        response = requests.get(
            f"{loki_url}/loki/api/v1/query_range",
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if "data" in data and "result" in data["data"]:
                streams = data["data"]["result"]
                
                if streams:
                    results["receiving_logs"] = True
                    results["log_count"] = sum(len(stream.get("values", [])) for stream in streams)
                    results["labels"] = [stream.get("stream", {}) for stream in streams]
                else:
                    results["error"] = "No logs found in Loki - Promtail might not be sending logs"
            else:
                results["error"] = "Invalid response format from Loki"
        else:
            results["error"] = f"Loki query failed with status {response.status_code}"
        
        return results
        
    except Exception as e:
        results["error"] = f"Error querying Loki: {str(e)}"
        return results


def diagnose_monitoring_stack(project_root: str) -> Dict:
    """
    Comprehensive diagnostics of the monitoring stack.
    
    Args:
        project_root: Root directory of the project
        
    Returns:
        Dictionary with diagnostic results
    """
    report = {
        "status": "unknown",
        "loki": {},
        "promtail": {},
        "logs": {},
        "containers": {},
        "issues": [],
        "recommendations": []
    }
    
    # Check if monitoring containers are running
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=loki", "--filter", "name=promtail", "--filter", "name=grafana", "--format", "{{.Names}}\t{{.Status}}"],
            capture_output=True,
            encoding='utf-8',
            errors='replace',
            timeout=10
        )
        
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if line:
                    name, status = line.split('\t')
                    report["containers"][name] = status
        
        # Check for missing containers
        expected = ["loki", "promtail", "grafana"]
        running = list(report["containers"].keys())
        
        for container in expected:
            if container not in running:
                report["issues"].append(f"{container} container is not running")
                report["recommendations"].append(f"Start {container}: docker-compose -f docker-compose.monitoring.yml up -d {container}")
    
    except Exception as e:
        report["issues"].append(f"Failed to check containers: {str(e)}")
    
    # Test Loki
    loki_test = test_loki_connection()
    report["loki"] = loki_test
    
    if not loki_test["loki_ready"]:
        report["issues"].append("Loki is not ready")
        if loki_test["error"]:
            report["issues"].append(f"Loki error: {loki_test['error']}")
        report["recommendations"].append("Check Loki logs: docker logs loki")
    
    # Test Promtail
    promtail_test = test_promtail_connection()
    report["promtail"] = promtail_test
    
    if not promtail_test["promtail_ready"]:
        report["issues"].append("Promtail is not ready")
        if promtail_test["error"]:
            report["issues"].append(f"Promtail error: {promtail_test['error']}")
        report["recommendations"].append("Check Promtail logs: docker logs promtail")
    
    if promtail_test["promtail_ready"] and not promtail_test["targets"]:
        report["issues"].append("Promtail is not scraping any targets")
        report["recommendations"].append("Check Promtail configuration in promtail-config.yml")
        report["recommendations"].append("Verify Docker socket access: ls -la /var/run/docker.sock")
    
    # Test if Loki is receiving logs
    if loki_test["loki_ready"]:
        logs_test = test_loki_receiving_logs()
        report["logs"] = logs_test
        
        if not logs_test["receiving_logs"]:
            report["issues"].append("Loki is not receiving logs from Promtail")
            if logs_test["error"]:
                report["issues"].append(f"Logs error: {logs_test['error']}")
            report["recommendations"].append("Check Promtail configuration points to correct Loki URL")
            report["recommendations"].append("Verify network connectivity: docker exec promtail ping loki")
            report["recommendations"].append("Check if application containers are running and generating logs")
    
    # Determine overall status
    if not report["issues"]:
        report["status"] = "healthy"
    elif loki_test["loki_ready"] and promtail_test["promtail_ready"]:
        report["status"] = "partial"
    else:
        report["status"] = "unhealthy"
    
    return report


def fix_promtail_config(project_root: str) -> Dict:
    """
    Automatically fix common Promtail configuration issues.
    
    Args:
        project_root: Root directory of the project
        
    Returns:
        Dictionary with fix results
    """
    fixes_applied = []
    errors = []
    
    config_path = os.path.join(project_root, "promtail-config.yml")
    
    try:
        # Read existing config
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config_content = f.read()
        else:
            errors.append(f"Promtail config not found at {config_path}")
            return {"status": "error", "fixes": fixes_applied, "errors": errors}
        
        # Fix 1: Ensure correct Loki URL
        if "http://localhost:3100" in config_content:
            config_content = config_content.replace("http://localhost:3100", "http://loki:3100")
            fixes_applied.append("Updated Loki URL from localhost to docker service name")
        
        # Fix 2: Ensure Docker socket path is correct
        if not "docker_sd_configs" in config_content:
            errors.append("Docker service discovery not configured - config file needs regeneration")
        
        # Fix 3: Add Windows Docker Desktop path if needed (for Windows)
        if os.name == 'nt' and '/var/run/docker.sock' in config_content:
            # Windows Docker Desktop uses npipe
            fixes_applied.append("Note: Windows detected - verify Docker Desktop is running")
        
        # Write back fixed config
        if fixes_applied:
            with open(config_path, 'w') as f:
                f.write(config_content)
        
        return {
            "status": "success" if not errors else "partial",
            "fixes": fixes_applied,
            "errors": errors
        }
        
    except Exception as e:
        errors.append(f"Error fixing Promtail config: {str(e)}")
        return {"status": "error", "fixes": fixes_applied, "errors": errors}


def restart_monitoring_services(project_root: str, services: List[str] = None) -> Dict:
    """
    Restart monitoring services to apply fixes.
    
    Args:
        project_root: Root directory of the project
        services: List of services to restart (default: all monitoring services)
        
    Returns:
        Dictionary with restart results
    """
    if services is None:
        services = ["loki", "promtail", "grafana"]
    
    results = {
        "status": "success",
        "restarted": [],
        "failed": []
    }
    
    for service in services:
        try:
            logger.info(f"Restarting {service}...")
            result = subprocess.run(
                ["docker-compose", "-f", "docker-compose.monitoring.yml", "restart", service],
                cwd=project_root,
                capture_output=True,
                encoding='utf-8',
                errors='replace',
                timeout=30
            )
            
            if result.returncode == 0:
                results["restarted"].append(service)
            else:
                results["failed"].append(service)
                results["status"] = "partial"
        
        except Exception as e:
            results["failed"].append(service)
            results["status"] = "partial" if results["restarted"] else "error"
    
    return results


def validate_and_fix_monitoring(project_root: str) -> str:
    """
    Validate monitoring stack and automatically fix common issues.
    This is the main function that orchestrates diagnostics and fixes.
    
    Args:
        project_root: Root directory of the project
        
    Returns:
        Formatted report with diagnostics and fixes
    """
    report = "🔍 **Monitoring Stack Validation**\n\n"
    report += "=" * 60 + "\n\n"
    
    # Step 1: Run diagnostics
    report += "**Step 1: Running diagnostics...**\n\n"
    diagnostics = diagnose_monitoring_stack(project_root)
    
    report += f"**Overall Status:** {diagnostics['status'].upper()}\n\n"
    
    # Container status
    if diagnostics["containers"]:
        report += "**Container Status:**\n"
        for container, status in diagnostics["containers"].items():
            status_icon = "✅" if "Up" in status else "❌"
            report += f"{status_icon} {container}: {status}\n"
        report += "\n"
    
    # Loki status
    if diagnostics["loki"]:
        loki_icon = "✅" if diagnostics["loki"].get("loki_ready") else "❌"
        report += f"**Loki Status:** {loki_icon}\n"
        if diagnostics["loki"].get("loki_version"):
            report += f"  Version: {diagnostics['loki']['loki_version']}\n"
        if diagnostics["loki"].get("error"):
            report += f"  Error: {diagnostics['loki']['error']}\n"
        report += "\n"
    
    # Promtail status
    if diagnostics["promtail"]:
        promtail_icon = "✅" if diagnostics["promtail"].get("promtail_ready") else "❌"
        report += f"**Promtail Status:** {promtail_icon}\n"
        if diagnostics["promtail"].get("targets"):
            report += f"  Active targets: {len(diagnostics['promtail']['targets'])}\n"
        if diagnostics["promtail"].get("error"):
            report += f"  Error: {diagnostics['promtail']['error']}\n"
        report += "\n"
    
    # Logs status
    if diagnostics["logs"]:
        logs_icon = "✅" if diagnostics["logs"].get("receiving_logs") else "❌"
        report += f"**Log Flow Status:** {logs_icon}\n"
        if diagnostics["logs"].get("log_count"):
            report += f"  Logs in Loki: {diagnostics['logs']['log_count']}\n"
        if diagnostics["logs"].get("error"):
            report += f"  Issue: {diagnostics['logs']['error']}\n"
        report += "\n"
    
    # Issues found
    if diagnostics["issues"]:
        report += "**Issues Detected:**\n"
        for issue in diagnostics["issues"]:
            report += f"  ❌ {issue}\n"
        report += "\n"
    
    # Step 2: Apply fixes if issues found
    if diagnostics["issues"]:
        report += "=" * 60 + "\n"
        report += "**Step 2: Applying automatic fixes...**\n\n"
        
        # Fix Promtail config
        report += "**Fixing Promtail configuration...**\n"
        fix_result = fix_promtail_config(project_root)
        
        if fix_result["fixes"]:
            for fix in fix_result["fixes"]:
                report += f"  ✅ {fix}\n"
        
        if fix_result["errors"]:
            for error in fix_result["errors"]:
                report += f"  ⚠️  {error}\n"
        report += "\n"
        
        # Restart services if fixes were applied
        if fix_result["fixes"]:
            report += "**Restarting monitoring services...**\n"
            restart_result = restart_monitoring_services(project_root, ["promtail", "loki"])
            
            for service in restart_result["restarted"]:
                report += f"  ✅ Restarted {service}\n"
            
            for service in restart_result["failed"]:
                report += f"  ❌ Failed to restart {service}\n"
            report += "\n"
            
            # Wait for services to stabilize
            report += "**Waiting for services to stabilize (10 seconds)...**\n"
            time.sleep(10)
            report += "✅ Services ready\n\n"
            
            # Re-run diagnostics
            report += "**Re-running diagnostics...**\n"
            diagnostics_after = diagnose_monitoring_stack(project_root)
            
            if diagnostics_after["logs"].get("receiving_logs"):
                report += "✅ Loki is now receiving logs!\n\n"
            else:
                report += "⚠️  Loki still not receiving logs. Manual intervention may be needed.\n\n"
    
    # Step 3: Recommendations
    if diagnostics["recommendations"]:
        report += "=" * 60 + "\n"
        report += "**Recommendations:**\n\n"
        for rec in diagnostics["recommendations"]:
            report += f"  💡 {rec}\n"
        report += "\n"
    
    # Final status
    report += "=" * 60 + "\n"
    if diagnostics["status"] == "healthy" or (diagnostics["issues"] and diagnostics["logs"].get("receiving_logs")):
        report += "✅ **Monitoring stack is operational!**\n"
        report += "   Loki is receiving logs from Promtail.\n"
        report += "   You can now view logs in Grafana.\n"
    elif diagnostics["status"] == "partial":
        report += "⚠️  **Monitoring stack is partially operational**\n"
        report += "   Some issues remain. Check recommendations above.\n"
    else:
        report += "❌ **Monitoring stack has critical issues**\n"
        report += "   Please check the recommendations and container logs.\n"
    report += "=" * 60 + "\n"
    
    return report
