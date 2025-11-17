# Enhanced Service Detection for Production Applications

## What Was Fixed

The service detection was enhanced to properly handle production-ready applications with various structures and frameworks.

## Previous Limitations

❌ Only detected exact directory names: `backend`, `frontend`, `api`, etc.  
❌ No support for monorepo structures  
❌ No framework-specific detection  
❌ No nested service detection  
❌ Limited to 7 hardcoded directory names  

## New Capabilities

✅ **Expanded Service Name Detection**
- Standard: `backend`, `frontend`, `api`, `client`, `server`, `web`, `app`
- Variants: `back-end`, `front-end`, `ui`, `www`, `service`, `services`

✅ **Monorepo Support**
- `packages/` - Detects all packages: `packages/backend`, `packages/frontend`
- `apps/` - Detects all apps: `apps/web`, `apps/api`
- `services/` - Detects all services: `services/auth`, `services/payments`
- `modules/` - Detects all modules

✅ **Nested Service Detection**
- `src/` - Checks nested source directories
- `lib/` - Checks library directories
- `core/` - Checks core application directories

✅ **Single-Service Projects**
- Detects root-level applications (no subdirectories needed)
- Automatically names as `app`

✅ **Framework-Specific Detection**

**Python:**
- Django (detects `manage.py`)
- Flask (detects `app.py` with Flask imports)
- FastAPI (detects FastAPI imports)
- General Python apps

**Node.js:**
- Next.js (detects `next` in dependencies)
- React (detects `react` in dependencies)
- Vue (detects `vue` in dependencies)
- Express (detects `express` in dependencies)
- General Node apps

**Other:**
- Java (Maven with `pom.xml`)
- Ruby (Rails with `Gemfile`)
- Go (with `go.mod`)
- .NET (with `.csproj`)
- Static sites (HTML files)

## Detection Strategies

### Strategy 1: Root-Level Single Service
```
my-app/
├── package.json    ← Detected as single service
├── src/
└── ...
```
**Result:** `{ "app": { "path": "my-app/", "type": "node", "framework": "react" } }`

### Strategy 2: Standard Service Names
```
my-app/
├── backend/
│   └── requirements.txt  ← Detected
├── frontend/
│   └── package.json      ← Detected
```
**Result:** 
```json
{
  "backend": { "path": "my-app/backend", "type": "python", "framework": "fastapi" },
  "frontend": { "path": "my-app/frontend", "type": "node", "framework": "nextjs" }
}
```

### Strategy 3: Monorepo Structure
```
my-app/
├── packages/
│   ├── api/
│   │   └── package.json    ← Detected
│   ├── web/
│   │   └── package.json    ← Detected
```
**Result:**
```json
{
  "packages-api": { "path": "my-app/packages/api", "type": "node", "framework": "express" },
  "packages-web": { "path": "my-app/packages/web", "type": "node", "framework": "react" }
}
```

### Strategy 4: Nested Services
```
my-app/
├── backend/
│   └── src/
│       └── requirements.txt  ← Detected in nested src/
```
**Result:** `{ "backend": { "path": "my-app/backend/src", "type": "python" } }`

### Strategy 5: Deep Recursive Search
If no services found in standard locations, searches all subdirectories (max 2 levels deep).

## Enhanced Analyzer

### Before
```python
analysis = {
    "app_type": "python",
    "entry_point": "main.py",
    "dependencies": [...]
}
```

### After
```python
analysis = {
    "app_type": "python",
    "framework": "fastapi",        # NEW: Specific framework
    "entry_point": "app.py",
    "port": 8000,                  # NEW: Default port
    "build_command": None,         # NEW: Build command
    "start_command": "uvicorn app:app --host 0.0.0.0 --port 8000",  # NEW
    "dependencies": [...]
}
```

## Detected Information

For each service, the system now detects:

1. **Service Type** - `python`, `node`, `java`, `ruby`, `go`, `dotnet`, `static`
2. **Framework** - `django`, `flask`, `fastapi`, `nextjs`, `react`, `vue`, `express`, etc.
3. **Entry Point** - Main file to run (`app.py`, `server.js`, etc.)
4. **Port** - Default port for the framework
5. **Build Command** - How to build (if needed)
6. **Start Command** - How to start the service
7. **Dependencies** - List of packages/modules

## Examples

### Django Backend + React Frontend
```
my-app/
├── backend/
│   ├── manage.py
│   └── requirements.txt
├── frontend/
│   ├── package.json
│   └── src/
```

**Detection:**
```json
{
  "backend": {
    "type": "python",
    "framework": "django",
    "port": 8000,
    "start_command": "python manage.py runserver 0.0.0.0:8000"
  },
  "frontend": {
    "type": "node",
    "framework": "react",
    "port": 3000,
    "start_command": "npm start"
  }
}
```

### Next.js Monorepo
```
my-app/
├── apps/
│   ├── web/
│   │   └── package.json (Next.js)
│   ├── admin/
│   │   └── package.json (Next.js)
```

**Detection:**
```json
{
  "apps-web": {
    "type": "node",
    "framework": "nextjs",
    "port": 3000,
    "build_command": "npm run build",
    "start_command": "npm start"
  },
  "apps-admin": {
    "type": "node",
    "framework": "nextjs",
    "port": 3000,
    "build_command": "npm run build",
    "start_command": "npm start"
  }
}
```

### FastAPI Microservices
```
my-app/
├── services/
│   ├── auth/
│   │   ├── app.py (FastAPI)
│   │   └── requirements.txt
│   ├── payments/
│   │   ├── main.py (FastAPI)
│   │   └── requirements.txt
```

**Detection:**
```json
{
  "services-auth": {
    "type": "python",
    "framework": "fastapi",
    "port": 8000,
    "entry_point": "app.py",
    "start_command": "uvicorn app:app --host 0.0.0.0 --port 8000"
  },
  "services-payments": {
    "type": "python",
    "framework": "fastapi",
    "port": 8000,
    "entry_point": "main.py",
    "start_command": "python main.py"
  }
}
```

### Single-Service Root
```
my-fastapi-app/
├── app.py
├── requirements.txt
└── models/
```

**Detection:**
```json
{
  "app": {
    "type": "python",
    "framework": "fastapi",
    "port": 8000,
    "entry_point": "app.py",
    "start_command": "uvicorn app:app --host 0.0.0.0 --port 8000"
  }
}
```

## Supported Project Structures

✅ Standard multi-service (backend/frontend)  
✅ Monorepos (packages/, apps/, services/)  
✅ Nested services (src/, lib/, core/)  
✅ Single-service at root  
✅ Microservices architecture  
✅ Mixed tech stacks  
✅ Framework-specific conventions  

## Testing the Detection

Use the `detect_project_services` tool:

```python
detect_project_services(project_root="C:\\MyApp")
```

**Output:**
```json
{
  "backend": {
    "path": "C:\\MyApp\\backend",
    "type": "python",
    "framework": "django",
    "analysis": {
      "port": 8000,
      "start_command": "python manage.py runserver 0.0.0.0:8000",
      "dependencies": ["django", "djangorestframework", "psycopg2"]
    }
  },
  "frontend": {
    "path": "C:\\MyApp\\frontend",
    "type": "node",
    "framework": "nextjs",
    "analysis": {
      "port": 3000,
      "build_command": "npm run build",
      "start_command": "npm start",
      "dependencies": ["next", "react", "react-dom"]
    }
  }
}
```

## Benefits

1. **Handles Real Production Apps** - Detects actual production project structures
2. **Framework Awareness** - Understands framework-specific conventions
3. **Flexible** - Works with monorepos, microservices, nested structures
4. **Smart Defaults** - Provides correct ports and start commands
5. **Comprehensive** - Detects 10+ frameworks across 7+ languages

The service detection now works with any production-ready application structure!
