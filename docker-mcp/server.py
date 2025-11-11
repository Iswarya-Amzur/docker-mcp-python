from fastmcp import FastMCP
import subprocess
import os
import json
import logging
from typing import Optional
from docker_tools.analyzer import analyze_application
from docker_tools.dockerfile_generator import generate_dockerfile
from docker_tools.docker_builder import build_docker_image
from docker_tools.test_runner import run_tests_in_container
from docker_tools.error_fixer import fix_containerization_errors
from docker_tools.multi_service_handler import dockerize_full_project, detect_services
from docker_tools.e2e_tester import (
    launch_and_test, 
    generate_playwright_test_template,
    start_docker_compose,
    stop_docker_compose,
    run_playwright_tests
)
from docker_tools.logging_monitor import (
    setup_complete_monitoring,
    fetch_logs_from_loki,
    analyze_logs_for_errors,
    suggest_fixes_for_errors,
    launch_grafana_dashboard,
    validate_and_fix_monitoring,
    diagnose_monitoring_stack,
    smart_dockerize_and_show_logs
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP("Amzure Docker MCP", version="1.0.0")

# Tool 1: Analyze Application Structure
@mcp.tool()
def analyze_app(app_path: str) -> str:
    """
    Analyze an application structure to understand its type, dependencies, 
    and containerization requirements.
    
    Args:
        app_path: Path to the application directory
    
    Returns:
        Analysis report with app type, dependencies, entry point, etc.
    """
    try:
        logger.info(f"Analyzing application at {app_path}")
        analysis = analyze_application(app_path)
        return json.dumps(analysis, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "status": "failed"})

# Tool 2: Generate Dockerfile
@mcp.tool()
def generate_docker_file(
    app_path: str, 
    app_type: Optional[str] = None,
    python_version: Optional[str] = None,
    additional_packages: Optional[str] = None
) -> str:
    """
    Generate an optimized Dockerfile for the application.
    
    Args:
        app_path: Path to the application
        app_type: Type of app (python, node, java, static, auto-detect). Defaults to auto.
        python_version: Python version for Python apps. Defaults to 3.11.
        additional_packages: Additional system packages to install
    
    Returns:
        Generated Dockerfile content
    """
    try:
        logger.info(f"Generating Dockerfile for {app_path}")
        dockerfile_content = generate_dockerfile(
            app_path, 
            app_type or "auto", 
            python_version or "3.11", 
            additional_packages or ""
        )
        return dockerfile_content
    except Exception as e:
        return f"Error generating Dockerfile: {str(e)}"

# Tool 3: Build Docker Image
@mcp.tool()
def build_image(
    app_path: str,
    image_name: Optional[str] = None,
    tag: Optional[str] = None,
    build_args: Optional[str] = None
) -> str:
    """
    Build a Docker image from the application with Dockerfile.
    
    Args:
        app_path: Path to the application directory containing Dockerfile
        image_name: Name for the Docker image. Defaults to my-app.
        tag: Tag for the image (e.g., latest, v1.0). Defaults to latest.
        build_args: Additional build arguments (comma-separated key=value pairs)
    
    Returns:
        Build status and logs
    """
    try:
        img_name = image_name or "my-app"
        img_tag = tag or "latest"
        logger.info(f"Building Docker image: {img_name}:{img_tag}")
        result = build_docker_image(app_path, img_name, img_tag, build_args or "")
        return result
    except Exception as e:
        return f"Error building image: {str(e)}"

# Tool 4: Run Tests in Container
@mcp.tool()
def test_container(
    image_name: str,
    test_command: Optional[str] = None,
    container_name: Optional[str] = None
) -> str:
    """
    Run tests inside the Docker container to validate the build.
    
    Args:
        image_name: Name of the Docker image to test
        test_command: Command to run tests (e.g., pytest, npm test, mvn test). Defaults to pytest.
        container_name: Name for the test container. Defaults to test-container.
    
    Returns:
        Test results and output
    """
    try:
        logger.info(f"Running tests in container: {image_name}")
        results = run_tests_in_container(
            image_name, 
            test_command or "pytest", 
            container_name or "test-container"
        )
        return results
    except Exception as e:
        return f"Error running tests: {str(e)}"

# Tool 5: Fix Containerization Errors
@mcp.tool()
def fix_errors(
    app_path: str,
    error_message: str,
    image_name: Optional[str] = None,
    suggested_fix: Optional[str] = None
) -> str:
    """
    Analyze containerization errors and suggest/apply fixes automatically.
    
    Args:
        app_path: Path to the application
        error_message: The error message from build or test failure
        image_name: Name of the image that failed. Defaults to my-app.
        suggested_fix: Optional suggested fix approach
    
    Returns:
        Fixed Dockerfile content and explanation
    """
    try:
        img_name = image_name or "my-app"
        logger.info(f"Analyzing and fixing errors for {img_name}")
        fix_result = fix_containerization_errors(
            app_path, 
            error_message, 
            img_name,
            suggested_fix or ""
        )
        return fix_result
    except Exception as e:
        return f"Error fixing issues: {str(e)}"

# Tool 6: Get Container Logs
@mcp.tool()
def get_container_logs(container_name: str, tail: Optional[int] = None) -> str:
    """
    Retrieve logs from a running or stopped container for debugging.
    
    Args:
        container_name: Name of the container
        tail: Number of lines to retrieve. Defaults to 50.
    
    Returns:
        Container logs
    """
    try:
        log_tail = tail if tail is not None else 50
        result = subprocess.run(
            ["docker", "logs", "--tail", str(log_tail), container_name],
            capture_output=True,
            encoding='utf-8',
            errors='replace',
            timeout=10
        )
        return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"
    except Exception as e:
        return f"Error retrieving logs: {str(e)}"

# Tool 7: Dockerize Full Project (Backend + Frontend)
@mcp.tool()
def dockerize_project(project_root: str) -> str:
    """
    Automatically detect and dockerize all services (backend, frontend, etc.) in a project.
    Creates Dockerfiles for each service and a unified docker-compose.yml file.
    
    Args:
        project_root: Root directory of the project containing backend/frontend folders
    
    Returns:
        Summary of dockerization process including created files and next steps
    """
    try:
        logger.info(f"Dockerizing full project at {project_root}")
        result = dockerize_full_project(project_root)
        return result
    except Exception as e:
        return f"Error dockerizing project: {str(e)}"

# Tool 8: Detect Services in Project
@mcp.tool()
def detect_project_services(project_root: str) -> str:
    """
    Detect all services (backend, frontend, api, client, etc.) in a project directory.
    
    Args:
        project_root: Root directory of the project
    
    Returns:
        JSON string with detected services and their details
    """
    try:
        logger.info(f"Detecting services in {project_root}")
        services = detect_services(project_root)
        return json.dumps(services, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "status": "failed"})

# Tool 9: Launch and Test Application End-to-End
@mcp.tool()
def test_application_e2e(
    project_root: str,
    backend_port: Optional[int] = None,
    frontend_port: Optional[int] = None,
    cleanup: Optional[bool] = None,
    headless: Optional[bool] = None,
    show_browser: Optional[bool] = None,
    use_system_browser: Optional[bool] = None
) -> str:
    """
    Launch the dockerized application in a browser and run end-to-end tests.
    PRIMARY ACTION: Opens the application in YOUR DEFAULT BROWSER (Chrome, Edge, Firefox).
    This is the main way to test your dockerized app - it launches in your actual browser!
    
    Args:
        project_root: Root directory with docker-compose.yml
        backend_port: Backend service port (default: 8000)
        frontend_port: Frontend service port (default: 3000)
        cleanup: Stop services after browser testing (default: False - keeps running)
        headless: Run browser in headless mode (default: False - SHOWS browser window)
        show_browser: Launch browser to show running application (default: True - ALWAYS ON)
        use_system_browser: Open in your default browser Chrome/Edge instead of Playwright (default: True)
    
    Returns:
        Test report with browser launch status and running service URLs
    """
    try:
        logger.info(f"Launching and testing application at {project_root}")
        result = launch_and_test(
            project_root,
            backend_port or 8000,
            frontend_port or 3000,
            cleanup if cleanup is not None else False,  # Keep running by default
            headless if headless is not None else False,  # Show browser by default
            show_browser if show_browser is not None else True,  # Always launch browser
            use_system_browser if use_system_browser is not None else True  # Use actual browser by default
        )
        return result
    except Exception as e:
        return f"Error running E2E tests: {str(e)}"

# Tool 10: Generate Playwright Test Template
@mcp.tool()
def create_playwright_tests(
    project_root: str,
    backend_url: Optional[str] = None,
    frontend_url: Optional[str] = None
) -> str:
    """
    Generate Playwright test templates for the project.
    Creates e2e-tests directory with configuration and sample tests.
    
    Args:
        project_root: Root directory of the project
        backend_url: Backend URL (default: http://localhost:8000)
        frontend_url: Frontend URL (default: http://localhost:3000)
    
    Returns:
        Path to generated test directory and next steps
    """
    try:
        logger.info(f"Generating Playwright tests for {project_root}")
        test_dir = generate_playwright_test_template(
            project_root,
            backend_url or "http://localhost:8000",
            frontend_url or "http://localhost:3000"
        )
        
        return f"""✅ **Playwright Test Template Created**

**Test Directory:** {test_dir}

**Files Created:**
- package.json (with @playwright/test dependency)
- playwright.config.js (Playwright configuration)
- tests/app.spec.js (Sample E2E tests)

**Next Steps:**
1. Install Playwright:
   ```
   cd {test_dir}
   npm install
   npx playwright install
   ```

2. Run tests:
   ```
   npm test
   ```

3. Run tests in UI mode:
   ```
   npm run test:ui
   ```

4. Customize tests in: {os.path.join(test_dir, 'tests', 'app.spec.js')}
"""
    except Exception as e:
        return f"Error generating Playwright tests: {str(e)}"

# Tool 11: Start Docker Compose Services
@mcp.tool()
def start_services(project_root: str, detached: Optional[bool] = None) -> str:
    """
    Start docker-compose services without running tests.
    
    Args:
        project_root: Root directory with docker-compose.yml
        detached: Run in background (default: True)
    
    Returns:
        Status message
    """
    try:
        logger.info(f"Starting services in {project_root}")
        result = start_docker_compose(project_root, detached if detached is not None else True)
        
        if result["status"] == "success":
            return f"✅ {result['message']}\n\n{result.get('output', '')}"
        else:
            return f"❌ {result['message']}\n\n{result.get('error', '')}"
    except Exception as e:
        return f"Error starting services: {str(e)}"

# Tool 12: Stop Docker Compose Services
@mcp.tool()
def stop_services(project_root: str) -> str:
    """
    Stop and remove docker-compose services.
    
    Args:
        project_root: Root directory with docker-compose.yml
    
    Returns:
        Status message
    """
    try:
        logger.info(f"Stopping services in {project_root}")
        result = stop_docker_compose(project_root)
        
        if result["status"] == "success":
            return f"✅ Services stopped successfully\n\n{result.get('output', '')}"
        else:
            return f"❌ Error stopping services\n\n{result.get('output', '')}"
    except Exception as e:
        return f"Error stopping services: {str(e)}"

# Tool 13: Launch Application in Browser
@mcp.tool()
def launch_app_in_browser(
    frontend_url: Optional[str] = None,
    browser: Optional[str] = None,
    headless: Optional[bool] = None,
    use_system_browser: Optional[bool] = None
) -> str:
    """
    Launch the application in a browser window (like opening it manually).
    Opens in YOUR DEFAULT BROWSER (Chrome, Edge, Firefox) by default!
    
    Args:
        frontend_url: URL of the frontend (default: http://localhost:3000)
        browser: Browser to use - chromium, firefox, webkit, or system (default: system)
        headless: Run in headless mode (default: False - shows browser window)
        use_system_browser: Open in your actual default browser (default: True)
    
    Returns:
        Status message with page title and screenshot location
    """
    from docker_tools.e2e_tester import launch_browser
    
    try:
        logger.info(f"Launching application in browser")
        
        # Default to system browser
        use_sys_browser = use_system_browser if use_system_browser is not None else True
        browser_type = browser or ("system" if use_sys_browser else "chromium")
        
        result = launch_browser(
            frontend_url or "http://localhost:3000",
            browser_type,
            headless if headless is not None else False,
            use_sys_browser
        )
        
        if result["status"] == "success":
            if use_sys_browser or browser_type == "system":
                return f"""✅ **Application Launched in Your Default Browser**

**URL:** {result.get('url')}

The application was opened in your system's default web browser (Chrome/Edge/Firefox).
The browser window should have opened automatically.
If not, manually visit: {result.get('url')}
"""
            else:
                return f"""✅ **Application Launched in Browser**

**Page Title:** {result.get('title', 'N/A')}
**URL:** {result.get('url')}
**Screenshot:** {result.get('screenshot')}

The application was opened in {browser_type} browser.
Browser window was kept open for 5 seconds for inspection.
"""
        else:
            return f"❌ {result.get('message')}"
    except Exception as e:
        return f"Error launching browser: {str(e)}"

# Tool 14: Setup Monitoring Stack
@mcp.tool()
def setup_monitoring(project_root: str, services: Optional[str] = None, validate: Optional[bool] = None) -> str:
    """
    Setup Grafana, Loki, and Promtail for log monitoring and visualization.
    Automatically validates that Loki is receiving logs and fixes common issues.
    PRIMARY ACTION: Dockerizes your app and shows logs in Grafana dashboard.
    
    Args:
        project_root: Root directory of the project
        services: Comma-separated list of service names to monitor (e.g., backend,frontend). Auto-detected if not provided.
        validate: Run validation and auto-fix after setup (default: True)
    
    Returns:
        Setup report with Grafana URL, credentials, and validation results
    """
    try:
        logger.info(f"Setting up monitoring for {project_root}")
        
        # Parse services or auto-detect
        if services:
            service_list = [s.strip() for s in services.split(',')]
        else:
            # Auto-detect services
            from docker_tools.multi_service_handler import detect_services
            detected = detect_services(project_root)
            service_list = list(detected.keys()) if detected else ["app"]
        
        # Setup monitoring stack
        result = setup_complete_monitoring(project_root, service_list)
        
        # Validate and fix if enabled (default: True)
        if validate if validate is not None else True:
            result += "\n\n" + "=" * 60 + "\n"
            result += "**Validating Monitoring Stack...**\n"
            result += "=" * 60 + "\n\n"
            
            validation_result = validate_and_fix_monitoring(project_root)
            result += validation_result
        
        return result
    except Exception as e:
        return f"Error setting up monitoring: {str(e)}"

# Tool 15: Show Application Logs
@mcp.tool()
def show_logs(
    service_name: Optional[str] = None,
    loki_url: Optional[str] = None,
    limit: Optional[int] = None,
    project_root: Optional[str] = None,
    auto_validate: Optional[bool] = None
) -> str:
    """
    Fetch and display logs from Loki for a specific service or all services.
    Automatically validates that Loki is receiving logs and fixes issues if needed.
    
    Args:
        service_name: Name of the service to show logs for. Shows all if not provided.
        loki_url: URL of Loki service (default: http://localhost:3100)
        limit: Number of log lines to fetch (default: 100)
        project_root: Root directory for validation (optional, enables auto-fix)
        auto_validate: Validate and fix monitoring before showing logs (default: True if project_root provided)
    
    Returns:
        Formatted logs from the service with optional validation report
    """
    try:
        logger.info(f"Fetching logs for service: {service_name or 'all'}")
        
        output = ""
        
        # Auto-validate if project_root is provided
        if project_root and (auto_validate if auto_validate is not None else True):
            output += "🔍 **Checking monitoring stack...**\n\n"
            
            # Quick diagnostic check
            diagnostics = diagnose_monitoring_stack(project_root)
            
            if not diagnostics["logs"].get("receiving_logs"):
                output += "⚠️  Loki is not receiving logs. Running automatic fix...\n\n"
                validation_result = validate_and_fix_monitoring(project_root)
                output += validation_result + "\n\n"
                output += "=" * 60 + "\n\n"
            else:
                output += "✅ Monitoring stack is healthy\n\n"
        
        # Build LogQL query
        if service_name:
            query = f'{{container=~".*{service_name}.*"}}'
        else:
            query = '{job="docker"}'
        
        result = fetch_logs_from_loki(
            loki_url or "http://localhost:3100",
            query,
            limit or 100
        )
        
        if result["status"] == "success":
            logs = result["logs"]
            
            if not logs:
                output += f"📋 **Logs for {service_name or 'All Services'}**\n\n"
                output += "⚠️  No logs found in Loki.\n\n"
                output += "**Possible reasons:**\n"
                output += "  - Application containers are not running\n"
                output += "  - Promtail is not collecting logs\n"
                output += "  - Services haven't generated any logs yet\n\n"
                if project_root:
                    output += "💡 Run validate_monitoring to diagnose and fix issues.\n"
                return output
            
            output += f"📋 **Logs for {service_name or 'All Services'}**\n\n"
            output += f"**Total Logs:** {result['count']}\n\n"
            
            for log in logs[:20]:  # Show first 20
                output += f"[{log['timestamp']}] {log['log']}\n"
            
            if result['count'] > 20:
                output += f"\n... and {result['count'] - 20} more logs\n"
            
            return output
        else:
            output += f"❌ Failed to fetch logs: {result['message']}\n\n"
            if project_root:
                output += "💡 Run validate_monitoring to diagnose and fix issues.\n"
            return output
    except Exception as e:
        return f"Error fetching logs: {str(e)}"

# Tool 16: Analyze Logs for Errors
@mcp.tool()
def analyze_logs(
    service_name: Optional[str] = None,
    loki_url: Optional[str] = None,
    limit: Optional[int] = None
) -> str:
    """
    Analyze logs to identify errors, exceptions, and suggest code fixes.
    Uses AI-powered pattern matching to detect common issues and provide solutions.
    
    Args:
        service_name: Name of the service to analyze. Analyzes all if not provided.
        loki_url: URL of Loki service (default: http://localhost:3100)
        limit: Number of log lines to analyze (default: 200)
    
    Returns:
        Analysis report with errors, warnings, and suggested fixes
    """
    try:
        logger.info(f"Analyzing logs for service: {service_name or 'all'}")
        
        # Build LogQL query
        if service_name:
            query = f'{{container=~".*{service_name}.*"}}'
        else:
            query = '{job="docker"}'
        
        # Fetch logs
        result = fetch_logs_from_loki(
            loki_url or "http://localhost:3100",
            query,
            limit or 200
        )
        
        if result["status"] != "success":
            return f"❌ {result['message']}"
        
        # Analyze logs
        analysis = analyze_logs_for_errors(result["logs"])
        
        # Generate suggestions
        suggestions = suggest_fixes_for_errors(analysis)
        
        # Format output
        output = f"🔍 **Log Analysis Report for {service_name or 'All Services'}**\n\n"
        output += "=" * 60 + "\n\n"
        output += f"**Total Logs Analyzed:** {analysis['total_logs']}\n"
        output += f"**Errors Found:** {len(analysis['errors'])}\n"
        output += f"**Warnings Found:** {len(analysis['warnings'])}\n"
        output += f"**Exceptions Found:** {len(analysis['exceptions'])}\n\n"
        
        if suggestions:
            output += "=" * 60 + "\n"
            output += "🔧 **SUGGESTED FIXES**\n"
            output += "=" * 60 + "\n\n"
            
            for idx, suggestion in enumerate(suggestions[:5], 1):  # Show top 5
                output += f"**Issue #{idx}: {suggestion['issue']}**\n\n"
                output += f"**Error Log:**\n```\n{suggestion['error_log'][:200]}...\n```\n\n"
                output += f"**Possible Causes:**\n"
                for cause in suggestion['possible_causes']:
                    output += f"  - {cause}\n"
                output += f"\n**Suggested Fixes:**\n"
                for fix in suggestion['suggested_fixes']:
                    output += f"  ✅ {fix}\n"
                output += "\n" + "-" * 60 + "\n\n"
        
        if analysis['errors']:
            output += "**Recent Errors:**\n"
            for error in analysis['errors'][:5]:
                output += f"  - {error['log'][:150]}...\n"
        
        if not suggestions and not analysis['errors']:
            output += "✅ No errors or issues detected!\n"
        
        return output
    except Exception as e:
        return f"Error analyzing logs: {str(e)}"

# Tool 17: Open Grafana Dashboard
@mcp.tool()
def open_grafana(grafana_url: Optional[str] = None) -> str:
    """
    Open Grafana dashboard in the default browser.
    
    Args:
        grafana_url: URL of Grafana (default: http://localhost:3001)
    
    Returns:
        Status message
    """
    try:
        result = launch_grafana_dashboard(grafana_url or "http://localhost:3001")
        return result
    except Exception as e:
        return f"Error opening Grafana: {str(e)}"

# Tool 18: Complete Workflow - Dockerize and Monitor
@mcp.tool()
def dockerize_and_monitor(project_root: str, services: Optional[str] = None) -> str:
    """
    Complete workflow: Dockerize application, setup monitoring, and open Grafana dashboard.
    ONE-COMMAND SOLUTION: Does everything - dockerizes your app and shows logs in Grafana!
    
    Args:
        project_root: Root directory of the project
        services: Comma-separated list of service names (e.g., backend,frontend). Auto-detected if not provided.
    
    Returns:
        Complete report with Grafana URL and next steps
    """
    try:
        logger.info(f"Starting complete dockerization and monitoring for {project_root}")
        
        output = "🚀 **Complete Dockerization and Monitoring**\n\n"
        output += "=" * 60 + "\n\n"
        
        # Step 1: Dockerize project
        output += "**STEP 1: Dockerizing Project...**\n\n"
        dockerize_result = dockerize_full_project(project_root)
        output += dockerize_result + "\n\n"
        
        # Step 2: Setup monitoring
        output += "=" * 60 + "\n"
        output += "**STEP 2: Setting up Monitoring Stack...**\n\n"
        
        # Parse services or auto-detect
        if services:
            service_list = [s.strip() for s in services.split(',')]
        else:
            from docker_tools.multi_service_handler import detect_services
            detected = detect_services(project_root)
            service_list = list(detected.keys()) if detected else ["app"]
        
        monitoring_result = setup_complete_monitoring(project_root, service_list)
        output += monitoring_result + "\n\n"
        
        # Step 3: Validate monitoring stack
        output += "=" * 60 + "\n"
        output += "**STEP 3: Validating Monitoring Stack...**\n\n"
        validation_result = validate_and_fix_monitoring(project_root)
        output += validation_result + "\n\n"
        
        # Step 4: Launch Grafana
        output += "=" * 60 + "\n"
        output += "**STEP 4: Launching Grafana Dashboard...**\n\n"
        launch_result = launch_grafana_dashboard("http://localhost:3001")
        output += launch_result + "\n\n"
        
        output += "=" * 60 + "\n"
        output += "✅ **COMPLETE! Your application is dockerized and monitored!**\n"
        output += "=" * 60 + "\n"
        
        return output
    except Exception as e:
        return f"Error in complete workflow: {str(e)}"

# Tool 19: Validate Monitoring Stack
@mcp.tool()
def validate_monitoring(project_root: str) -> str:
    """
    Validate that Loki is receiving logs from Promtail and automatically fix common issues.
    Use this when you want to check if monitoring is working correctly.
    
    Args:
        project_root: Root directory of the project
    
    Returns:
        Detailed validation report with diagnostics and fixes applied
    """
    try:
        logger.info(f"Validating monitoring stack for {project_root}")
        result = validate_and_fix_monitoring(project_root)
        return result
    except Exception as e:
        return f"Error validating monitoring: {str(e)}"

# Tool 20: Smart Dockerize and Show Logs (Intelligent Workflow)
@mcp.tool()
def show_app_logs(project_root: str, auto_fix: Optional[bool] = None) -> str:
    """
    🎯 PRIMARY TOOL: Intelligent end-to-end workflow for "show me the logs" requests.
    
    This tool does EVERYTHING automatically:
    1. Analyzes your application structure
    2. Checks if containers are running (starts them if needed)
    3. Sets up monitoring (Grafana + Loki + Promtail) if not already configured
    4. Validates that Loki is receiving logs from Promtail
    5. Auto-fixes common issues (config, connections, service restarts)
    6. Launches Grafana dashboard in your browser
    7. Verifies logs are actually visible and shows samples
    
    USE THIS WHEN USER SAYS:
    - "dockerize my application and show me the logs in grafana dashboard"
    - "show me the logs of this application"
    - "show logs in grafana"
    - "monitor my application"
    - Any similar request about viewing application logs
    
    Args:
        project_root: Root directory of the project/application
        auto_fix: Automatically fix issues if found (default: True)
    
    Returns:
        Comprehensive report with all steps, status, and final results
    """
    try:
        logger.info(f"Running smart dockerize and show logs for {project_root}")
        result = smart_dockerize_and_show_logs(
            project_root,
            auto_fix if auto_fix is not None else True
        )
        return result
    except Exception as e:
        return f"Error in smart workflow: {str(e)}"

def main():
    """Main entry point for the MCP server"""
    # Run MCP server with stdio transport (works with Claude Desktop, etc.)
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
