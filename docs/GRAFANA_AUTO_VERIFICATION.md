# Grafana Auto-Verification & Fix System

## Overview

This document describes the comprehensive automatic verification and fix system for Grafana dashboard issues, implemented to handle provisioning errors and ensure the dashboard is working correctly.

## Problem Addressed

The Grafana logs showed several provisioning errors:
```
logger=provisioning.dashboard level=error msg="can't read dashboard provisioning files from directory" 
    path=/etc/grafana/provisioning/dashboards error="open /etc/grafana/provisioning/dashboards: no such file or directory"

logger=provisioning.alerting level=error msg="can't read alerting provisioning files from directory" 
    path=/etc/grafana/provisioning/alerting error="open /etc/grafana/provisioning/alerting: no such file or directory"

logger=provisioning.plugins level=error msg="Failed to read plugin provisioning files from directory" 
    path=/etc/grafana/provisioning/plugins error="open /etc/grafana/provisioning/plugins: no such file or directory"
```

## Solution Components

### 1. Enhanced Log Checking (`check_grafana_logs`)

**Location:** `docker-mcp/docker_tools/logging_monitor.py`

**Features:**
- Retrieves last 200 lines of Grafana logs (increased from 100)
- Detects multiple types of errors:
  - Dashboard provisioning errors
  - Datasource configuration errors
  - **NEW:** Provisioning directory errors (dashboards, alerting, plugins)
  - General errors and warnings

**Returns:**
```python
{
    "status": "healthy" | "has_issues" | "has_errors" | "error",
    "errors": [...],
    "warnings": [...],
    "dashboard_errors": [...],
    "datasource_errors": [...],
    "provisioning_errors": [...]  # NEW
}
```

### 2. Automatic Fix Mechanism (`fix_grafana_dashboard_errors`)

**Location:** `docker-mcp/docker_tools/logging_monitor.py`

**Fixes Applied:**

#### A. Missing Provisioning Directories
- Creates all required provisioning directories:
  - `/grafana/provisioning/dashboards`
  - `/grafana/provisioning/datasources`
  - `/grafana/provisioning/alerting`
  - `/grafana/provisioning/plugins`
  - `/grafana/provisioning/notifiers`

- Creates empty configuration files for:
  - `alerting/alerting.yml`
  - `plugins/plugins.yml`

#### B. Dashboard Structure Issues
- Regenerates dashboard JSON with correct structure
- Ensures title is at root level
- Validates panel configurations

#### C. Datasource Issues
- Regenerates datasource configuration
- Ensures Loki connection is properly configured

#### D. Service Restart
- Automatically restarts Grafana after fixes
- Waits for Grafana to stabilize (8 seconds)

**Returns:**
```python
{
    "status": "success" | "partial" | "no_fixes_applied" | "error",
    "fixes_applied": [...],
    "errors": [...]
}
```

### 3. Post-Fix Verification (`verify_grafana_after_fix`)

**Location:** `docker-mcp/docker_tools/logging_monitor.py`

**Verification Steps:**
1. Waits for Grafana to stabilize (3 seconds)
2. Re-checks Grafana logs for remaining issues
3. Captures screenshot of dashboard to verify accessibility
4. Compiles list of any remaining issues

**Returns:**
```python
{
    "status": "success" | "partial" | "error",
    "log_check": {...},
    "screenshot": {...},
    "issues_remaining": [...],
    "all_clear": True | False
}
```

### 4. Enhanced Screenshot Capture (`capture_grafana_screenshot`)

**Location:** `docker-mcp/docker_tools/logging_monitor.py`

**Improvements:**
- Handles login page automatically
- Waits for dashboard to load completely
- Captures full-page screenshots
- Returns base64-encoded image data
- Higher resolution (1920x1080 viewport)

**Parameters:**
```python
capture_grafana_screenshot(
    grafana_url="http://localhost:3001",
    output_path=None,  # Auto-generated if not provided
    wait_for_login=False  # Set to True to handle login
)
```

## Workflow Integration

The automatic verification is integrated into the main workflow (`smart_dockerize_and_show_logs`):

### STEP 7: Analyze & Auto-Fix
```
1. Check Grafana logs for errors
2. Display all detected issues
3. If auto_fix=True:
   a. Apply automatic fixes
   b. Restart Grafana
   c. Run comprehensive verification
   d. Capture verification screenshot
   e. Report results
```

### STEP 8: Final Screenshot
```
1. Wait for complete stabilization
2. Capture final dashboard screenshot with login handling
3. Provide visual confirmation of working dashboard
```

## Usage

### Automatic (Recommended)
When using `show_app_logs()` or `smart_dockerize_and_show_logs()`:
```python
from docker_tools.logging_monitor import smart_dockerize_and_show_logs

result = smart_dockerize_and_show_logs(
    project_root="C:\\MyApp",
    auto_fix=True  # Enable automatic fixes (default)
)
```

The system will automatically:
1. Detect Grafana issues
2. Apply fixes
3. Verify the fixes worked
4. Capture screenshots
5. Report the final status

### Manual Verification
To manually verify Grafana after making changes:
```python
from docker_tools.logging_monitor import verify_grafana_after_fix

verification = verify_grafana_after_fix("C:\\MyApp")

if verification["all_clear"]:
    print("✅ Grafana is working correctly!")
else:
    print(f"⚠️ Issues remain: {verification['issues_remaining']}")
```

## Expected Outcomes

### Successful Auto-Fix
```
⚠️  Issues detected in Grafana logs:

**Provisioning Errors:**
  ❌ Dashboard provisioning directory not found
     💡 Fix: Create directory and ensure volume mount

🔧 Applying Automatic Fixes...

  ✅ Created directory: C:\MyApp\grafana\provisioning\dashboards
  ✅ Created directory: C:\MyApp\grafana\provisioning\datasources
  ✅ Created directory: C:\MyApp\grafana\provisioning\alerting
  ✅ Created directory: C:\MyApp\grafana\provisioning\plugins
  ✅ Created empty alerting config
  ✅ Created empty plugins config
  ✅ Restarted Grafana to reload configuration

🔍 Verifying Fixes...

✅ **ALL ISSUES RESOLVED!**
   Grafana logs are now clean
   Dashboard is accessible

📸 Verification screenshot captured: C:\MyApp\grafana_verification_after_fix.png
```

### If Issues Remain
```
⚠️  Some issues remain:
   - Dashboard title cannot be empty
   - Failed to load datasource

Manual intervention may be required.
```

## Error Handling

The system gracefully handles:
- Network timeouts
- Docker command failures
- Screenshot capture failures (marked as optional)
- Playwright installation issues
- File system permission errors

All errors are logged and reported without stopping the workflow.

## Benefits

1. **Automatic Problem Resolution**: Most common Grafana issues are fixed automatically
2. **Visual Verification**: Screenshots provide proof that dashboard is working
3. **Comprehensive Logging**: All actions and results are documented
4. **Graceful Degradation**: System continues even if verification fails
5. **User-Friendly Reporting**: Clear, actionable feedback at each step

## Testing

To test the auto-fix system:

1. Delete provisioning directories:
   ```bash
   Remove-Item -Recurse -Force C:\MyApp\grafana\provisioning
   ```

2. Restart Grafana:
   ```bash
   docker-compose -f docker-compose.monitoring.yml restart grafana
   ```

3. Run the workflow:
   ```python
   smart_dockerize_and_show_logs("C:\\MyApp", auto_fix=True)
   ```

4. Verify:
   - Directories are recreated
   - Grafana logs are clean
   - Screenshot shows working dashboard

## Future Enhancements

Potential improvements:
- Add retry logic for transient network issues
- Implement health checks before verification
- Add metrics collection for monitoring success rate
- Create dashboard templates for different app types
- Support custom provisioning configurations

## Related Files

- `docker-mcp/docker_tools/logging_monitor.py` - Main implementation
- `docker-mcp/docker_tools/comprehensive_workflow_async.py` - Async workflow integration
- `docs/GRAFANA_FIX_SUMMARY.md` - Previous fix documentation
- `docs/MONITORING_GUIDE.md` - General monitoring setup guide

## Support

If automatic fixes don't resolve issues:
1. Check Grafana logs: `docker logs grafana`
2. Verify volume mounts in `docker-compose.monitoring.yml`
3. Ensure Docker has filesystem access
4. Review screenshot for visual clues
5. Check Loki connection: `curl http://localhost:3100/ready`
