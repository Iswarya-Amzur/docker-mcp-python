# 🔄 Automatic Cleanup and Rebuild Guide

## What's New?

The docker-mcp tool now **automatically cleans up existing containers** before building to avoid port conflicts, and **rebuilds containers when Dockerfiles are updated**.

## How It Works

### 1. **Automatic Container Cleanup** (Step 4)
Before building new containers, the tool automatically:
- ✅ Stops all running docker-compose services using `docker-compose down -v`
- ✅ Stops and removes individual containers that might conflict
- ✅ **Skips monitoring containers** (Loki, Promtail, Grafana, Prometheus) to keep your monitoring stack running
- ✅ Prevents port conflicts by ensuring a clean slate

### 2. **Smart Dockerfile Updates** (Step 2)
When Dockerfiles are regenerated:
- ✅ Tracks which Dockerfiles were updated
- ✅ Triggers automatic rebuild when updates are detected
- ✅ Shows rebuild indicator: "🔄 Dockerfiles were updated - rebuilding images..."

### 3. **Automatic Build and Run** (Step 5)
After cleanup, the tool:
- ✅ Builds all Docker images with `docker-compose up --build`
- ✅ Starts containers in detached mode
- ✅ Waits for services to be ready
- ✅ Provides access URLs for your application

## Workflow Steps

```
Step 1: Detecting Services
   ↓
Step 2: Generating Dockerfiles (tracks updates)
   ↓
Step 3: Generating docker-compose.yml
   ↓
Step 4: Cleaning Up Existing Containers ⭐ NEW
   ├─ Stop docker-compose services
   ├─ Stop conflicting containers
   ├─ Remove old containers
   └─ Keep monitoring containers running
   ↓
Step 5: Building and Starting Containers ⭐ UPDATED
   ├─ Rebuild if Dockerfiles updated
   ├─ Build all images
   └─ Start containers
   ↓
Step 6: Waiting for Services
```

## Usage

### Standard Usage (with cleanup)
```python
dockerize_project(project_root="C:\\MyApp")
```

This will:
1. Detect services
2. Generate Dockerfiles
3. Generate docker-compose.yml
4. **Clean up existing containers** ⭐
5. **Build and start containers** ⭐
6. Wait for services to be ready

### Manual Mode (skip auto-start)
```python
dockerize_full_project(project_root="C:\\MyApp", auto_start=False)
```

This will only generate files without cleanup or building.

## Benefits

### ✅ No More Port Conflicts
The cleanup step removes containers that might be using the same ports as your new application.

### ✅ Fresh Builds Every Time
When Dockerfiles are updated, containers are automatically rebuilt to pick up the changes.

### ✅ Monitoring Stays Running
Your Loki/Grafana monitoring stack is preserved during cleanup, so you don't lose logs.

### ✅ Zero Manual Intervention
Everything happens automatically - no need to manually run `docker-compose down` or `docker stop`.

## Example Output

```
🐳 **Dockerizing Project: C:\MyApp**

**Step 1: Detecting Services (Enhanced)...**
✅ Found 2 application service(s):
  - backend: python
  - frontend: node

**Step 2: Generating Dockerfiles...**
✅ backend: Dockerfile created at C:\MyApp\backend\Dockerfile
✅ frontend: Dockerfile created at C:\MyApp\frontend\Dockerfile

**Step 3: Generating docker-compose.yml...**
✅ docker-compose.yml created at C:\MyApp\docker-compose.yml

**Step 4: Cleaning Up Existing Containers...**
✅ Stopped containers: docker-compose services
✅ Removed containers: backend-container, frontend-container

**Step 5: Building and Starting Containers...**
🔄 Dockerfiles were updated - rebuilding images...
⏳ This may take a few minutes on first build...

✅ Containers built and started successfully!

**Step 6: Waiting for Services to be Ready...**
✅ Services are ready!
   ✅ backend
   ✅ frontend

🚀 **Application is Running!**
============================================================
   🔧 Backend:  http://localhost:8000
   🌐 Frontend: http://localhost:3000
============================================================
```

## Technical Details

### Cleanup Function
Located in: `docker_tools/multi_service_handler.py` and `multi_service_handler_enhanced.py`

```python
def cleanup_containers(project_root: str) -> dict:
    """
    Stop and remove all running containers to avoid port conflicts.
    Skips monitoring containers (Loki, Promtail, Grafana, Prometheus).
    """
```

### What Gets Cleaned Up?
- ✅ All docker-compose services in the project
- ✅ Standalone containers that might conflict
- ❌ Monitoring containers (preserved)

### What Triggers a Rebuild?
- ✅ Any Dockerfile is created or updated
- ✅ docker-compose.yml is regenerated
- ✅ Manual call to `dockerize_project()`

## Troubleshooting

### Issue: Monitoring containers stopped during cleanup
**Solution:** The tool is designed to skip containers with names containing: `loki`, `promtail`, `grafana`, `prometheus`. Check your container names match this pattern.

### Issue: Cleanup fails with permission errors
**Solution:** Ensure Docker is running and you have permissions. Try running Docker Desktop as administrator on Windows.

### Issue: Containers don't rebuild after Dockerfile changes
**Solution:** The tool tracks updates automatically. If you manually edit Dockerfiles, call `dockerize_project()` again to trigger a rebuild.

## Best Practices

1. **Let the tool handle cleanup** - Don't manually run `docker-compose down` before dockerizing
2. **Keep monitoring containers named properly** - Use names like `loki`, `grafana`, `promtail` so they're preserved
3. **Wait for Step 6 completion** - Ensure services are fully ready before accessing them
4. **Check the output** - The tool reports exactly what was cleaned up and rebuilt

## Migration from Old Behavior

### Old Way
```bash
# Manual cleanup required
docker-compose down
docker stop $(docker ps -q)
docker rm $(docker ps -aq)

# Then dockerize
dockerize_project(project_root="C:\\MyApp")
```

### New Way
```python
# Everything automatic!
dockerize_project(project_root="C:\\MyApp")
```

---

**Note:** This enhancement is available in both `multi_service_handler.py` and `multi_service_handler_enhanced.py`.
