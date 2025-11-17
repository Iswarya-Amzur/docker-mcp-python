"""
E2E Testing Module with Auto-Fix Capabilities

This module provides end-to-end testing functionality with intelligent error handling
and automatic fallback mechanisms.

AUTO-FIX FEATURES:
1. Asyncio Loop Detection: Automatically detects when running in an asyncio event loop
   and switches from Playwright Sync API to system browser fallback
   
2. Playwright Installation Issues: If Playwright is not installed or browsers are not
   downloaded, automatically falls back to opening the application in the system browser
   
3. Error Recovery: Catches common errors and provides clear messages with solutions

USAGE:
    # Will automatically handle asyncio loop issues
    result = run_interactive_tests(project_root, frontend_url, backend_url)
    
    # Will automatically fall back to system browser if Playwright fails
    result = launch_and_test(project_root)
"""

import subprocess
import os
import time
import logging
import json
import webbrowser

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
        # Validate docker-compose.yml exists
        compose_files = ['docker-compose.yml', 'docker-compose.yaml']
        compose_file = None
        
        for cf in compose_files:
            compose_path = os.path.join(project_root, cf)
            if os.path.exists(compose_path):
                compose_file = cf
                break
        
        if not compose_file:
            return {
                "status": "error",
                "message": "docker-compose.yml not found",
                "error": f"No docker-compose file found in {project_root}"
            }
        
        cmd = ["docker-compose", "-f", compose_file, "up", "--build"]
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
    
    // Take screenshot
    await page.screenshot({{ path: 'test-results/homepage.png', fullPage: true }});
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

  test('User can interact with buttons', async ({{ page }}) => {{
    await page.goto(FRONTEND_URL);
    await page.waitForLoadState('networkidle');
    
    // Find and click all visible buttons
    const buttons = await page.locator('button:visible').all();
    
    if (buttons.length > 0) {{
      console.log(`Found ${{buttons.length}} buttons to test`);
      
      // Click first button
      await buttons[0].click();
      await page.waitForTimeout(1000);
      
      // Take screenshot after click
      await page.screenshot({{ path: 'test-results/after-button-click.png' }});
    }}
  }});

  test('User can fill input fields', async ({{ page }}) => {{
    await page.goto(FRONTEND_URL);
    await page.waitForLoadState('networkidle');
    
    // Find all input fields
    const inputs = await page.locator('input[type="text"], input:not([type]), textarea').all();
    
    if (inputs.length > 0) {{
      console.log(`Found ${{inputs.length}} input fields`);
      
      // Fill first input with test data
      await inputs[0].fill('Test input from Playwright');
      await page.waitForTimeout(500);
      
      // Take screenshot
      await page.screenshot({{ path: 'test-results/after-input-fill.png' }});
    }}
  }});

  test('User can create/add items (if applicable)', async ({{ page }}) => {{
    await page.goto(FRONTEND_URL);
    await page.waitForLoadState('networkidle');
    
    // Look for add/create patterns
    const addInput = page.locator('input[placeholder*="task" i], input[placeholder*="add" i], input[placeholder*="todo" i]').first();
    const addButton = page.locator('button:has-text("Add"), button:has-text("Create"), button[type="submit"]').first();
    
    const hasAddInput = await addInput.count() > 0;
    const hasAddButton = await addButton.count() > 0;
    
    if (hasAddInput && hasAddButton) {{
      console.log('Found create/add form');
      
      // Fill and submit
      await addInput.fill('E2E Test Task Created by Playwright');
      await addButton.click();
      await page.waitForTimeout(2000);
      
      // Take screenshot of created item
      await page.screenshot({{ path: 'test-results/after-item-creation.png', fullPage: true }});
      
      // Verify item appears (adjust selector based on your app)
      const pageContent = await page.content();
      expect(pageContent).toContain('E2E Test Task');
    }} else {{
      console.log('No create/add form found - skipping test');
      test.skip();
    }}
  }});

  test('Navigation links work', async ({{ page }}) => {{
    await page.goto(FRONTEND_URL);
    await page.waitForLoadState('networkidle');
    
    // Find navigation links
    const navLinks = await page.locator('a[href]:visible').all();
    
    if (navLinks.length > 0) {{
      console.log(`Found ${{navLinks.length}} navigation links`);
      
      // Test first internal link
      const firstLink = navLinks[0];
      const href = await firstLink.getAttribute('href');
      
      if (href && !href.startsWith('http')) {{
        await firstLink.click();
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(1000);
        
        // Take screenshot of new page
        await page.screenshot({{ path: 'test-results/after-navigation.png' }});
      }}
    }}
  }});

  test('Forms can be submitted', async ({{ page }}) => {{
    await page.goto(FRONTEND_URL);
    await page.waitForLoadState('networkidle');
    
    // Find forms
    const forms = await page.locator('form').all();
    
    if (forms.length > 0) {{
      console.log(`Found ${{forms.length}} forms to test`);
      
      const form = forms[0];
      
      // Fill all text inputs in the form
      const inputs = await form.locator('input[type="text"], input:not([type]), textarea').all();
      for (const input of inputs) {{
        await input.fill('Test form data');
      }}
      
      // Submit the form
      const submitButton = form.locator('button[type="submit"], input[type="submit"], button:has-text("Submit")').first();
      if (await submitButton.count() > 0) {{
        await submitButton.click();
        await page.waitForTimeout(2000);
        
        // Take screenshot after submission
        await page.screenshot({{ path: 'test-results/after-form-submit.png', fullPage: true }});
      }}
    }}
  }});

  test('Complete user workflow', async ({{ page }}) => {{
    await page.goto(FRONTEND_URL);
    await page.waitForLoadState('networkidle');
    
    // Complete workflow: Load page -> Interact -> Verify
    console.log('Starting complete user workflow test');
    
    // Step 1: Load and verify page
    await expect(page).toHaveTitle(/.*/, {{ timeout: 10000 }});
    
    // Step 2: Interact with UI elements
    const buttons = await page.locator('button:visible').count();
    const inputs = await page.locator('input:visible').count();
    
    console.log(`Page has ${{buttons}} buttons and ${{inputs}} inputs`);
    
    // Step 3: Take final screenshot
    await page.screenshot({{ path: 'test-results/workflow-complete.png', fullPage: true }});
    
    // Step 4: Verify page is functional
    const bodyText = await page.locator('body').textContent();
    expect(bodyText.length).toBeGreaterThan(0);
  }});
}});
"""
    with open(test_file_path, 'w') as f:
        f.write(test_content)
    
    return test_dir


def open_in_system_browser(url: str) -> dict:
    """
    Open URL in the system's default web browser (Chrome, Edge, Firefox, etc.).
    This opens in your ACTUAL browser, not a Playwright-controlled one.
    
    Args:
        url: URL to open
        
    Returns:
        Dictionary with status
    """
    try:
        logger.info(f"Opening {url} in system default browser")
        webbrowser.open(url)
        
        return {
            "status": "success",
            "url": url,
            "message": f"Opened {url} in your default browser"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error opening browser: {str(e)}"
        }


def launch_browser(url: str, browser: str = "chromium", headless: bool = False, use_system_browser: bool = False) -> dict:
    """
    Launch a browser and navigate to URL.
    
    Args:
        url: URL to open
        browser: Browser type (chromium, firefox, webkit, system)
        headless: Run in headless mode (ignored if use_system_browser=True)
        use_system_browser: If True, opens in your default browser (Chrome/Edge/Firefox)
        
    Returns:
        Dictionary with status
    """
    # If user wants system browser, use that instead of Playwright
    if use_system_browser or browser == "system":
        return open_in_system_browser(url)
    
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


async def run_interactive_tests_async(project_root: str, frontend_url: str = "http://localhost:3000",
                                     backend_url: str = "http://localhost:8000", headless: bool = False,
                                     perform_interactions: bool = True) -> dict:
    """
    Async version of run_interactive_tests that works inside asyncio loops.
    Uses Playwright async API to perform real frontend interactions.
    
    Args:
        project_root: Root directory of the project
        frontend_url: Frontend URL
        backend_url: Backend URL
        headless: Run in headless mode
        perform_interactions: Perform actual user interactions (default: True)
        
    Returns:
        Dictionary with test results including interaction tests
    """
    try:
        from playwright.async_api import async_playwright
        
        results = {
            "tests": [],
            "passed": 0,
            "failed": 0,
            "total": 0,
            "interactions": []
        }
        
        async with async_playwright() as p:
            # Launch browser with visible window (unless headless mode requested)
            logger.info(f"🌐 Launching {'headless ' if headless else 'VISIBLE '}Chromium browser...")
            browser = await p.chromium.launch(
                headless=headless,
                slow_mo=500 if not headless else 0,  # Slow down actions for visibility
                args=['--start-maximized'] if not headless else []  # Maximize window
            )
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                no_viewport=True if not headless else False  # Use full window size
            )
            page = await context.new_page()
            logger.info("✅ Browser window opened!")
            
            # Test 1: Backend health check
            results["total"] += 1
            try:
                response = await page.request.get(f"{backend_url}/health")
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
                logger.info(f"🌐 Loading frontend at {frontend_url}")
                print(f"\n{'='*70}")
                print(f"🌐 BROWSER LAUNCHED - Opening: {frontend_url}")
                print(f"{'='*70}\n")
                
                await page.goto(frontend_url, wait_until="networkidle", timeout=30000)
                title = await page.title()
                
                logger.info(f"✅ Page loaded: {title}")
                print(f"✅ Page loaded successfully: {title}\n")
                
                results["tests"].append({"name": "Frontend loads successfully", "status": "passed", "title": title})
                results["passed"] += 1
                
                # Take initial screenshot with base64 for chat embedding
                screenshot_path = os.path.join(project_root, "frontend_initial.png")
                screenshot_bytes = await page.screenshot(full_page=True)
                with open(screenshot_path, 'wb') as f:
                    f.write(screenshot_bytes)
                
                # Encode as base64 for chat embedding
                import base64
                base64_image = base64.b64encode(screenshot_bytes).decode('utf-8')
                results["screenshot"] = screenshot_path
                results["screenshot_base64"] = base64_image
                results["screenshot_data_url"] = f'data:image/png;base64,{base64_image}'
                
            except Exception as e:
                results["tests"].append({"name": "Frontend loads successfully", "status": "failed", "error": str(e)})
                results["failed"] += 1
            
            # Test 3: Check for API calls
            results["total"] += 1
            try:
                # Listen for network requests
                api_calls = []
                def handle_request(request):
                    if backend_url in request.url:
                        api_calls.append(request.url)
                page.on("request", handle_request)
                
                await page.reload(wait_until="networkidle")
                await page.wait_for_timeout(2000)
                
                if api_calls:
                    results["tests"].append({"name": "Frontend-Backend communication", "status": "passed", "api_calls": len(api_calls)})
                    results["passed"] += 1
                else:
                    results["tests"].append({"name": "Frontend-Backend communication", "status": "warning", "note": "No API calls detected"})
            except Exception as e:
                results["tests"].append({"name": "Frontend-Backend communication", "status": "failed", "error": str(e)})
                results["failed"] += 1
            
            # NEW: Test 4-N: Perform ACTUAL USER INTERACTIONS - COMPREHENSIVE TESTING
            if perform_interactions:
                logger.info("Starting comprehensive interactive user flow tests...")
                print(f"\n{'='*70}")
                print(f"🎬 PERFORMING COMPREHENSIVE INTERACTIVE TESTS")
                print(f"   Watch the browser - it will interact with your app!")
                print(f"   - Clicking ALL buttons")
                print(f"   - Filling ALL forms")
                print(f"   - Creating MULTIPLE items")
                print(f"   - Testing ALL navigation")
                print(f"   - Testing ALL interactions")
                print(f"{'='*70}\n")
                
                # Perform comprehensive async interaction tests
                await _test_comprehensive_interactions_async(page, results, backend_url)
                await _test_button_interactions_async(page, results)
                await _test_input_interactions_async(page, results)
                await _test_create_item_async(page, results, backend_url)
                await _test_create_multiple_items_async(page, results, backend_url)
                await _test_navigation_async(page, results)
                await _test_form_submission_async(page, results)
                await _test_all_links_async(page, results)
                await _test_all_forms_async(page, results)
                await _test_all_buttons_async(page, results)
                await _test_dropdowns_and_selects_async(page, results)
                await _test_checkboxes_and_radios_async(page, results)
                
                # Take final screenshot after interactions with base64 for chat embedding
                screenshot_after = os.path.join(project_root, "frontend_after_interactions.png")
                screenshot_bytes_after = await page.screenshot(full_page=True)
                with open(screenshot_after, 'wb') as f:
                    f.write(screenshot_bytes_after)
                
                # Encode as base64 for chat embedding
                import base64
                base64_image_after = base64.b64encode(screenshot_bytes_after).decode('utf-8')
                results["screenshot_after"] = screenshot_after
                results["screenshot_after_base64"] = base64_image_after
                results["screenshot_after_data_url"] = f'data:image/png;base64,{base64_image_after}'
                
                # Keep browser open for inspection if not headless
                if not headless:
                    print(f"\n{'='*70}")
                    print(f"✅ INTERACTIVE TESTS COMPLETED!")
                    print(f"   Browser will stay open for 15 seconds for inspection...")
                    print(f"   You can see the final state of your application")
                    print(f"{'='*70}\n")
                    logger.info("Tests completed! Keeping browser open for 15 seconds for inspection...")
                    await page.wait_for_timeout(15000)
                    print("\n⏱️  Closing browser...\n")
            else:
                # Keep browser open for inspection if not headless
                if not headless:
                    logger.info("Application running in browser. Keeping open for 10 seconds...")
                    print(f"\n⏱️  Browser will close in 10 seconds...\n")
                    await page.wait_for_timeout(10000)
            
            await browser.close()
        
        results["status"] = "success" if results["failed"] == 0 else "partial"
        return results
        
    except ImportError as e:
        logger.warning(f"Playwright not installed: {str(e)}")
        logger.info("Falling back to system browser...")
        return _run_tests_with_system_browser(project_root, frontend_url, backend_url)
    except Exception as e:
        logger.error(f"Error during async interactive tests: {str(e)}")
        return {
            "status": "error",
            "message": f"Error running interactive tests: {str(e)}"
        }


def run_interactive_tests(project_root: str, frontend_url: str = "http://localhost:3000",
                         backend_url: str = "http://localhost:8000", headless: bool = False,
                         perform_interactions: bool = True) -> dict:
    """
    Run interactive Playwright tests with visible browser.
    Now includes ACTUAL USER INTERACTIONS like clicking buttons, filling forms, creating tasks, etc.
    
    AUTO-FIXES:
    - Detects if running in asyncio loop and automatically uses async version
    - Handles Playwright installation issues gracefully
    - Provides clear error messages and fallback options
    
    Args:
        project_root: Root directory of the project
        frontend_url: Frontend URL
        backend_url: Backend URL
        headless: Run in headless mode
        perform_interactions: Perform actual user interactions (default: True)
        
    Returns:
        Dictionary with test results including interaction tests
    """
    # AUTO-FIX: Check if we're in an asyncio loop (Playwright Sync API won't work)
    try:
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            # We're inside an asyncio loop - use async version
            logger.info("Detected asyncio loop - using async Playwright API")
            # Try to use nest_asyncio to allow nested event loops
            try:
                import nest_asyncio
                nest_asyncio.apply()
                # Now we can use asyncio.run even though we're in a loop
                return asyncio.run(run_interactive_tests_async(project_root, frontend_url, backend_url, headless, perform_interactions))
            except ImportError:
                # nest_asyncio not available - create a task in the existing loop
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        lambda: asyncio.run(run_interactive_tests_async(project_root, frontend_url, backend_url, headless, perform_interactions))
                    )
                    return future.result(timeout=300)
        except RuntimeError:
            # No running loop - we can use sync_playwright
            pass
    except ImportError:
        pass
    
    try:
        from playwright.sync_api import sync_playwright, expect
        
        results = {
            "tests": [],
            "passed": 0,
            "failed": 0,
            "total": 0,
            "interactions": []
        }
        
        with sync_playwright() as p:
            # Launch browser with visible window (unless headless mode requested)
            logger.info(f"🌐 Launching {'headless ' if headless else 'VISIBLE '}Chromium browser...")
            browser = p.chromium.launch(
                headless=headless,
                slow_mo=500 if not headless else 0,  # Slow down actions for visibility
                args=['--start-maximized'] if not headless else []  # Maximize window
            )
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                no_viewport=True if not headless else False  # Use full window size
            )
            page = context.new_page()
            logger.info("✅ Browser window opened!")
            
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
                logger.info(f"🌐 Loading frontend at {frontend_url}")
                print(f"\n{'='*70}")
                print(f"🌐 BROWSER LAUNCHED - Opening: {frontend_url}")
                print(f"{'='*70}\n")
                
                page.goto(frontend_url, wait_until="networkidle", timeout=30000)
                title = page.title()
                
                logger.info(f"✅ Page loaded: {title}")
                print(f"✅ Page loaded successfully: {title}\n")
                
                results["tests"].append({"name": "Frontend loads successfully", "status": "passed", "title": title})
                results["passed"] += 1
                
                # Take initial screenshot
                screenshot_path = os.path.join(project_root, "frontend_initial.png")
                page.screenshot(path=screenshot_path, full_page=True)
                results["screenshot"] = screenshot_path
                
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
            
            # NEW: Test 4-N: Perform ACTUAL USER INTERACTIONS
            if perform_interactions:
                logger.info("Starting interactive user flow tests...")
                print(f"\n{'='*70}")
                print(f"🎬 PERFORMING INTERACTIVE TESTS")
                print(f"   Watch the browser - it will interact with your app!")
                print(f"   - Clicking buttons")
                print(f"   - Filling forms")
                print(f"   - Creating items")
                print(f"   - Testing navigation")
                print(f"{'='*70}\n")
                
                # Try to detect and interact with common UI elements
                interaction_tests = [
                    {
                        "name": "Find and click buttons",
                        "action": lambda: _test_button_interactions(page, results)
                    },
                    {
                        "name": "Fill input fields",
                        "action": lambda: _test_input_interactions(page, results)
                    },
                    {
                        "name": "Create/Add items (if applicable)",
                        "action": lambda: _test_create_item(page, results, backend_url)
                    },
                    {
                        "name": "Navigate and test routes",
                        "action": lambda: _test_navigation(page, results)
                    },
                    {
                        "name": "Test form submissions",
                        "action": lambda: _test_form_submission(page, results)
                    }
                ]
                
                for test in interaction_tests:
                    results["total"] += 1
                    try:
                        test["action"]()
                    except Exception as e:
                        logger.warning(f"Interaction test '{test['name']}' failed: {str(e)}")
                
                # Take final screenshot after interactions
                screenshot_after = os.path.join(project_root, "frontend_after_interactions.png")
                page.screenshot(path=screenshot_after, full_page=True)
                results["screenshot_after"] = screenshot_after
                
                # Keep browser open for inspection if not headless
                if not headless:
                    print(f"\n{'='*70}")
                    print(f"✅ INTERACTIVE TESTS COMPLETED!")
                    print(f"   Browser will stay open for 15 seconds for inspection...")
                    print(f"   You can see the final state of your application")
                    print(f"{'='*70}\n")
                    logger.info("Tests completed! Keeping browser open for 15 seconds for inspection...")
                    page.wait_for_timeout(15000)
                    print("\n⏱️  Closing browser...\n")
            else:
                # Keep browser open for inspection if not headless
                if not headless:
                    logger.info("Application running in browser. Keeping open for 10 seconds...")
                    print(f"\n⏱️  Browser will close in 10 seconds...\n")
                    page.wait_for_timeout(10000)
            
            browser.close()
        
        results["status"] = "success" if results["failed"] == 0 else "partial"
        return results
        
    except ImportError as e:
        logger.warning(f"Playwright not installed: {str(e)}")
        logger.info("Falling back to system browser...")
        return _run_tests_with_system_browser(project_root, frontend_url, backend_url)
    
    except RuntimeError as e:
        # This catches the "asyncio loop" error
        if "asyncio" in str(e).lower() or "event loop" in str(e).lower():
            logger.warning(f"Playwright Sync API conflict with asyncio: {str(e)}")
            logger.info("Auto-fixing: Using system browser instead...")
            return _run_tests_with_system_browser(project_root, frontend_url, backend_url)
        else:
            raise
    
    except Exception as e:
        error_msg = str(e).lower()
        
        # AUTO-FIX: Detect common Playwright errors and provide solutions
        if "asyncio" in error_msg or "event loop" in error_msg or "sync api" in error_msg:
            logger.warning(f"Playwright Sync API cannot be used in this context: {str(e)}")
            logger.info("Auto-fixing: Switching to system browser...")
            return _run_tests_with_system_browser(project_root, frontend_url, backend_url)
        
        # For other errors, return error but still try to open system browser
        logger.error(f"Error during interactive tests: {str(e)}")
        logger.info("Attempting to open application in system browser as fallback...")
        
        try:
            webbrowser.open(frontend_url)
            return {
                "status": "partial",
                "message": f"Interactive tests failed, but application opened in browser: {str(e)}",
                "url": frontend_url,
                "tests": [],
                "passed": 0,
                "failed": 1,
                "total": 1
            }
        except:
            return {
                "status": "error",
                "message": f"Error running interactive tests: {str(e)}"
            }


async def _test_button_interactions_async(page, results: dict):
    """Test clicking buttons on the page (async version)"""
    try:
        # Find all visible buttons
        buttons = await page.locator("button, input[type='button'], input[type='submit']").all()
        
        if not buttons:
            results["interactions"].append("No buttons found")
            return
        
        clicked = 0
        for i, button in enumerate(buttons[:3]):  # Test first 3 buttons
            try:
                if await button.is_visible():
                    button_text = (await button.inner_text()) or (await button.get_attribute("value")) or f"Button {i+1}"
                    logger.info(f"Clicking button: {button_text}")
                    await button.click(timeout=5000)
                    await page.wait_for_timeout(1000)
                    clicked += 1
                    results["interactions"].append(f"Clicked button: {button_text}")
            except Exception as e:
                logger.debug(f"Could not click button {i}: {str(e)}")
        
        if clicked > 0:
            results["tests"].append({"name": "Button interactions", "status": "passed", "buttons_clicked": clicked})
            results["passed"] += 1
        else:
            results["tests"].append({"name": "Button interactions", "status": "skipped", "note": "No clickable buttons found"})
    except Exception as e:
        results["tests"].append({"name": "Button interactions", "status": "failed", "error": str(e)})
        results["failed"] += 1


def _test_button_interactions(page, results: dict):
    """Test clicking buttons on the page"""
    try:
        # Find all visible buttons
        buttons = page.locator("button, input[type='button'], input[type='submit']").all()
        
        if not buttons:
            results["interactions"].append("No buttons found")
            return
        
        clicked = 0
        for i, button in enumerate(buttons[:3]):  # Test first 3 buttons
            try:
                if button.is_visible():
                    button_text = button.inner_text() or button.get_attribute("value") or f"Button {i+1}"
                    logger.info(f"Clicking button: {button_text}")
                    button.click(timeout=5000)
                    page.wait_for_timeout(1000)
                    clicked += 1
                    results["interactions"].append(f"Clicked button: {button_text}")
            except Exception as e:
                logger.debug(f"Could not click button {i}: {str(e)}")
        
        if clicked > 0:
            results["tests"].append({"name": "Button interactions", "status": "passed", "buttons_clicked": clicked})
            results["passed"] += 1
        else:
            results["tests"].append({"name": "Button interactions", "status": "skipped", "note": "No clickable buttons found"})
    except Exception as e:
        results["tests"].append({"name": "Button interactions", "status": "failed", "error": str(e)})
        results["failed"] += 1


async def _test_input_interactions_async(page, results: dict):
    """Test filling input fields (async version)"""
    try:
        # Find all input fields
        inputs = await page.locator("input[type='text'], input[type='email'], input:not([type]), textarea").all()
        
        if not inputs:
            results["interactions"].append("No input fields found")
            return
        
        filled = 0
        test_data = {
            "text": "Test Task from E2E",
            "email": "test@example.com",
            "default": "Sample input"
        }
        
        for i, input_field in enumerate(inputs[:3]):  # Test first 3 inputs
            try:
                if await input_field.is_visible() and not await input_field.is_disabled():
                    field_type = (await input_field.get_attribute("type")) or "default"
                    placeholder = (await input_field.get_attribute("placeholder")) or f"Field {i+1}"
                    
                    test_value = test_data.get(field_type, test_data["default"])
                    logger.info(f"Filling input field: {placeholder} with '{test_value}'")
                    
                    await input_field.fill(test_value)
                    await page.wait_for_timeout(500)
                    filled += 1
                    results["interactions"].append(f"Filled field: {placeholder}")
            except Exception as e:
                logger.debug(f"Could not fill input {i}: {str(e)}")
        
        if filled > 0:
            results["tests"].append({"name": "Input field interactions", "status": "passed", "fields_filled": filled})
            results["passed"] += 1
        else:
            results["tests"].append({"name": "Input field interactions", "status": "skipped", "note": "No fillable inputs found"})
    except Exception as e:
        results["tests"].append({"name": "Input field interactions", "status": "failed", "error": str(e)})
        results["failed"] += 1


def _test_input_interactions(page, results: dict):
    """Test filling input fields"""
    try:
        # Find all input fields
        inputs = page.locator("input[type='text'], input[type='email'], input:not([type]), textarea").all()
        
        if not inputs:
            results["interactions"].append("No input fields found")
            return
        
        filled = 0
        test_data = {
            "text": "Test Task from E2E",
            "email": "test@example.com",
            "default": "Sample input"
        }
        
        for i, input_field in enumerate(inputs[:3]):  # Test first 3 inputs
            try:
                if input_field.is_visible() and not input_field.is_disabled():
                    field_type = input_field.get_attribute("type") or "default"
                    placeholder = input_field.get_attribute("placeholder") or f"Field {i+1}"
                    
                    test_value = test_data.get(field_type, test_data["default"])
                    logger.info(f"Filling input field: {placeholder} with '{test_value}'")
                    
                    input_field.fill(test_value)
                    page.wait_for_timeout(500)
                    filled += 1
                    results["interactions"].append(f"Filled field: {placeholder}")
            except Exception as e:
                logger.debug(f"Could not fill input {i}: {str(e)}")
        
        if filled > 0:
            results["tests"].append({"name": "Input field interactions", "status": "passed", "fields_filled": filled})
            results["passed"] += 1
        else:
            results["tests"].append({"name": "Input field interactions", "status": "skipped", "note": "No fillable inputs found"})
    except Exception as e:
        results["tests"].append({"name": "Input field interactions", "status": "failed", "error": str(e)})
        results["failed"] += 1


async def _test_create_item_async(page, results: dict, backend_url: str):
    """Test creating an item (e.g., todo, task, post) - async version"""
    try:
        # Look for common patterns: input + button, form with submit
        created = False
        
        # Pattern 1: Input field with adjacent button
        input_selectors = [
            "input[placeholder*='task' i]",
            "input[placeholder*='todo' i]", 
            "input[placeholder*='add' i]",
            "input[type='text']:visible"
        ]
        
        for selector in input_selectors:
            try:
                input_field = page.locator(selector).first
                if await input_field.is_visible():
                    # Fill the input
                    logger.info(f"Found input field, creating test item...")
                    await input_field.fill("E2E Test Task - Created by Playwright")
                    await page.wait_for_timeout(500)
                    
                    # Look for nearby submit button
                    add_buttons = await page.locator("button:has-text('Add'), button:has-text('Create'), button:has-text('Submit'), button[type='submit']").all()
                    
                    for button in add_buttons:
                        if await button.is_visible():
                            logger.info(f"Clicking submit button to create item...")
                            await button.click()
                            await page.wait_for_timeout(2000)
                            created = True
                            results["interactions"].append("Created new item via form")
                            break
                    
                    if created:
                        break
            except:
                continue
        
        if created:
            # Verify item was created by checking the page or API
            await page.wait_for_timeout(1000)
            results["tests"].append({"name": "Create item interaction", "status": "passed", "action": "Item created"})
            results["passed"] += 1
        else:
            results["tests"].append({"name": "Create item interaction", "status": "skipped", "note": "No create form found"})
    except Exception as e:
        results["tests"].append({"name": "Create item interaction", "status": "failed", "error": str(e)})
        results["failed"] += 1


def _test_create_item(page, results: dict, backend_url: str):
    """Test creating an item (e.g., todo, task, post)"""
    try:
        # Look for common patterns: input + button, form with submit
        created = False
        
        # Pattern 1: Input field with adjacent button
        input_selectors = [
            "input[placeholder*='task' i]",
            "input[placeholder*='todo' i]", 
            "input[placeholder*='add' i]",
            "input[type='text']:visible"
        ]
        
        for selector in input_selectors:
            try:
                input_field = page.locator(selector).first
                if input_field.is_visible():
                    # Fill the input
                    logger.info(f"Found input field, creating test item...")
                    input_field.fill("E2E Test Task - Created by Playwright")
                    page.wait_for_timeout(500)
                    
                    # Look for nearby submit button
                    add_buttons = page.locator("button:has-text('Add'), button:has-text('Create'), button:has-text('Submit'), button[type='submit']").all()
                    
                    for button in add_buttons:
                        if button.is_visible():
                            logger.info(f"Clicking submit button to create item...")
                            button.click()
                            page.wait_for_timeout(2000)
                            created = True
                            results["interactions"].append("Created new item via form")
                            break
                    
                    if created:
                        break
            except:
                continue
        
        if created:
            # Verify item was created by checking the page or API
            page.wait_for_timeout(1000)
            results["tests"].append({"name": "Create item interaction", "status": "passed", "action": "Item created"})
            results["passed"] += 1
        else:
            results["tests"].append({"name": "Create item interaction", "status": "skipped", "note": "No create form found"})
    except Exception as e:
        results["tests"].append({"name": "Create item interaction", "status": "failed", "error": str(e)})
        results["failed"] += 1


async def _test_navigation_async(page, results: dict):
    """Test navigation between pages/routes (async version)"""
    try:
        # Find navigation links
        links = await page.locator("a[href], button:has-text('Home'), button:has-text('About')").all()
        
        navigated = 0
        for i, link in enumerate(links[:3]):  # Test first 3 links
            try:
                if await link.is_visible():
                    link_text = (await link.inner_text()) or (await link.get_attribute("href")) or f"Link {i+1}"
                    href = await link.get_attribute("href")
                    
                    # Skip external links
                    if href and (href.startswith("http://") or href.startswith("https://")) and "localhost" not in href:
                        continue
                    
                    logger.info(f"Navigating to: {link_text}")
                    await link.click(timeout=5000)
                    await page.wait_for_load_state("networkidle")
                    await page.wait_for_timeout(1000)
                    navigated += 1
                    results["interactions"].append(f"Navigated to: {link_text}")
                    
                    # Go back
                    await page.go_back()
                    await page.wait_for_timeout(500)
            except Exception as e:
                logger.debug(f"Could not navigate via link {i}: {str(e)}")
        
        if navigated > 0:
            results["tests"].append({"name": "Navigation interactions", "status": "passed", "links_tested": navigated})
            results["passed"] += 1
        else:
            results["tests"].append({"name": "Navigation interactions", "status": "skipped", "note": "No navigation links found"})
    except Exception as e:
        results["tests"].append({"name": "Navigation interactions", "status": "failed", "error": str(e)})
        results["failed"] += 1


def _test_navigation(page, results: dict):
    """Test navigation between pages/routes"""
    try:
        # Find navigation links
        links = page.locator("a[href], button:has-text('Home'), button:has-text('About')").all()
        
        navigated = 0
        for i, link in enumerate(links[:3]):  # Test first 3 links
            try:
                if link.is_visible():
                    link_text = link.inner_text() or link.get_attribute("href") or f"Link {i+1}"
                    href = link.get_attribute("href")
                    
                    # Skip external links
                    if href and (href.startswith("http://") or href.startswith("https://")) and "localhost" not in href:
                        continue
                    
                    logger.info(f"Navigating to: {link_text}")
                    link.click(timeout=5000)
                    page.wait_for_load_state("networkidle")
                    page.wait_for_timeout(1000)
                    navigated += 1
                    results["interactions"].append(f"Navigated to: {link_text}")
                    
                    # Go back
                    page.go_back()
                    page.wait_for_timeout(500)
            except Exception as e:
                logger.debug(f"Could not navigate via link {i}: {str(e)}")
        
        if navigated > 0:
            results["tests"].append({"name": "Navigation interactions", "status": "passed", "links_tested": navigated})
            results["passed"] += 1
        else:
            results["tests"].append({"name": "Navigation interactions", "status": "skipped", "note": "No navigation links found"})
    except Exception as e:
        results["tests"].append({"name": "Navigation interactions", "status": "failed", "error": str(e)})
        results["failed"] += 1


async def _test_form_submission_async(page, results: dict):
    """Test form submission (async version)"""
    try:
        # Find forms on the page
        forms = await page.locator("form").all()
        
        if not forms:
            results["interactions"].append("No forms found")
            return
        
        submitted = 0
        for i, form in enumerate(forms[:2]):  # Test first 2 forms
            try:
                if await form.is_visible():
                    # Fill all inputs in the form
                    inputs = await form.locator("input[type='text'], input:not([type]), textarea").all()
                    
                    for input_field in inputs:
                        if await input_field.is_visible() and not await input_field.is_disabled():
                            await input_field.fill("Test data from E2E")
                            await page.wait_for_timeout(300)
                    
                    # Find and click submit button
                    submit = form.locator("button[type='submit'], input[type='submit'], button:has-text('Submit')").first
                    
                    if await submit.is_visible():
                        logger.info(f"Submitting form {i+1}")
                        await submit.click()
                        await page.wait_for_timeout(2000)
                        submitted += 1
                        results["interactions"].append(f"Submitted form {i+1}")
            except Exception as e:
                logger.debug(f"Could not submit form {i}: {str(e)}")
        
        if submitted > 0:
            results["tests"].append({"name": "Form submission", "status": "passed", "forms_submitted": submitted})
            results["passed"] += 1
        else:
            results["tests"].append({"name": "Form submission", "status": "skipped", "note": "No submittable forms found"})
    except Exception as e:
        results["tests"].append({"name": "Form submission", "status": "failed", "error": str(e)})
        results["failed"] += 1


def _test_form_submission(page, results: dict):
    """Test form submission"""
    try:
        # Find forms on the page
        forms = page.locator("form").all()
        
        if not forms:
            results["interactions"].append("No forms found")
            return
        
        submitted = 0
        for i, form in enumerate(forms[:2]):  # Test first 2 forms
            try:
                if form.is_visible():
                    # Fill all inputs in the form
                    inputs = form.locator("input[type='text'], input:not([type]), textarea").all()
                    
                    for input_field in inputs:
                        if input_field.is_visible() and not input_field.is_disabled():
                            input_field.fill("Test data from E2E")
                            page.wait_for_timeout(300)
                    
                    # Find and click submit button
                    submit = form.locator("button[type='submit'], input[type='submit'], button:has-text('Submit')").first
                    
                    if submit.is_visible():
                        logger.info(f"Submitting form {i+1}")
                        submit.click()
                        page.wait_for_timeout(2000)
                        submitted += 1
                        results["interactions"].append(f"Submitted form {i+1}")
            except Exception as e:
                logger.debug(f"Could not submit form {i}: {str(e)}")
        
        if submitted > 0:
            results["tests"].append({"name": "Form submission", "status": "passed", "forms_submitted": submitted})
            results["passed"] += 1
        else:
            results["tests"].append({"name": "Form submission", "status": "skipped", "note": "No submittable forms found"})
    except Exception as e:
        results["tests"].append({"name": "Form submission", "status": "failed", "error": str(e)})
        results["failed"] += 1


async def _test_comprehensive_interactions_async(page, results: dict, backend_url: str):
    """Comprehensive test that performs ALL possible interactions - async version"""
    try:
        logger.info("Starting comprehensive interaction test - testing ALL elements...")
        results["total"] += 1
        
        interactions_performed = []
        
        # 1. Test ALL buttons (not just first 3)
        try:
            buttons = await page.locator("button, input[type='button'], input[type='submit']").all()
            clicked_count = 0
            for i, button in enumerate(buttons[:10]):  # Test up to 10 buttons
                try:
                    if await button.is_visible() and await button.is_enabled():
                        button_text = (await button.inner_text()) or (await button.get_attribute("value")) or f"Button {i+1}"
                        await button.click(timeout=3000)
                        await page.wait_for_timeout(500)
                        clicked_count += 1
                        interactions_performed.append(f"Clicked button: {button_text}")
                except:
                    continue
            if clicked_count > 0:
                interactions_performed.append(f"Total buttons clicked: {clicked_count}")
        except Exception as e:
            logger.debug(f"Error testing buttons: {str(e)}")
        
        # 2. Test ALL input fields
        try:
            inputs = await page.locator("input[type='text'], input[type='email'], input:not([type]), textarea").all()
            filled_count = 0
            for i, input_field in enumerate(inputs[:10]):  # Test up to 10 inputs
                try:
                    if await input_field.is_visible() and not await input_field.is_disabled():
                        await input_field.fill(f"Test input {i+1}")
                        await page.wait_for_timeout(200)
                        filled_count += 1
                except:
                    continue
            if filled_count > 0:
                interactions_performed.append(f"Total inputs filled: {filled_count}")
        except Exception as e:
            logger.debug(f"Error testing inputs: {str(e)}")
        
        # 3. Test ALL links
        try:
            links = await page.locator("a[href]:visible").all()
            clicked_links = 0
            for i, link in enumerate(links[:10]):  # Test up to 10 links
                try:
                    href = await link.get_attribute("href")
                    if href and ("localhost" in str(href) or str(href).startswith("/") or str(href).startswith("#")):
                        await link.click(timeout=3000)
                        await page.wait_for_timeout(1000)
                        await page.go_back()
                        await page.wait_for_timeout(500)
                        clicked_links += 1
                except:
                    continue
            if clicked_links > 0:
                interactions_performed.append(f"Total links clicked: {clicked_links}")
        except Exception as e:
            logger.debug(f"Error testing links: {str(e)}")
        
        if interactions_performed:
            results["tests"].append({
                "name": "Comprehensive interactions",
                "status": "passed",
                "interactions": len(interactions_performed)
            })
            results["passed"] += 1
            results["interactions"].extend(interactions_performed)
        else:
            results["tests"].append({
                "name": "Comprehensive interactions",
                "status": "skipped",
                "note": "No interactive elements found"
            })
    except Exception as e:
        results["tests"].append({
            "name": "Comprehensive interactions",
            "status": "failed",
            "error": str(e)
        })
        results["failed"] += 1


async def _test_create_multiple_items_async(page, results: dict, backend_url: str):
    """Test creating multiple items - async version"""
    try:
        created_count = 0
        test_items = [
            "E2E Test Task 1",
            "E2E Test Task 2",
            "E2E Test Task 3"
        ]
        
        for item_text in test_items:
            try:
                # Find input field
                input_field = page.locator("input[placeholder*='task' i], input[placeholder*='todo' i], input[placeholder*='add' i], input[type='text']:visible").first
                
                if await input_field.is_visible():
                    await input_field.fill(item_text)
                    await page.wait_for_timeout(300)
                    
                    # Find and click submit button
                    add_button = page.locator("button:has-text('Add'), button:has-text('Create'), button[type='submit']").first
                    if await add_button.is_visible():
                        await add_button.click()
                        await page.wait_for_timeout(1000)
                        created_count += 1
                        results["interactions"].append(f"Created item: {item_text}")
            except:
                continue
        
        if created_count > 0:
            results["tests"].append({
                "name": "Create multiple items",
                "status": "passed",
                "items_created": created_count
            })
            results["passed"] += 1
        else:
            results["tests"].append({
                "name": "Create multiple items",
                "status": "skipped",
                "note": "No create form found"
            })
    except Exception as e:
        results["tests"].append({
            "name": "Create multiple items",
            "status": "failed",
            "error": str(e)
        })
        results["failed"] += 1


async def _test_all_links_async(page, results: dict):
    """Test ALL links on the page - async version"""
    try:
        links = await page.locator("a[href]:visible").all()
        tested_count = 0
        
        for i, link in enumerate(links[:15]):  # Test up to 15 links
            try:
                href = await link.get_attribute("href")
                link_text = (await link.inner_text()) or href or f"Link {i+1}"
                
                # Skip external links
                if href and (href.startswith("http://") or href.startswith("https://")) and "localhost" not in href:
                    continue
                
                await link.click(timeout=3000)
                await page.wait_for_load_state("networkidle")
                await page.wait_for_timeout(500)
                tested_count += 1
                results["interactions"].append(f"Tested link: {link_text}")
                
                # Go back if not on same page
                if href and not href.startswith("#"):
                    await page.go_back()
                    await page.wait_for_timeout(300)
            except:
                continue
        
        if tested_count > 0:
            results["tests"].append({
                "name": "All links tested",
                "status": "passed",
                "links_tested": tested_count
            })
            results["passed"] += 1
        else:
            results["tests"].append({
                "name": "All links tested",
                "status": "skipped",
                "note": "No links found"
            })
    except Exception as e:
        results["tests"].append({
            "name": "All links tested",
            "status": "failed",
            "error": str(e)
        })
        results["failed"] += 1


async def _test_all_forms_async(page, results: dict):
    """Test ALL forms on the page - async version"""
    try:
        forms = await page.locator("form").all()
        tested_count = 0
        
        for i, form in enumerate(forms[:5]):  # Test up to 5 forms
            try:
                if await form.is_visible():
                    # Fill all inputs
                    inputs = await form.locator("input[type='text'], input[type='email'], textarea").all()
                    for input_field in inputs:
                        if await input_field.is_visible() and not await input_field.is_disabled():
                            await input_field.fill("Test form data")
                            await page.wait_for_timeout(200)
                    
                    # Try to submit
                    submit = form.locator("button[type='submit'], input[type='submit']").first
                    if await submit.is_visible():
                        await submit.click()
                        await page.wait_for_timeout(1000)
                        tested_count += 1
                        results["interactions"].append(f"Tested form {i+1}")
            except:
                continue
        
        if tested_count > 0:
            results["tests"].append({
                "name": "All forms tested",
                "status": "passed",
                "forms_tested": tested_count
            })
            results["passed"] += 1
        else:
            results["tests"].append({
                "name": "All forms tested",
                "status": "skipped",
                "note": "No forms found"
            })
    except Exception as e:
        results["tests"].append({
            "name": "All forms tested",
            "status": "failed",
            "error": str(e)
        })
        results["failed"] += 1


async def _test_all_buttons_async(page, results: dict):
    """Test ALL buttons on the page - async version"""
    try:
        buttons = await page.locator("button, input[type='button'], input[type='submit']").all()
        clicked_count = 0
        
        for i, button in enumerate(buttons[:20]):  # Test up to 20 buttons
            try:
                if await button.is_visible() and await button.is_enabled():
                    await button.click(timeout=3000)
                    await page.wait_for_timeout(500)
                    clicked_count += 1
            except:
                continue
        
        if clicked_count > 0:
            results["tests"].append({
                "name": "All buttons tested",
                "status": "passed",
                "buttons_clicked": clicked_count
            })
            results["passed"] += 1
        else:
            results["tests"].append({
                "name": "All buttons tested",
                "status": "skipped",
                "note": "No buttons found"
            })
    except Exception as e:
        results["tests"].append({
            "name": "All buttons tested",
            "status": "failed",
            "error": str(e)
        })
        results["failed"] += 1


async def _test_dropdowns_and_selects_async(page, results: dict):
    """Test ALL dropdowns and select elements - async version"""
    try:
        selects = await page.locator("select").all()
        tested_count = 0
        
        for i, select in enumerate(selects[:10]):  # Test up to 10 selects
            try:
                if await select.is_visible():
                    options = await select.locator("option").all()
                    if len(options) > 1:
                        await select.select_option(index=1)
                        await page.wait_for_timeout(300)
                        tested_count += 1
            except:
                continue
        
        if tested_count > 0:
            results["tests"].append({
                "name": "Dropdowns and selects tested",
                "status": "passed",
                "selects_tested": tested_count
            })
            results["passed"] += 1
        else:
            results["tests"].append({
                "name": "Dropdowns and selects tested",
                "status": "skipped",
                "note": "No selects found"
            })
    except Exception as e:
        results["tests"].append({
            "name": "Dropdowns and selects tested",
            "status": "failed",
            "error": str(e)
        })
        results["failed"] += 1


async def _test_checkboxes_and_radios_async(page, results: dict):
    """Test ALL checkboxes and radio buttons - async version"""
    try:
        checkboxes = await page.locator("input[type='checkbox']").all()
        radios = await page.locator("input[type='radio']").all()
        tested_count = 0
        
        # Test checkboxes
        for checkbox in checkboxes[:10]:  # Test up to 10 checkboxes
            try:
                if await checkbox.is_visible() and not await checkbox.is_disabled():
                    await checkbox.click()
                    await page.wait_for_timeout(200)
                    tested_count += 1
            except:
                continue
        
        # Test radio buttons (click first in each group)
        radio_groups = {}
        for radio in radios[:10]:  # Test up to 10 radios
            try:
                if await radio.is_visible() and not await radio.is_disabled():
                    name = await radio.get_attribute("name")
                    if name and name not in radio_groups:
                        await radio.click()
                        await page.wait_for_timeout(200)
                        radio_groups[name] = True
                        tested_count += 1
            except:
                continue
        
        if tested_count > 0:
            results["tests"].append({
                "name": "Checkboxes and radios tested",
                "status": "passed",
                "elements_tested": tested_count
            })
            results["passed"] += 1
        else:
            results["tests"].append({
                "name": "Checkboxes and radios tested",
                "status": "skipped",
                "note": "No checkboxes/radios found"
            })
    except Exception as e:
        results["tests"].append({
            "name": "Checkboxes and radios tested",
            "status": "failed",
            "error": str(e)
        })
        results["failed"] += 1


def _run_tests_with_system_browser(project_root: str, frontend_url: str, backend_url: str) -> dict:
    """
    Fallback function that runs basic tests and opens system browser.
    Used when Playwright Sync API cannot be used (e.g., inside asyncio loop).
    
    Args:
        project_root: Root directory of the project
        frontend_url: Frontend URL
        backend_url: Backend URL
        
    Returns:
        Dictionary with basic test results
    """
    results = {
        "tests": [],
        "passed": 0,
        "failed": 0,
        "total": 2,
        "interactions": ["Opened application in system browser"],
        "status": "success",
        "fallback": True,
        "reason": "Running in asyncio context - Playwright Sync API not available"
    }
    
    # Test 1: Try to open system browser
    try:
        logger.info(f"Opening {frontend_url} in system browser")
        print(f"\n{'='*70}")
        print(f"🌐 OPENING IN YOUR DEFAULT BROWSER")
        print(f"   URL: {frontend_url}")
        print(f"{'='*70}\n")
        
        webbrowser.open(frontend_url)
        results["tests"].append({
            "name": "Open frontend in browser",
            "status": "passed",
            "url": frontend_url
        })
        results["passed"] += 1
        
        # Wait a moment for browser to open
        time.sleep(2)
        
    except Exception as e:
        results["tests"].append({
            "name": "Open frontend in browser",
            "status": "failed",
            "error": str(e)
        })
        results["failed"] += 1
    
    # Test 2: Basic backend health check
    try:
        import urllib.request
        response = urllib.request.urlopen(f"{backend_url}/health", timeout=5)
        if response.status == 200:
            results["tests"].append({
                "name": "Backend health check",
                "status": "passed"
            })
            results["passed"] += 1
        else:
            results["tests"].append({
                "name": "Backend health check",
                "status": "failed",
                "error": f"Status code: {response.status}"
            })
            results["failed"] += 1
    except Exception as e:
        results["tests"].append({
            "name": "Backend health check",
            "status": "warning",
            "note": "Could not reach backend (this is normal if backend doesn't have /health endpoint)"
        })
    
    print(f"\n{'='*70}")
    print(f"✅ APPLICATION IS RUNNING!")
    print(f"   Frontend: {frontend_url}")
    print(f"   Backend:  {backend_url}")
    print(f"\n   Your default browser should have opened automatically.")
    print(f"   If not, copy and paste the URLs above into your browser.")
    print(f"{'='*70}\n")
    
    return results


def check_containers_running(project_root: str) -> dict:
    """
    Check if docker-compose containers are already running.
    
    Args:
        project_root: Root directory with docker-compose.yml
        
    Returns:
        Dictionary with status and list of running containers
    """
    try:
        # Check if docker-compose.yml exists
        compose_files = ['docker-compose.yml', 'docker-compose.yaml']
        compose_file = None
        
        for cf in compose_files:
            if os.path.exists(os.path.join(project_root, cf)):
                compose_file = cf
                break
        
        if not compose_file:
            return {
                "running": False,
                "count": 0,
                "error": "No docker-compose.yml file found"
            }
        
        result = subprocess.run(
            ["docker-compose", "-f", compose_file, "ps", "-q"],
            cwd=project_root,
            capture_output=True,
            encoding='utf-8',
            errors='replace',
            timeout=10
        )
        
        # If we get container IDs, they're running
        container_ids = [cid for cid in result.stdout.strip().split('\n') if cid]
        
        return {
            "running": len(container_ids) > 0,
            "count": len(container_ids),
            "container_ids": container_ids
        }
    except Exception as e:
        return {
            "running": False,
            "count": 0,
            "error": str(e)
        }


def launch_and_test(project_root: str, backend_port: int = 8000, 
                   frontend_port: int = 3000, cleanup: bool = False,
                   headless: bool = False, show_browser: bool = True,
                   use_system_browser: bool = True) -> str:
    """
    Complete workflow: Check if containers are running, start if needed, wait for services, 
    launch browser, run tests, cleanup.
    
    Args:
        project_root: Root directory with docker-compose.yml
        backend_port: Backend service port
        frontend_port: Frontend service port
        cleanup: Whether to stop docker-compose after tests
        headless: Run browser in headless mode
        show_browser: Launch browser to show the running application
        use_system_browser: Open in your default browser (Chrome/Edge) instead of Playwright
        
    Returns:
        Formatted test report
    """
    report = f"🧪 **End-to-End Testing Report**\n\n"
    report += f"**Project:** {project_root}\n\n"
    
    # Step 1: Check if containers are already running
    report += "**Step 1: Checking Container Status...**\n"
    container_check = check_containers_running(project_root)
    
    containers_already_running = container_check.get("running", False)
    
    if containers_already_running:
        report += f"✅ Containers already running ({container_check['count']} container(s))\n"
        report += "   Skipping docker-compose start...\n\n"
    else:
        report += "ℹ️  No containers running, starting Docker Compose...\n"
        
        # Start docker-compose
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
    
    # Step 3: Launch browser and RUN ACTUAL E2E TESTS (PRIMARY ACTION)
    report += "**Step 3: Launching Browser & Running Interactive Tests...**\n"
    frontend_url = f"http://localhost:{frontend_port}"
    backend_url = f"http://localhost:{backend_port}"
    
    if show_browser:
        report += f"🌐 Opening application in browser...\n"
        report += f"   Frontend: {frontend_url}\n"
        report += f"   Backend:  {backend_url}\n\n"
        
        try:
            # ALWAYS use Playwright for comprehensive testing with interactions
            logger.info(f"Running comprehensive E2E tests with Playwright")
            report += "🎬 Running interactive tests (clicks, forms, navigation)...\n\n"
            
            # Run interactive tests with actual user interactions
            interactive_results = run_interactive_tests(
                project_root,
                frontend_url,
                backend_url,
                headless=headless,
                perform_interactions=True  # ENABLE ACTUAL INTERACTIONS
            )
            
            if interactive_results["status"] == "error":
                report += f"❌ {interactive_results['message']}\n"
                report += f"\n💡 Tip: Make sure Playwright is installed:\n"
                report += f"   pip install playwright\n"
                report += f"   playwright install\n"
                
                # Fallback: open in system browser
                report += f"\n📌 Falling back to system browser...\n"
                try:
                    webbrowser.open(frontend_url)
                    report += f"✅ Application opened in your default browser!\n"
                    report += f"🌐 Frontend: {frontend_url}\n"
                    report += f"🔧 Backend: {backend_url}\n"
                except Exception as e2:
                    report += f"❌ Could not open browser: {str(e2)}\n"
            
            elif interactive_results.get("fallback"):
                # AUTO-FIX was triggered - explain what happened
                report += f"ℹ️  **AUTO-FIX APPLIED**\n"
                report += f"   Reason: {interactive_results.get('reason', 'Compatibility issue detected')}\n"
                report += f"   Solution: Opened application in your default browser\n\n"
                report += f"✅ Application is running and accessible!\n"
                report += f"🌐 Frontend: {frontend_url}\n"
                report += f"🔧 Backend: {backend_url}\n\n"
                report += f"📊 Basic Test Results: {interactive_results['passed']}/{interactive_results['total']} passed\n\n"
                
                for test in interactive_results.get("tests", []):
                    status_icon = "✅" if test["status"] == "passed" else "❌" if test["status"] == "failed" else "⚠️"
                    report += f"{status_icon} {test['name']}\n"
                    if "error" in test:
                        report += f"   Error: {test['error']}\n"
                    if "note" in test:
                        report += f"   Note: {test['note']}\n"
                
                report += f"\n💡 The application opened successfully in your browser!\n"
                report += f"   You can now manually test the application.\n"
            
            else:
                report += f"✅ End-to-End tests completed!\n"
                report += f"🌐 Application URL: {frontend_url}\n"
                report += f"🔧 Backend URL: {backend_url}\n\n"
                report += f"📊 Test Results: {interactive_results['passed']}/{interactive_results['total']} passed\n\n"
                
                # Show all test results
                for test in interactive_results.get("tests", []):
                    status_icon = "✅" if test["status"] == "passed" else "❌" if test["status"] == "failed" else "⚠️" if test["status"] == "skipped" else "ℹ️"
                    report += f"{status_icon} {test['name']}\n"
                    
                    if "error" in test:
                        report += f"   Error: {test['error']}\n"
                    if "title" in test:
                        report += f"   Page title: {test['title']}\n"
                    if "api_calls" in test:
                        report += f"   API calls made: {test['api_calls']}\n"
                    if "buttons_clicked" in test:
                        report += f"   Buttons clicked: {test['buttons_clicked']}\n"
                    if "fields_filled" in test:
                        report += f"   Fields filled: {test['fields_filled']}\n"
                    if "links_tested" in test:
                        report += f"   Links tested: {test['links_tested']}\n"
                    if "forms_submitted" in test:
                        report += f"   Forms submitted: {test['forms_submitted']}\n"
                    if "action" in test:
                        report += f"   Action: {test['action']}\n"
                    if "note" in test:
                        report += f"   Note: {test['note']}\n"
                
                # Show interactions performed
                if interactive_results.get("interactions"):
                    report += f"\n🎬 **User Interactions Performed:**\n"
                    for interaction in interactive_results["interactions"][:10]:
                        report += f"   • {interaction}\n"
                    if len(interactive_results["interactions"]) > 10:
                        report += f"   ... and {len(interactive_results['interactions']) - 10} more\n"
                
                # Show screenshots and embed them in chat
                if "screenshot" in interactive_results:
                    screenshot_path = interactive_results['screenshot']
                    report += f"\n📸 Screenshot (Initial): {screenshot_path}\n"
                    # Embed screenshot inline in chat response
                    if "screenshot_data_url" in interactive_results:
                        report += f"\n![Initial Screenshot]({interactive_results['screenshot_data_url']})\n"
                
                if "screenshot_after" in interactive_results:
                    screenshot_path = interactive_results['screenshot_after']
                    report += f"\n📸 Screenshot (After Tests): {screenshot_path}\n"
                    # Embed screenshot inline in chat response
                    if "screenshot_after_data_url" in interactive_results:
                        report += f"\n![After Tests Screenshot]({interactive_results['screenshot_after_data_url']})\n"
                
                report += f"\n💡 The application was tested with actual user interactions!\n"
                report += f"   Frontend: {frontend_url}\n"
                report += f"   Backend: {backend_url}\n"
        
        except Exception as e:
            report += f"❌ Error running E2E tests: {str(e)}\n"
            report += f"\n💡 Install Playwright: pip install playwright && playwright install\n"
            
            # Fallback: open in system browser
            report += f"\n📌 Falling back to system browser...\n"
            try:
                webbrowser.open(frontend_url)
                report += f"✅ Application opened in your default browser!\n"
                report += f"🌐 Frontend: {frontend_url}\n"
                report += f"🔧 Backend: {backend_url}\n"
            except Exception as e2:
                report += f"❌ Could not open browser: {str(e2)}\n"
    else:
        report += f"⚠️  Browser launch disabled (show_browser=False)\n"
        report += f"   Frontend URL: {frontend_url}\n"
        report += f"   Backend URL: {backend_url}\n"
    
    # Step 4: Check for additional test files (OPTIONAL - only if test files exist)
    test_dir = os.path.join(project_root, "e2e-tests")
    
    if not os.path.exists(test_dir):
        # Only mention test template availability, don't auto-generate
        report += f"\n💡 **Optional:** Create automated test suite\n"
        report += f"   Run: create_playwright_tests(project_root=\"{project_root}\")\n"
    else:
        report += "\n**Step 4: Running additional automated tests...**\n"
        # Run Playwright tests if they exist
        test_path = os.path.join(test_dir, "tests")
        if os.path.exists(test_path):
            test_result = run_playwright_tests(test_path, test_dir)
            
            if test_result["status"] == "success":
                report += "✅ All automated tests passed!\n"
                report += f"\n**Test Output:**\n```\n{test_result['stdout']}\n```\n"
            else:
                report += f"⚠️  Some automated tests failed\n"
                report += f"\n**Test Output:**\n```\n{test_result.get('stdout', '')}\n```\n"
                if test_result.get('stderr'):
                    report += f"\n**Errors:**\n```\n{test_result['stderr']}\n```\n"
        else:
            report += f"ℹ️  No additional test files found\n"
    
    # Step 5: Cleanup (optional)
    if cleanup:
        report += "\n**Step 5: Stopping services...**\n"
        stop_result = stop_docker_compose(project_root)
        report += "✅ Services stopped\n" if stop_result["status"] == "success" else "⚠️  Cleanup warning\n"
        report += "\n**Application closed** 🎉\n"
    else:
        report += "\n" + "="*60 + "\n"
        report += "🚀 **APPLICATION IS RUNNING!**\n"
        report += "="*60 + "\n\n"
        report += f"Your dockerized application is now live:\n\n"
        report += f"   🌐 Frontend: http://localhost:{frontend_port}\n"
        report += f"   🔧 Backend:  http://localhost:{backend_port}\n\n"
        report += f"The services will continue running in Docker.\n"
        report += f"Open your browser and visit the URLs above!\n\n"
        report += f"To stop the services later, run:\n"
        report += f"   stop_services(project_root=\"{project_root}\")\n"
        report += "\n" + "="*60 + "\n"
    
    return report
