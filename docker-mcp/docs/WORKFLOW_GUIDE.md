# Smart Dockerize & Show Logs Workflow Guide

## Overview

The **show_app_logs** tool is the most intelligent and comprehensive workflow in Docker MCP. It handles everything automatically when you ask to see application logs.

## When to Use

Use this tool when you want to:
- "Dockerize my application and show me the logs in grafana dashboard"
- "Show me the logs of this application"
- "Monitor my application"
- "View logs in Grafana"

## What It Does Automatically

### 🔍 Step 1: Application Analysis
- Detects application type (Python, Node.js, Java, etc.)
- Identifies dependencies
- Finds entry points
- Determines containerization requirements

### 📦 Step 2: Container Status Check
- Lists all running and stopped containers
- Identifies application vs monitoring containers
- Starts containers if they're stopped
- Dockerizes application if no containers exist

### 🛠️ Step 3: Monitoring Setup
- Creates Grafana + Loki + Promtail stack if needed
- Generates proper configuration files
- Starts monitoring containers
- Waits for services to be ready

### ✅ Step 4: Validation & Auto-Fix
- Tests Loki connection and health
- Tests Promtail connection and targets
- Verifies logs are flowing from Promtail → Loki
- **Auto-fixes common issues:**
  - Wrong Loki URL in Promtail config
  - Missing Docker socket access
  - Service connectivity problems
  - Container not running errors

### 🌐 Step 5: Browser Launch
- Opens Grafana dashboard in default browser
- Provides login credentials (admin/admin)
- Direct access to log visualization

### 📊 Step 6: Log Verification
- Queries Loki to verify logs are present
- Shows sample log entries
- Reports log count and status
- Provides troubleshooting steps if needed

## Usage Examples

### Basic Usage
```python
show_app_logs(project_root="C:\\Users\\YourName\\MyProject")
```

### With Manual Fix Control
```python
show_app_logs(
    project_root="C:\\Users\\YourName\\MyProject",
    auto_fix=False  # Don't auto-fix, just report issues
)
```

## Output Format

The tool provides a comprehensive report with:

```
🚀 Smart Dockerization & Log Monitoring
============================================================

STEP 1: Analyzing Application...
📁 Application Type: python
📦 Dependencies: 25 packages
🎯 Entry Point: app.py
✅ Analysis complete

============================================================
STEP 2: Checking Container Status...
📦 Found 3 application container(s)
✅ Running: 3
⏸️  Stopped: 0
✅ Application containers are running

============================================================
STEP 3: Setting Up Monitoring Stack...
✅ Monitoring stack already configured
✅ Monitoring containers started

============================================================
STEP 4: Validating Log Flow (Loki ← Promtail)...
✅ Loki: Ready
✅ Promtail: Ready
✅ Log Flow: Active

============================================================
STEP 5: Launching Grafana Dashboard...
✅ Grafana opened in browser: http://localhost:3001
   Username: admin
   Password: admin

============================================================
STEP 6: Verifying Logs in Grafana...
✅ SUCCESS! Loki has 1543 log entries
   Your logs should be visible in Grafana dashboard

Sample Recent Logs:
  • 2024-01-15 10:23:45 INFO Starting application server on port 8000...
  • 2024-01-15 10:23:46 INFO Database connection established...
  • 2024-01-15 10:23:47 INFO Application ready to receive requests...

============================================================
📊 FINAL STATUS
============================================================

✅ ALL SYSTEMS OPERATIONAL

Your application is:
  ✅ Dockerized and running
  ✅ Monitored by Grafana + Loki + Promtail
  ✅ Logs are flowing and visible

Next Steps:
  1. Open Grafana: http://localhost:3001
  2. Navigate to Dashboards → Application Logs
  3. View real-time logs from your services
============================================================
```

## Auto-Fix Capabilities

The workflow automatically fixes these common issues:

### Issue 1: Wrong Loki URL
**Problem:** Promtail configured with `http://localhost:3100` instead of docker service name  
**Fix:** Updates config to use `http://loki:3100`  
**Action:** Restarts Promtail to apply changes

### Issue 2: No Log Targets
**Problem:** Promtail not collecting from any containers  
**Fix:** Verifies Docker socket access and configuration  
**Action:** Restarts services and re-validates

### Issue 3: Services Not Running
**Problem:** Loki or Promtail containers stopped  
**Fix:** Starts containers with docker-compose  
**Action:** Waits for readiness and validates

### Issue 4: No Docker Compose
**Problem:** Application not dockerized  
**Fix:** Runs full dockerization workflow  
**Action:** Creates Dockerfile, docker-compose.yml, starts containers

## Troubleshooting

If logs still don't appear after auto-fix:

### 1. Check Application Logs
```bash
docker logs <container_name>
```
Verify your application is actually generating log output.

### 2. Check Promtail Logs
```bash
docker logs promtail
```
Look for errors connecting to Loki or reading container logs.

### 3. Verify Promtail Targets
```bash
curl http://localhost:9080/targets
```
Should show active targets (containers being monitored).

### 4. Test Loki Connection
```bash
curl http://localhost:3100/ready
```
Should return "ready" if Loki is operational.

### 5. Query Loki Directly
```bash
curl 'http://localhost:3100/loki/api/v1/query?query={job="docker"}'
```
Should return JSON with log entries if logs are flowing.

## Architecture

```
┌─────────────────┐
│   Application   │
│   Containers    │
└────────┬────────┘
         │ stdout/stderr
         ↓
┌─────────────────┐      ┌──────────────┐
│    Promtail     │─────→│     Loki     │
│  (Log Collect)  │ HTTP │ (Log Store)  │
└─────────────────┘      └──────┬───────┘
                                 │ LogQL
                                 ↓
                         ┌───────────────┐
                         │    Grafana    │
                         │ (Visualize)   │
                         └───────────────┘
```

## Configuration Files Created

The workflow creates these files automatically:

### 1. docker-compose.monitoring.yml
Defines Grafana, Loki, and Promtail services with proper networking.

### 2. promtail-config.yml
Configures log collection from Docker containers using Docker service discovery.

### 3. grafana/provisioning/datasources/loki.yml
Automatically configures Loki as Grafana data source.

### 4. grafana/provisioning/dashboards/app-logs.json
Pre-configured dashboard showing logs from all services.

## Performance Considerations

- **Startup Time:** 20-30 seconds for complete workflow
- **Log Retention:** Default Loki retention (check config for adjustment)
- **Resource Usage:** 
  - Grafana: ~200MB RAM
  - Loki: ~100MB RAM + log storage
  - Promtail: ~50MB RAM

## Security Notes

- Default Grafana credentials: admin/admin (change after first login)
- Loki API is exposed on localhost only by default
- Promtail requires Docker socket access (read-only)

## Related Tools

- **validate_monitoring**: Just validate without full workflow
- **show_logs**: Fetch logs programmatically without browser
- **dockerize_and_monitor**: Similar but without validation checks
- **setup_monitoring**: Just setup monitoring stack
