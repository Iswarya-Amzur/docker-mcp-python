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

### Multi-Service Tools (NEW! ✨)
7. **dockerize_project** - Automatically dockerize entire projects with backend + frontend
8. **detect_project_services** - Detect all services in a project

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

## Troubleshooting

### Encoding Errors on Windows
All subprocess calls use `encoding='utf-8'` and `errors='replace'` to handle special characters properly.

### Port Conflicts
Edit the port mappings in `docker-compose.yml`:
```yaml
ports:
  - "8001:8000"  # Change 8001 to your preferred port
```

### Service Not Detected
Ensure your project follows standard naming conventions:
- Backend: `backend/`, `api/`, `server/`
- Frontend: `frontend/`, `client/`, `web/`, `app/`

## Contributing

Feel free to submit issues and pull requests!

## License

MIT License
