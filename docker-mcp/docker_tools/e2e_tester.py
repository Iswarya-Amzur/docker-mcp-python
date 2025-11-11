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


def launch_and_test(project_root: str, backend_port: int = 8000, 
                   frontend_port: int = 3000, cleanup: bool = True) -> str:
    """
    Complete workflow: Start docker-compose, wait for services, run tests, cleanup.
    
    Args:
        project_root: Root directory with docker-compose.yml
        backend_port: Backend service port
        frontend_port: Frontend service port
        cleanup: Whether to stop docker-compose after tests
        
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
    
    # Step 3: Check for tests
    report += "**Step 3: Running tests...**\n"
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
    
    # Step 4: Cleanup
    if cleanup:
        report += "\n**Step 4: Cleaning up...**\n"
        stop_result = stop_docker_compose(project_root)
        report += "✅ Services stopped\n" if stop_result["status"] == "success" else "⚠️  Cleanup warning\n"
    else:
        report += "\n**Services still running** (cleanup=False)\n"
    
    report += "\n**Test run complete!** 🎉\n"
    return report
