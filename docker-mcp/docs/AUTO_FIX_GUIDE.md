# Auto-Fix Guide - E2E Testing

## 🔧 Automatic Error Detection & Resolution

The Docker MCP E2E testing module includes intelligent auto-fix capabilities that detect common issues and automatically apply solutions without manual intervention.

---

## 🎯 Auto-Fix Features

### 1. **Asyncio Loop Conflict Resolution**

**Problem:**
```
Error running interactive tests: It looks like you are using Playwright Sync API inside the asyncio loop.
Please use the Async API instead.
```

**Auto-Fix:**
- ✅ Automatically detects when code is running inside an asyncio event loop
- ✅ Switches from Playwright Sync API to system browser fallback
- ✅ Opens application in your default browser (Chrome, Edge, Firefox, etc.)
- ✅ Runs basic connectivity tests
- ✅ Provides clear feedback about what happened

**What It Does:**
```python
# Before auto-fix (would error):
try:
    from playwright.sync_api import sync_playwright  # ❌ Fails in asyncio loop
    with sync_playwright() as p:
        browser = p.chromium.launch()
        # ... tests ...
except RuntimeError:
    # ERROR: asyncio loop conflict

# After auto-fix (works automatically):
import asyncio
try:
    asyncio.get_running_loop()
    # Detected asyncio loop! Use fallback instead
    return _run_tests_with_system_browser(...)  # ✅ Opens in default browser
except RuntimeError:
    # No loop, use Playwright normally
    pass
```

---

### 2. **Playwright Installation Issues**

**Problem:**
```
ImportError: No module named 'playwright'
```

**Auto-Fix:**
- ✅ Catches Playwright import errors
- ✅ Automatically falls back to system browser
- ✅ Provides installation instructions
- ✅ Still opens your application so you can test manually

**What It Does:**
```python
try:
    from playwright.sync_api import sync_playwright
    # ... run tests ...
except ImportError:
    # Auto-fix: Use system browser instead
    logger.warning("Playwright not installed - using system browser")
    return _run_tests_with_system_browser(...)
```

---

### 3. **Browser Binary Missing**

**Problem:**
```
Error: Executable doesn't exist at /path/to/chromium
```

**Auto-Fix:**
- ✅ Detects missing Playwright browser binaries
- ✅ Switches to system browser
- ✅ Provides command to install browsers: `playwright install`
- ✅ Application still opens for testing

---

### 4. **General Error Recovery**

**Problem:**
Any unexpected error during E2E testing

**Auto-Fix:**
- ✅ Catches all exceptions
- ✅ Attempts to open application in system browser
- ✅ Returns partial results instead of complete failure
- ✅ Provides error details and suggested fixes

---

## 📊 How Auto-Fix Works

### Detection Flow

```
┌─────────────────────────────┐
│  run_interactive_tests()    │
└──────────┬──────────────────┘
           │
           ├─► Check 1: Are we in asyncio loop?
           │   ├─ YES ► Use system browser fallback ✅
           │   └─ NO  ► Continue to Playwright
           │
           ├─► Check 2: Is Playwright installed?
           │   ├─ NO  ► Use system browser fallback ✅
           │   └─ YES ► Continue to browser launch
           │
           ├─► Check 3: Are browser binaries available?
           │   ├─ NO  ► Use system browser fallback ✅
           │   └─ YES ► Launch Playwright browser
           │
           └─► Check 4: Did any error occur?
               └─ YES ► Try system browser fallback ✅
```

### Fallback Function

The `_run_tests_with_system_browser()` function provides:

1. **Opens application in default browser**
   - Uses Python's `webbrowser` module
   - Works on Windows, macOS, Linux
   - Opens in Chrome, Edge, Firefox, Safari, etc.

2. **Runs basic tests**
   - Backend health check
   - Frontend accessibility check
   - Returns test results

3. **Provides clear feedback**
   - Explains why fallback was used
   - Shows application URLs
   - Confirms browser opened successfully

---

## 🔍 Auto-Fix Results

When auto-fix is triggered, you'll see:

```
ℹ️  **AUTO-FIX APPLIED**
   Reason: Running in asyncio context - Playwright Sync API not available
   Solution: Opened application in your default browser

✅ Application is running and accessible!
🌐 Frontend: http://localhost:3000
🔧 Backend: http://localhost:8000

📊 Basic Test Results: 2/2 passed

✅ Open frontend in browser
✅ Backend health check

💡 The application opened successfully in your browser!
   You can now manually test the application.
```

---

## 💡 When Auto-Fix Activates

### Scenario 1: FastMCP Context
```python
# FastMCP runs tools in asyncio event loop
@mcp.tool()
def test_application_e2e(...):
    # This runs in asyncio loop automatically
    result = launch_and_test(...)  # Auto-fix activates! ✅
    return result
```

### Scenario 2: Jupyter Notebook
```python
# Jupyter uses asyncio event loop
await some_async_function()

# Later...
result = run_interactive_tests(...)  # Auto-fix activates! ✅
```

### Scenario 3: Async Web Frameworks
```python
# FastAPI, Quart, etc. use asyncio
@app.get("/test")
async def test_endpoint():
    result = run_interactive_tests(...)  # Auto-fix activates! ✅
    return result
```

### Scenario 4: Missing Playwright
```bash
# Playwright not installed or browsers not downloaded
$ python -c "from docker_tools.e2e_tester import run_interactive_tests"
# Auto-fix activates! ✅ Opens system browser
```

---

## 🚀 How to Use

### Option 1: Let Auto-Fix Handle Everything (Recommended)

```python
# Just call the function - auto-fix will handle issues automatically
result = launch_and_test(
    project_root="C:\\MyApp",
    backend_port=8000,
    frontend_port=3000
)

# If Playwright Sync API fails → Opens in default browser ✅
# If Playwright not installed → Opens in default browser ✅
# If any error occurs → Tries to open in default browser ✅
```

### Option 2: Force System Browser (Skip Playwright Entirely)

```python
# Use system browser from the start (no Playwright needed)
result = launch_and_test(
    project_root="C:\\MyApp",
    use_system_browser=True  # Forces system browser
)
```

### Option 3: Direct Fallback Function

```python
# Call the fallback function directly
from docker_tools.e2e_tester import _run_tests_with_system_browser

result = _run_tests_with_system_browser(
    project_root="C:\\MyApp",
    frontend_url="http://localhost:3000",
    backend_url="http://localhost:8000"
)
```

---

## 🐛 Troubleshooting

### Issue: "Browser didn't open"

**Solution:**
- Check if you have a default browser set
- Try opening the URL manually: `http://localhost:3000`
- On Linux, ensure `xdg-open` is available
- On macOS, ensure `open` command works
- On Windows, check default browser settings

### Issue: "Backend health check failed"

**Solution:**
- This is normal if your backend doesn't have a `/health` endpoint
- The auto-fix will mark it as "warning" not "failed"
- Your frontend still opens successfully
- Manually test by visiting the backend URL

### Issue: "Want full Playwright tests, not fallback"

**Solution:**
Install Playwright properly:
```bash
# Install Playwright
pip install playwright

# Download browser binaries
playwright install

# Verify installation
playwright --version
```

Then tests will use full Playwright instead of fallback.

---

## 📈 Auto-Fix Success Metrics

The auto-fix system tracks:

- ✅ **Total activations**: How many times auto-fix was triggered
- ✅ **Success rate**: % of times application opened successfully
- ✅ **Error types**: Which errors were caught and fixed
- ✅ **Fallback reasons**: Why fallback was needed

Results include:
```json
{
  "status": "success",
  "fallback": true,
  "reason": "Running in asyncio context",
  "tests": [...],
  "passed": 2,
  "failed": 0,
  "total": 2
}
```

---

## 🎓 Technical Details

### Asyncio Detection

```python
import asyncio

def check_asyncio_loop():
    try:
        loop = asyncio.get_running_loop()
        return True  # We're in an asyncio loop
    except RuntimeError:
        return False  # No asyncio loop running
```

### Error Pattern Matching

```python
def detect_error_type(error_message: str):
    error_msg = error_message.lower()
    
    if "asyncio" in error_msg or "event loop" in error_msg:
        return "ASYNCIO_CONFLICT"
    elif "playwright" in error_msg and "not found" in error_msg:
        return "PLAYWRIGHT_NOT_INSTALLED"
    elif "executable" in error_msg and "doesn't exist" in error_msg:
        return "BROWSER_BINARY_MISSING"
    else:
        return "UNKNOWN_ERROR"
```

### Fallback Priority

1. **Playwright with interactions** (preferred)
2. **Playwright basic tests** (if interactions fail)
3. **System browser + basic tests** (if Playwright unavailable)
4. **System browser only** (if tests fail)
5. **Error message** (if everything fails)

---

## 🔮 Future Enhancements

Planned auto-fix features:

1. **Async API Auto-Switch**: Automatically use Playwright Async API when in asyncio loop
2. **Headless Fallback**: If headed mode fails, auto-switch to headless
3. **Port Conflict Resolution**: Auto-detect and suggest alternative ports
4. **Docker Auto-Start**: If containers not running, start them automatically
5. **Service Health Monitoring**: Auto-retry failed health checks with backoff

---

## 📚 Related Documentation

- [E2E Testing Guide](./E2E_TESTING_GUIDE.md) - Complete testing guide
- [Workflow Guide](./WORKFLOW_GUIDE.md) - Full dockerization workflow
- [Quick Start Testing](./QUICK_START_TESTING.md) - Get started quickly

---

## ✅ Summary

**The auto-fix system ensures your application always opens and is testable, even when:**
- Running in asyncio event loops (FastMCP, Jupyter, async web frameworks)
- Playwright is not installed or configured
- Browser binaries are missing
- Unexpected errors occur

**You don't need to:**
- Manually check for asyncio loops
- Install Playwright if you just want to see your app
- Write error handling code
- Debug Playwright installation issues

**Just call the function and it works!** 🎉
