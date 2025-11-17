# Quick Fix Guide: Grafana Dashboard "Title Cannot Be Empty" Error

## The Problem
```
ERROR: Dashboard title cannot be empty
ERROR: failed to load dashboard from /etc/grafana/provisioning/dashboards/app-logs.json
```

## The Solution
✅ **Fixed automatically** by the updated `show_app_logs()` tool!

## What Was Wrong
The dashboard JSON was missing required fields at the **root level**:
- Missing `"uid"` at root
- Missing `"title"` at root  
- Missing `"id"` at root

## How It Works Now

### Step-by-Step Workflow:

1. **Launch Grafana Dashboard**
   - Opens browser to dashboard URL
   
2. **Check Grafana Logs** ← NEW!
   - Analyzes last 100 lines of `docker logs grafana`
   - Detects provisioning errors
   - Identifies specific issues
   
3. **Automatically Fix Errors** ← NEW!
   - Regenerates dashboard with correct JSON structure
   - Restarts Grafana container
   - Waits for reload
   
4. **Verify Fix** ← NEW!
   - Re-checks Grafana logs
   - Confirms errors are gone
   
5. **Capture Screenshot** ← NEW!
   - Takes full-page screenshot of dashboard
   - Saves to project directory
   - Verifies dashboard is rendering
   
6. **Final Report**
   - Shows all fixes applied
   - Confirms dashboard is working
   - Displays screenshot location

## Usage

Just run the tool normally - fixes are automatic!

```python
show_app_logs(project_root="C:\\MyProject")
```

## What You'll See

### Before the Fix:
```
⚠️  Issues detected in Grafana logs:

**Dashboard Errors:**
  ❌ Dashboard title cannot be empty
     💡 Fix: Dashboard JSON structure incorrect - needs title at root level
```

### During Auto-Fix:
```
**Applying Automatic Fixes...**

  ✅ Regenerated dashboard JSON with correct structure
  ✅ Restarted Grafana to reload dashboard

**Re-checking Grafana logs after fixes...**
```

### After the Fix:
```
✅ Grafana logs are now clean!

**STEP 8: Capturing Dashboard Screenshot...**
✅ Dashboard screenshot captured: grafana_dashboard_verification.png
   Screenshot confirms dashboard is accessible
```

## Manual Verification

If you want to check manually:

```bash
# 1. Check Grafana logs
docker logs grafana | grep -i "error"

# 2. Check dashboard file
docker exec grafana cat /etc/grafana/provisioning/dashboards/app-logs.json

# 3. Open dashboard
# http://localhost:3001/d/app-logs/application-logs

# 4. Check screenshot
# Look for: grafana_dashboard_verification.png in project directory
```

## What Changed in the Code

### Dashboard JSON Structure (Before):
```json
{
  "dashboard": {
    "uid": "app-logs",
    "title": "Application Logs"
  }
}
```

### Dashboard JSON Structure (After):
```json
{
  "id": null,
  "uid": "app-logs",          ← Added at root
  "title": "Application Logs", ← Added at root
  "dashboard": {
    "id": null,
    "uid": "app-logs",
    "title": "Application Logs"
  }
}
```

## Common Questions

**Q: Will this fix existing broken dashboards?**  
A: Yes! The tool regenerates the dashboard with the correct structure.

**Q: Do I need to manually restart anything?**  
A: No! The tool automatically restarts Grafana after fixing.

**Q: What if screenshot capture fails?**  
A: Dashboard will still work. Screenshot is just for verification.

**Q: How do I disable auto-fix?**  
A: Use `show_app_logs(project_root=".", auto_fix=False)`

**Q: Where is the screenshot saved?**  
A: In your project root as `grafana_dashboard_verification.png`

## Disable Auto-Fix

If you want to see errors without fixing:

```python
show_app_logs(project_root="C:\\MyProject", auto_fix=False)
```

This will:
- ✅ Show errors detected
- ✅ Suggest fixes
- ❌ Not apply fixes automatically

## Files Modified

- `docker_tools/logging_monitor.py` - Core fix implementation
- Added 3 new functions:
  - `check_grafana_logs()` - Log analysis
  - `fix_grafana_dashboard_errors()` - Auto-fix
  - `capture_grafana_screenshot()` - Screenshot verification

## Success Indicators

You'll know it's working when you see:

1. ✅ No errors in Grafana logs
2. ✅ Dashboard loads without "Not Found" error
3. ✅ Screenshot file created
4. ✅ Logs visible in dashboard panels
5. ✅ Auto-refresh working (every 5 seconds)

## Troubleshooting

### Still seeing "title cannot be empty"?
- The dashboard file may be cached
- Solution: `docker-compose -f docker-compose.monitoring.yml restart grafana`

### Screenshot capture fails?
- Playwright may not be installed
- Solution: `pip install playwright; playwright install chromium`

### Dashboard directory not found?
- Volume mount may be incorrect
- Check `docker-compose.monitoring.yml` has:
  ```yaml
  volumes:
    - ./grafana/provisioning:/etc/grafana/provisioning
  ```

## Next Steps

After the fix:
1. Open http://localhost:3001/d/app-logs/application-logs
2. Login with admin/admin
3. See your logs in real-time!
4. Check the screenshot to confirm it's working

## Related Docs

- Full details: `GRAFANA_AUTO_FIX_SUMMARY.md`
- Dashboard fix: `GRAFANA_DASHBOARD_FIX.md`
- Monitoring guide: `docs/MONITORING_GUIDE.md`
