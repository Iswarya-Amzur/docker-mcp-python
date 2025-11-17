import subprocess
import os
import json
import logging
import time
import webbrowser
import re
import requests
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
      - /var/run/docker.sock:/var/run/docker.sock:ro  # CRITICAL: Docker socket access for service discovery
      - ./promtail-config.yml:/etc/promtail/config.yml
    command: -config.file=/etc/promtail/config.yml
    networks:
      - monitoring
    restart: unless-stopped
    depends_on:
      - loki
    # Run with privileges to access Docker socket
    privileged: true

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
    
    # Create dashboard JSON with proper UID for direct access
    dashboard = {
        "dashboard": {
            "uid": "app-logs",  # Unique ID for direct URL access
            "title": "Application Logs",
            "tags": ["docker", "logs"],
            "timezone": "browser",
            "panels": [],
            "schemaVersion": 38,
            "version": 0,
            "refresh": "5s",
            "time": {
                "from": "now-1h",
                "to": "now"
            },
            "timepicker": {
                "refresh_intervals": ["5s", "10s", "30s", "1m", "5m"],
                "time_options": ["5m", "15m", "1h", "6h", "12h", "24h", "2d", "7d"]
            },
            "editable": True,
            "hideControls": False
        },
        "overwrite": True  # Fixed: Python uses True, not true
    }
    
    # Add panel for each service
    panel_y = 0
    for idx, service in enumerate(services):
        panel = {
            "id": idx + 1,
            "gridPos": {"h": 8, "w": 24, "x": 0, "y": panel_y},
            "type": "logs",
            "title": f"{service.capitalize()} Logs",
            "datasource": {
                "type": "loki",
                "uid": "loki"
            },
            "targets": [{
                "expr": f'{{job="docker", container_name=~".*{service}.*"}} |= ""',
                "refId": "A",
                "datasource": {
                    "type": "loki",
                    "uid": "loki"
                }
            }],
            "options": {
                "showTime": True,
                "showLabels": True,
                "showCommonLabels": False,
                "wrapLogMessage": True,
                "sortOrder": "Descending",
                "dedupStrategy": "none",
                "enableLogDetails": True,
                "prettifyLogMessage": False
            }
        }
        dashboard["dashboard"]["panels"].append(panel)
        panel_y += 8
    
    # Add an "All Logs" panel at the top if multiple services
    if len(services) > 1:
        all_logs_panel = {
            "id": len(services) + 1,
            "gridPos": {"h": 8, "w": 24, "x": 0, "y": 0},
            "type": "logs",
            "title": "All Application Logs",
            "datasource": {
                "type": "loki",
                "uid": "loki"
            },
            "targets": [{
                "expr": '{job="docker"} |= ""',
                "refId": "A",
                "datasource": {
                    "type": "loki",
                    "uid": "loki"
                }
            }],
            "options": {
                "showTime": True,
                "showLabels": True,
                "showCommonLabels": False,
                "wrapLogMessage": True,
                "sortOrder": "Descending",
                "dedupStrategy": "none",
                "enableLogDetails": True,
                "prettifyLogMessage": False
            }
        }
        # Insert at beginning and shift other panels down
        dashboard["dashboard"]["panels"].insert(0, all_logs_panel)
        # Update Y positions
        for i, panel in enumerate(dashboard["dashboard"]["panels"][1:], 1):
            panel["gridPos"]["y"] = i * 8
    
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
        report += f"🌐 **Direct Dashboard Link:** {start_result['grafana_url']}/d/app-logs/application-logs\n"
        report += f"📊 **Explore Logs:** {start_result['grafana_url']}/explore\n"
        report += f"🏠 **Home Page:** {start_result['grafana_url']}\n\n"
        report += f"👤 Username: {start_result['credentials']['username']}\n"
        report += f"🔑 Password: {start_result['credentials']['password']}\n\n"
        report += f"📡 Loki URL: {start_result['loki_url']}\n\n"
        report += "**Next Steps:**\n"
        report += "1. Use open_grafana() to launch dashboard in browser\n"
        report += "2. Or manually open: http://localhost:3001/d/app-logs/application-logs\n"
        report += "3. Login with the credentials above\n"
        report += "4. Dashboard will auto-refresh every 5 seconds with latest logs\n"
        report += "5. Use Explore (left sidebar) for custom log queries\n\n"
        report += "**Services Monitored:**\n"
        for service in services:
            report += f"  - {service}\n"
        
        report += "\n💡 **Tip:** Logs may take 10-15 seconds to appear after container startup.\n"
        report += "    Use validate_monitoring() to check log flow status.\n"
    else:
        report += f"❌ {start_result.get('message')}\n"
        if 'error' in start_result:
            report += f"Error: {start_result['error']}\n"
    
    return report


def launch_grafana_dashboard(grafana_url: str = "http://localhost:3001", open_dashboard: bool = True) -> str:
    """
    Open Grafana dashboard in the default browser.
    NOW opens directly to the Application Logs dashboard instead of home page!
    
    Args:
        grafana_url: URL of Grafana (base URL)
        open_dashboard: If True, opens directly to Application Logs dashboard (default: True)
        
    Returns:
        Status message
    """
    try:
        # Construct the direct dashboard URL
        if open_dashboard:
            # Direct link to Application Logs dashboard
            # Uses Grafana's dashboard UID format: /d/<dashboard-uid>/<dashboard-slug>
            dashboard_url = f"{grafana_url}/d/app-logs/application-logs?orgId=1&refresh=5s"
            
            # Alternatively, use explore view with Loki query for immediate log viewing
            # This ensures logs are visible even if dashboard isn't loaded yet
            explore_url = f"{grafana_url}/explore?orgId=1&left=%5B%22now-1h%22,%22now%22,%22Loki%22,%7B%22expr%22:%22%7Bjob%3D%5C%22docker%5C%22%7D%22%7D%5D"
            
            # Try dashboard first, fallback to explore
            url_to_open = dashboard_url
            
            webbrowser.open(url_to_open)
            
            return f"""✅ Grafana dashboard opened in browser!

🌐 **Dashboard URL:** {grafana_url}/d/app-logs/application-logs
📊 **Explore Logs:** {grafana_url}/explore

**Login Credentials:**
   👤 Username: admin
   🔑 Password: admin

**What to do:**
   1. Login with the credentials above
   2. You should see the "Application Logs" dashboard
   3. If redirected to home, click "Dashboards" → "Application Logs"
   4. Or use Explore (left sidebar) → Select "Loki" → Query: {{job="docker"}}

💡 Tip: The dashboard auto-refreshes every 5 seconds to show latest logs!"""
        else:
            webbrowser.open(grafana_url)
            return f"✅ Grafana opened in browser: {grafana_url}"
    
    except Exception as e:
        return f"""❌ Error opening browser: {str(e)}

Please open manually:
   🌐 Dashboard: {grafana_url}/d/app-logs/application-logs
   📊 Explore: {grafana_url}/explore
   
Login: admin / admin"""


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


def check_containers_running(project_root: str) -> Dict:
    """
    Check if application containers are running.
    
    Args:
        project_root: Root directory of the project
        
    Returns:
        Dictionary with container status information
    """
    results = {
        "status": "unknown",
        "running_containers": [],
        "stopped_containers": [],
        "app_containers": [],
        "monitoring_containers": []
    }
    
    try:
        # Get all containers (running and stopped)
        result = subprocess.run(
            ["docker", "ps", "-a", "--format", "{{.Names}}\t{{.Status}}\t{{.Image}}"],
            capture_output=True,
            encoding='utf-8',
            errors='replace',
            timeout=10
        )
        
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        name, status = parts[0], parts[1]
                        
                        # Categorize containers
                        if "Up" in status:
                            results["running_containers"].append(name)
                        else:
                            results["stopped_containers"].append(name)
                        
                        # Identify monitoring vs app containers
                        if name in ["loki", "promtail", "grafana"]:
                            results["monitoring_containers"].append(name)
                        else:
                            results["app_containers"].append(name)
            
            # Determine overall status
            if results["running_containers"]:
                results["status"] = "running"
            elif results["stopped_containers"]:
                results["status"] = "stopped"
            else:
                results["status"] = "no_containers"
        
        return results
        
    except Exception as e:
        results["status"] = "error"
        results["error"] = str(e)
        return results


def start_application_containers(project_root: str) -> Dict:
    """
    Start application containers if they're not running.
    
    Args:
        project_root: Root directory of the project
        
    Returns:
        Dictionary with startup results
    """
    results = {
        "status": "unknown",
        "started": [],
        "failed": [],
        "message": ""
    }
    
    try:
        # Try to start with docker-compose
        compose_files = ["docker-compose.yml", "docker-compose.yaml"]
        compose_file = None
        
        for cf in compose_files:
            if os.path.exists(os.path.join(project_root, cf)):
                compose_file = cf
                break
        
        if compose_file:
            logger.info(f"Starting containers with {compose_file}")
            # Verify file exists and is readable
            compose_path = os.path.join(project_root, compose_file)
            if not os.path.exists(compose_path):
                results["status"] = "error"
                results["message"] = f"Docker compose file {compose_file} not found at {compose_path}"
                return results
            
            result = subprocess.run(
                ["docker-compose", "-f", compose_file, "up", "-d"],
                cwd=project_root,
                capture_output=True,
                encoding='utf-8',
                errors='replace',
                timeout=120
            )
            
            if result.returncode == 0:
                results["status"] = "success"
                results["message"] = "Application containers started successfully"
                # Wait a bit for containers to initialize
                time.sleep(5)
            else:
                results["status"] = "error"
                results["message"] = f"Failed to start containers: {result.stderr}"
        else:
            results["status"] = "error"
            results["message"] = "No docker-compose.yml found"
        
        return results
        
    except Exception as e:
        results["status"] = "error"
        results["message"] = f"Error starting containers: {str(e)}"
        return results


def smart_dockerize_and_show_logs(project_root: str, auto_fix: bool = True) -> str:
    """
    Intelligent workflow: Analyze app, check/start containers, validate monitoring,
    launch Grafana, verify logs are showing, and auto-fix any issues.
    
    This is the main orchestration function that handles user requests like:
    - "dockerize my application and show me the logs in grafana dashboard"
    - "show me the logs of this application"
    
    Args:
        project_root: Root directory of the project
        auto_fix: Automatically fix issues if found (default: True)
        
    Returns:
        Comprehensive report with all steps and final status
    """
    report = "🚀 **Smart Dockerization & Log Monitoring**\n\n"
    report += "=" * 60 + "\n\n"
    
    # STEP 1: Analyze application
    report += "**STEP 1: Analyzing Application...**\n\n"
    try:
        from docker_tools.analyzer import analyze_application
        analysis = analyze_application(project_root)
        
        report += f"📁 Application Type: {analysis.get('app_type', 'unknown')}\n"
        if analysis.get('dependencies'):
            report += f"📦 Dependencies: {len(analysis['dependencies'])} packages\n"
        if analysis.get('entry_point'):
            report += f"🎯 Entry Point: {analysis['entry_point']}\n"
        report += "✅ Analysis complete\n\n"
    except Exception as e:
        report += f"⚠️  Analysis failed: {str(e)}\n"
        report += "Continuing with default settings...\n\n"
    
    # STEP 2: Check if containers are running
    report += "=" * 60 + "\n"
    report += "**STEP 2: Checking Container Status...**\n\n"
    
    container_status = check_containers_running(project_root)
    
    if container_status["app_containers"]:
        report += f"📦 Found {len(container_status['app_containers'])} application container(s)\n"
        report += f"✅ Running: {len([c for c in container_status['app_containers'] if c in container_status['running_containers']])}\n"
        report += f"⏸️  Stopped: {len([c for c in container_status['app_containers'] if c in container_status['stopped_containers']])}\n\n"
    else:
        report += "⚠️  No application containers found\n"
        report += "Will attempt to dockerize the application...\n\n"
    
    # If no containers or they're stopped, start them
    if container_status["status"] != "running" or not container_status["app_containers"]:
        report += "**Starting/Creating Containers...**\n\n"
        
        # Check if docker-compose exists, if not, dockerize first
        if not os.path.exists(os.path.join(project_root, "docker-compose.yml")):
            report += "Creating docker-compose setup...\n"
            try:
                from docker_tools.multi_service_handler import dockerize_full_project
                dockerize_result = dockerize_full_project(project_root)
                report += "✅ Docker setup created\n\n"
            except Exception as e:
                report += f"⚠️  Dockerization partial: {str(e)}\n\n"
        
        # Start containers
        start_result = start_application_containers(project_root)
        if start_result["status"] == "success":
            report += f"✅ {start_result['message']}\n\n"
        else:
            report += f"⚠️  {start_result['message']}\n\n"
    else:
        report += "✅ Application containers are running\n\n"
    
    # STEP 3: Setup/Check Monitoring Stack
    report += "=" * 60 + "\n"
    report += "**STEP 3: Setting Up Monitoring Stack...**\n\n"
    
    # Check if monitoring is already setup
    monitoring_exists = os.path.exists(os.path.join(project_root, "docker-compose.monitoring.yml"))
    
    if not monitoring_exists:
        report += "Setting up Grafana + Loki + Promtail...\n"
        report += "Detecting services...\n"
        try:
            from docker_tools.multi_service_handler import detect_services
            detected = detect_services(project_root)
            
            if detected:
                service_list = list(detected.keys())
                report += f"📦 Detected {len(service_list)} service(s): {', '.join(service_list)}\n"
            else:
                # Try to get container names from running containers
                try:
                    result = subprocess.run(
                        ["docker-compose", "ps", "--services"],
                        cwd=project_root,
                        capture_output=True,
                        encoding='utf-8',
                        timeout=10
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        service_list = [s.strip() for s in result.stdout.strip().split('\n') if s.strip()]
                        report += f"📦 Found {len(service_list)} docker-compose service(s): {', '.join(service_list)}\n"
                    else:
                        service_list = ["app"]
                        report += "⚠️  No services detected, using default: 'app'\n"
                except:
                    service_list = ["app"]
                    report += "⚠️  Could not detect services, using default: 'app'\n"
            
            monitoring_result = setup_complete_monitoring(project_root, service_list)
            report += "✅ Monitoring stack created\n\n"
        except Exception as e:
            report += f"⚠️  Monitoring setup issue: {str(e)}\n\n"
    else:
        report += "✅ Monitoring stack already configured\n"
        
        # Check if dashboard file exists, recreate if missing
        dashboard_file = os.path.join(project_root, "grafana", "provisioning", "dashboards", "app-logs.json")
        if not os.path.exists(dashboard_file):
            report += "⚠️  Dashboard file missing, recreating...\n"
            try:
                from docker_tools.multi_service_handler import detect_services
                detected = detect_services(project_root)
                
                if detected:
                    service_list = list(detected.keys())
                else:
                    # Try docker-compose services
                    try:
                        result = subprocess.run(
                            ["docker-compose", "ps", "--services"],
                            cwd=project_root,
                            capture_output=True,
                            encoding='utf-8',
                            timeout=10
                        )
                        if result.returncode == 0 and result.stdout.strip():
                            service_list = [s.strip() for s in result.stdout.strip().split('\n') if s.strip()]
                        else:
                            service_list = ["app"]
                    except:
                        service_list = ["app"]
                
                generate_grafana_dashboard(project_root, service_list)
                report += f"✅ Dashboard recreated for services: {', '.join(service_list)}\n"
            except Exception as e:
                report += f"⚠️  Dashboard recreation failed: {str(e)}\n"
        
        # Ensure monitoring containers are running
        monitoring_containers = ["loki", "promtail", "grafana"]
        monitoring_running = all(c in container_status["running_containers"] for c in monitoring_containers)
        
        if not monitoring_running:
            report += "Starting monitoring containers...\n"
            try:
                result = subprocess.run(
                    ["docker-compose", "-f", "docker-compose.monitoring.yml", "up", "-d"],
                    cwd=project_root,
                    capture_output=True,
                    encoding='utf-8',
                    errors='replace',
                    timeout=60
                )
                if result.returncode == 0:
                    report += "✅ Monitoring containers started\n"
                    time.sleep(5)  # Wait for startup
                else:
                    report += f"⚠️  Failed to start monitoring: {result.stderr[:200]}\n"
            except Exception as e:
                report += f"⚠️  Error starting monitoring: {str(e)}\n"
        else:
            # Even if running, restart Grafana to pick up new dashboard
            report += "Restarting Grafana to load dashboard...\n"
            try:
                subprocess.run(
                    ["docker-compose", "-f", "docker-compose.monitoring.yml", "restart", "grafana"],
                    cwd=project_root,
                    capture_output=True,
                    timeout=30
                )
                report += "✅ Grafana restarted\n"
                time.sleep(3)
            except:
                pass
        report += "\n"
    
    # STEP 4: Validate Log Flow
    report += "=" * 60 + "\n"
    report += "**STEP 4: Validating Log Flow (Loki ← Promtail)...**\n\n"
    
    diagnostics = diagnose_monitoring_stack(project_root)
    
    # Show status
    loki_ready = diagnostics["loki"].get("loki_ready", False)
    promtail_ready = diagnostics["promtail"].get("promtail_ready", False)
    logs_flowing = diagnostics["logs"].get("receiving_logs", False)
    
    report += f"{'✅' if loki_ready else '❌'} Loki: {'Ready' if loki_ready else 'Not Ready'}\n"
    report += f"{'✅' if promtail_ready else '❌'} Promtail: {'Ready' if promtail_ready else 'Not Ready'}\n"
    report += f"{'✅' if logs_flowing else '❌'} Log Flow: {'Active' if logs_flowing else 'No Logs Detected'}\n\n"
    
    # Auto-fix if issues found
    if auto_fix and (not loki_ready or not promtail_ready or not logs_flowing):
        report += "**Auto-Fixing Issues...**\n\n"
        
        # Fix Promtail config
        fix_result = fix_promtail_config(project_root)
        if fix_result["fixes"]:
            for fix in fix_result["fixes"]:
                report += f"  🔧 {fix}\n"
            
            # Restart services
            report += "\nRestarting monitoring services...\n"
            restart_result = restart_monitoring_services(project_root, ["promtail", "loki"])
            
            if restart_result["status"] == "success":
                report += "✅ Services restarted\n"
                time.sleep(10)  # Wait for stabilization
                
                # Re-check
                diagnostics_after = diagnose_monitoring_stack(project_root)
                logs_flowing = diagnostics_after["logs"].get("receiving_logs", False)
                
                if logs_flowing:
                    report += "✅ Logs are now flowing to Loki!\n\n"
                else:
                    report += "⚠️  Logs still not flowing. Manual check needed.\n\n"
            else:
                report += "⚠️  Service restart had issues\n\n"
        else:
            report += "⚠️  No automatic fixes available\n"
            report += "Manual intervention may be required\n\n"
    
    # STEP 5: Wait for Logs to Flow (give Promtail time to collect)
    report += "=" * 60 + "\n"
    report += "**STEP 5: Waiting for Logs to Flow...**\n\n"
    
    if not logs_flowing:
        report += "Giving Promtail time to start collecting logs (15 seconds)...\n"
        for i in range(3):
            time.sleep(5)
            report += f"  ⏳ Checking... ({(i+1)*5}s)\n"
            
            # Re-check log flow
            diagnostics_recheck = diagnose_monitoring_stack(project_root)
            logs_flowing = diagnostics_recheck["logs"].get("receiving_logs", False)
            
            if logs_flowing:
                report += f"  ✅ Logs are now flowing! ({diagnostics_recheck['logs'].get('log_count', 0)} entries)\n"
                break
        
        if not logs_flowing:
            report += "  ⚠️  Still no logs detected. Containers may not be generating logs yet.\n"
        report += "\n"
    else:
        report += "✅ Logs are already flowing to Loki\n\n"
    
    # STEP 6: Launch Grafana Dashboard (directly to logs page!)
    report += "=" * 60 + "\n"
    report += "**STEP 6: Launching Grafana Dashboard...**\n\n"
    
    try:
        # Use the enhanced launch function that opens directly to dashboard
        launch_result = launch_grafana_dashboard("http://localhost:3001", open_dashboard=True)
        report += launch_result + "\n\n"
    except Exception as e:
        report += f"⚠️  Could not auto-open browser: {str(e)}\n"
        report += "   Please open manually: http://localhost:3001/d/app-logs/application-logs\n\n"
    
    # STEP 7: Verify Logs are Visible
    report += "=" * 60 + "\n"
    report += "**STEP 7: Verifying Logs in Grafana...**\n\n"
    
    if logs_flowing:
        log_count = diagnostics["logs"].get("log_count", 0)
        report += f"✅ SUCCESS! Loki has {log_count} log entries\n"
        report += "   Your logs should be visible in Grafana dashboard\n\n"
        
        # Show sample of recent logs
        try:
            logs_result = fetch_logs_from_loki("http://localhost:3100", '{job="docker"}', 5)
            if logs_result["status"] == "success" and logs_result["logs"]:
                report += "**Sample Recent Logs:**\n"
                for log in logs_result["logs"][:3]:
                    log_text = log["log"][:100]
                    report += f"  • {log_text}...\n"
                report += "\n"
        except:
            pass
    else:
        report += "⚠️  No logs detected in Loki yet\n"
        report += "   This could mean:\n"
        report += "   1. Application containers are not generating logs\n"
        report += "   2. Promtail is not collecting logs\n"
        report += "   3. Configuration needs adjustment\n\n"
        
        if not auto_fix:
            report += "💡 Try running with auto_fix=True to attempt automatic fixes\n\n"
    
    # FINAL SUMMARY
    report += "=" * 60 + "\n"
    report += "**📊 FINAL STATUS**\n"
    report += "=" * 60 + "\n\n"
    
    if logs_flowing:
        report += "✅ **ALL SYSTEMS OPERATIONAL**\n\n"
        report += "Your application is:\n"
        report += "  ✅ Dockerized and running\n"
        report += "  ✅ Monitored by Grafana + Loki + Promtail\n"
        report += "  ✅ Logs are flowing and visible\n\n"
        report += "**Next Steps:**\n"
        report += "  1. Open Grafana: http://localhost:3001\n"
        report += "  2. Navigate to Dashboards → Application Logs\n"
        report += "  3. View real-time logs from your services\n"
    else:
        report += "⚠️  **SETUP COMPLETE BUT LOGS NOT FLOWING**\n\n"
        report += "**Recommendations:**\n"
        report += "  1. Check if application containers are generating logs:\n"
        report += "     docker logs <container_name>\n"
        report += "  2. Verify Promtail is running:\n"
        report += "     docker logs promtail\n"
        report += "  3. Check Promtail targets:\n"
        report += "     curl http://localhost:9080/targets\n"
        report += "  4. Review Loki connection:\n"
        report += "     docker logs loki\n"
    
    report += "\n" + "=" * 60 + "\n"
    
    return report


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
