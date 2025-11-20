# Port Detection Fix for Vite and Frontend Frameworks

## Problem

Port detection was not working correctly for Vite and other frontend frameworks. The system would fall back to default port 3000 or 8000 instead of detecting the correct port from configuration files like `vite.config.js`.

**Example Issue:**
- Vite projects have `vite.config.js` with `server: { port: 5173 }`
- Port detector was returning 8000 or 3000 instead of 5173

## Root Cause

In `port_detector.py`, the `detect_ports_in_code()` function had a framework filter that only included some frontend frameworks but **not Vite**:

```python
# OLD CODE - Missing Vite!
elif framework_lower in ['react', 'vue', 'angular', 'next']:
    detected_ports.update(_detect_frontend_ports(app_path))
```

When framework was 'vite', it would skip `_detect_frontend_ports()` and fall back to generic detection or framework defaults, missing the actual port configuration in `vite.config.js`.

## Solution

### 1. Added Vite to Framework Detection List

```python
# NEW CODE - Includes all frontend frameworks
elif framework_lower in ['react', 'vue', 'angular', 'next', 'vite', 'svelte', 'gatsby', 'nuxt']:
    detected_ports.update(_detect_frontend_ports(app_path))
```

### 2. Added Vite Default Port

Also added Vite's default port (5173) to the fallback defaults:

```python
defaults = {
    # ... other frameworks
    'vite': 5173,  # Vite default dev server port
    # ...
}
```

## How Port Detection Works Now

1. **Framework-specific detection** (if framework hint provided):
   - Django → `_detect_django_ports()`
   - Flask → `_detect_flask_ports()`
   - FastAPI → `_detect_fastapi_ports()`
   - Express/Node → `_detect_node_ports()`
   - **Vite/React/Vue/Angular/etc** → `_detect_frontend_ports()` ✅

2. **Frontend port detection** scans:
   - `vite.config.js` / `vite.config.ts` → `port: 5173`
   - `webpack.config.js` → `port: 8080`
   - `angular.json` → `"port": 4200`
   - `vue.config.js` → `port: 8080`
   - `next.config.js` → `port: 3000`
   - `package.json` scripts with `--port` flags

3. **Confidence scoring**:
   - Config file match: +15 confidence bonus
   - Multiple occurrences: +2 per occurrence (up to +10)
   - Common dev ports (3000, 5000, 8000, etc): +5 bonus

4. **Fallback to framework default**:
   - If no port detected or confidence < 5
   - Returns framework-specific default (e.g., 5173 for Vite)

## Test Results

### Before Fix
```
Language: node ✅
Framework: vite ✅
Port: 8000 ❌  (incorrect fallback)
```

### After Fix
```
Language: node ✅
Framework: vite ✅
Port: 5173 ✅  (detected from vite.config.js)
```

### All Tests Passing

✅ **Test 1**: Root language priority (2/2 passed)
- React with Android directory → Node, Vite, 5173
- Java Spring Boot → Java

✅ **Test 2**: Language detection (3/3 passed)
- Python Flask → python, flask, 5000
- Node Express → node, express, 3000
- React Vite → node, vite, 5173

✅ **Test 3**: User scenario (all checks passed)
- issue-tracker with android/ → Node, Vite, 5173

## Files Modified

1. **`docker_tools/port_detector.py`**:
   - Line 38: Added 'vite', 'svelte', 'gatsby', 'nuxt' to frontend framework detection
   - Line 367: Added 'vite': 5173 to default ports
   - Line 377: Changed fallback default from 8000 to 3000

## Impact

✅ **Vite projects** now correctly detect port 5173 from config files  
✅ **Svelte projects** now correctly detect ports from config  
✅ **Gatsby projects** now correctly detect ports from config  
✅ **Nuxt projects** now correctly detect ports from config  
✅ **All frontend frameworks** benefit from enhanced config file scanning

## Usage

No code changes required - port detection is automatic:

```python
from docker_tools.analyzer import analyze_application

# Vite project with vite.config.js containing port: 5173
analysis = analyze_application("/path/to/vite-app")

print(analysis['port'])  # 5173 (correctly detected!)
print(analysis['framework'])  # 'vite'
```

The port detection now:
1. Scans `vite.config.js` for port configuration
2. Falls back to framework default (5173) if not found
3. Works for all frontend frameworks (React, Vue, Angular, Vite, Svelte, Gatsby, Nuxt)
