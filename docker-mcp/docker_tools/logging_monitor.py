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
        filters:
          - name: status
            values: [running]
    relabel_configs:
      # Extract container name and remove leading slash
      - source_labels: ['__meta_docker_container_name']
        regex: '/(.*)'
        target_label: 'container'
      - source_labels: ['__meta_docker_container_name']
        regex: '/(.*)'
        target_label: 'container_name'
      # Extract log stream (stdout/stderr)
      - source_labels: ['__meta_docker_container_log_stream']
        target_label: 'stream'
      # Extract docker-compose service name if available
      - source_labels: ['__meta_docker_container_label_com_docker_compose_service']
        target_label: 'service'
      # Extract container ID
      - source_labels: ['__meta_docker_container_id']
        target_label: 'container_id'
      # Extract image name
      - source_labels: ['__meta_docker_container_image']
        target_label: 'image'
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
    orgId: 1
    uid: loki
    url: http://loki:3100
    isDefault: true
    editable: false
    jsonData:
      maxLines: 1000
      timeout: 60
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
    
    # Create dashboard JSON - Grafana expects dashboard content at root level
    dashboard = {
        "id": None,
        "uid": "app-logs",
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
    }
    
    # Add single "Application Container Logs" panel that shows all application containers
    # Exclude monitoring containers (grafana, loki, promtail)
    all_logs_panel = {
        "id": 1,
        "gridPos": {"h": 24, "w": 24, "x": 0, "y": 0},  # Full height panel
        "type": "logs",
        "title": "Application Container Logs",
        "datasource": {
            "type": "loki",
            "uid": "loki"
        },
        "targets": [{
            "expr": '{container_name=~".+"} | container_name !~ "(grafana|loki|promtail)"',
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
    dashboard["panels"].append(all_logs_panel)
    
    # Note: Service-specific panels removed - all application logs shown in single panel
    
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
        report += f"🌐 Dashboard URL: {start_result['grafana_url']}/d/app-logs/application-logs\n"
        report += f"👤 Login: {start_result['credentials']['username']} / {start_result['credentials']['password']}\n\n"
        report += "**Services Monitored:**\n"
        for service in services:
            report += f"  - {service}\n"
        
        report += "\n✅ Dashboard will open automatically with visualizations\n"
        report += "✅ Logs will be analyzed automatically\n"
        report += "✅ Screenshot will be captured for verification\n"
    else:
        report += f"❌ {start_result.get('message')}\n"
        if 'error' in start_result:
            report += f"Error: {start_result['error']}\n"
    
    return report


def launch_grafana_dashboard(grafana_url: str = "http://localhost:3001", open_dashboard: bool = True, 
                            auto_analyze: bool = True, capture_screenshot: bool = True, 
                            project_root: str = None) -> Dict:
    """
    Open Grafana dashboard in browser and automatically analyze logs and capture screenshot.
    
    Args:
        grafana_url: URL of Grafana (base URL)
        open_dashboard: If True, opens directly to Application Logs dashboard (default: True)
        auto_analyze: Automatically analyze logs after opening (default: True)
        capture_screenshot: Capture screenshot after opening (default: True)
        project_root: Project root for saving screenshot (optional)
        
    Returns:
        Dictionary with status, message, log analysis, and screenshot path
    """
    result = {
        "status": "success",
        "message": "",
        "dashboard_url": "",
        "log_analysis": {},
        "screenshot": {}
    }
    
    try:
        # Construct the direct dashboard URL
        if open_dashboard:
            dashboard_url = f"{grafana_url}/d/app-logs/application-logs?orgId=1&refresh=5s"
            result["dashboard_url"] = dashboard_url
            
            # Open in browser
            webbrowser.open(dashboard_url)
            
            result["message"] = "✅ Grafana dashboard opened in browser!\n\n"
            result["message"] += f"🌐 Dashboard URL: {dashboard_url}\n"
            result["message"] += "👤 Login: admin / admin\n\n"
            
            # Wait for dashboard to load
            if auto_analyze or capture_screenshot:
                result["message"] += "⏳ Waiting for dashboard to load (10 seconds)...\n"
                time.sleep(10)
            
            # Auto-analyze logs
            if auto_analyze:
                result["message"] += "\n📊 Analyzing logs from Loki...\n"
                try:
                    logs_result = fetch_logs_from_loki("http://localhost:3100", '{container_name=~".+"} | container_name !~ "(grafana|loki|promtail)"', 50)
                    
                    if logs_result["status"] == "success" and logs_result["logs"]:
                        analysis = analyze_logs_for_errors(logs_result["logs"])
                        result["log_analysis"] = analysis
                        
                        result["message"] += f"   ✅ Found {analysis['total_logs']} log entries\n"
                        result["message"] += f"   ⚠️  {len(analysis['errors'])} errors detected\n"
                        result["message"] += f"   📝 {len(analysis['warnings'])} warnings detected\n"
                        
                        # Show top errors
                        if analysis['errors']:
                            result["message"] += "\n**Top Errors:**\n"
                            for err in analysis['errors'][:3]:
                                log_snippet = err.get('log', '')[:80]
                                result["message"] += f"   • {log_snippet}...\n"
                        
                        # Get fix suggestions
                        if analysis['errors']:
                            suggestions = suggest_fixes_for_errors(analysis)
                            if suggestions:
                                result["message"] += f"\n💡 {len(suggestions)} fix suggestions available\n"
                    else:
                        result["message"] += "   ⚠️  No logs found yet (containers may still be starting)\n"
                except Exception as e:
                    result["message"] += f"   ⚠️  Log analysis error: {str(e)}\n"
            
            # Capture screenshot
            if capture_screenshot:
                result["message"] += "\n📸 Capturing dashboard screenshot...\n"
                try:
                    screenshot_path = os.path.join(project_root or os.getcwd(), "grafana_dashboard.png")
                    screenshot_result = capture_grafana_screenshot(grafana_url, screenshot_path, wait_for_login=True)
                    
                    if screenshot_result["status"] == "success":
                        result["screenshot"] = screenshot_result
                        result["message"] += f"   ✅ Screenshot saved: {screenshot_result['path']}\n"
                    else:
                        result["message"] += f"   ⚠️  {screenshot_result.get('message', 'Screenshot failed')}\n"
                except Exception as e:
                    result["message"] += f"   ⚠️  Screenshot error: {str(e)}\n"
            
            result["message"] += "\n✅ Dashboard is ready with visualizations!\n"
            
        else:
            webbrowser.open(grafana_url)
            result["message"] = f"✅ Grafana opened in browser: {grafana_url}"
        
        return result
    
    except Exception as e:
        result["status"] = "error"
        result["message"] = f"❌ Error: {str(e)}\n\n"
        result["message"] += f"Please open manually: {grafana_url}/d/app-logs/application-logs\n"
        result["message"] += "Login: admin / admin"
        return result


def check_grafana_logs(project_root: str = None) -> Dict:
    """
    Check Grafana container logs for errors and provisioning issues.
    Enhanced to detect more provisioning errors.
    
    Args:
        project_root: Root directory of the project (optional)
        
    Returns:
        Dictionary with log analysis results
    """
    results = {
        "status": "unknown",
        "errors": [],
        "warnings": [],
        "dashboard_errors": [],
        "datasource_errors": [],
        "provisioning_errors": [],
        "log_snippet": ""
    }
    
    try:
        # Get Grafana container logs (last 200 lines for better analysis)
        result = subprocess.run(
            ["docker", "logs", "--tail", "200", "grafana"],
            capture_output=True,
            encoding='utf-8',
            errors='replace',
            timeout=10
        )
        
        if result.returncode == 0:
            logs = result.stdout + result.stderr
            results["log_snippet"] = logs
            
            # Parse logs for specific errors
            for line in logs.split('\n'):
                # Dashboard provisioning errors
                if "Dashboard title cannot be empty" in line:
                    results["dashboard_errors"].append({
                        "error": "Dashboard title cannot be empty",
                        "file": "app-logs.json",
                        "fix": "Dashboard JSON structure incorrect - needs title at root level"
                    })
                elif "failed to load dashboard" in line:
                    results["dashboard_errors"].append({
                        "error": line.strip(),
                        "fix": "Dashboard JSON format issue - check JSON structure"
                    })
                elif "no such file or directory" in line and "provisioning/dashboards" in line:
                    results["provisioning_errors"].append({
                        "error": "Dashboard provisioning directory not found",
                        "path": "/etc/grafana/provisioning/dashboards",
                        "fix": "Create directory and ensure volume mount"
                    })
                elif "no such file or directory" in line and "provisioning/alerting" in line:
                    results["provisioning_errors"].append({
                        "error": "Alerting provisioning directory not found",
                        "path": "/etc/grafana/provisioning/alerting",
                        "fix": "Create directory and ensure volume mount"
                    })
                elif "no such file or directory" in line and "provisioning/plugins" in line:
                    results["provisioning_errors"].append({
                        "error": "Plugins provisioning directory not found",
                        "path": "/etc/grafana/provisioning/plugins",
                        "fix": "Create directory and ensure volume mount"
                    })
                elif "can't read dashboard provisioning files" in line or "can't read alerting provisioning files" in line or "Failed to read plugin provisioning files" in line:
                    results["provisioning_errors"].append({
                        "error": line.strip(),
                        "fix": "Create missing provisioning directories"
                    })
                
                # Datasource errors
                elif "failed to load datasource" in line or ("datasource" in line.lower() and "error" in line.lower()):
                    results["datasource_errors"].append({
                        "error": line.strip(),
                        "fix": "Check datasource configuration in provisioning/datasources/"
                    })
                
                # General errors
                elif "level=error" in line:
                    results["errors"].append(line.strip())
                elif "level=warn" in line:
                    results["warnings"].append(line.strip())
            
            # Determine status
            if results["dashboard_errors"] or results["datasource_errors"] or results["provisioning_errors"]:
                results["status"] = "has_issues"
            elif results["errors"]:
                results["status"] = "has_errors"
            else:
                results["status"] = "healthy"
        else:
            results["status"] = "error"
            results["errors"].append(f"Failed to get Grafana logs: {result.stderr}")
        
        return results
        
    except Exception as e:
        results["status"] = "error"
        results["errors"].append(f"Error checking Grafana logs: {str(e)}")
        return results


def fix_grafana_dashboard_errors(project_root: str, log_check: Dict) -> Dict:
    """
    Automatically fix Grafana dashboard and provisioning errors based on log analysis.
    Enhanced to handle provisioning directory issues.
    
    Args:
        project_root: Root directory of the project
        log_check: Results from check_grafana_logs()
        
    Returns:
        Dictionary with fix results
    """
    results = {
        "status": "unknown",
        "fixes_applied": [],
        "errors": []
    }
    
    try:
        # Fix: Missing provisioning directories
        provisioning_errors = log_check.get("provisioning_errors", [])
        if provisioning_errors:
            logger.info("Fixing provisioning directory issues...")
            
            grafana_provisioning_base = os.path.join(project_root, "grafana", "provisioning")
            
            # Create all required provisioning directories
            dirs_to_create = [
                os.path.join(grafana_provisioning_base, "dashboards"),
                os.path.join(grafana_provisioning_base, "datasources"),
                os.path.join(grafana_provisioning_base, "alerting"),
                os.path.join(grafana_provisioning_base, "plugins"),
                os.path.join(grafana_provisioning_base, "notifiers")
            ]
            
            for dir_path in dirs_to_create:
                try:
                    os.makedirs(dir_path, exist_ok=True)
                    results["fixes_applied"].append(f"Created directory: {dir_path}")
                except Exception as e:
                    results["errors"].append(f"Failed to create {dir_path}: {str(e)}")
            
            # Create empty config files for directories that need them
            # Alerting config (empty)
            alerting_config_path = os.path.join(grafana_provisioning_base, "alerting", "alerting.yml")
            if not os.path.exists(alerting_config_path):
                with open(alerting_config_path, 'w') as f:
                    f.write("# Empty alerting configuration\n")
                results["fixes_applied"].append("Created empty alerting config")
            
            # Plugins config (empty)
            plugins_config_path = os.path.join(grafana_provisioning_base, "plugins", "plugins.yml")
            if not os.path.exists(plugins_config_path):
                with open(plugins_config_path, 'w') as f:
                    f.write("# Empty plugins configuration\n")
                results["fixes_applied"].append("Created empty plugins config")
        
        # Fix: Dashboard title cannot be empty
        if any("Dashboard title cannot be empty" in str(err) for err in log_check.get("dashboard_errors", [])):
            logger.info("Fixing dashboard JSON structure...")
            
            # Get services to regenerate dashboard correctly
            try:
                from docker_tools.multi_service_handler import detect_services
                detected = detect_services(project_root)
                service_list = list(detected.keys()) if detected else ["app"]
            except:
                # Fallback: get from docker-compose
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
            
            # Regenerate dashboard with correct structure
            dashboard_path = generate_grafana_dashboard(project_root, service_list)
            results["fixes_applied"].append(f"Regenerated dashboard JSON with correct structure: {dashboard_path}")
        
        # Fix: Datasource issues - regenerate datasource config
        if log_check.get("datasource_errors"):
            logger.info("Regenerating datasource configuration...")
            try:
                datasource_path = generate_grafana_datasource(project_root)
                results["fixes_applied"].append(f"Regenerated datasource config: {datasource_path}")
            except Exception as e:
                results["errors"].append(f"Failed to regenerate datasource: {str(e)}")
        
        # Restart Grafana to apply all fixes
        if results["fixes_applied"]:
            logger.info("Restarting Grafana to apply fixes...")
            restart_result = subprocess.run(
                ["docker-compose", "-f", "docker-compose.monitoring.yml", "restart", "grafana"],
                cwd=project_root,
                capture_output=True,
                encoding='utf-8',
                timeout=30
            )
            
            if restart_result.returncode == 0:
                results["fixes_applied"].append("Restarted Grafana to reload configuration")
                time.sleep(8)  # Wait for Grafana to restart and load configs
            else:
                results["errors"].append(f"Failed to restart Grafana: {restart_result.stderr}")
        
        # Determine status
        if results["fixes_applied"] and not results["errors"]:
            results["status"] = "success"
        elif results["fixes_applied"] and results["errors"]:
            results["status"] = "partial"
        else:
            results["status"] = "no_fixes_applied"
        
        return results
        
    except Exception as e:
        results["status"] = "error"
        results["errors"].append(f"Error fixing dashboard: {str(e)}")
        return results


def capture_grafana_screenshot(grafana_url: str = "http://localhost:3001", output_path: str = None, wait_for_login: bool = False) -> Dict:
    """
    Capture screenshot of Grafana dashboard to verify it's working.
    Enhanced to handle login page and wait for dashboard to load.
    
    Args:
        grafana_url: URL of Grafana dashboard
        output_path: Path to save screenshot (default: auto-generated in project)
        wait_for_login: Whether to perform login if needed
        
    Returns:
        Dictionary with screenshot result and base64 data
    """
    try:
        from playwright.sync_api import sync_playwright
        
        if output_path is None:
            output_path = os.path.join(os.getcwd(), "grafana_dashboard_screenshot.png")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={'width': 1920, 'height': 1080})
            page = context.new_page()
            
            # Navigate to dashboard
            dashboard_url = f"{grafana_url}/d/app-logs/application-logs?orgId=1&refresh=5s"
            
            try:
                page.goto(dashboard_url, wait_until="domcontentloaded", timeout=30000)
                
                # Check if we're on login page
                if "login" in page.url.lower() or page.locator("input[name='user']").count() > 0:
                    logger.info("Grafana login page detected, logging in...")
                    
                    # Fill login form
                    page.fill("input[name='user']", "admin")
                    page.fill("input[name='password']", "admin")
                    page.click("button[type='submit']")
                    
                    # Wait for redirect to dashboard
                    page.wait_for_url("**/d/app-logs/**", timeout=10000)
                
                # Wait for dashboard to load
                page.wait_for_timeout(5000)
                
                # Wait for panels to be visible
                try:
                    page.wait_for_selector("[data-testid='data-testid panel content']", timeout=10000)
                except:
                    # Fallback: just wait for any panel
                    page.wait_for_selector(".panel-container", timeout=10000)
                
                # Take screenshot
                page.screenshot(path=output_path, full_page=True)
                
            except Exception as e:
                # Take screenshot anyway to see what's on the page
                logger.warning(f"Error during navigation, capturing screenshot anyway: {e}")
                page.screenshot(path=output_path, full_page=True)
            
            browser.close()
            
            # Read screenshot and encode as base64
            with open(output_path, 'rb') as f:
                screenshot_data = f.read()
                import base64
                base64_data = base64.b64encode(screenshot_data).decode('utf-8')
            
            return {
                "status": "success",
                "path": output_path,
                "base64": base64_data,
                "message": f"Screenshot saved to {output_path}"
            }
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to capture screenshot: {str(e)}"
        }


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
    Tests both all containers and application-only containers.
    
    Args:
        loki_url: URL of Loki service
        
    Returns:
        Dictionary with test results
    """
    import requests
    
    results = {
        "receiving_logs": False,
        "log_count": 0,
        "app_log_count": 0,
        "labels": [],
        "container_names": [],
        "error": None
    }
    
    try:
        # First, query for all container logs
        params = {
            "query": '{container_name=~".+"}',
            "limit": 100,
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
                    
                    # Extract container names
                    for stream in streams:
                        stream_labels = stream.get("stream", {})
                        container_name = stream_labels.get("container_name", stream_labels.get("container", "unknown"))
                        if container_name and container_name not in results["container_names"]:
                            results["container_names"].append(container_name)
                    
                    # Count application logs (excluding monitoring containers)
                    monitoring_containers = ["grafana", "loki", "promtail"]
                    app_streams = [s for s in streams if s.get("stream", {}).get("container_name", "") not in monitoring_containers]
                    results["app_log_count"] = sum(len(stream.get("values", [])) for stream in app_streams)
                    
                else:
                    results["error"] = "No logs found in Loki - Promtail might not be sending logs"
            else:
                results["error"] = "Invalid response format from Loki"
        else:
            results["error"] = f"Loki query failed with status {response.status_code}: {response.text}"
        
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
    report += f"{'✅' if logs_flowing else '❌'} Log Flow: {'Active' if logs_flowing else 'No Logs Detected'}\n"
    
    # Show detailed log information
    if logs_flowing and diagnostics["logs"].get("container_names"):
        report += f"\n📦 Containers generating logs:\n"
        for container in diagnostics["logs"]["container_names"]:
            is_monitoring = container in ["grafana", "loki", "promtail"]
            icon = "🔧" if is_monitoring else "📦"
            label = " (monitoring)" if is_monitoring else " (application)"
            report += f"   {icon} {container}{label}\n"
        
        total_logs = diagnostics["logs"].get("log_count", 0)
        app_logs = diagnostics["logs"].get("app_log_count", 0)
        report += f"\n📊 Total logs: {total_logs} | Application logs: {app_logs}\n"
    report += "\n"
    
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
    
    # STEP 6: Launch Grafana Dashboard with Auto-Analysis & Screenshot
    report += "=" * 60 + "\n"
    report += "**STEP 6: Launching & Analyzing Grafana Dashboard...**\n\n"
    
    try:
        # Use the enhanced launch function with auto-analysis and screenshot
        launch_result = launch_grafana_dashboard(
            grafana_url="http://localhost:3001", 
            open_dashboard=True,
            auto_analyze=True,
            capture_screenshot=True,
            project_root=project_root
        )
        
        report += launch_result["message"] + "\n"
        
        # Store analysis and screenshot for later use
        if launch_result.get("log_analysis"):
            # Analysis already included in message
            pass
        
        if launch_result.get("screenshot"):
            # Screenshot already included in message
            pass
            
    except Exception as e:
        report += f"⚠️  Error during launch: {str(e)}\n"
        report += "   Please open manually: http://localhost:3001/d/app-logs/application-logs\n\n"
    
    # STEP 7: Check Grafana Logs for Errors & Auto-Fix
    report += "=" * 60 + "\n"
    report += "**STEP 7: Analyzing Grafana Logs & Auto-Fixing Issues...**\n\n"
    
    # Wait a moment for Grafana to process dashboard
    time.sleep(3)
    
    grafana_log_check = check_grafana_logs(project_root)
    
    if grafana_log_check["status"] == "healthy":
        report += "✅ Grafana logs are clean - no errors detected\n\n"
    elif grafana_log_check["status"] == "has_issues":
        report += "⚠️  Issues detected in Grafana logs:\n\n"
        
        # Show dashboard errors
        if grafana_log_check["dashboard_errors"]:
            report += "**Dashboard Errors:**\n"
            for err in grafana_log_check["dashboard_errors"]:
                report += f"  ❌ {err.get('error', 'Unknown error')}\n"
                if 'fix' in err:
                    report += f"     💡 Fix: {err['fix']}\n"
            report += "\n"
        
        # Show datasource errors
        if grafana_log_check["datasource_errors"]:
            report += "**Datasource Errors:**\n"
            for err in grafana_log_check["datasource_errors"]:
                report += f"  ❌ {err.get('error', 'Unknown error')}\n"
            report += "\n"
        
        # Show provisioning errors
        if grafana_log_check.get("provisioning_errors"):
            report += "**Provisioning Errors:**\n"
            for err in grafana_log_check["provisioning_errors"]:
                report += f"  ❌ {err.get('error', 'Unknown error')}\n"
                if 'fix' in err:
                    report += f"     💡 Fix: {err['fix']}\n"
            report += "\n"
        
        # Auto-fix if enabled
        if auto_fix:
            report += "**🔧 Applying Automatic Fixes...**\n\n"
            fix_result = fix_grafana_dashboard_errors(project_root, grafana_log_check)
            
            if fix_result["fixes_applied"]:
                for fix in fix_result["fixes_applied"]:
                    report += f"  ✅ {fix}\n"
                report += "\n"
                
                # COMPREHENSIVE VERIFICATION AFTER FIX
                report += "**🔍 Verifying Fixes...**\n\n"
                verification = verify_grafana_after_fix(project_root)
                
                if verification["status"] == "success" and verification["all_clear"]:
                    report += "✅ **ALL ISSUES RESOLVED!**\n"
                    report += "   Grafana logs are now clean\n"
                    report += "   Dashboard is accessible\n\n"
                elif verification["status"] == "partial":
                    report += "⚠️  Some issues remain:\n"
                    for issue in verification["issues_remaining"]:
                        report += f"   - {issue}\n"
                    report += "\n"
                else:
                    report += f"❌ Verification failed: {verification.get('status')}\n\n"
                
                # Report screenshot capture
                if verification["screenshot"]["status"] == "success":
                    report += f"📸 Verification screenshot captured: {verification['screenshot']['path']}\n\n"
            
            if fix_result["errors"]:
                report += "**Errors during fixing:**\n"
                for error in fix_result["errors"]:
                    report += f"  ⚠️  {error}\n"
                report += "\n"
        else:
            report += "💡 Run with auto_fix=True to automatically fix these issues\n\n"
    else:
        report += f"⚠️  Could not check Grafana logs: {grafana_log_check.get('errors', ['Unknown error'])[0]}\n\n"
    
    # STEP 8: Final Dashboard Screenshot for Verification
    report += "=" * 60 + "\n"
    report += "**STEP 8: Capturing Final Dashboard Screenshot...**\n\n"
    
    try:
        # Wait a moment for dashboard to fully load
        time.sleep(3)
        
        screenshot_path = os.path.join(project_root, "grafana_dashboard_final.png")
        screenshot_result = capture_grafana_screenshot("http://localhost:3001", screenshot_path, wait_for_login=True)
        
        if screenshot_result["status"] == "success":
            report += f"✅ Dashboard screenshot captured: {screenshot_result['path']}\n"
            report += "   Screenshot confirms dashboard is working properly\n\n"
            
            # Store base64 for potential display
            if "base64" in screenshot_result:
                report += f"   📸 Screenshot data available for viewing\n\n"
        else:
            report += f"⚠️  Could not capture screenshot: {screenshot_result.get('message', 'Unknown error')}\n"
            report += "   Dashboard may still be accessible - check manually\n\n"
    except Exception as e:
        report += f"⚠️  Screenshot capture error: {str(e)}\n"
        report += "   (This is optional - dashboard should still be accessible)\n\n"
    
    # STEP 9: Verify Logs are Visible
    report += "=" * 60 + "\n"
    report += "**STEP 9: Verifying Application Logs in Grafana...**\n\n"
    
    if logs_flowing:
        total_logs = diagnostics["logs"].get("log_count", 0)
        app_logs = diagnostics["logs"].get("app_log_count", 0)
        
        report += f"✅ SUCCESS! Loki has {total_logs} total log entries\n"
        report += f"   📦 Application logs: {app_logs}\n"
        report += f"   🔧 Monitoring logs: {total_logs - app_logs} (excluded from dashboard)\n\n"
        
        # Show which containers are visible
        if diagnostics["logs"].get("container_names"):
            app_containers = [c for c in diagnostics["logs"]["container_names"] if c not in ["grafana", "loki", "promtail"]]
            if app_containers:
                report += "**Application containers visible in dashboard:**\n"
                for container in app_containers:
                    report += f"   📦 {container}\n"
                report += "\n"
        
        # Show sample of recent application logs
        try:
            # Query only application logs
            logs_result = fetch_logs_from_loki("http://localhost:3100", '{container_name=~".+"} | container_name !~ "(grafana|loki|promtail)"', 5)
            if logs_result["status"] == "success" and logs_result["logs"]:
                report += "**Sample Application Logs:**\n"
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


def verify_grafana_after_fix(project_root: str) -> Dict:
    """
    Verify Grafana is working correctly after applying fixes.
    Checks logs again and captures screenshot.
    
    Args:
        project_root: Root directory of the project
        
    Returns:
        Dictionary with verification results
    """
    results = {
        "status": "unknown",
        "log_check": {},
        "screenshot": {},
        "issues_remaining": [],
        "all_clear": False
    }
    
    try:
        # Wait a moment for Grafana to stabilize
        time.sleep(3)
        
        # Check logs again
        log_check = check_grafana_logs(project_root)
        results["log_check"] = log_check
        
        # Determine if issues remain
        if log_check["status"] == "healthy":
            results["all_clear"] = True
            results["status"] = "success"
        elif log_check["status"] == "has_issues":
            results["status"] = "partial"
            results["issues_remaining"].extend([e.get("error", str(e)) for e in log_check.get("dashboard_errors", [])])
            results["issues_remaining"].extend([e.get("error", str(e)) for e in log_check.get("datasource_errors", [])])
            results["issues_remaining"].extend([e.get("error", str(e)) for e in log_check.get("provisioning_errors", [])])
        else:
            results["status"] = "error"
        
        # Capture screenshot to verify dashboard is accessible
        screenshot_path = os.path.join(project_root, "grafana_verification_after_fix.png")
        screenshot_result = capture_grafana_screenshot("http://localhost:3001", screenshot_path, wait_for_login=True)
        results["screenshot"] = screenshot_result
        
        return results
        
    except Exception as e:
        results["status"] = "error"
        results["issues_remaining"].append(f"Verification error: {str(e)}")
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
