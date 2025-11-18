# Automatic Container Health Fix

## Overview

The Docker MCP monitoring stack now includes **automatic container health detection and fixing**. When containers become unhealthy due to missing packages or other common issues, the system can automatically detect and resolve them without manual intervention.

## Features

### 1. Automatic Health Monitoring
- Continuously checks all running containers for health status
- Detects containers marked as "unhealthy" by Docker health checks
- Analyzes health check logs to identify root causes

### 2. Auto-Fix for Common Issues

#### Missing Python Packages
- **Detection**: Identifies `ModuleNotFoundError` in health check logs
- **Fix**: Automatically installs missing packages using `pip install`
- **Verification**: Restarts container and re-checks health status

**Example:**
```
Container: backend-container
Issue: ModuleNotFoundError: No module named 'requests'
Auto-Fix: 
  1. Install 'requests' package: docker exec -u 0 backend-container pip install requests
  2. Restart container: docker restart backend-container
  3. Wait 10 seconds for stabilization
  4. Re-check health status
```

#### Other Detected Issues
- **Connection Refused**: Logged for manual review (service may not be ready yet)
- **Permission Denied**: Logged for manual review (file/directory permissions)

### 3. Integration with Monitoring Workflow

The auto-fix is integrated into the main `smart_dockerize_and_show_logs` workflow:

```
STEP 1: Analyze Application
STEP 2: Check Container Status
STEP 2.5: Check and Fix Container Health  ← AUTO-FIX HERE
STEP 3: Setup Monitoring Stack
STEP 4: Validate Log Flow
STEP 5: Wait for Logs to Flow
STEP 6: Launch Grafana Dashboard
```

## Usage

### Programmatic Usage

```python
from docker_tools.logging_monitor import check_and_fix_container_health

# Check and fix all containers
result = check_and_fix_container_health()

# Check result
if result['status'] == 'healthy':
    print("All containers are healthy!")
elif result['status'] == 'success':
    print(f"Fixed {len(result['fixes_applied'])} issues")
    for fix in result['fixes_applied']:
        print(f"  - {fix}")
```

### Command Line Testing

```bash
# Run the test script
python test_auto_fix_health.py

# Or integrate with existing workflows
cd test-app
python -c "from docker_tools.logging_monitor import smart_dockerize_and_show_logs; smart_dockerize_and_show_logs('.')"
```

### MCP Tool Usage

The auto-fix is automatically triggered when using the MCP tool:

```json
{
  "tool": "dockerize_and_test",
  "parameters": {
    "project_root": "/path/to/project",
    "auto_fix_errors": true  // Enable auto-fix (default: true)
  }
}
```

## How It Works

### Detection Process

1. **Get Container List**: Query Docker for all running containers
2. **Check Health Status**: Inspect each container's health check status
3. **Analyze Logs**: For unhealthy containers, fetch health check logs
4. **Pattern Matching**: Search logs for known error patterns:
   - `ModuleNotFoundError: No module named 'xxx'`
   - `ImportError: cannot import name 'xxx'`
   - `Connection refused`
   - `Permission denied`

### Fix Application

For **missing Python packages**:
```bash
# 1. Extract module name from error
ModuleNotFoundError: No module named 'requests' → module_name = 'requests'

# 2. Install package as root (bypass permission issues)
docker exec -u 0 container_name pip install module_name

# 3. Restart container
docker restart container_name

# 4. Wait for stabilization (10 seconds)

# 5. Re-check health
docker ps -a --format "{{.Names}}\t{{.Status}}"
```

### Result Reporting

The function returns a detailed result dictionary:

```python
{
    "status": "success" | "healthy" | "partial" | "no_fixes_available" | "error",
    "containers_checked": ["backend", "frontend", "grafana", ...],
    "unhealthy_containers": ["backend"],
    "fixes_applied": [
        "Installed 'requests' in backend-container",
        "Restarted backend-container"
    ],
    "errors": [
        "Failed to install module X",
        "Container Y still unhealthy"
    ]
}
```

## Status Codes

- **`healthy`**: All containers are healthy, no fixes needed
- **`success`**: Fixes were applied and all containers are now healthy
- **`partial`**: Fixes were applied but some containers are still unhealthy
- **`no_fixes_available`**: Unhealthy containers detected but no automatic fixes available
- **`error`**: Error occurred during health check process

## Configuration

### Enable/Disable Auto-Fix

```python
# Enable auto-fix (default)
smart_dockerize_and_show_logs(project_root, auto_fix=True)

# Disable auto-fix (manual intervention only)
smart_dockerize_and_show_logs(project_root, auto_fix=False)
```

### Timeout Settings

The auto-fix has built-in timeouts:
- **Package Installation**: 60 seconds
- **Container Restart**: 30 seconds
- **Stabilization Wait**: 10 seconds
- **Health Re-check**: 10 seconds

## Limitations

### What It Can Fix
- ✅ Missing Python packages (`ModuleNotFoundError`)
- ✅ Missing Python modules (`ImportError`)

### What It Cannot Fix (Logged Only)
- ⚠️ Connection refused (may resolve on its own as services start)
- ⚠️ Permission denied (requires Dockerfile or volume changes)
- ⚠️ Configuration errors (requires manual review)
- ⚠️ Network issues (requires Docker network configuration)
- ⚠️ Resource constraints (requires Docker resource limits adjustment)

## Best Practices

1. **Always enable auto-fix in development**: Speeds up debugging
2. **Review logs after auto-fix**: Ensure fixes are appropriate
3. **Update Dockerfiles**: Add missing packages to `requirements.txt` or Dockerfile to prevent recurrence
4. **Monitor container logs**: Use Grafana dashboard to track container health over time

## Examples

### Example 1: Missing Package Fix

**Before:**
```
Container: backend-container
Status: unhealthy (FailingStreak: 28)
Health Log: ModuleNotFoundError: No module named 'requests'
```

**Auto-Fix Applied:**
```
✅ Installed 'requests' in backend-container
✅ Restarted backend-container
```

**After:**
```
Container: backend-container
Status: healthy
Health Log: (no errors)
```

### Example 2: Multiple Containers

**Before:**
```
Container: backend-container - unhealthy (missing 'requests')
Container: worker-container - unhealthy (missing 'celery')
Container: frontend-container - healthy
```

**Auto-Fix Applied:**
```
✅ Installed 'requests' in backend-container
✅ Restarted backend-container
✅ Installed 'celery' in worker-container
✅ Restarted worker-container
```

**After:**
```
Container: backend-container - healthy
Container: worker-container - healthy
Container: frontend-container - healthy
```

## Testing

Run the test suite to verify auto-fix functionality:

```bash
# Basic health check test
python test_auto_fix_health.py

# Full workflow test with auto-fix
python docker-mcp/test_e2e_workflow.py

# Manual simulation (create unhealthy container)
# 1. Remove package from container
docker exec -u 0 backend-container pip uninstall -y requests

# 2. Wait for health check to fail (30-60 seconds)
docker inspect --format='{{.State.Health.Status}}' backend-container
# Output: unhealthy

# 3. Run auto-fix
python -c "from docker_tools.logging_monitor import check_and_fix_container_health; result = check_and_fix_container_health(); print(result)"

# 4. Verify fix
docker inspect --format='{{.State.Health.Status}}' backend-container
# Output: healthy (after 30-40 seconds)
```

## Troubleshooting

### Container Still Unhealthy After Fix

**Possible Causes:**
1. Package installation failed (check install logs)
2. Container needs more time to start (wait 30-60 seconds)
3. Health check configuration is incorrect
4. Other underlying issues (not package-related)

**Solution:**
```bash
# Check container logs
docker logs backend-container --tail 50

# Manually inspect health
docker inspect backend-container

# Re-run auto-fix
python -c "from docker_tools.logging_monitor import check_and_fix_container_health; check_and_fix_container_health()"
```

### Auto-Fix Not Detecting Issue

**Possible Causes:**
1. Health check not configured in Dockerfile
2. Error pattern not recognized
3. Container not marked as "unhealthy" yet

**Solution:**
```bash
# Add health check to Dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=2)" || exit 1

# Rebuild container
docker-compose build
docker-compose up -d
```

## Future Enhancements

Planned improvements for auto-fix:
- [ ] Auto-fix for Node.js/npm package issues
- [ ] Auto-fix for database connection issues
- [ ] Auto-fix for port conflicts
- [ ] Auto-fix for volume permission issues
- [ ] Configurable retry logic
- [ ] Integration with Grafana alerts
- [ ] Email/Slack notifications on auto-fix
- [ ] Detailed fix logs in Grafana dashboard

## Related Documentation

- [Monitoring Guide](docs/MONITORING_GUIDE.md)
- [Grafana Dashboard Fix](docs/GRAFANA_DASHBOARD_FIX.md)
- [E2E Testing Guide](docs/E2E_TESTING_GUIDE.md)
- [Complete Workflow Guide](docs/COMPLETE_WORKFLOW_GUIDE.md)
