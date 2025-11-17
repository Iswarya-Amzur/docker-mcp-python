# Grafana Dashboard & Real-Time Logs Fix

## Issues Fixed

### 1. **Dashboard Not Found Error**
**Problem**: Grafana showing "Dashboard not found" when navigating to `/d/app-logs/application-logs`

**Root Cause**:
- Datasource UID was missing in the datasource configuration
- Dashboard was referencing `uid: "loki"` but datasource wasn't configured with that UID
- Dashboard structure didn't match Grafana's expected format

**Fix Applied**:
- Added `uid: loki` to the datasource configuration in `generate_grafana_datasource()`
- Added `orgId: 1` and `editable: false` for proper provisioning
- Ensured dashboard references match the datasource UID

### 2. **Real-Time Logs Not Showing**
**Problem**: Dashboard created but no logs appearing, even when containers are running

**Root Causes**:
- LogQL queries were too restrictive: `{job="docker", container_name=~".*service.*"}`
- Promtail not extracting proper labels from Docker containers
- Missing filter for running containers only

**Fix Applied**:
- Simplified LogQL queries: `{job="docker"}` for "All Logs" panel
- Used case-insensitive regex for service-specific panels: `{job="docker"} |~ "(?i)service"`
- Enhanced Promtail configuration with better label extraction:
  - `container_name` - Full container name
  - `container_id` - Container ID
  - `image` - Docker image name
  - `service` - Docker Compose service name
  - `stream` - stdout/stderr
- Added filter to only scrape running containers

### 3. **Dashboard Always Shows "All Logs" Panel**
**Problem**: Even single-service apps need a working logs view

**Fix Applied**:
- Always create an "All Docker Container Logs" panel as the first panel
- This ensures at least one panel will show logs from all containers
- Service-specific panels are additional, not replacements

## Configuration Files Updated

### 1. Datasource Configuration (`grafana/provisioning/datasources/loki.yml`)
```yaml
apiVersion: 1

datasources:
  - name: Loki
    type: loki
    access: proxy
    orgId: 1
    uid: loki          # CRITICAL: Must match dashboard references
    url: http://loki:3100
    isDefault: true
    editable: false
    jsonData:
      maxLines: 1000
      timeout: 60
```

### 2. Promtail Configuration (`promtail-config.yml`)
```yaml
server:
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
            values: [running]    # Only scrape running containers
    relabel_configs:
      # Extract container name (remove leading slash)
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
```

### 3. Dashboard Configuration
- **Dashboard UID**: `app-logs`
- **Direct URL**: `http://localhost:3001/d/app-logs/application-logs`
- **Main Panel**: "All Docker Container Logs" - Shows ALL logs from ALL Docker containers
- **Query**: `{job="docker"}` - Simple, catches everything
- **Auto-refresh**: Every 5 seconds

## How to Apply the Fixes

### Option 1: Recreate Monitoring Stack (Recommended)
```bash
# Stop and remove existing monitoring
cd your-project-directory
docker-compose -f docker-compose.monitoring.yml down -v

# Remove old configuration files
Remove-Item -Recurse -Force grafana, promtail-config.yml -ErrorAction SilentlyContinue

# Run the dockerization tool again (it will use the new fixed code)
# The tool will regenerate all configs with the fixes
```

### Option 2: Manual Update (If you want to keep existing setup)

1. **Update datasource configuration**:
```bash
# Edit grafana/provisioning/datasources/loki.yml
# Add the uid: loki line (see config above)
```

2. **Update Promtail configuration**:
```bash
# Edit promtail-config.yml
# Add the enhanced relabel_configs (see config above)
```

3. **Restart services to apply changes**:
```bash
docker-compose -f docker-compose.monitoring.yml restart promtail loki grafana
```

4. **Wait for services to stabilize** (10-15 seconds)

5. **Access Grafana**:
   - URL: http://localhost:3001/d/app-logs/application-logs
   - Login: admin / admin
   - You should now see the "All Docker Container Logs" panel with real-time logs

## Verification Steps

### 1. Check Promtail is Scraping Targets
```bash
# Should show discovered Docker containers
curl http://localhost:9080/targets
```

### 2. Check Loki is Receiving Logs
```bash
# Should return log entries
curl 'http://localhost:3100/loki/api/v1/query_range?query={job="docker"}&limit=10'
```

### 3. Check Grafana Dashboard
1. Open http://localhost:3001
2. Login with admin/admin
3. Navigate to Dashboards → Application Logs
4. You should see logs appearing in real-time
5. If not, check:
   - Are your application containers running? `docker ps`
   - Are they generating logs? `docker logs <container-name>`
   - Is Promtail running? `docker logs promtail`
   - Is Loki running? `docker logs loki`

## Troubleshooting

### Dashboard Still Shows "Not Found"
- **Issue**: Dashboard file not loaded by Grafana
- **Solution**: 
  ```bash
  # Restart Grafana to reload provisioned dashboards
  docker-compose -f docker-compose.monitoring.yml restart grafana
  
  # Wait 10 seconds, then access:
  # http://localhost:3001/d/app-logs/application-logs
  ```

### No Logs Appearing in Dashboard
- **Issue**: Promtail not collecting logs
- **Check**:
  1. Are containers running and generating logs?
     ```bash
     docker ps
     docker logs <your-app-container>
     ```
  2. Is Promtail seeing targets?
     ```bash
     curl http://localhost:9080/targets
     ```
  3. Check Promtail logs for errors:
     ```bash
     docker logs promtail
     ```
  4. Verify Docker socket access:
     ```bash
     # On Windows with Docker Desktop, check Docker is running
     docker version
     ```

### Logs Appear But Are Delayed
- **Issue**: Default refresh interval might be too long
- **Solution**: 
  - Dashboard is set to auto-refresh every 5 seconds
  - You can manually adjust in Grafana: Top-right corner → Refresh interval → 5s

### "No Data" Error in Panel
- **Issue**: LogQL query not matching any logs
- **Solution**:
  1. Go to Explore (left sidebar in Grafana)
  2. Select "Loki" datasource
  3. Try simple query: `{job="docker"}`
  4. If this works, dashboard should work too
  5. If this doesn't work, check Loki is receiving logs (see verification steps)

## Code Changes Summary

**File**: `docker_tools/logging_monitor.py`

**Functions Modified**:
1. `generate_grafana_datasource()` - Added UID and orgId
2. `generate_promtail_config()` - Enhanced label extraction
3. `generate_grafana_dashboard()` - Improved LogQL queries and always include "All Logs" panel

**Key Changes**:
- Line ~147: Added `uid: loki` and `orgId: 1` to datasource config
- Line ~99-121: Enhanced Promtail relabel_configs with more labels
- Line ~242-246: Changed LogQL query from `{job="docker", container_name=~".*service.*"}` to `{job="docker"} |~ "(?i)service"`
- Line ~277-305: Always create "All Docker Container Logs" panel with query `{job="docker"}`

## Testing the Fixes

Use the MCP tool to test:

```python
# In your MCP client (GitHub Copilot Chat):
# Run the show_app_logs tool on any project

show_app_logs(project_root="C:\\Users\\IswaryaK\\your-project")

# Expected result:
# - Monitoring stack created
# - Grafana opens automatically
# - Dashboard loads successfully (no "Not Found" error)
# - Logs appear in real-time from running containers
```

## Additional Notes

- **Dashboard UID**: The `uid: "app-logs"` in dashboard config must be unique and used in URL
- **Datasource UID**: The `uid: "loki"` in datasource config must match dashboard references
- **orgId**: Default Grafana organization is 1
- **LogQL Syntax**: `{job="docker"}` is simplest query that matches all Docker logs
- **Case-insensitive search**: `|~ "(?i)pattern"` uses regex flag for case-insensitive matching

## Success Criteria

✅ Grafana dashboard loads without "Not Found" error
✅ "All Docker Container Logs" panel shows real-time logs
✅ Logs auto-refresh every 5 seconds
✅ Container names visible in log labels
✅ Can filter logs by clicking on labels
✅ Logs from all running containers appear within 10-15 seconds of container start

## Related Documentation

- Original issue: Screenshot showing "Dashboard not found" in Grafana at `localhost:3001/d/app-logs/application-logs`
- See also: `docs/GRAFANA_FIX_SUMMARY.md` for previous fixes
- See also: `docs/MONITORING_GUIDE.md` for monitoring stack overview
