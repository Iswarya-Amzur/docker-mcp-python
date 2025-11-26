from fastmcp import FastMCP
import subprocess
import os
import json
import logging
from typing import Optional
try:
    from mcp.types import TextContent, ImageContent
except ImportError:
    # Fallback if mcp types not available
    TextContent = dict
    ImageContent = dict
from docker_tools.analyzer import analyze_application
from docker_tools.dockerfile_generator import generate_dockerfile
from docker_tools.docker_builder import build_docker_image
from docker_tools.test_runner import run_tests_in_container
from docker_tools.error_fixer import fix_containerization_errors
from docker_tools.multi_service_handler import dockerize_full_project, detect_services
from docker_tools.e2e_tester_async import (
    launch_and_test_async,
    check_containers_running_async,
    start_docker_compose_async,
    wait_for_services_async,
    test_with_playwright_mcp
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
from docker_tools.comprehensive_workflow_async import (
    comprehensive_dockerize_and_test_async,
    detect_database_services,
    validate_dockerfile
)

import sys

# Configure logging
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP("Amzur Docker MCP", version="2.0.0")

# ============================================================================
# COMPREHENSIVE WORKFLOW TOOL (MAIN ORCHESTRATOR)
# ============================================================================

# Tool 0: Comprehensive Dockerize and Test (ULTIMATE TOOL - ASYNC)
@mcp.tool()
async def dockerize_and_test(
    project_root: str,
    test_e2e: Optional[bool] = True,
    monitor_logs: Optional[bool] = False,
    auto_fix_errors: Optional[bool] = True,
    parallel_builds: Optional[bool] = True,
    max_retries: Optional[int] = 3
) -> dict:
    """
    🎯 ULTIMATE COMPREHENSIVE TOOL - Complete Async Workflow Orchestrator
    
    USE THIS TOOL WHEN:
    - User asks to "dockerize this application and test it"
    - User wants to "dockerize and test"
    - User wants complete workflow (dockerize + test + monitor)
    - User wants end-to-end automation from code to running tests
    
    DO NOT USE THIS TOOL WHEN:
    - User just wants a screenshot (use capture_app_screenshot)
    - User just wants to dockerize (use dockerize_project)
    - User just wants to test existing containers (use test_application_e2e)
    
    This tool handles EVERYTHING automatically using ASYNC Playwright:
    
    1. ✅ Analyzes codebase and detects ALL services (including databases)
    2. ✅ Analyzes dependencies and auto-adds missing packages (NEW)
    3. ✅ Creates/validates Docker files (checks if they exist, validates them)
    4. ✅ Builds containers in parallel with automatic retry (NEW)
    5. ✅ Automatically fixes common errors (Dockerfile, dependencies, ports) (ENHANCED)
    6. ✅ Launches application and waits for health checks
    7. ✅ Performs REAL browser interactions using direct Playwright library
    8. ✅ Captures screenshots during testing (as evidence)
    9. ✅ Tests application end-to-end with actual Playwright automation
    10. ✅ Sets up Grafana monitoring (if requested)
    
    Perfect for:
    - "dockerize this application and test it"
    - "dockerize and show me the logs in grafana"
    - "dockerize, test, and monitor this app"
    - Complete end-to-end workflow automation
    
    Args:
        project_root: Root directory of your project
        test_e2e: Run end-to-end tests with browser interactions (default: True)
        monitor_logs: Set up Grafana monitoring (default: False)
        auto_fix_errors: Automatically fix errors encountered (default: True)
        parallel_builds: Build services in parallel for faster builds (default: True) (NEW)
        max_retries: Maximum retry attempts per service (default: 3) (NEW)
    
    Returns:
        Dict with:
        - report: Formatted text report
        - screenshots: Dict with base64-encoded screenshots
        - services: Detected services
        - databases: Detected databases
        - tests: Test results
        
    Example:
        dockerize_and_test(project_root="C:\\MyApp", test_e2e=True, parallel_builds=True)
        
        Result: Complete workflow with REAL browser interactions and BASE64 screenshots!
    """
    try:
        logger.info(f"Running ENHANCED ASYNC comprehensive workflow for {project_root}")
        result = await comprehensive_dockerize_and_test_async(
            project_root,
            test_e2e=test_e2e if test_e2e is not None else True,
            monitor_logs=monitor_logs if monitor_logs is not None else False,
            auto_fix_errors=auto_fix_errors if auto_fix_errors is not None else True,
            parallel_builds=parallel_builds if parallel_builds is not None else True,
            max_retries=max_retries if max_retries is not None else 3
        )
        
        # Return result directly - Playwright MCP handles screenshot format
        return {
            "status": result.get("status", "success"),
            "report": result.get("report", ""),
            "screenshots": result.get("screenshots", {}),
            "services": result.get("services", {}),
            "databases": result.get("databases", {}),
            "tests": result.get("tests", [])
        }
    except Exception as e:
        logger.error(f"Error in comprehensive workflow: {e}", exc_info=True)
        return {
            "status": "error",
            "report": f"Error in comprehensive workflow: {str(e)}",
            "screenshots": {},
            "services": {},
            "databases": {},
            "tests": []
        }


# ============================================================================
# CORE TOOLS (7 Essential Tools + Enhanced)
# ============================================================================

# Tool 1: Dockerize Complete Project (MAIN TOOL)
@mcp.tool()
def dockerize_project(project_root: str, auto_start: bool = False) -> str:
    """
    🎯 PRIMARY DOCKERIZATION TOOL
    
    Automatically dockerize your entire application (single or multi-service).
    Handles EVERYTHING:
    - Detects all services (backend, frontend, API, etc.)
    - Analyzes each service (dependencies, framework, entry points)
    - Generates optimized Dockerfiles for each service
    - Creates docker-compose.yml for orchestration
    - Optionally builds and starts containers (if auto_start=True)
    
    Works with:
    - Multi-service projects (backend + frontend)
    - Single service applications
    - Python (Flask, Django, FastAPI)
    - Node.js (React, Vue, Express, Next.js)
    - Mixed technology stacks
    
    Args:
        project_root: Root directory of your project
        auto_start: Automatically build and start containers (default: False)
                   Set to True to build and start, False to only generate files
    
    Returns:
        Complete dockerization report with:
        - Detected services
        - Generated files
        - Build status (if auto_start=True)
        - Running container URLs (if auto_start=True)
        
    Example:
        dockerize_project(project_root="C:\\MyApp", auto_start=False)
        
        Result: Dockerfiles and docker-compose.yml generated!
        To start: docker-compose up --build
    """
    try:
        logger.info(f"Dockerizing full project at {project_root} (auto_start={auto_start})")
        result = dockerize_full_project(project_root, auto_start=auto_start)
        return result
    except Exception as e:
        return f"Error dockerizing project: {str(e)}"


# Tool 2: Test Application End-to-End (MAIN TESTING TOOL)
@mcp.tool()
async def test_application_e2e(
    project_root: str,
    backend_port: Optional[int] = None,
    frontend_port: Optional[int] = None,
    cleanup: Optional[bool] = None,
    headless: Optional[bool] = None
) -> dict:
    """
    🎯 PRIMARY TESTING TOOL - Direct Playwright Browser Automation
    
    Complete end-to-end TESTING using direct Playwright library (Async API).
    This tool TESTS your application by performing user interactions.
    
    USE THIS TOOL WHEN:
    - User asks to "test the application"
    - User wants to "run E2E tests"
    - User wants to "verify the app works"
    - User wants to "test with interactions"
    - User wants automated testing with clicks, form fills, etc.
    
    DO NOT USE THIS TOOL WHEN:
    - User just wants a screenshot (use capture_app_screenshot instead)
    - User just wants to "see" the app without testing
    - User asks to "launch and take screenshot" (use capture_app_screenshot)
    
    What it does:
    - Checks if containers are running (starts them if needed)
    - **DETECTS PORTS AUTOMATICALLY** from your code if not specified
    - Waits for services to be ready
    - Launches VISIBLE browser window (Chromium) with Playwright Async API
    - Loads your application
    - Performs REAL user interactions:
      * Clicks buttons
      * Fills forms
      * Creates items
      * Navigates pages
      * Submits forms
    - Captures screenshots during testing (as evidence)
    - Validates frontend-backend communication
    - Generates detailed test report
    - Keeps browser open 15 seconds for inspection
    
    Perfect for:
    - TESTING your dockerized app functionality
    - Automated QA validation
    - E2E test automation
    - Troubleshooting functional issues
    
    Args:
        project_root: Root directory with docker-compose.yml
        backend_port: Backend port (auto-detected if not provided)
        frontend_port: Frontend port (auto-detected if not provided)
        cleanup: Stop containers after test (default: False - keeps running)
        headless: Run browser in headless mode (default: False - shows browser)
    
    Returns:
        Dict with:
        - steps: List of workflow steps
        - tests: Test results
        - screenshots: Base64-encoded screenshots
        - test_summary: Passed/failed counts
        
    Example:
        test_application_e2e(project_root="C:\\MyApp")
        
        Result: Browser opens, performs REAL interactions, returns BASE64 screenshots!
    """
    try:
        logger.info(f"Launching and testing application at {project_root} (ASYNC)")
        
        # Auto-detect ports if not provided
        if backend_port is None or frontend_port is None:
            logger.info("🔍 Auto-detecting ports from project services...")
            try:
                # First check docker-compose.yml for running container ports
                detected_backend = backend_port
                detected_frontend = frontend_port
                
                compose_file = os.path.join(project_root, 'docker-compose.yml')
                if os.path.exists(compose_file):
                    try:
                        import yaml
                        with open(compose_file, 'r') as f:
                            compose_data = yaml.safe_load(f)
                            if compose_data and 'services' in compose_data:
                                for svc_name, svc_config in compose_data['services'].items():
                                    ports = svc_config.get('ports', [])
                                    for port_mapping in ports:
                                        if isinstance(port_mapping, str):
                                            # Format: "5173:5173" or "5173:80"
                                            host_port = port_mapping.split(':')[0]
                                            try:
                                                host_port_num = int(host_port)
                                                logger.info(f"   Found port {host_port_num} in docker-compose for '{svc_name}'")
                                                
                                                if 'frontend' in svc_name.lower() or 'client' in svc_name.lower() or 'web' in svc_name.lower():
                                                    if detected_frontend is None:
                                                        detected_frontend = host_port_num
                                                        logger.info(f"   ✅ Using port {host_port_num} for frontend from docker-compose")
                                                elif 'backend' in svc_name.lower() or 'api' in svc_name.lower() or 'server' in svc_name.lower():
                                                    if detected_backend is None:
                                                        detected_backend = host_port_num
                                                        logger.info(f"   ✅ Using port {host_port_num} for backend from docker-compose")
                                            except ValueError:
                                                pass
                    except Exception as e:
                        logger.warning(f"Could not parse docker-compose.yml: {e}")
                
                # Then check service analysis if still not found
                detection_result = detect_services(project_root)
                services = detection_result.get('application_services', {})
                
                if detected_backend is None:
                    detected_backend = 8000
                if detected_frontend is None:
                    detected_frontend = 3000
                
                for name, service_info in services.items():
                    analysis = service_info.get('analysis', {})
                    detected_port = analysis.get('port') or service_info.get('port')
                    
                    if detected_port:
                        logger.info(f"   Found port {detected_port} for service '{name}'")
                        
                        # Categorize services
                        if name.lower() in ['backend', 'api', 'server'] or 'backend' in name.lower():
                            if backend_port is None:
                                detected_backend = detected_port
                                logger.info(f"   ✅ Using port {detected_port} for backend")
                        elif name.lower() in ['frontend', 'client', 'web', 'ui'] or 'frontend' in name.lower():
                            if frontend_port is None:
                                detected_frontend = detected_port
                                logger.info(f"   ✅ Using port {detected_port} for frontend")
                        elif len(services) == 1:
                            # Single service app
                            app_type = service_info.get('language', '').lower()
                            if app_type in ['node', 'javascript', 'typescript']:
                                if frontend_port is None:
                                    detected_frontend = detected_port
                                    logger.info(f"   ✅ Using port {detected_port} for frontend (Node.js)")
                            else:
                                if backend_port is None:
                                    detected_backend = detected_port
                                    logger.info(f"   ✅ Using port {detected_port} for backend")
                
                # Use detected ports (docker-compose takes priority, already set above)
                backend_port = detected_backend
                frontend_port = detected_frontend
                
                logger.info(f"🌐 Final detected ports: backend={backend_port}, frontend={frontend_port}")
                
            except Exception as e:
                logger.warning(f"⚠️ Port detection failed, using defaults: {e}")
                backend_port = backend_port or 8000
                frontend_port = frontend_port or 3000
        
        # Use our Playwright integration (works like Playwright MCP)
        result = await launch_and_test_async(
            project_root,
            backend_port,
            frontend_port,
            cleanup if cleanup is not None else False,
            headless if headless is not None else False,
            show_browser=True
        )
        
        # Format result for chat display with inline screenshots
        formatted_output = "🚀 **Intelligent E2E Test Results** (Playwright MCP Style)\n\n"
        formatted_output += f"🌐 **Testing URLs:**\n"
        formatted_output += f"   - Frontend: http://localhost:{frontend_port}\n"
        formatted_output += f"   - Backend: http://localhost:{backend_port}\n\n"
        
        # Add steps
        if 'steps' in result:
            formatted_output += "**Workflow Steps:**\n"
            for step in result['steps']:
                status_icon = "✅" if step.get('status') == 'success' else "⏳" if step.get('status') == 'running' else "❌"
                formatted_output += f"{status_icon} {step.get('name', 'Step')}\n"
            formatted_output += "\n"
        
        # Add interactions performed
        if 'interactions' in result and result['interactions']:
            formatted_output += "**🤖 Intelligent Actions Performed:**\n"
            for interaction in result['interactions'][:10]:  # Show first 10
                formatted_output += f"   • {interaction}\n"
            if len(result.get('interactions', [])) > 10:
                formatted_output += f"   ... and {len(result['interactions']) - 10} more actions\n"
            formatted_output += "\n"
        
        # Add test summary
        if 'test_summary' in result:
            summary = result['test_summary']
            formatted_output += f"**Test Summary:** {summary.get('passed', 0)}/{summary.get('total', 0)} tests passed\n"
            if summary.get('failed', 0) > 0:
                formatted_output += f"   ⚠️ {summary.get('failed', 0)} tests failed\n"
            formatted_output += "\n"
        
        # Return result directly - Playwright MCP handles screenshot format
        return {
            "status": result.get("status", "success"),
            "report": formatted_output,
            "steps": result.get("steps", []),
            "tests": result.get("tests", []),
            "screenshots": result.get("screenshots", {}),
            "test_summary": result.get("test_summary", {})
        }
    except Exception as e:
        logger.error(f"Error running E2E tests: {e}", exc_info=True)
        return {
            "status": "error",
            "message": f"Error running E2E tests: {str(e)}",
            "steps": [],
            "tests": [],
            "screenshots": {}
        }


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


# Tool 7: Detect Project Services (INSPECTION TOOL - ENHANCED)
@mcp.tool()
def detect_project_services(project_root: str, include_databases: Optional[bool] = True) -> str:
    """
    Detect all services in a multi-service project (ENHANCED with database detection).
    
    What it does:
    - Scans project directory
    - Identifies all services (backend, frontend, API, client, etc.)
    - Detects database services (PostgreSQL, MySQL, MongoDB, Redis, SQLite)
    - Analyzes each service type
    - Determines technology stack
    - Shows dependencies
    
    Perfect for:
    - Understanding project structure
    - Before dockerization
    - Multi-service projects
    - Microservices architecture
    - Database service detection
    
    Args:
        project_root: Root directory of your project
        include_databases: Also detect database services (default: True)
    
    Returns:
        JSON report with detected services and database details
        
    Example:
        detect_project_services(project_root="C:\\MyApp", include_databases=True)
        
        Result:
        {
          "application_services": {
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
          },
          "database_services": {
            "postgresql_db": {
              "type": "postgresql",
              "detected_from": "docker-compose.yml"
            }
          }
        }
    """
    try:
        logger.info(f"Detecting services in {project_root}")
        services = detect_services(project_root)
        result = {"application_services": services}
        
        if include_databases:
            databases = detect_database_services(project_root)
            result["database_services"] = databases
        
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "status": "failed"})


# Tool 8: View Application Logs (NEW)
@mcp.tool()
def view_logs(
    project_root: str,
    service_name: Optional[str] = None,
    tail: Optional[int] = None,
    follow: Optional[bool] = None
) -> str:
    """
    View application logs directly from Docker containers.
    
    What it does:
    - Checks if containers are running
    - Retrieves logs from specified service or all services
    - Shows recent log entries (tail)
    - Can follow logs in real-time (streaming)
    
    Perfect for:
    - Debugging application issues
    - Monitoring application behavior
    - Viewing real-time logs
    - Troubleshooting container problems
    
    Args:
        project_root: Root directory with docker-compose.yml
        service_name: Specific service to view logs for (None = all services)
        tail: Number of recent lines to show (default: 100)
        follow: Stream logs in real-time (default: False)
    
    Returns:
        Formatted log output with:
        - Service name(s)
        - Log entries
        - Timestamps
    
    Example:
        view_logs(project_root="C:\\MyApp", service_name="backend", tail=50)
        
        Result: Shows last 50 lines of backend service logs
    """
    try:
        logger.info(f"Viewing logs for {service_name or 'all services'} in {project_root}")
        result = view_application_logs(
            project_root,
            service_name=service_name,
            tail=tail or 100,
            follow=follow if follow is not None else False
        )
        return result
    except Exception as e:
        return f"Error viewing logs: {str(e)}"


# Tool 9: Capture Screenshot (NEW)
@mcp.tool()
def capture_app_screenshot(
    url: str,
    output_path: Optional[str] = None,
    wait_time: Optional[int] = None
):
    """
    🎯 LAUNCH APPLICATION AND TAKE SCREENSHOT
    
    Simple tool to launch your application in a browser and capture a screenshot.
    Use this when you just want to see what the app looks like, WITHOUT running tests.
    
    What it does:
    - Launches headless browser
    - Navigates to your application URL
    - Waits for page to load
    - Captures full-page screenshot
    - Displays screenshot in chat
    - Saves to specified path
    
    USE THIS TOOL WHEN:
    - User asks to "launch and take screenshot"
    - User asks to "capture screenshot of the application"
    - User wants to see the app visually (no testing needed)
    - User wants to document application appearance
    
    DO NOT USE THIS TOOL WHEN:
    - User wants to RUN TESTS or TEST the application
    - User wants to interact with the app (clicking, filling forms)
    - User wants to verify functionality
    
    Perfect for:
    - Quick visual verification
    - Documenting application state
    - Creating screenshots for reports
    - Showing what the app looks like
    
    Args:
        url: URL to capture
        output_path: Path to save screenshot (default: ./screenshot.png)
        wait_time: Seconds to wait before capturing (default: 3)
    
    Returns:
        Status message with screenshot path
        
    Example:
        capture_app_screenshot(url="http://localhost:5173", output_path="./app.png")
        
        Result: Screenshot saved to ./app.png
    """
    try:
        if not output_path:
            output_path = os.path.join(os.getcwd(), "screenshot.png")
        
        logger.info(f"Capturing screenshot of {url}")
        # Capture with base64 for chat embedding
        result = capture_screenshot(url, output_path, wait_time or 3, return_base64=True)
        
        if result['status'] == 'success':
            screenshot_path = result['path']
            analysis = analyze_screenshot(screenshot_path)
            
            # Build text response
            text_response = f"✅ Screenshot captured successfully!\n\n"
            text_response += f"Path: {screenshot_path}\n"
            text_response += f"URL: {result['url']}\n"
            text_response += f"Analysis: {analysis['analysis']}\n"
            
            # Try to return structured content with text and image
            try:
                content = [
                    TextContent(
                        type="text",
                        text=text_response
                    )
                ]
                
                # Add image content if base64 is available
                if 'base64' in result:
                    content.append(
                        ImageContent(
                            type="image",
                            data=result['base64'],
                            mimeType="image/png"
                        )
                    )
                
                return content
            except:
                # Fallback to simple string if structured content doesn't work
                return text_response
        else:
            return f"❌ Failed to capture screenshot: {result.get('message', 'Unknown error')}"
    except Exception as e:
        return f"Error capturing screenshot: {str(e)}"


# Tool 10: Launch Application and Take Screenshot (COMBINED TOOL)
@mcp.tool()
async def launch_and_screenshot(
    project_root: str,
    frontend_port: Optional[int] = None,
    backend_port: Optional[int] = None
) -> dict:
    """
    🎯 LAUNCH APPLICATION AND TAKE SCREENSHOT
    
    **USE THIS TOOL WHEN:**
    - User asks to "launch the application and take a screenshot"
    - User asks to "start the app and capture screenshot"
    - User wants to "see what the app looks like"
    - User wants to "launch and show me the UI"
    - User wants screenshot WITHOUT running tests
    
    **DO NOT USE THIS TOOL WHEN:**
    - User wants to TEST the application (use test_application_e2e)
    - User wants to DOCKERIZE and test (use dockerize_and_test)
    - Application is already running and you have URL (use capture_app_screenshot)
    
    What this tool does:
    1. Checks if containers are running
    2. Starts containers if needed (with docker-compose)
    3. Auto-detects ports from your code
    4. Waits for application to be ready
    5. Captures full-page screenshot
    6. Returns screenshot for display in chat
    7. Keeps containers running
    
    Perfect for:
    - Quick visual check of dockerized app
    - Showing what the app looks like
    - Documentation screenshots
    - Visual verification without testing
    
    Args:
        project_root: Root directory with docker-compose.yml
        frontend_port: Frontend port (auto-detected if not provided)
        backend_port: Backend port (auto-detected if not provided)
    
    Returns:
        Dict with screenshot and status
        
    Example:
        launch_and_screenshot(project_root="C:\\MyApp")
        
        Result: App starts, screenshot captured and displayed!
    """
    try:
        logger.info(f"Launching application at {project_root} for screenshot")
        
        # Auto-detect ports if not provided
        if frontend_port is None or backend_port is None:
            from docker_tools.port_detector import detect_ports
            detected = detect_ports(project_root)
            frontend_port = frontend_port or detected.get('frontend', 5173)
            backend_port = backend_port or detected.get('backend', 8000)
            logger.info(f"Auto-detected ports - Frontend: {frontend_port}, Backend: {backend_port}")
        
        # Check if containers are running
        status = await check_containers_running_async(project_root)
        
        if not status.get("running"):
            logger.info("Containers not running, starting them...")
            start_result = await start_docker_compose_async(project_root, detached=True)
            if start_result.get("status") != "success":
                return {
                    "status": "error",
                    "message": f"Failed to start containers: {start_result.get('message')}"
                }
            logger.info("Containers started, waiting for services...")
            
            # Wait for services to be ready
            await wait_for_services_async(
                backend_port=backend_port,
                frontend_port=frontend_port,
                timeout=60
            )
        else:
            logger.info(f"Containers already running ({status.get('count')} containers)")
        
        # Capture screenshot
        frontend_url = f"http://localhost:{frontend_port}"
        logger.info(f"Capturing screenshot of {frontend_url}")
        
        # Use the capture_screenshot function
        screenshot_path = os.path.join(project_root, "app_screenshot.png")
        result = capture_screenshot(frontend_url, screenshot_path, wait_time=3, return_base64=True)
        
        if result['status'] == 'success':
            analysis = analyze_screenshot(screenshot_path)
            
            response_text = f"✅ **Application Launched and Screenshot Captured!**\n\n"
            response_text += f"**Frontend URL:** {frontend_url}\n"
            response_text += f"**Screenshot Path:** {screenshot_path}\n"
            response_text += f"**Analysis:** {analysis['analysis']}\n\n"
            response_text += f"**Containers Status:** {status.get('count')} containers running\n"
            response_text += f"**Note:** Containers are still running - access app at {frontend_url}\n"
            
            return {
                "status": "success",
                "message": response_text,
                "screenshot_path": screenshot_path,
                "screenshot_base64": result.get('base64', ''),
                "frontend_url": frontend_url,
                "containers_running": status.get('count', 0),
                "screenshots": {
                    "initial": result.get('data_url', '')
                }
            }
        else:
            return {
                "status": "error",
                "message": f"Screenshot capture failed: {result.get('message')}"
            }
            
    except Exception as e:
        logger.error(f"Error in launch_and_screenshot: {e}", exc_info=True)
        return {
            "status": "error",
            "message": f"Error launching and capturing screenshot: {str(e)}"
        }


# Tool 11: Validate Dockerfile (NEW)
@mcp.tool()
def validate_dockerfile_file(dockerfile_path: str) -> str:
    """
    Validate a Dockerfile for common issues and best practices.
    
    What it does:
    - Checks if Dockerfile exists
    - Validates syntax and structure
    - Identifies security issues
    - Suggests best practices
    - Provides recommendations
    
    Perfect for:
    - Before building images
    - Code review
    - CI/CD pipelines
    - Ensuring Dockerfile quality
    
    Args:
        dockerfile_path: Path to Dockerfile
    
    Returns:
        Validation report with:
        - Validity status
        - Issues found
        - Warnings
        - Recommendations
        
    Example:
        validate_dockerfile_file(dockerfile_path="./backend/Dockerfile")
        
        Result: Detailed validation report with issues and recommendations
    """
    try:
        logger.info(f"Validating Dockerfile at {dockerfile_path}")
        validation = validate_dockerfile(dockerfile_path)
        
        report = f"📋 **Dockerfile Validation Report**\n\n"
        report += f"**File:** {dockerfile_path}\n"
        report += f"**Status:** {'✅ Valid' if validation['valid'] else '❌ Invalid'}\n\n"
        
        if validation['issues']:
            report += "**Issues:**\n"
            for issue in validation['issues']:
                report += f"  ❌ {issue}\n"
            report += "\n"
        
        if validation['warnings']:
            report += "**Warnings:**\n"
            for warning in validation['warnings']:
                report += f"  ⚠️  {warning}\n"
            report += "\n"
        
        if validation['recommendations']:
            report += "**Recommendations:**\n"
            for rec in validation['recommendations']:
                report += f"  💡 {rec}\n"
            report += "\n"
        
        if not validation['issues'] and not validation['warnings']:
            report += "✅ No issues found! Dockerfile looks good.\n"
        
        return report
    except Exception as e:
        return f"Error validating Dockerfile: {str(e)}"


def main():
    """Main entry point for the MCP server"""
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
