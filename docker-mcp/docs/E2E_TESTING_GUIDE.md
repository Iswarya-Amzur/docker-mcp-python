# End-to-End Testing with Docker MCP

## Overview
The Docker MCP now includes integrated Playwright testing to automatically test your dockerized applications end-to-end!

## New Tools Added

### 1. `test_application_e2e` - Complete E2E Test Runner
**What it does:**
- Starts your docker-compose stack
- Waits for all services to be ready
- Runs Playwright tests
- Reports results
- Cleans up services

**Usage:**
```python
test_application_e2e(
    project_root="C:\\Users\\YourName\\MyProject",
    backend_port=8000,      # optional
    frontend_port=3000,     # optional
    cleanup=True            # optional
)
```

**Output:**
- Complete test report with pass/fail status
- Service startup logs
- Test execution results
- Cleanup confirmation

---

### 2. `create_playwright_tests` - Test Template Generator
**What it does:**
- Creates `e2e-tests` directory
- Generates `package.json` with Playwright
- Creates `playwright.config.js`
- Generates sample test file with common scenarios

**Usage:**
```python
create_playwright_tests(
    project_root="C:\\Users\\YourName\\MyProject",
    backend_url="http://localhost:8000",   # optional
    frontend_url="http://localhost:3000"   # optional
)
```

**Generated Files:**
```
MyProject/
└── e2e-tests/
    ├── package.json
    ├── playwright.config.js
    └── tests/
        └── app.spec.js
```

**Sample Tests Included:**
- Backend health check
- Frontend loads successfully
- Frontend-Backend communication
- API endpoint accessibility
- Complete user flow template

---

### 3. `start_services` - Start Docker Compose
**What it does:**
- Starts docker-compose in detached mode
- Builds images if needed
- Returns startup status

**Usage:**
```python
start_services(
    project_root="C:\\Users\\YourName\\MyProject",
    detached=True  # optional
)
```

---

### 4. `stop_services` - Stop Docker Compose
**What it does:**
- Stops all containers
- Removes containers and networks
- Returns cleanup status

**Usage:**
```python
stop_services(project_root="C:\\Users\\YourName\\MyProject")
```

---

## Complete Workflow Example

### Step 1: Dockerize Your Project
```python
dockerize_project(project_root="C:\\Users\\YourName\\MyProject")
```

### Step 2: Generate Test Templates
```python
create_playwright_tests(project_root="C:\\Users\\YourName\\MyProject")
```

### Step 3: Install Playwright (One Time)
```bash
cd MyProject/e2e-tests
npm install
npx playwright install
```

### Step 4: Customize Tests
Edit `e2e-tests/tests/app.spec.js` to add your specific test scenarios.

### Step 5: Run E2E Tests
```python
test_application_e2e(project_root="C:\\Users\\YourName\\MyProject")
```

---

## Test Report Example

```
🧪 **End-to-End Testing Report**

**Project:** C:\Users\YourName\MyProject

**Step 1: Starting Docker Compose...**
✅ Services started

**Step 2: Waiting for services to be ready...**
✅ Services ready: {'backend': True, 'frontend': True}

**Step 3: Running tests...**
✅ All tests passed!

**Test Output:**
```
Running 5 tests using 1 worker
✓ Backend health check (1.2s)
✓ Frontend loads successfully (2.3s)
✓ Frontend can communicate with backend (1.8s)
✓ API endpoints are accessible (0.9s)
✓ Complete user flow (3.1s)

5 passed (9.3s)
```

**Step 4: Cleaning up...**
✅ Services stopped

**Test run complete!** 🎉
```

---

## Advanced Usage

### Run Tests Without Cleanup
Keep services running for debugging:
```python
test_application_e2e(
    project_root="C:\\Users\\YourName\\MyProject",
    cleanup=False
)
```

### Custom Ports
Test applications on non-standard ports:
```python
test_application_e2e(
    project_root="C:\\Users\\YourName\\MyProject",
    backend_port=5000,
    frontend_port=8080
)
```

### Manual Control
Start and stop services independently:
```python
# Start
start_services(project_root="C:\\Users\\YourName\\MyProject")

# Do manual testing...

# Stop
stop_services(project_root="C:\\Users\\YourName\\MyProject")
```

---

## Playwright Test Features

### Included Test Scenarios
1. **Backend Health Check** - Verifies backend is running
2. **Frontend Load Test** - Ensures frontend renders
3. **API Integration Test** - Tests frontend-backend communication
4. **Endpoint Validation** - Checks all API endpoints
5. **User Flow Template** - Customize for your app's workflows

### Test Configuration
Edit `playwright.config.js` to customize:
- Browsers (Chromium, Firefox, WebKit)
- Timeouts
- Retries
- Screenshots/Videos
- Trace recording

### Writing Custom Tests
```javascript
test('My custom test', async ({ page }) => {
  await page.goto('http://localhost:3000');
  
  // Your test logic
  await page.click('#my-button');
  await expect(page.locator('#result')).toHaveText('Success');
});
```

---

## Troubleshooting

### Tests Fail - Services Not Ready
Increase wait timeout:
- Edit `e2e_tester.py` line with `wait_for_services(..., timeout=120)`

### Playwright Not Installed
```bash
cd e2e-tests
npm install
npx playwright install
```

### Port Already in Use
```bash
# Stop any running containers
docker-compose down
# Or change ports in docker-compose.yml
```

### Tests Pass Locally But Fail in MCP
- Ensure services have time to start
- Check service health endpoints
- Verify network connectivity between services

---

## Integration with CI/CD

You can use these tools in CI/CD pipelines:

```yaml
# GitHub Actions example
- name: Run E2E Tests
  run: |
    python -c "from docker_tools.e2e_tester import launch_and_test; launch_and_test('.')"
```

---

## Benefits

✅ **Automated Testing** - No manual steps, just run one command  
✅ **Complete Coverage** - Tests entire stack (backend + frontend)  
✅ **Real Environment** - Tests against actual Docker containers  
✅ **CI/CD Ready** - Easy integration with pipelines  
✅ **Developer Friendly** - Clear reports and error messages  
✅ **Customizable** - Extend tests for your specific needs  

---

## Next Steps

1. **Restart your MCP server** to load the new tools
2. **Dockerize your project** using `dockerize_project`
3. **Generate tests** using `create_playwright_tests`
4. **Install Playwright** in the e2e-tests directory
5. **Run E2E tests** using `test_application_e2e`
6. **Iterate** - Customize tests and re-run as needed

Happy Testing! 🎉
