# Grafana Dashboard Auto-Fix Implementation

## Critical Issue Fixed

**Error**: `"Dashboard title cannot be empty"`

**Root Cause**: Grafana provisioning API requires the dashboard JSON to have `title` and `uid` at the **root level**, not just nested inside the `dashboard` object.

### Incorrect Structure (Before):
```json
{
  "dashboard": {
    "uid": "app-logs",
    "title": "Application Logs",
    ...
  },
  "overwrite": true
}
```

### Correct Structure (After):
```json
{
  "id": null,
  "uid": "app-logs",           // ← At root level
  "title": "Application Logs",  // ← At root level
  "dashboard": {
    "id": null,
    "uid": "app-logs",
    "title": "Application Logs",
    ...
  },
  "overwrite": true
}
```

## New Features Added

### 1. **Automatic Grafana Log Checking** (`check_grafana_logs()`)

Automatically analyzes Grafana container logs to detect:
- ✅ Dashboard provisioning errors ("Dashboard title cannot be empty")
- ✅ Dashboard loading failures
- ✅ Missing directory mounts
- ✅ Datasource configuration errors
- ✅ General errors and warnings

**Returns**: Categorized errors with suggested fixes

### 2. **Automatic Error Fixing** (`fix_grafana_dashboard_errors()`)

Automatically fixes detected issues:
- ✅ Regenerates dashboard JSON with correct structure
- ✅ Restarts Grafana to reload configuration
- ✅ Validates fixes by re-checking logs
- ✅ Provides detailed report of fixes applied

**Fixes Applied**:
- Dashboard JSON structure (title at root level)
- Dashboard file regeneration
- Grafana service restart

### 3. **Dashboard Screenshot Verification** (`capture_grafana_screenshot()`)

Takes a screenshot of the Grafana dashboard to verify it's working:
- ✅ Uses Playwright for automated browser capture
- ✅ Saves screenshot to project directory
- ✅ Returns base64-encoded image for display
- ✅ Confirms dashboard is accessible and rendering

### 4. **Enhanced Workflow** (`smart_dockerize_and_show_logs()`)

Updated workflow now includes automatic verification:

```
STEP 6: Launch Grafana Dashboard
  ↓
STEP 7: Check Grafana Logs for Errors
  ├─ Analyze logs
  ├─ Detect dashboard errors
  ├─ Apply automatic fixes
  └─ Re-check logs after fixing
  ↓
STEP 8: Capture Dashboard Screenshot
  ├─ Take full-page screenshot
  ├─ Save to project directory
  └─ Verify dashboard is rendering
  ↓
STEP 9: Verify Logs are Visible
  └─ Confirm real-time log flow
```

## Usage

### Automatic Mode (Recommended)
```python
# The tool will automatically:
# 1. Launch Grafana
# 2. Check logs for errors
# 3. Fix any issues found
# 4. Take screenshot to verify
# 5. Report final status

show_app_logs(project_root="C:\\MyProject", auto_fix=True)
```

### What Happens Automatically:

1. **Dashboard Launch**: Opens Grafana at `http://localhost:3001/d/app-logs/application-logs`

2. **Log Analysis**: Checks Grafana container logs for errors:
   ```bash
   docker logs --tail 100 grafana
   ```

3. **Error Detection**: Identifies specific issues:
   - "Dashboard title cannot be empty"
   - "failed to load dashboard"
   - "no such file or directory"
   - Datasource errors

4. **Automatic Fixing**:
   - Regenerates dashboard JSON with correct structure
   - Restarts Grafana container
   - Waits for reload (5 seconds)

5. **Verification**:
   - Re-checks logs to confirm fix
   - Captures screenshot
   - Validates dashboard is accessible

6. **Final Report**: Shows:
   - ✅ All fixes applied
   - ✅ Screenshot location
   - ✅ Dashboard status
   - ✅ Log flow verification

## Log Checking Examples

### Healthy Logs:
```
✅ Grafana logs are clean - no errors detected
```

### Issues Detected:
```
⚠️  Issues detected in Grafana logs:

**Dashboard Errors:**
  ❌ Dashboard title cannot be empty
     💡 Fix: Dashboard JSON structure incorrect - needs title at root level

**Applying Automatic Fixes...**

  ✅ Regenerated dashboard JSON with correct structure: .../app-logs.json
  ✅ Restarted Grafana to reload dashboard

**Re-checking Grafana logs after fixes...**
✅ Grafana logs are now clean!
```

### Screenshot Verification:
```
**STEP 8: Capturing Dashboard Screenshot...**

✅ Dashboard screenshot captured: C:\MyProject\grafana_dashboard_verification.png
   Screenshot confirms dashboard is accessible
   📸 Screenshot available (base64 encoded)
```

## Error Patterns Detected

### Dashboard Errors:
1. **"Dashboard title cannot be empty"**
   - Fix: Regenerate JSON with title at root level
   
2. **"failed to load dashboard"**
   - Fix: Check JSON syntax and structure
   
3. **"no such file or directory" + "provisioning/dashboards"**
   - Fix: Check volume mount in docker-compose.yml

### Datasource Errors:
1. **"failed to load datasource"**
   - Fix: Check datasource configuration
   
2. **Datasource connection errors**
   - Fix: Verify Loki URL and connectivity

## Code Changes

### Files Modified:

1. **`docker_tools/logging_monitor.py`**:
   - Fixed `generate_grafana_dashboard()` - Lines ~218-243
   - Added `check_grafana_logs()` - New function
   - Added `fix_grafana_dashboard_errors()` - New function
   - Added `capture_grafana_screenshot()` - New function
   - Updated `smart_dockerize_and_show_logs()` - Lines ~1730-1820

### Key Changes:

```python
# OLD: Dashboard JSON structure
dashboard = {
    "dashboard": {
        "uid": "app-logs",
        "title": "Application Logs",
        ...
    }
}

# NEW: Correct structure with root-level fields
dashboard = {
    "id": None,
    "uid": "app-logs",           # Root level
    "title": "Application Logs",  # Root level
    "dashboard": {
        "id": None,
        "uid": "app-logs",
        "title": "Application Logs",
        ...
    }
}
```

## Testing

### Test Scenario 1: Dashboard Error Fix
```bash
# Start with broken dashboard
docker-compose -f docker-compose.monitoring.yml up -d

# Check logs - will show "Dashboard title cannot be empty"
docker logs grafana

# Run tool with auto_fix
show_app_logs(project_root=".", auto_fix=True)

# Expected result:
# - Error detected
# - Dashboard regenerated
# - Grafana restarted
# - Logs clean
# - Screenshot captured
# - Dashboard accessible
```

### Test Scenario 2: Manual Verification
```bash
# After running the tool, verify:
1. Dashboard loads: http://localhost:3001/d/app-logs/application-logs
2. No "Dashboard not found" error
3. Logs appear in panels
4. Screenshot file exists: grafana_dashboard_verification.png
5. Grafana logs are clean: docker logs grafana | grep -i error
```

## Troubleshooting

### Issue: Screenshot Fails
**Cause**: Playwright not installed or Grafana not accessible

**Solution**:
```bash
pip install playwright
playwright install chromium
```

### Issue: Dashboard Still Not Loading
**Cause**: Volume mount issue or JSON syntax error

**Check**:
```bash
# Verify dashboard file exists
docker exec grafana ls -la /etc/grafana/provisioning/dashboards/

# Check file content
docker exec grafana cat /etc/grafana/provisioning/dashboards/app-logs.json

# Verify volume mount in docker-compose.monitoring.yml:
volumes:
  - ./grafana/provisioning:/etc/grafana/provisioning
```

### Issue: Logs Show "no such file or directory"
**Cause**: Dashboard directory not mounted properly

**Fix**:
1. Check `docker-compose.monitoring.yml` has correct volume mounts
2. Regenerate monitoring stack:
   ```bash
   docker-compose -f docker-compose.monitoring.yml down -v
   # Run show_app_logs() again
   ```

## Benefits

### Before This Fix:
- ❌ Dashboard provisioning failed silently
- ❌ "Dashboard not found" error in browser
- ❌ Manual log checking required
- ❌ Manual JSON editing required
- ❌ No verification of dashboard functionality

### After This Fix:
- ✅ Dashboard provisions correctly
- ✅ Automatic error detection
- ✅ Automatic error fixing
- ✅ Screenshot verification
- ✅ Complete workflow validation
- ✅ User sees working dashboard immediately

## Related Documentation

- Main fix document: `GRAFANA_DASHBOARD_FIX.md`
- Monitoring guide: `docs/MONITORING_GUIDE.md`
- Previous fixes: `docs/GRAFANA_FIX_SUMMARY.md`

## Success Criteria

When running `show_app_logs()`, you should see:

```
✅ Grafana logs are clean - no errors detected
✅ Dashboard screenshot captured
✅ Dashboard confirms is accessible
✅ Logs are flowing and visible

📊 FINAL STATUS
✅ ALL SYSTEMS OPERATIONAL

Your application is:
  ✅ Dockerized and running
  ✅ Monitored by Grafana + Loki + Promtail
  ✅ Logs are flowing and visible
  ✅ Dashboard verified with screenshot
```

## Implementation Date
November 17, 2025

## Issue Reference
- Original error: "Dashboard title cannot be empty"
- Grafana logs showing repeated provisioning failures
- Dashboard not found at `/d/app-logs/application-logs`
