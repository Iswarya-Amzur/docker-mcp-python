# 📊 Docker MCP Monitoring Guide

Complete guide for setting up and using Grafana log monitoring with Docker MCP.

## 🎯 Overview

The Docker MCP monitoring stack provides:
- **Grafana**: Visual dashboards for log exploration
- **Loki**: Log aggregation and querying
- **Promtail**: Automatic log collection from containers
- **AI-powered analysis**: Smart error detection and fix suggestions

## 🚀 Quick Start

### One-Command Solution

The fastest way to dockerize your app and see logs in Grafana:

```
dockerize_and_monitor(project_root="/path/to/your/project")
```

This single command will:
1. ✅ Detect all services (backend, frontend, etc.)
2. ✅ Generate Dockerfiles for each service
3. ✅ Create docker-compose.yml
4. ✅ Setup Grafana + Loki + Promtail
5. ✅ Start all services
6. ✅ Open Grafana dashboard in your browser

**Result:** Your app is running and logs are visible in Grafana!

---

## 📋 Available Tools

### 1. Setup Monitoring Stack

Setup Grafana monitoring for your dockerized application:

```
setup_monitoring(
    project_root="/path/to/project",
    services="backend,frontend"  # Optional, auto-detected if not provided
)
```

**What it does:**
- Generates Loki configuration for log aggregation
- Generates Promtail configuration for log collection
- Creates Grafana datasource pointing to Loki
- Generates pre-configured dashboards
- Starts monitoring stack (Grafana, Loki, Promtail)

**Output:**
```
📊 GRAFANA DASHBOARD READY!
🌐 Grafana URL: http://localhost:3001
👤 Username: admin
🔑 Password: admin
```

---

### 2. Show Application Logs

Fetch and display logs from your services:

```
show_logs(
    service_name="backend",  # Optional, shows all if not provided
    limit=100  # Number of log lines
)
```

**Example output:**
```
📋 Logs for backend

Total Logs: 47

[2024-01-15T10:30:45Z] INFO: Server started on port 8000
[2024-01-15T10:30:46Z] INFO: Database connection established
[2024-01-15T10:31:12Z] ERROR: Failed to process request: Connection timeout
```

---

### 3. Analyze Logs for Errors

AI-powered log analysis with automatic fix suggestions:

```
analyze_logs(
    service_name="backend",  # Optional
    limit=200  # Logs to analyze
)
```

**What it detects:**
- ❌ Errors and exceptions
- ⚠️ Warnings
- 🔍 Common patterns (connection issues, missing modules, permissions, etc.)

**Example output:**
```
🔍 Log Analysis Report

Total Logs Analyzed: 183
Errors Found: 5
Warnings Found: 2
Exceptions Found: 1

🔧 SUGGESTED FIXES

Issue #1: Module Not Found / Import Error

Error Log:
ModuleNotFoundError: No module named 'requests'

Possible Causes:
  - Missing dependency
  - Package not installed in Docker image

Suggested Fixes:
  ✅ Add missing package to requirements.txt
  ✅ Rebuild Docker image: docker-compose build
  ✅ Verify package is installed: pip list
```

---

### 4. Open Grafana Dashboard

Launch Grafana in your browser:

```
open_grafana(grafana_url="http://localhost:3001")
```

Opens Grafana dashboard automatically where you can:
- View real-time logs
- Search and filter logs
- Create custom queries
- Set up alerts

---

### 5. Complete Workflow

Full automation - dockerize and monitor in one command:

```
dockerize_and_monitor(
    project_root="/path/to/project",
    services="backend,frontend,api"  # Optional
)
```

**Complete workflow:**
1. Analyzes project structure
2. Generates Dockerfiles
3. Creates docker-compose.yml
4. Builds Docker images
5. Starts application services
6. Configures monitoring stack
7. Starts Grafana/Loki/Promtail
8. Opens Grafana in browser

**Perfect for:** First-time setup or complete refresh

---

## 🏗️ Architecture

### Services and Ports

| Service   | Port | Purpose                    |
|-----------|------|----------------------------|
| Grafana   | 3001 | Dashboard and visualization|
| Loki      | 3100 | Log aggregation           |
| Promtail  | 9080 | Log collection            |

### Data Flow

```
Docker Containers → Promtail → Loki → Grafana
                     (collect)  (store)  (visualize)
```

1. **Promtail** watches Docker container logs
2. **Loki** indexes and stores logs efficiently
3. **Grafana** provides visual interface and queries

---

## 📁 Generated Files

When you setup monitoring, these files are created:

```
project-root/
├── docker-compose.monitoring.yml   # Monitoring services
├── promtail-config.yml            # Log collection config
└── grafana/
    └── provisioning/
        ├── datasources/
        │   └── loki.yml           # Loki datasource
        └── dashboards/
            ├── provider.yml       # Dashboard provider
            └── app-logs.json      # Pre-built dashboard
```

---

## 🎨 Using Grafana Dashboard

### Login

1. Open http://localhost:3001
2. Username: `admin`
3. Password: `admin`

### Navigate to Logs

1. Click **Dashboards** in sidebar
2. Select **Application Logs**
3. View logs from all services

### Search Logs

Use Loki's LogQL query language:

```logql
# All logs from backend
{container=~".*backend.*"}

# Error logs only
{container=~".*backend.*"} |= "ERROR"

# Logs in time range
{container=~".*frontend.*"} [5m]
```

### Filter by Service

Pre-built panels show logs separated by service:
- Backend Logs
- Frontend Logs
- API Logs
- (Custom services you define)

---

## 🔍 Log Analysis Features

### Automatic Error Detection

The `analyze_logs` tool automatically finds:

1. **Connection Errors**
   - Connection refused
   - Timeouts
   - Network issues

2. **Import Errors**
   - Missing modules
   - Package not found
   - Wrong Python path

3. **Permission Errors**
   - File access denied
   - Docker volume permissions
   - User privileges

4. **Memory Issues**
   - Out of memory
   - OOM kills
   - Memory leaks

5. **Database Errors**
   - Connection failures
   - SQL errors
   - Schema issues

6. **HTTP Errors**
   - 404 Not Found
   - 500 Internal Server Error
   - Authentication failures

### AI-Powered Fix Suggestions

For each detected error, you get:
- **Issue description**: What went wrong
- **Possible causes**: Why it happened
- **Suggested fixes**: How to resolve it
- **Code examples**: Exact commands or config changes

---

## 🛠️ Troubleshooting

### Grafana Not Accessible

**Problem:** Can't access http://localhost:3001

**Solutions:**
```bash
# Check if Grafana is running
docker ps | grep grafana

# View Grafana logs
docker logs grafana

# Restart monitoring stack
cd /path/to/project
docker-compose -f docker-compose.monitoring.yml restart
```

### No Logs Visible

**Problem:** Grafana shows no logs

**Solutions:**
1. Ensure your app containers are running:
   ```bash
   docker ps
   ```

2. Check Promtail is collecting logs:
   ```bash
   docker logs promtail
   ```

3. Verify Loki is receiving logs:
   ```bash
   curl http://localhost:3100/ready
   ```

4. Check Loki datasource in Grafana:
   - Go to Configuration → Data Sources
   - Click on Loki
   - Click "Test" button

### Logs Not Being Collected

**Problem:** Only seeing monitoring stack logs

**Cause:** Promtail needs access to Docker socket

**Solution:**
Ensure `promtail-config.yml` has correct Docker socket path:
```yaml
scrape_configs:
  - job_name: docker
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
```

On Windows with Docker Desktop, this is handled automatically.

---

## 📊 Dashboard Customization

### Add New Panel

1. Open Grafana dashboard
2. Click "Add panel" at top
3. Select "Logs" visualization
4. Set query: `{container=~".*yourservice.*"}`
5. Click "Apply"

### Create Custom Dashboard

1. Click "+" in sidebar → "Dashboard"
2. Add panels for each service
3. Configure queries and visualizations
4. Save dashboard

### Export Dashboard

1. Open dashboard
2. Click share icon → "Export"
3. Save JSON file
4. Place in `grafana/provisioning/dashboards/`

---

## 🚀 Advanced Usage

### Filter Logs by Log Level

```logql
# Only errors
{container=~".*backend.*"} |= "ERROR"

# Warnings and errors
{container=~".*backend.*"} |~ "ERROR|WARNING"

# Exclude info logs
{container=~".*backend.*"} != "INFO"
```

### Count Errors Over Time

```logql
sum(rate({container=~".*backend.*"} |= "ERROR" [5m]))
```

### Extract JSON Fields

```logql
{container=~".*backend.*"} | json | level="error"
```

### Multi-Service Search

```logql
# All services with errors
{job="docker"} |= "ERROR"

# Specific services
{container=~".*(backend|frontend).*"} |= "ERROR"
```

---

## 🔄 Workflow Examples

### Example 1: First Time Setup

User: "Dockerize my application and show me the logs in Grafana"

```
dockerize_and_monitor(project_root="/home/user/myapp")
```

**Result:**
- App dockerized
- Monitoring configured
- Grafana opens automatically
- Logs visible immediately

---

### Example 2: Check Recent Errors

User: "Show me recent errors from backend"

```
analyze_logs(service_name="backend", limit=100)
```

**Result:**
- Analyzes last 100 log lines
- Lists all errors
- Provides fix suggestions
- Shows error patterns

---

### Example 3: Monitor Specific Service

User: "Show logs for the API service"

```
show_logs(service_name="api", limit=50)
```

**Result:**
- Displays last 50 log lines from API
- Shows timestamps
- Formatted for readability

---

### Example 4: Setup Only Monitoring

User: "Add monitoring to my existing docker-compose setup"

```
setup_monitoring(
    project_root="/path/to/project",
    services="web,database,redis"
)
```

**Result:**
- Adds monitoring to existing setup
- Doesn't modify your docker-compose.yml
- Creates separate monitoring compose file
- Starts monitoring stack

---

## 🎓 Best Practices

### 1. Regular Log Analysis

Run log analysis periodically:
```
analyze_logs(limit=500)  # Analyze more logs
```

### 2. Service-Specific Monitoring

Create separate dashboards for critical services:
```
setup_monitoring(
    project_root="/path/to/project",
    services="payment-service,auth-service"
)
```

### 3. Log Retention

Loki stores logs in `/loki` volume. Configure retention:
- Default: 7 days
- Adjust in Loki config for longer retention

### 4. Alert Setup

Set up alerts in Grafana for critical errors:
1. Create alert rule
2. Set threshold (e.g., >10 errors in 5 minutes)
3. Configure notification channel (email, Slack, etc.)

---

## 📚 Additional Resources

### Loki Query Language (LogQL)

Full documentation: https://grafana.com/docs/loki/latest/logql/

### Grafana Dashboards

Browse community dashboards: https://grafana.com/grafana/dashboards/

### Docker Logging

Docker logging best practices: https://docs.docker.com/config/containers/logging/

---

## 🆘 Support

### Common Issues

1. **Port conflicts**: Change ports in `docker-compose.monitoring.yml`
2. **Memory issues**: Increase Docker memory allocation
3. **Slow queries**: Reduce log retention or add filters

### Debug Mode

Enable debug logging in Grafana:
```yaml
environment:
  - GF_LOG_LEVEL=debug
```

---

## ✅ Summary

| Use Case | Tool | Command |
|----------|------|---------|
| First-time setup | dockerize_and_monitor | Full automation |
| Add monitoring | setup_monitoring | Monitoring only |
| View logs | show_logs | Quick log view |
| Find errors | analyze_logs | AI-powered analysis |
| Open dashboard | open_grafana | Browser launch |

**Remember:** The monitoring stack runs alongside your app - it doesn't modify your application code or configurations!

---

**Happy Monitoring! 📊🚀**
