import subprocess
import os
import time
import logging
import json

logger = logging.getLogger(__name__)


def start_docker_compose(project_root: str, detached: bool = True) -> dict:
    """
    Start docker-compose stack.
    
    Args:
        project_root: Root directory containing docker-compose.yml
        detached: Run in detached mode (default: True)
        
    Returns:
        Dictionary with status and output
    """
    try:
        cmd = ["docker-compose", "up", "--build"]
        if detached:
            cmd.append("-d")
        
        logger.info(f"Starting docker-compose in {project_root}")
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            encoding='utf-8',
            errors='replace',
            timeout=300
        )
        
        if result.returncode == 0:
            return {
                "status": "success",
                "message": "Docker Compose started successfully",
                "output": result.stdout
            }
        else:
            return {
                "status": "error",
                "message": "Failed to start Docker Compose",
                "error": result.stderr
            }
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "message": "Docker Compose startup timeout (5 minutes)"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error starting Docker Compose: {str(e)}"
        }


def stop_docker_compose(project_root: str) -> dict:
    """
    Stop and remove docker-compose stack.
    
    Args:
        project_root: Root directory containing docker-compose.yml
        
    Returns:
        Dictionary with status and output
    """
    try:
        logger.info(f"Stopping docker-compose in {project_root}")
        result = subprocess.run(
            ["docker-compose", "down"],
            cwd=project_root,
            capture_output=True,
            encoding='utf-8',
            errors='replace',
            timeout=60
        )
        
        return {
            "status": "success" if result.returncode == 0 else "error",
            "output": result.stdout if result.returncode == 0 else result.stderr
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error stopping Docker Compose: {str(e)}"
        }


def wait_for_services(host: str = "localhost", backend_port: int = 8000, 
                      frontend_port: int = 3000, timeout: int = 60) -> dict:
    """
    Wait for services to be ready by checking if ports are responding.
    
    Args:
        host: Host to check (default: localhost)
        backend_port: Backend port to check
        frontend_port: Frontend port to check
        timeout: Maximum time to wait in seconds
        
    Returns:
        Dictionary with status
    """
    import socket
    
    start_time = time.time()
    services_ready = {"backend": False, "frontend": False}
    
    while time.time() - start_time < timeout:
        # Check backend
        if not services_ready["backend"]:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((host, backend_port))
                sock.close()
                if result == 0:
                    services_ready["backend"] = True
                    logger.info(f"Backend is ready on port {backend_port}")
            except:
                pass
        
        # Check frontend
        if not services_ready["frontend"]:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((host, frontend_port))
                sock.close()
                if result == 0:
                    services_ready["frontend"] = True
                    logger.info(f"Frontend is ready on port {frontend_port}")
            except:
                pass
        
        # If both ready, return success
        if services_ready["backend"] and services_ready["frontend"]:
            return {
                "status": "success",
                "message": "All services are ready",
                "services": services_ready
            }
        
        time.sleep(2)
    
    return {
        "status": "partial" if any(services_ready.values()) else "error",
        "message": f"Services readiness timeout after {timeout}s",
        "services": services_ready
    }


def run_playwright_tests(test_path: str, project_root: str = None, 
                        browser: str = "chromium") -> dict:
    """
    Run Playwright tests.
    
    Args:
        test_path: Path to test file or directory
        project_root: Root directory for the tests (default: test_path parent)
        browser: Browser to use (chromium, firefox, webkit)
        
    Returns:
        Dictionary with test results
    """
    try:
        if project_root is None:
            project_root = os.path.dirname(test_path)
        
        # Check if playwright is installed
        check_cmd = ["npx", "playwright", "--version"]
        check_result = subprocess.run(
            check_cmd,
            cwd=project_root,
            capture_output=True,
            encoding='utf-8',
            errors='replace'
        )
        
        if check_result.returncode != 0:
            return {
                "status": "error",
                "message": "Playwright not installed. Run: npm install -D @playwright/test"
            }
        
        # Run tests
        logger.info(f"Running Playwright tests from {test_path}")
        cmd = ["npx", "playwright", "test", test_path, "--reporter=json"]
        
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            encoding='utf-8',
            errors='replace',
            timeout=300
        )
        
        # Parse results
        try:
            # Try to parse JSON output
            output_lines = result.stdout.split('\n')
            for line in output_lines:
                if line.strip().startswith('{'):
                    test_results = json.loads(line)
                    break
            else:
                test_results = {"raw_output": result.stdout}
        except:
            test_results = {"raw_output": result.stdout}
        
        return {
            "status": "success" if result.returncode == 0 else "failed",
            "exit_code": result.returncode,
            "results": test_results,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
        
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "message": "Playwright tests timeout (5 minutes)"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error running Playwright tests: {str(e)}"
        }


def run_python_playwright_tests(test_path: str, browser: str = "chromium") -> dict:
    """
    Run Playwright tests using Python.
    
    Args:
        test_path: Path to Python test file
        browser: Browser to use
        
    Returns:
        Dictionary with test results
    """
    try:
        logger.info(f"Running Python Playwright tests from {test_path}")
        cmd = ["python", "-m", "pytest", test_path, "-v", "--tb=short"]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            encoding='utf-8',
            errors='replace',
            timeout=300
        )
        
        return {
            "status": "success" if result.returncode == 0 else "failed",
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
        
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "message": "Python Playwright tests timeout (5 minutes)"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error running Python Playwright tests: {str(e)}"
        }


def generate_playwright_test_template(project_root: str, backend_url: str = "http://localhost:8000",
                                      frontend_url: str = "http://localhost:3000") -> str:
    """
    Generate a sample Playwright test file.
    
    Args:
        project_root: Root directory of the project
        backend_url: URL of the backend service
        frontend_url: URL of the frontend service
        
    Returns:
        Path to the generated test file
    """
    test_dir = os.path.join(project_root, "e2e-tests")
    os.makedirs(test_dir, exist_ok=True)
    
    # Create package.json if it doesn't exist
    package_json_path = os.path.join(test_dir, "package.json")
    if not os.path.exists(package_json_path):
        package_json = {
            "name": "e2e-tests",
            "version": "1.0.0",
            "devDependencies": {
                "@playwright/test": "^1.40.0"
            },
            "scripts": {
                "test": "playwright test",
                "test:headed": "playwright test --headed",
                "test:ui": "playwright test --ui"
            }
        }
        with open(package_json_path, 'w') as f:
            json.dump(package_json, f, indent=2)
    
    # Create playwright.config.js
    config_path = os.path.join(test_dir, "playwright.config.js")
    config_content = f"""import {{ defineConfig, devices }} from '@playwright/test';

export default defineConfig({{
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {{
    baseURL: '{frontend_url}',
    trace: 'on-first-retry',
  }},
  projects: [
    {{
      name: 'chromium',
      use: {{ ...devices['Desktop Chrome'] }},
    }},
  ],
  webServer: {{
    command: 'docker-compose up',
    url: '{frontend_url}',
    reuseExistingServer: !process.env.CI,
  }},
}});
"""
    with open(config_path, 'w') as f:
        f.write(config_content)
    
    # Create test file
    tests_dir = os.path.join(test_dir, "tests")
    os.makedirs(tests_dir, exist_ok=True)
    
    test_file_path = os.path.join(tests_dir, "app.spec.js")
    test_content = f"""import {{ test, expect }} from '@playwright/test';

const BACKEND_URL = '{backend_url}';
const FRONTEND_URL = '{frontend_url}';

test.describe('Application E2E Tests', () => {{
  
  test('Backend health check', async ({{ request }}) => {{
    const response = await request.get(`${{BACKEND_URL}}/health`);
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.status).toBe('healthy');
  }});

  test('Frontend loads successfully', async ({{ page }}) => {{
    await page.goto(FRONTEND_URL);
    await expect(page).toHaveTitle(/.*/, {{ timeout: 10000 }});
  }});

  test('Frontend can communicate with backend', async ({{ page }}) => {{
    await page.goto(FRONTEND_URL);
    
    // Wait for page to load
    await page.waitForLoadState('networkidle');
    
    // Check if API data is displayed
    const hasContent = await page.locator('body').textContent();
    expect(hasContent).toBeTruthy();
  }});

  test('API endpoints are accessible', async ({{ request }}) => {{
    // Test main API endpoint
    const response = await request.get(`${{BACKEND_URL}}/api/items`);
    expect(response.ok()).toBeTruthy();
  }});

  test('Complete user flow', async ({{ page }}) => {{
    await page.goto(FRONTEND_URL);
    
    // Add your specific user flow tests here
    // Example: Click button, fill form, submit, check results
    
    await page.waitForTimeout(1000);
  }});
}});
"""
    with open(test_file_path, 'w') as f:
        f.write(test_content)
    
    return test_dir


def launch_browser(url: str, browser: str = "chromium", headless: bool = False) -> dict:
    """
    Launch a browser and navigate to URL using Playwright.
    
    Args:
        url: URL to open
        browser: Browser type (chromium, firefox, webkit)
        headless: Run in headless mode
        
    Returns:
        Dictionary with status
    """
    try:
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            # Launch browser
            if browser == "firefox":
                browser_instance = p.firefox.launch(headless=headless)
            elif browser == "webkit":
                browser_instance = p.webkit.launch(headless=headless)
            else:
                browser_instance = p.chromium.launch(headless=headless)
            
            context = browser_instance.new_context()
            page = context.new_page()
            
            # Navigate to URL
            logger.info(f"Opening {url} in {browser}")
            page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Take screenshot
            screenshot_path = os.path.join(os.getcwd(), "app_screenshot.png")
            page.screenshot(path=screenshot_path)
            
            # Keep browser open for manual inspection (5 seconds)
            if not headless:
                logger.info("Browser launched. Keeping open for inspection...")
                page.wait_for_timeout(5000)
            
            # Get page info
            title = page.title()
            url_final = page.url
            
            browser_instance.close()
            
            return {
                "status": "success",
                "title": title,
                "url": url_final,
                "screenshot": screenshot_path
            }
    except ImportError:
        return {
            "status": "error",
            "message": "Playwright not installed. Run: pip install playwright && playwright install"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error launching browser: {str(e)}"
        }


def run_interactive_tests(project_root: str, frontend_url: str = "http://localhost:3000",
                         backend_url: str = "http://localhost:8000", headless: bool = False) -> dict:
    """
    Run interactive Playwright tests with visible browser.
    
    Args:
        project_root: Root directory of the project
        frontend_url: Frontend URL
        backend_url: Backend URL
        headless: Run in headless mode
        
    Returns:
        Dictionary with test results
    """
    try:
        from playwright.sync_api import sync_playwright, expect
        
        results = {
            "tests": [],
            "passed": 0,
            "failed": 0,
            "total": 0
        }
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            context = browser.new_context()
            page = context.new_page()
            
            # Test 1: Backend health check
            results["total"] += 1
            try:
                response = page.request.get(f"{backend_url}/health")
                if response.ok:
                    results["tests"].append({"name": "Backend health check", "status": "passed"})
                    results["passed"] += 1
                else:
                    results["tests"].append({"name": "Backend health check", "status": "failed", "error": f"Status {response.status}"})
                    results["failed"] += 1
            except Exception as e:
                results["tests"].append({"name": "Backend health check", "status": "failed", "error": str(e)})
                results["failed"] += 1
            
            # Test 2: Frontend loads
            results["total"] += 1
            try:
                logger.info(f"Loading frontend at {frontend_url}")
                page.goto(frontend_url, wait_until="networkidle", timeout=30000)
                title = page.title()
                results["tests"].append({"name": "Frontend loads successfully", "status": "passed", "title": title})
                results["passed"] += 1
                
                # Take screenshot
                screenshot_path = os.path.join(project_root, "frontend_screenshot.png")
                page.screenshot(path=screenshot_path, full_page=True)
                results["screenshot"] = screenshot_path
                
                # Keep browser open for inspection if not headless
                if not headless:
                    logger.info("Application running in browser. Keeping open for 10 seconds...")
                    page.wait_for_timeout(10000)
                
            except Exception as e:
                results["tests"].append({"name": "Frontend loads successfully", "status": "failed", "error": str(e)})
                results["failed"] += 1
            
            # Test 3: Check for API calls
            results["total"] += 1
            try:
                # Listen for network requests
                api_calls = []
                page.on("request", lambda request: api_calls.append(request.url) if backend_url in request.url else None)
                
                page.reload(wait_until="networkidle")
                page.wait_for_timeout(2000)
                
                if api_calls:
                    results["tests"].append({"name": "Frontend-Backend communication", "status": "passed", "api_calls": len(api_calls)})
                    results["passed"] += 1
                else:
                    results["tests"].append({"name": "Frontend-Backend communication", "status": "warning", "note": "No API calls detected"})
            except Exception as e:
                results["tests"].append({"name": "Frontend-Backend communication", "status": "failed", "error": str(e)})
                results["failed"] += 1
            
            browser.close()
        
        results["status"] = "success" if results["failed"] == 0 else "partial"
        return results
        
    except ImportError:
        return {
            "status": "error",
            "message": "Playwright not installed. Run: pip install playwright && playwright install"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error running interactive tests: {str(e)}"
        }


def launch_and_test(project_root: str, backend_port: int = 8000, 
                   frontend_port: int = 3000, cleanup: bool = True,
                   headless: bool = False, show_browser: bool = True) -> str:
    """
    Complete workflow: Start docker-compose, wait for services, launch browser, run tests, cleanup.
    
    Args:
        project_root: Root directory with docker-compose.yml
        backend_port: Backend service port
        frontend_port: Frontend service port
        cleanup: Whether to stop docker-compose after tests
        headless: Run browser in headless mode
        show_browser: Launch browser to show the running application
        
    Returns:
        Formatted test report
    """
    report = f"🧪 **End-to-End Testing Report**\n\n"
    report += f"**Project:** {project_root}\n\n"
    
    # Step 1: Start docker-compose
    report += "**Step 1: Starting Docker Compose...**\n"
    start_result = start_docker_compose(project_root, detached=True)
    
    if start_result["status"] != "success":
        report += f"❌ Failed to start services\n{start_result.get('error', start_result.get('message'))}\n"
        return report
    
    report += "✅ Services started\n\n"
    
    # Step 2: Wait for services
    report += "**Step 2: Waiting for services to be ready...**\n"
    wait_result = wait_for_services("localhost", backend_port, frontend_port, timeout=60)
    
    if wait_result["status"] == "error":
        report += f"❌ Services not ready: {wait_result['message']}\n"
        if cleanup:
            stop_docker_compose(project_root)
        return report
    
    report += f"✅ Services ready: {wait_result['services']}\n\n"
    
    # Step 3: Launch browser and show application
    if show_browser:
        report += "**Step 3: Launching application in browser...**\n"
        frontend_url = f"http://localhost:{frontend_port}"
        backend_url = f"http://localhost:{backend_port}"
        
        try:
            # Run interactive tests with browser
            interactive_results = run_interactive_tests(
                project_root,
                frontend_url,
                backend_url,
                headless=headless
            )
            
            if interactive_results["status"] == "error":
                report += f"❌ {interactive_results['message']}\n"
            else:
                report += f"🌐 Application launched at: {frontend_url}\n"
                report += f"📊 Tests completed: {interactive_results['passed']}/{interactive_results['total']} passed\n\n"
                
                for test in interactive_results.get("tests", []):
                    status_icon = "✅" if test["status"] == "passed" else "❌" if test["status"] == "failed" else "⚠️"
                    report += f"{status_icon} {test['name']}\n"
                    if "error" in test:
                        report += f"   Error: {test['error']}\n"
                    if "title" in test:
                        report += f"   Page title: {test['title']}\n"
                    if "api_calls" in test:
                        report += f"   API calls made: {test['api_calls']}\n"
                
                if "screenshot" in interactive_results:
                    report += f"\n📸 Screenshot saved: {interactive_results['screenshot']}\n"
        
        except Exception as e:
            report += f"❌ Error launching browser: {str(e)}\n"
    
    # Step 4: Check for additional test files
    report += "\n**Step 4: Running additional tests...**\n"
    test_dir = os.path.join(project_root, "e2e-tests")
    
    if not os.path.exists(test_dir):
        report += "⚠️  No e2e-tests directory found. Generating test template...\n"
        generate_playwright_test_template(
            project_root,
            f"http://localhost:{backend_port}",
            f"http://localhost:{frontend_port}"
        )
        report += f"✅ Test template created at: {test_dir}\n"
        report += "📝 Run 'npm install' in e2e-tests directory, then run tests again.\n\n"
    else:
        # Run Playwright tests
        test_path = os.path.join(test_dir, "tests")
        if os.path.exists(test_path):
            test_result = run_playwright_tests(test_path, test_dir)
            
            if test_result["status"] == "success":
                report += "✅ All tests passed!\n"
                report += f"\n**Test Output:**\n```\n{test_result['stdout']}\n```\n"
            else:
                report += f"❌ Tests failed (exit code: {test_result.get('exit_code')})\n"
                report += f"\n**Test Output:**\n```\n{test_result.get('stdout', '')}\n```\n"
                if test_result.get('stderr'):
                    report += f"\n**Errors:**\n```\n{test_result['stderr']}\n```\n"
        else:
            report += f"⚠️  No tests found in {test_path}\n"
    
    # Step 5: Cleanup
    if cleanup:
        report += "\n**Step 5: Cleaning up...**\n"
        stop_result = stop_docker_compose(project_root)
        report += "✅ Services stopped\n" if stop_result["status"] == "success" else "⚠️  Cleanup warning\n"
    else:
        report += "\n**Services still running** (cleanup=False)\n"
    
    report += "\n**Test run complete!** 🎉\n"
    return report
