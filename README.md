# Docker MCP Server

A Model Context Protocol (MCP) server that provides Docker containerization tools for applications. It can automatically detect, analyze, and dockerize both single services and multi-service projects (backend + frontend).

## Features

### Single Service Tools
1. **analyze_app** - Analyze application structure and dependencies
2. **generate_docker_file** - Generate optimized Dockerfile for a service
3. **build_image** - Build Docker image with real-time output
4. **test_container** - Run tests inside a container
5. **fix_errors** - Analyze and suggest fixes for containerization errors
6. **get_container_logs** - Retrieve container logs for debugging

### Multi-Service Tools
7. **dockerize_project** - Automatically dockerize entire projects with backend + frontend
8. **detect_project_services** - Detect all services in a project

### End-to-End Testing Tools 🧪
9. **test_application_e2e** - Launch app in browser and run Playwright tests
10. **create_playwright_tests** - Generate Playwright test templates
11. **start_services** - Start docker-compose services
12. **stop_services** - Stop docker-compose services
13. **launch_app_in_browser** - Open app in browser window

### Log Monitoring Tools (NEW! 📊)
14. **setup_monitoring** - Setup Grafana/Loki/Promtail with auto-validation
15. **show_logs** - Fetch and display logs (auto-validates connection)
16. **analyze_logs** - AI-powered log analysis with fix suggestions
17. **open_grafana** - Launch Grafana dashboard in browser
18. **dockerize_and_monitor** - Complete workflow: dockerize + monitor + validate
19. **validate_monitoring** - Validate Loki/Promtail connection and auto-fix issues
20. **show_app_logs** - 🎯 SMART WORKFLOW: Complete end-to-end solution (analyze → dockerize → monitor → validate → launch → verify)

## Installation

1. Clone this repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure Claude Desktop or VS Code to use this MCP server

### Claude Desktop Configuration

Edit `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "docker-mcp": {
      "command": "python",
      "args": [
        "C:\\path\\to\\docker-mcp\\server.py"
      ]
    }
  }
}
```

### VS Code Configuration

Create `.vscode/mcp.json` in your workspace:

```json
{
  "servers": {
    "docker-mcp": {
      "type": "stdio",
      "command": "python",
      "args": ["C:\\path\\to\\docker-mcp\\server.py"],
      "cwd": "C:\\path\\to\\docker-mcp"
    }
  }
}
```

## Usage

### Dockerizing a Full Project (Backend + Frontend)

Use the **dockerize_project** tool with your project root:

```
dockerize_project(project_root="C:\\Users\\YourName\\MyProject")
```

This will:
1. ✅ Detect all services (backend, frontend, api, client, etc.)
2. ✅ Analyze each service and determine its type (Python, Node.js, etc.)
3. ✅ Generate optimized Dockerfiles for each service
4. ✅ Create a unified `docker-compose.yml` that runs all services together
5. ✅ Set up proper networking and port mappings

**Example Project Structure:**
```
MyProject/
├── backend/          # Python/Django/Flask app
│   ├── app.py
│   └── requirements.txt
├── frontend/         # React/Vue/Next.js app
│   ├── package.json
│   └── src/
├── docker-compose.yml (generated)
└── Dockerfiles (generated in each service)
```

**After dockerization, run:**
```bash
docker-compose up --build
```

### End-to-End Testing with Playwright

Test your dockerized application automatically:

1. **Generate test templates:**
```
create_playwright_tests(project_root="C:\\path\\to\\MyProject")
```

2. **Install Playwright (one time):**
```bash
cd MyProject/e2e-tests
npm install
npx playwright install
```

3. **Run complete E2E tests:**
```
test_application_e2e(project_root="C:\\path\\to\\MyProject")
```

This will:
- ✅ Start all services with docker-compose
- ✅ Wait for services to be ready
- ✅ Run Playwright tests against the running app
- ✅ Generate a detailed test report
- ✅ Clean up and stop services

**Manual control:**
```
start_services(project_root="C:\\path\\to\\MyProject")  # Start only
stop_services(project_root="C:\\path\\to\\MyProject")   # Stop only
```

### Single Service Dockerization

For single services, use the individual tools:

1. **Analyze the app:**
```
analyze_app(app_path="C:\\path\\to\\backend")
```

2. **Generate Dockerfile:**
```
generate_docker_file(app_path="C:\\path\\to\\backend", app_type="python")
```

3. **Build the image:**
```
build_image(app_path="C:\\path\\to\\backend", image_name="my-app", tag="latest")
```

## Supported Technologies

- **Python**: Flask, Django, FastAPI
- **Node.js**: Express, React, Next.js, Vue, Angular
- **Static Sites**: HTML/CSS/JS
- **Java**: Spring Boot
- **Ruby**: Rails, Sinatra

## Docker Compose Features

The generated `docker-compose.yml` includes:
- ✅ Multi-service setup with proper networking
- ✅ Automatic port mapping (backend: 8000, frontend: 3000)
- ✅ Environment variable configuration
- ✅ Volume mounting for development
- ✅ Service dependencies (frontend depends on backend)
- ✅ Optional database and Redis services (commented out)
- ✅ Health checks for all services

## Log Monitoring with Grafana

**NEW!** Monitor your dockerized applications with Grafana dashboards:

### Quick Start - One Command

```
dockerize_and_monitor(project_root="C:\\path\\to\\MyProject")
```

This will:
1. ✅ Dockerize your entire project (backend + frontend)
2. ✅ Setup Grafana + Loki + Promtail monitoring stack
3. ✅ Generate pre-configured dashboards
4. ✅ Start all services
5. ✅ Open Grafana in your browser

**Access Grafana:**
- URL: http://localhost:3001
- Username: `admin`
- Password: `admin`

### Individual Monitoring Tools

**Setup monitoring only:**
```
setup_monitoring(project_root="C:\\path\\to\\MyProject", services="backend,frontend")
```

**View logs:**
```
show_logs(service_name="backend", limit=100)
```

**Analyze logs for errors:**
```
analyze_logs(service_name="backend")
```

This provides:
- ✅ Error detection
- ✅ Pattern recognition
- ✅ AI-powered fix suggestions
- ✅ Root cause analysis

**Open dashboard:**
```
open_grafana()
```

### What You Get

- **Real-time log streaming** from all containers
- **Pre-built dashboards** for each service
- **Log search** with powerful query language
- **Error analysis** with automatic fix suggestions
- **Pattern detection** for common issues

See [MONITORING_GUIDE.md](./MONITORING_GUIDE.md) for complete documentation.

---

## Troubleshooting

### Encoding Errors on Windows
All subprocess calls use `encoding='utf-8'` and `errors='replace'` to handle special characters properly.

### Port Conflicts
Edit the port mappings in `docker-compose.yml`:
```yaml
ports:
  - "8001:8000"  # Change 8001 to your preferred port
```

For monitoring ports:
- Grafana: 3001 (default)
- Loki: 3100 (default)

### Service Not Detected
Ensure your project follows standard naming conventions:
- Backend: `backend/`, `api/`, `server/`
- Frontend: `frontend/`, `client/`, `web/`, `app/`

### Grafana Not Accessible
Check if monitoring stack is running:
```bash
docker ps | grep -E "grafana|loki|promtail"
```

Restart monitoring stack:
```bash
docker-compose -f docker-compose.monitoring.yml restart
```

## Contributing

Feel free to submit issues and pull requests!

## License

MIT License
