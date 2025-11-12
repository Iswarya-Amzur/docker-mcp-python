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
mcp = FastMCP("Amzur Docker MCP", version="2.0.0")

# ============================================================================
# CORE TOOLS (7 Essential Tools)
# ============================================================================

# Tool 1: Dockerize Complete Project (MAIN TOOL)
@mcp.tool()
def dockerize_project(project_root: str) -> str:
    """
    🎯 PRIMARY DOCKERIZATION TOOL
    
    Automatically dockerize your entire application (single or multi-service).
    Handles EVERYTHING:
    - Detects all services (backend, frontend, API, etc.)
    - Analyzes each service (dependencies, framework, entry points)
    - Generates optimized Dockerfiles for each service
    - Creates docker-compose.yml for orchestration
    - Builds all Docker images
    - Starts all containers
    - Waits for services to be ready
    - Provides URLs to access your application
    
    Works with:
    - Multi-service projects (backend + frontend)
    - Single service applications
    - Python (Flask, Django, FastAPI)
    - Node.js (React, Vue, Express, Next.js)
    - Mixed technology stacks
    
    Args:
        project_root: Root directory of your project
    
    Returns:
        Complete dockerization report with:
        - Detected services
        - Generated files
        - Build status
        - Running container URLs
        
    Example:
        dockerize_project(project_root="C:\\MyApp")
        
        Result: Application fully dockerized, built, and running!
        Access at: http://localhost:3000 (frontend), http://localhost:8000 (backend)
    """
    try:
        logger.info(f"Dockerizing full project at {project_root}")
        result = dockerize_full_project(project_root, auto_start=True)
        return result
    except Exception as e:
        return f"Error dockerizing project: {str(e)}"


# Tool 2: Test Application End-to-End (MAIN TESTING TOOL)
@mcp.tool()
def test_application_e2e(
    project_root: str,
    backend_port: Optional[int] = None,
    frontend_port: Optional[int] = None,
    cleanup: Optional[bool] = None,
    headless: Optional[bool] = None
) -> str:
    """
    🎯 PRIMARY TESTING TOOL
    
    Complete end-to-end testing with REAL browser interactions.
    
    What it does:
    - Checks if containers are running (starts them if needed)
    - Waits for services to be ready
    - Launches VISIBLE browser window (Chromium)
    - Loads your application
    - Performs REAL user interactions:
      * Clicks buttons
      * Fills forms
      * Creates items
      * Navigates pages
      * Submits forms
    - Takes before/after screenshots
    - Validates frontend-backend communication
    - Generates detailed test report
    - Keeps browser open 15 seconds for inspection
    
    Perfect for:
    - Verifying your dockerized app works
    - Visual testing and demos
    - QA validation
    - Troubleshooting UI issues
    
    Args:
        project_root: Root directory with docker-compose.yml
        backend_port: Backend port (default: 8000)
        frontend_port: Frontend port (default: 3000)
        cleanup: Stop containers after test (default: False - keeps running)
        headless: Run browser in headless mode (default: False - shows browser)
    
    Returns:
        Detailed test report with:
        - Test results (passed/failed)
        - All interactions performed
        - Screenshots (before/after)
        - Service URLs
        
    Example:
        test_application_e2e(project_root="C:\\MyApp")
        
        Result: Browser opens, performs interactions, shows detailed report!
    """
    try:
        logger.info(f"Launching and testing application at {project_root}")
        result = launch_and_test(
            project_root,
            backend_port or 8000,
            frontend_port or 3000,
            cleanup if cleanup is not None else False,
            headless if headless is not None else False,
            show_browser=True,  # Always show browser
            use_system_browser=False  # Use Playwright for interactions
        )
        return result
    except Exception as e:
        return f"Error running E2E tests: {str(e)}"


# Tool 3: Show Application Logs in Grafana (MAIN MONITORING TOOL)
@mcp.tool()
def show_app_logs(project_root: str, auto_fix: Optional[bool] = None) -> str:
    """
    🎯 PRIMARY MONITORING TOOL
    
    One-command solution for "show me the logs in Grafana dashboard".
    
    Intelligent workflow that handles EVERYTHING:
    1. Analyzes your application
    2. Checks if containers are running
    3. Starts containers if needed
    4. Sets up Grafana + Loki + Promtail monitoring stack
    5. Validates Loki is receiving logs
    6. Auto-fixes common issues (Docker socket, config, restarts)
    7. Waits for logs to flow (with validation)
    8. Launches Grafana dashboard in browser
    9. Opens directly to logs dashboard (not home page)
    10. Shows sample logs in report
    
    Perfect for:
    - "dockerize and show logs in grafana"
    - "monitor my application"
    - "show me the logs"
    - Debugging and troubleshooting
    - Production monitoring setup
    
    Auto-fixes:
    - Missing Docker socket access
    - Promtail configuration issues
    - Loki connection problems
    - Dashboard provisioning errors
    - Service restart needs
    
    Args:
        project_root: Root directory of your application
        auto_fix: Automatically fix issues (default: True)
    
    Returns:
        Comprehensive report with:
        - Dockerization status
        - Monitoring setup status
        - Validation results
        - Grafana dashboard URL (opens automatically)
        - Sample logs
        - Any fixes applied
        
    Example:
        show_app_logs(project_root="C:\\MyApp")
        
        Result: Application dockerized, monitored, Grafana opens with real logs!
        Access at: http://localhost:3001/d/app-logs/application-logs
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


# Tool 4: Analyze Logs with AI (LOG ANALYSIS TOOL)
@mcp.tool()
def analyze_logs(
    service_name: Optional[str] = None,
    loki_url: Optional[str] = None,
    limit: Optional[int] = None
) -> str:
    """
    Analyze logs using AI to identify errors and suggest fixes.
    
    What it does:
    - Fetches logs from Loki
    - Identifies errors, warnings, exceptions
    - Detects patterns (connection errors, syntax errors, etc.)
    - Provides possible causes
    - Suggests code fixes
    - Prioritizes critical issues
    
    Perfect for:
    - Debugging application errors
    - Finding root causes
    - Getting fix suggestions
    - Log pattern analysis
    
    Args:
        service_name: Service to analyze (e.g., "backend", "frontend"). Shows all if not provided.
        loki_url: Loki URL (default: http://localhost:3100)
        limit: Number of log lines to analyze (default: 200)
    
    Returns:
        Analysis report with:
        - Error count and categories
        - Top issues with fix suggestions
        - Root cause analysis
        - Code fix recommendations
        
    Example:
        analyze_logs(service_name="backend")
        
        Result: Finds "Connection refused to database" error,
                suggests checking DATABASE_URL env variable
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
            
            for idx, suggestion in enumerate(suggestions[:5], 1):
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


# Tool 5: Fix Containerization Errors (ERROR FIXING TOOL)
@mcp.tool()
def fix_errors(
    app_path: str,
    error_message: str,
    image_name: Optional[str] = None,
    suggested_fix: Optional[str] = None
) -> str:
    """
    Analyze containerization errors and auto-fix Dockerfile issues.
    
    What it does:
    - Analyzes build/runtime errors
    - Identifies root cause
    - Suggests fixes
    - Can automatically apply fixes to Dockerfile
    
    Perfect for:
    - Build failures
    - Runtime errors
    - Dependency issues
    - Configuration problems
    
    Common fixes:
    - Missing dependencies
    - Wrong Python/Node version
    - Incorrect paths
    - Port conflicts
    - Permission issues
    
    Args:
        app_path: Path to your application
        error_message: The error from docker build or docker run
        image_name: Docker image name (default: my-app)
        suggested_fix: Optional fix approach
    
    Returns:
        Fixed Dockerfile and explanation
        
    Example:
        fix_errors(
            app_path="C:\\MyApp\\backend",
            error_message="ModuleNotFoundError: No module named 'flask'"
        )
        
        Result: Adds 'flask' to requirements.txt and updates Dockerfile
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


# Tool 6: Create Playwright Test Templates (TEST GENERATION TOOL)
@mcp.tool()
def create_playwright_tests(
    project_root: str,
    backend_url: Optional[str] = None,
    frontend_url: Optional[str] = None
) -> str:
    """
    Generate Playwright test templates for automated testing.
    
    What it does:
    - Creates e2e-tests directory
    - Generates package.json with Playwright
    - Creates playwright.config.js
    - Generates sample test file with:
      * Backend API tests
      * Frontend load tests
      * Button interaction tests
      * Form submission tests
      * Navigation tests
      * Full workflow tests
    
    Perfect for:
    - Setting up automated testing
    - CI/CD integration
    - Regression testing
    - Test-driven development
    
    Args:
        project_root: Root directory of your project
        backend_url: Backend URL (default: http://localhost:8000)
        frontend_url: Frontend URL (default: http://localhost:3000)
    
    Returns:
        Test directory path and setup instructions
        
    Example:
        create_playwright_tests(project_root="C:\\MyApp")
        
        Result: Creates e2e-tests/ with ready-to-run tests
        Run with: cd e2e-tests && npm install && npm test
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
- tests/app.spec.js (Sample E2E tests with 9+ test scenarios)

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

**Generated Tests Include:**
- Backend health check
- Frontend loads successfully
- Frontend-Backend communication
- API endpoints accessibility
- Button interactions
- Input field filling
- Item creation (CRUD)
- Navigation testing
- Form submission
- Complete user workflows
"""
    except Exception as e:
        return f"Error generating Playwright tests: {str(e)}"


# Tool 7: Detect Project Services (INSPECTION TOOL)
@mcp.tool()
def detect_project_services(project_root: str) -> str:
    """
    Detect all services in a multi-service project.
    
    What it does:
    - Scans project directory
    - Identifies all services (backend, frontend, API, client, etc.)
    - Analyzes each service type
    - Determines technology stack
    - Shows dependencies
    
    Perfect for:
    - Understanding project structure
    - Before dockerization
    - Multi-service projects
    - Microservices architecture
    
    Args:
        project_root: Root directory of your project
    
    Returns:
        JSON report with detected services and details
        
    Example:
        detect_project_services(project_root="C:\\MyApp")
        
        Result:
        {
          "backend": {
            "path": "C:\\MyApp\\backend",
            "type": "python",
            "analysis": { ... }
          },
          "frontend": {
            "path": "C:\\MyApp\\frontend",
            "type": "node",
            "analysis": { ... }
          }
        }
    """
    try:
        logger.info(f"Detecting services in {project_root}")
        services = detect_services(project_root)
        return json.dumps(services, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "status": "failed"})


def main():
    """Main entry point for the MCP server"""
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
