# Docker MCP Server

A Model Context Protocol (MCP) server that provides Docker containerization tools for applications. It can automatically detect, analyze, and dockerize both single services and multi-service projects (backend + frontend).

## 🚀 Version 2.0 - Streamlined & Simplified!

**Now with only 7 essential tools** (down from 20!) - Each tool is a complete workflow, not a single step.

## The 7 Essential Tools

### 1. **dockerize_project** 🐳 - Complete Dockerization
**Primary dockerization tool** - One command to dockerize everything!
- Detects all services (backend, frontend, API, etc.)
- Analyzes each service automatically
- Generates optimized Dockerfiles
- Creates docker-compose.yml
- **Builds all images**
- **Starts all containers**
- **Waits for services to be ready**
- Provides access URLs

**Use:** `dockerize_project(project_root="C:\\MyApp")`

---

### 2. **test_application_e2e** 🧪 - Browser Automation Testing
**Primary testing tool** - Direct Playwright browser automation!
- Checks container status (starts if needed)
- **Launches visible browser** using Playwright library (Chromium)
- **Performs real browser automation:**
  - Clicks buttons
  - Fills forms
  - Creates items
  - Navigates pages
  - Submits forms
- Captures screenshots as base64
- Validates frontend-backend communication
- **Keeps browser open 15 seconds for inspection**
- Generates detailed test report

**Use:** `test_application_e2e(project_root="C:\\MyApp")`

---

### 3. **show_app_logs** 📊 - Intelligent Log Monitoring
**Primary monitoring tool** - One command to see logs in Grafana!
- Dockerizes app if needed
- Starts containers if needed
- Sets up Grafana + Loki + Promtail
- **Validates logs are flowing**
- **Auto-fixes common issues** (Docker socket, config)
- **Launches Grafana dashboard** (directly to logs page!)
- Shows sample logs

**Use:** `show_app_logs(project_root="C:\\MyApp")`

---

### 4. **analyze_logs** 🔍 - AI-Powered Log Analysis
**Log analysis tool** - Find errors and get fix suggestions!
- Fetches logs from Loki
- Identifies errors, warnings, exceptions
- Detects patterns (connection errors, syntax errors)
- **Provides root cause analysis**
- **Suggests code fixes**

**Use:** `analyze_logs(service_name="backend")`

---

### 5. **fix_errors** 🔧 - Error Fixing
**Error fixing tool** - Auto-fix Dockerfile issues!
- Analyzes build/runtime errors
- Identifies root cause
- Suggests fixes
- Can automatically apply fixes

**Use:** `fix_errors(app_path="C:\\MyApp", error_message="...")`

---

### 6. **create_playwright_tests** 🎬 - Test Template Generation
**Test generation tool** - Generate Playwright test templates!
- Creates e2e-tests directory
- Generates Playwright config (direct library usage)
- Creates sample test templates (9+ scenarios)
- Ready for CI/CD integration

**Use:** `create_playwright_tests(project_root="C:\\MyApp")`

---

### 7. **detect_project_services** 🔎 - Service Detection
**Inspection tool** - See what services your project has!
- Scans project directory
- Identifies all services
- Analyzes technology stack
- Shows structure

**Use:** `detect_project_services(project_root="C:\\MyApp")`

---

## 🎯 Why Only 7 Tools?

**Before:** 20 tools, unclear which to use, multiple steps required  
**After:** 7 tools, each is a complete workflow, clear purpose

**Example - Dockerization:**
- ❌ Old: `analyze_app` → `generate_docker_file` → `build_image` → `start_services` (4 tools!)
- ✅ New: `dockerize_project` (1 tool does everything!)

**Example - Monitoring:**
- ❌ Old: `setup_monitoring` → `validate_monitoring` → `show_logs` → `open_grafana` (4 tools!)
- ✅ New: `show_app_logs` (1 tool does everything!)

See [TOOL_CONSOLIDATION.md](docs/TOOL_CONSOLIDATION.md) for full details.

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

### 🚀 Complete Automated Workflow (NEW!)

**One-Command Dockerization with Auto-Build & Auto-Start:**

```python
dockerize_project(project_root="C:\\Users\\YourName\\MyProject")
```

This now does EVERYTHING automatically:
1. ✅ Detect all services (backend, frontend, api, client, etc.)
2. ✅ Analyze each service and determine its type (Python, Node.js, etc.)
3. ✅ Generate optimized Dockerfiles for each service
4. ✅ Create a unified `docker-compose.yml` that runs all services together
5. ✅ Set up proper networking and port mappings
6. ✅ **BUILD all Docker images** (NEW! ⚡)
7. ✅ **START all containers** (NEW! 🚀)
8. ✅ **WAIT for services to be ready** (NEW! ⏱️)
9. ✅ **Display access URLs** (NEW! 🌐)

**Your application is now RUNNING and ready to test!**

---

### 🧪 Automated E2E Testing with Browser Launch (NEW!)

**One-Command Testing with Visible Browser & Real Interactions:**

```python
test_application_e2e(project_root="C:\\Users\\YourName\\MyProject")
```

This now:
1. ✅ **Checks if containers are running** (skips rebuild if already running)
2. ✅ **Starts containers if needed** (automatic)
3. ✅ **Waits for services to be ready** (health checks)
4. ✅ **LAUNCHES VISIBLE BROWSER** (Chromium window you can see!)
5. ✅ **Loads your application** (navigates to frontend)
6. ✅ **Performs REAL USER INTERACTIONS:**
   - 🖱️ Clicks buttons
   - ⌨️ Fills input fields
   - ➕ Creates tasks/items
   - 🔗 Tests navigation
   - 📝 Submits forms
7. ✅ **Takes before/after screenshots**
8. ✅ **Keeps browser open 15 seconds** for inspection
9. ✅ **Generates detailed report** with all interactions

**You SEE the browser and watch it interact with your app in SLOW MOTION!**

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

### 🎯 Real End-to-End Testing with ACTUAL User Interactions

**NEW!** The testing tool now performs REAL user interactions, not just opening the page!

**One command to test everything:**
```
test_application_e2e(project_root="C:\\path\\to\\MyProject")
```

**What it does NOW:**
- ✅ Starts all services with docker-compose
- ✅ Waits for services to be ready
- ✅ Opens browser (visible - you can watch!)
- ✅ **CLICKS BUTTONS** like a real user 🖱️
- ✅ **FILLS INPUT FIELDS** with test data ⌨️
- ✅ **CREATES TASKS/ITEMS** in your app ➕
- ✅ **NAVIGATES BETWEEN PAGES** 🔄
- ✅ **SUBMITS FORMS** 📝
- ✅ Takes before/after screenshots 📸
- ✅ Provides detailed interaction report 📊
- ✅ Proves your app works end-to-end! ✨

**Sample Test Report:**
```
📊 Test Results: 8/8 passed

🎬 User Interactions Performed:
   • Clicked button: Add Task
   • Filled field: "Enter task name" with "Test Task"
   • Created new item via form
   • Navigated to: About page
   • Submitted form successfully

📸 Screenshots saved:
   - frontend_initial.png
   - frontend_after_interactions.png
```

**For custom tests:**
1. Generate test templates:
   ```
   create_playwright_tests(project_root="C:\\path\\to\\MyProject")
   ```

2. Install Playwright (one time):
   ```bash
   cd MyProject/e2e-tests
   npm install
   npx playwright install
   ```

3. Customize tests in `e2e-tests/tests/app.spec.js` for your specific app

📖 **Full guide:** See `docs/REAL_E2E_TESTING.md` for detailed examples

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
