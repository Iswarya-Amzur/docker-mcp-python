# Direct Playwright Integration

## Overview
This Docker MCP uses **direct Playwright Python library** for all browser automation testing. There are no wrappers, no MCP capability layers, just pure Playwright integration.

## What is Playwright?
Playwright is a powerful browser automation library that enables:
- Cross-browser testing (Chromium, Firefox, WebKit)
- Real browser interactions (clicks, forms, navigation)
- Screenshot and video capture
- Network interception
- Mobile emulation

## Our Integration

### Direct Library Usage
```python
from playwright.async_api import async_playwright

async def run_tests():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Direct Playwright API calls
        await page.goto('http://localhost:3000')
        await page.click('button.submit')
        await page.fill('input[name="task"]', 'Test Task')
        
        # Capture screenshot
        screenshot = await page.screenshot(full_page=True)
        
        await browser.close()
```

### Key Features

#### 1. Async API Integration
- Uses `playwright.async_api` for seamless asyncio integration
- Works natively with FastMCP's event loop
- No blocking operations

#### 2. Real Browser Automation
```python
# Button clicks
await button.click(timeout=5000)

# Form filling
await input_field.fill("Test data")

# Navigation
await page.goto(url, wait_until="networkidle")
await link.click()
await page.go_back()

# Element interactions
await element.hover()
await element.scroll_into_view_if_needed()
```

#### 3. Screenshot Capture
```python
# Capture as PNG bytes
screenshot_bytes = await page.screenshot(full_page=True, type='png')

# Convert to base64 for chat display
base64_image = base64.b64encode(screenshot_bytes).decode('utf-8')
data_url = f"data:image/png;base64,{base64_image}"
```

#### 4. Network Monitoring
```python
# Track API calls
api_calls = []
page.on("request", lambda req: api_calls.append(req.url))

# Check if frontend communicates with backend
await page.reload(wait_until="networkidle")
if api_calls:
    print(f"Detected {len(api_calls)} API calls")
```

## Test Automation Features

### 8 Automated Test Types

1. **Backend Health Check**
   ```python
   response = await page.request.get(f"{backend_url}/health")
   assert response.ok
   ```

2. **Frontend Load Test**
   ```python
   await page.goto(frontend_url, wait_until="networkidle")
   title = await page.title()
   ```

3. **API Communication**
   ```python
   page.on("request", lambda req: track_api_call(req))
   await page.reload()
   ```

4. **Button Interactions**
   ```python
   buttons = await page.locator("button").all()
   for button in buttons:
       await button.click()
   ```

5. **Input Field Interactions**
   ```python
   inputs = await page.locator("input[type='text']").all()
   for input_field in inputs:
       await input_field.fill("Test data")
   ```

6. **Item Creation (CRUD)**
   ```python
   await page.fill("input[placeholder*='task']", "New Task")
   await page.click("button:has-text('Add')")
   ```

7. **Navigation Testing**
   ```python
   links = await page.locator("a[href]").all()
   for link in links:
       await link.click()
       await page.go_back()
   ```

8. **Form Submission**
   ```python
   forms = await page.locator("form").all()
   for form in forms:
       await form.locator("input").fill("Test")
       await form.locator("button[type='submit']").click()
   ```

## Browser Configuration

### Visible Browser Mode (Default)
```python
browser = await p.chromium.launch(
    headless=False,        # Visible window
    slow_mo=500,          # 500ms delay between actions (visible)
    args=['--start-maximized']  # Full screen
)

context = await browser.new_context(
    viewport={"width": 1920, "height": 1080},
    no_viewport=True  # Use full window size
)
```

### Headless Mode (CI/CD)
```python
browser = await p.chromium.launch(
    headless=True,  # No visible window
    slow_mo=0       # Fast execution
)
```

## Installation

### Playwright Installation
```bash
pip install playwright
playwright install chromium
```

### Verify Installation
```python
from playwright.async_api import async_playwright

async def verify():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        print("✅ Playwright installed successfully!")
        await browser.close()
```

## Files Using Direct Playwright

### 1. `e2e_tester_async.py`
Main testing module using Playwright Async API:
- `run_interactive_tests_async()` - Main test runner
- `screenshot_to_base64()` - Screenshot capture
- All interaction test functions

### 2. `comprehensive_workflow_async.py`
Workflow orchestrator that calls E2E tester:
- `comprehensive_dockerize_and_test_async()` - Main workflow
- Integrates Playwright tests into full workflow

### 3. `comprehensive_workflow.py`
Sync version with Playwright fallback:
- `capture_screenshot()` - Screenshot utility
- `capture_screenshot_async()` - Async screenshot utility

### 4. `server.py`
MCP server with async tools:
- `test_application_e2e()` - Async tool using Playwright
- `dockerize_and_test()` - Async tool with E2E tests
- `capture_app_screenshot()` - Screenshot utility

## No MCP Wrappers

### What We DON'T Use
❌ Playwright MCP server  
❌ MCP capability layer  
❌ Playwright through external service  
❌ Any abstraction on top of Playwright  

### What We DO Use
✅ Direct `playwright` Python package  
✅ `playwright.async_api` module  
✅ Direct browser automation API  
✅ Native Playwright features  

## Benefits

### 1. Performance
- Direct API calls (no network overhead)
- Async operations (non-blocking)
- Native browser control

### 2. Features
- Full Playwright API access
- All browser capabilities
- Latest Playwright features

### 3. Reliability
- No dependency on external services
- Direct library control
- Predictable behavior

### 4. Simplicity
- One library to install
- Standard Python imports
- Clean async/await syntax

## Example Usage

### Basic Test
```python
result = await test_application_e2e(
    project_root="C:\\MyApp",
    backend_port=8000,
    frontend_port=3000,
    headless=False
)

# Result contains:
{
    "steps": [...],
    "tests": [...],
    "screenshots": {
        "initial": "data:image/png;base64,...",
        "after": "data:image/png;base64,..."
    },
    "test_summary": {
        "passed": 8,
        "failed": 0,
        "total": 8
    }
}
```

### Complete Workflow
```python
result = await dockerize_and_test(
    project_root="C:\\MyApp",
    test_e2e=True,
    auto_fix_errors=True
)

# Automatically:
# 1. Dockerizes app
# 2. Starts containers
# 3. Runs Playwright tests
# 4. Returns base64 screenshots
```

## Debugging

### Enable Playwright Debug Logs
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Playwright Inspector
```python
browser = await p.chromium.launch(
    headless=False,
    slow_mo=1000  # Slow down for inspection
)
```

### Keep Browser Open
```python
# Tests keep browser open for 15 seconds
await page.wait_for_timeout(15000)
```

## Comparison: Direct vs MCP Wrapper

| Feature | Direct Playwright | Playwright MCP |
|---------|------------------|----------------|
| Installation | `pip install playwright` | MCP server setup |
| Import | `from playwright.async_api import ...` | MCP client calls |
| Performance | Direct (fast) | Network overhead |
| Features | All Playwright features | Limited by MCP |
| Debugging | Native tools | Through MCP layer |
| Complexity | Simple | Additional layer |

## Conclusion

Our Docker MCP uses **direct Playwright Python library** for all browser automation. This provides:

✅ Full Playwright feature set  
✅ Maximum performance  
✅ Clean async integration  
✅ No external dependencies  
✅ Simple, maintainable code  

No wrappers. No MCP layers. Just pure Playwright.
