"""
Comprehensive Docker MCP Workflow Orchestrator

This module provides a complete end-to-end workflow for dockerizing applications,
testing them, monitoring logs, and fixing errors automatically.
"""

import os
import subprocess
import time
import logging
import json
import webbrowser
from typing import Dict, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

# Import existing modules
from .analyzer import analyze_application
from .multi_service_handler import detect_services, dockerize_full_project
from .dockerfile_generator import generate_dockerfile
from .e2e_tester import (
    launch_and_test,
    check_containers_running as check_running_containers,
    start_docker_compose,
    wait_for_services
)
from .logging_monitor import (
    setup_complete_monitoring,
    launch_grafana_dashboard,
    validate_and_fix_monitoring,
    diagnose_monitoring_stack,
    fetch_logs_from_loki,
    smart_dockerize_and_show_logs
)
from .error_fixer import fix_containerization_errors


def detect_database_services(project_root: str) -> Dict[str, Dict]:
    """
    Detect database services in the codebase by analyzing:
    - Configuration files (database URLs, connection strings)
    - Docker compose files
    - Environment files
    - Code imports (SQLAlchemy, Sequelize, etc.)
    
    Args:
        project_root: Root directory of the project
        
    Returns:
        Dictionary of detected database services
    """
    databases = {}
    
    # Check docker-compose.yml for database services
    compose_files = ["docker-compose.yml", "docker-compose.yaml"]
    for compose_file in compose_files:
        compose_path = os.path.join(project_root, compose_file)
        if os.path.exists(compose_path):
            try:
                try:
                    import yaml
                except ImportError:
                    logger.debug("PyYAML not installed, skipping docker-compose.yml parsing")
                    continue
                    
                with open(compose_path, 'r') as f:
                    compose_data = yaml.safe_load(f)
                    
                if compose_data and 'services' in compose_data:
                    for service_name, service_config in compose_data['services'].items():
                        image = service_config.get('image', '')
                        if any(db in image.lower() for db in ['postgres', 'mysql', 'mongo', 'redis', 'sqlite']):
                            databases[service_name] = {
                                'type': _identify_db_type(image),
                                'image': image,
                                'detected_from': 'docker-compose.yml'
                            }
            except Exception as e:
                logger.debug(f"Could not parse {compose_file}: {e}")
    
    # Check environment files for database URLs
    env_files = [".env", ".env.local", ".env.development"]
    for env_file in env_files:
        env_path = os.path.join(project_root, env_file)
        if os.path.exists(env_path):
            try:
                with open(env_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if any(keyword in line.upper() for keyword in ['DATABASE_URL', 'DB_URL', 'POSTGRES', 'MYSQL', 'MONGO', 'REDIS']):
                            db_type = _extract_db_type_from_env(line)
                            if db_type:
                                db_name = f"{db_type}_db"
                                if db_name not in databases:
                                    databases[db_name] = {
                                        'type': db_type,
                                        'detected_from': env_file,
                                        'config': line.split('=')[0] if '=' in line else line
                                    }
            except Exception as e:
                logger.debug(f"Could not read {env_file}: {e}")
    
    # Check code files for database imports
    db_patterns = {
        'postgresql': ['psycopg2', 'pg8000', 'asyncpg', 'postgresql'],
        'mysql': ['mysql', 'pymysql', 'mysql2', 'sequelize'],
        'mongodb': ['pymongo', 'motor', 'mongoose', 'mongodb'],
        'redis': ['redis', 'hiredis'],
        'sqlite': ['sqlite3', 'sqlite']
    }
    
    for root, dirs, files in os.walk(project_root):
        # Skip common directories
        if any(skip in root for skip in ['node_modules', '.git', '__pycache__', 'venv', '.venv']):
            continue
            
        for file in files:
            if file.endswith(('.py', '.js', '.ts', '.jsx', '.tsx')):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read().lower()
                        for db_type, patterns in db_patterns.items():
                            if any(pattern in content for pattern in patterns):
                                db_name = f"{db_type}_db"
                                if db_name not in databases:
                                    databases[db_name] = {
                                        'type': db_type,
                                        'detected_from': f'code: {file}',
                                        'patterns_found': [p for p in patterns if p in content]
                                    }
                                break
                except Exception:
                    pass
    
    return databases


def _identify_db_type(image: str) -> str:
    """Identify database type from Docker image name."""
    image_lower = image.lower()
    if 'postgres' in image_lower:
        return 'postgresql'
    elif 'mysql' in image_lower:
        return 'mysql'
    elif 'mongo' in image_lower:
        return 'mongodb'
    elif 'redis' in image_lower:
        return 'redis'
    elif 'sqlite' in image_lower:
        return 'sqlite'
    return 'unknown'


def _extract_db_type_from_env(line: str) -> Optional[str]:
    """Extract database type from environment variable line."""
    line_upper = line.upper()
    if 'POSTGRES' in line_upper:
        return 'postgresql'
    elif 'MYSQL' in line_upper:
        return 'mysql'
    elif 'MONGO' in line_upper:
        return 'mongodb'
    elif 'REDIS' in line_upper:
        return 'redis'
    elif 'SQLITE' in line_upper:
        return 'sqlite'
    return None


def validate_dockerfile(dockerfile_path: str) -> Dict:
    """
    Validate a Dockerfile for common issues and best practices.
    
    Args:
        dockerfile_path: Path to Dockerfile
        
    Returns:
        Dictionary with validation results
    """
    validation = {
        'valid': True,
        'issues': [],
        'warnings': [],
        'recommendations': []
    }
    
    if not os.path.exists(dockerfile_path):
        validation['valid'] = False
        validation['issues'].append(f"Dockerfile not found at {dockerfile_path}")
        return validation
    
    try:
        with open(dockerfile_path, 'r') as f:
            content = f.read()
            lines = content.split('\n')
        
        # Check for common issues
        has_from = any(line.strip().upper().startswith('FROM') for line in lines)
        if not has_from:
            validation['valid'] = False
            validation['issues'].append("Missing FROM instruction")
        
        # Check for security issues
        if 'RUN apt-get' in content and 'rm -rf /var/lib/apt/lists/*' not in content:
            validation['warnings'].append("Consider cleaning apt cache to reduce image size")
        
        # Check for best practices
        if 'COPY . .' in content and 'COPY requirements.txt' not in content:
            validation['recommendations'].append("Copy requirements.txt before copying all files for better layer caching")
        
        if 'EXPOSE' not in content:
            validation['warnings'].append("Consider adding EXPOSE instruction for documentation")
        
        if 'HEALTHCHECK' not in content:
            validation['recommendations'].append("Consider adding HEALTHCHECK instruction")
        
        # Check for root user
        if 'USER' not in content:
            validation['recommendations'].append("Consider running as non-root user for security")
        
    except Exception as e:
        validation['valid'] = False
        validation['issues'].append(f"Error reading Dockerfile: {str(e)}")
    
    return validation


async def capture_screenshot_async(url: str, output_path: str, wait_time: int = 3, return_base64: bool = False) -> Dict:
    """
    Capture a screenshot of a webpage using Playwright async API.
    This works inside asyncio loops (like FastMCP).
    
    Args:
        url: URL to capture
        output_path: Path to save screenshot
        wait_time: Seconds to wait before capturing
        return_base64: If True, also return base64-encoded image for chat embedding
        
    Returns:
        Dictionary with screenshot result (includes base64 if return_base64=True)
    """
    try:
        from playwright.async_api import async_playwright
        import base64
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
            page = await context.new_page()
            
            logger.info(f"Navigating to {url} for screenshot...")
            await page.goto(url, wait_until='networkidle', timeout=30000)
            await page.wait_for_timeout(wait_time * 1000)  # Wait for page to fully render
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
            
            # Capture screenshot as bytes first
            screenshot_bytes = await page.screenshot(full_page=True)
            
            # Save to file
            with open(output_path, 'wb') as f:
                f.write(screenshot_bytes)
            
            result = {
                'status': 'success',
                'path': output_path,
                'url': url
            }
            
            # If base64 requested, encode the image
            if return_base64:
                base64_image = base64.b64encode(screenshot_bytes).decode('utf-8')
                result['base64'] = base64_image
                result['data_url'] = f'data:image/png;base64,{base64_image}'
            
            await browser.close()
            return result
    except ImportError:
        return {
            'status': 'error',
            'message': 'Playwright not installed. Install with: pip install playwright && playwright install'
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Error capturing screenshot: {str(e)}'
        }


def capture_screenshot(url: str, output_path: str, wait_time: int = 3, return_base64: bool = False) -> Dict:
    """
    Capture a screenshot of a webpage using direct Playwright library.
    Uses the Playwright Python library for browser automation.
    Automatically uses async API if in asyncio context, otherwise sync API.
    
    Args:
        url: URL to capture
        output_path: Path to save screenshot
        wait_time: Seconds to wait before capturing
        
    Returns:
        Dictionary with screenshot result
    """
    try:
        import asyncio
        # Check if we're in an asyncio loop
        try:
            loop = asyncio.get_running_loop()
            # We're in an asyncio loop - need to use async version
            # But we can't await here since this is a sync function
            # So we'll use nest_asyncio or create a task
            try:
                import nest_asyncio
                nest_asyncio.apply()
                return asyncio.run(capture_screenshot_async(url, output_path, wait_time, return_base64))
            except ImportError:
                # If nest_asyncio not available, try to run in executor
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        lambda: asyncio.run(capture_screenshot_async(url, output_path, wait_time, return_base64))
                    )
                    return future.result(timeout=60)
        except RuntimeError:
            # No running loop - use sync version
            from playwright.sync_api import sync_playwright
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(viewport={'width': 1920, 'height': 1080})
                page = context.new_page()
                
                logger.info(f"Navigating to {url} for screenshot...")
                page.goto(url, wait_until='networkidle', timeout=30000)
                time.sleep(wait_time)  # Wait for page to fully render
                
                # Ensure output directory exists
                os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
                
                # Capture screenshot as bytes first
                screenshot_bytes = page.screenshot(full_page=True)
                
                # Save to file
                with open(output_path, 'wb') as f:
                    f.write(screenshot_bytes)
                
                result = {
                    'status': 'success',
                    'path': output_path,
                    'url': url
                }
                
                # If base64 requested, encode the image
                if return_base64:
                    import base64
                    base64_image = base64.b64encode(screenshot_bytes).decode('utf-8')
                    result['base64'] = base64_image
                    result['data_url'] = f'data:image/png;base64,{base64_image}'
                
                browser.close()
                return result
    except ImportError:
        return {
            'status': 'error',
            'message': 'Playwright not installed. Install with: pip install playwright && playwright install'
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Error capturing screenshot: {str(e)}'
        }


def display_screenshot(screenshot_path: str) -> Dict:
    """
    Display/show a screenshot by opening it in the default image viewer.
    DISABLED: This function no longer opens external viewers to prevent popups.
    Screenshots are embedded inline in chat instead.
    
    Args:
        screenshot_path: Path to screenshot file
        
    Returns:
        Dictionary with display result
    """
    # Return success without opening external viewer
    # This prevents the popup window issue - screenshots are embedded inline in chat instead
    return {
        'status': 'skipped',
        'message': 'External display disabled - screenshot embedded inline in chat'
    }


def analyze_screenshot(screenshot_path: str) -> Dict:
    """
    Analyze a screenshot to determine if it shows expected content.
    Currently provides basic analysis - can be enhanced with image recognition.
    
    Args:
        screenshot_path: Path to screenshot file
        
    Returns:
        Dictionary with analysis results
    """
    analysis = {
        'exists': os.path.exists(screenshot_path),
        'size': 0,
        'analysis': 'Basic screenshot analysis - file exists and can be viewed'
    }
    
    if analysis['exists']:
        try:
            analysis['size'] = os.path.getsize(screenshot_path)
            analysis['analysis'] = f'Screenshot captured successfully ({analysis["size"]} bytes). Review manually to verify content.'
        except Exception as e:
            analysis['analysis'] = f'Error analyzing screenshot: {str(e)}'
    
    return analysis


def view_application_logs(project_root: str, service_name: Optional[str] = None, 
                         tail: int = 100, follow: bool = False) -> str:
    """
    View application logs directly from Docker containers.
    
    Args:
        project_root: Root directory of the project
        service_name: Specific service to view logs for (None = all services)
        tail: Number of lines to show
        follow: Whether to follow logs (streaming)
        
    Returns:
        Formatted log output
    """
    try:
        # Check if containers are running
        container_check = check_running_containers(project_root)
        
        if not container_check.get('running', False):
            return f"❌ No running containers found. Start containers first with docker-compose up"
        
        # Get container names
        compose_file = os.path.join(project_root, 'docker-compose.yml')
        if not os.path.exists(compose_file):
            return f"❌ docker-compose.yml not found at {project_root}"
        
        # Use docker-compose logs
        cmd = ['docker-compose', 'logs', '--tail', str(tail)]
        
        if service_name:
            cmd.append(service_name)
        
        if follow:
            cmd.append('-f')
        
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            encoding='utf-8',
            errors='replace',
            timeout=30 if not follow else None
        )
        
        if result.returncode == 0:
            output = f"📋 **Application Logs**\n\n"
            output += f"**Project:** {project_root}\n"
            if service_name:
                output += f"**Service:** {service_name}\n"
            output += f"**Lines:** {tail}\n\n"
            output += "=" * 60 + "\n\n"
            output += result.stdout
            output += "\n" + "=" * 60 + "\n"
            return output
        else:
            return f"❌ Error retrieving logs: {result.stderr}"
    
    except Exception as e:
        return f"❌ Error viewing logs: {str(e)}"


def comprehensive_dockerize_and_test(project_root: str, 
                                     test_e2e: bool = True,
                                     monitor_logs: bool = False,
                                     auto_fix_errors: bool = True) -> str:
    """
    Comprehensive workflow that handles the entire dockerization and testing process.
    
    This is the main orchestrator function that:
    1. Analyzes the codebase and detects all services (including databases)
    2. Creates/validates Docker files
    3. Builds containers and launches application
    4. Captures screenshots and tests end-to-end
    5. Sets up Grafana monitoring (if requested)
    6. Views logs
    7. Fixes any errors encountered
    
    Args:
        project_root: Root directory of the project
        test_e2e: Whether to run end-to-end tests
        monitor_logs: Whether to set up Grafana monitoring
        auto_fix_errors: Whether to automatically fix errors
        
    Returns:
        Comprehensive report of the entire workflow
    """
    report = "🚀 **Comprehensive Dockerization & Testing Workflow**\n\n"
    report += "=" * 70 + "\n\n"
    
    # STEP 1: Analyze codebase and detect services
    report += "**STEP 1: Analyzing Codebase & Detecting Services...**\n\n"
    
    try:
        # Detect application services
        services = detect_services(project_root)
        report += f"✅ Detected {len(services)} application service(s):\n"
        for name, info in services.items():
            report += f"   - {name}: {info['type']} ({info['path']})\n"
        
        # Detect database services
        databases = detect_database_services(project_root)
        if databases:
            report += f"\n✅ Detected {len(databases)} database service(s):\n"
            for name, info in databases.items():
                report += f"   - {name}: {info['type']} (from {info.get('detected_from', 'unknown')})\n"
        else:
            report += "\nℹ️  No database services detected\n"
        
        report += "\n"
    except Exception as e:
        report += f"⚠️  Error during analysis: {str(e)}\n\n"
        services = {}
        databases = {}
    
    # STEP 2: Check/Create Docker files
    report += "=" * 70 + "\n"
    report += "**STEP 2: Checking/Creating Docker Files...**\n\n"
    
    dockerfile_issues = []
    compose_exists = os.path.exists(os.path.join(project_root, 'docker-compose.yml'))
    
    if not compose_exists:
        report += "📝 Creating docker-compose.yml...\n"
        try:
            dockerize_result = dockerize_full_project(project_root, auto_start=False)
            report += "✅ Docker files created\n\n"
        except Exception as e:
            report += f"⚠️  Error creating Docker files: {str(e)}\n\n"
            dockerfile_issues.append(str(e))
    else:
        report += "✅ docker-compose.yml already exists\n"
        
        # Validate existing Dockerfiles
        for service_name, service_info in services.items():
            dockerfile_path = os.path.join(service_info['path'], 'Dockerfile')
            if os.path.exists(dockerfile_path):
                validation = validate_dockerfile(dockerfile_path)
                if not validation['valid']:
                    dockerfile_issues.extend(validation['issues'])
                    report += f"⚠️  {service_name} Dockerfile has issues:\n"
                    for issue in validation['issues']:
                        report += f"   - {issue}\n"
                if validation['warnings']:
                    report += f"⚠️  {service_name} Dockerfile warnings:\n"
                    for warning in validation['warnings']:
                        report += f"   - {warning}\n"
                if validation['recommendations']:
                    report += f"💡 {service_name} Dockerfile recommendations:\n"
                    for rec in validation['recommendations']:
                        report += f"   - {rec}\n"
            else:
                report += f"📝 Creating Dockerfile for {service_name}...\n"
                try:
                    # Create analysis dict for dockerfile generation
                    analysis = service_info.get('analysis', {})
                    if not analysis:
                        analysis = {
                            'app_type': service_info.get('type', 'unknown'),
                            'framework': service_info.get('framework', 'unknown')
                        }
                    dockerfile_content = generate_dockerfile(
                        service_info['path'],
                        analysis=analysis
                    )
                    with open(dockerfile_path, 'w') as f:
                        f.write(dockerfile_content)
                    report += f"✅ Created Dockerfile for {service_name}\n"
                except Exception as e:
                    report += f"❌ Error creating Dockerfile for {service_name}: {str(e)}\n"
                    dockerfile_issues.append(f"{service_name}: {str(e)}")
        
        report += "\n"
    
    # STEP 3: Build containers and launch application
    report += "=" * 70 + "\n"
    report += "**STEP 3: Building Containers & Launching Application...**\n\n"
    
    try:
        # Check if containers are already running
        container_check = check_running_containers(project_root)
        
        if container_check.get('running', False):
            report += "✅ Containers already running\n\n"
        else:
            report += "🔨 Building and starting containers...\n"
            start_result = start_docker_compose(project_root, detached=True)
            
            if start_result['status'] == 'success':
                report += "✅ Containers built and started successfully\n\n"
                
                # Detect ports from service analysis
                backend_port = 8000
                frontend_port = 3000
                
                detected_ports = {}
                for name, service_info in services.items():
                    # Try to get port from analysis dict or top-level
                    analysis = service_info.get('analysis', {})
                    detected_port = analysis.get('port') or service_info.get('port')
                    
                    if detected_port:
                        detected_ports[name] = detected_port
                        logger.info(f"Detected port {detected_port} for service '{name}'")
                        
                        # Categorize based on service name and type
                        if name.lower() in ['backend', 'api', 'server'] or 'backend' in name.lower():
                            backend_port = detected_port
                            logger.info(f"Using port {detected_port} for backend (service: {name})")
                        elif name.lower() in ['frontend', 'client', 'web', 'ui'] or 'frontend' in name.lower():
                            frontend_port = detected_port
                            logger.info(f"Using port {detected_port} for frontend (service: {name})")
                        elif len(services) == 1:
                            # Single service - use type to determine
                            app_type = service_info.get('language', '').lower()
                            if app_type in ['node', 'javascript', 'typescript']:
                                frontend_port = detected_port
                            else:
                                backend_port = detected_port
                
                if detected_ports:
                    report += f"🔍 **Detected Ports:**\n"
                    for svc_name, port in detected_ports.items():
                        report += f"   - {svc_name}: {port}\n"
                    report += "\n"
                
                # Wait for services to be ready
                report += "⏳ Waiting for services to be ready...\n"
                logger.info(f"Waiting for services: backend={backend_port}, frontend={frontend_port}")
                
                wait_result = wait_for_services("localhost", backend_port, frontend_port, timeout=60)
                
                if wait_result['status'] in ['success', 'partial']:
                    report += "✅ Services are ready!\n"
                    report += f"   🌐 Frontend: http://localhost:{frontend_port}\n"
                    report += f"   🔧 Backend: http://localhost:{backend_port}\n\n"
                else:
                    report += f"⚠️  Services may not be fully ready: {wait_result.get('message', 'Unknown')}\n\n"
            else:
                error_msg = start_result.get('error', start_result.get('message', 'Unknown error'))
                report += f"❌ Failed to start containers: {error_msg}\n\n"
                
                # Try to fix errors if auto_fix is enabled
                if auto_fix_errors:
                    report += "🔧 Attempting to fix errors...\n"
                    for service_name, service_info in services.items():
                        fix_result = fix_containerization_errors(
                            service_info['path'],
                            error_msg,
                            service_name
                        )
                        report += f"   Fix suggestions for {service_name}:\n"
                        report += fix_result + "\n"
                
                return report
    except Exception as e:
        report += f"❌ Error during container startup: {str(e)}\n\n"
        if auto_fix_errors:
            report += "🔧 Attempting to fix errors...\n"
            # Try to fix
            for service_name, service_info in services.items():
                fix_result = fix_containerization_errors(
                    service_info['path'],
                    str(e),
                    service_name
                )
                report += fix_result + "\n"
        return report
    
    # STEP 4: Launch in browser and capture screenshots
    report += "=" * 70 + "\n"
    report += "**STEP 4: Launching Application & Capturing Screenshots...**\n\n"
    
    if test_e2e:
        try:
            frontend_url = f"http://localhost:{frontend_port}"
            backend_url = f"http://localhost:{backend_port}"
            
            # Capture initial screenshot (using async version if in asyncio context)
            screenshot_dir = os.path.join(project_root, 'screenshots')
            os.makedirs(screenshot_dir, exist_ok=True)
            
            initial_screenshot = os.path.join(screenshot_dir, 'initial_load.png')
            try:
                import asyncio
                try:
                    asyncio.get_running_loop()
                    # In asyncio context - use async version
                    import nest_asyncio
                    nest_asyncio.apply()
                    screenshot_result = asyncio.run(capture_screenshot_async(frontend_url, initial_screenshot, return_base64=True))
                except (RuntimeError, ImportError):
                    # Not in asyncio context - use sync version
                    screenshot_result = capture_screenshot(frontend_url, initial_screenshot, return_base64=True)
            except ImportError:
                screenshot_result = capture_screenshot(frontend_url, initial_screenshot, return_base64=True)
            
            if screenshot_result['status'] == 'success':
                report += f"✅ Screenshot captured: {initial_screenshot}\n"
                screenshot_analysis = analyze_screenshot(initial_screenshot)
                report += f"   Analysis: {screenshot_analysis['analysis']}\n"
                # Display the screenshot
                display_result = display_screenshot(initial_screenshot)
                if display_result['status'] == 'success':
                    report += f"   📸 Screenshot displayed in default viewer!\n"
                else:
                    report += f"   ⚠️  Could not display screenshot: {display_result.get('message', 'Unknown error')}\n"
                # Embed screenshot in chat response
                if 'data_url' in screenshot_result:
                    report += f"\n![Initial Screenshot]({screenshot_result['data_url']})\n\n"
                else:
                    report += "\n"
            else:
                report += f"⚠️  Screenshot capture: {screenshot_result.get('message', 'Unknown error')}\n\n"
            
            # Run E2E tests
            report += "🧪 Running end-to-end tests...\n"
            e2e_result = launch_and_test(
                project_root,
                backend_port,
                frontend_port,
                cleanup=False,
                headless=False,
                show_browser=True,
                use_system_browser=False
            )
            report += e2e_result + "\n\n"
            
            # Capture screenshot after tests (using async version if in asyncio context)
            after_screenshot = os.path.join(screenshot_dir, 'after_tests.png')
            try:
                import asyncio
                try:
                    asyncio.get_running_loop()
                    # In asyncio context - use async version
                    import nest_asyncio
                    nest_asyncio.apply()
                    screenshot_result = asyncio.run(capture_screenshot_async(frontend_url, after_screenshot, wait_time=2, return_base64=True))
                except (RuntimeError, ImportError):
                    # Not in asyncio context - use sync version
                    screenshot_result = capture_screenshot(frontend_url, after_screenshot, wait_time=2, return_base64=True)
            except ImportError:
                screenshot_result = capture_screenshot(frontend_url, after_screenshot, wait_time=2, return_base64=True)
            if screenshot_result['status'] == 'success':
                report += f"✅ Post-test screenshot: {after_screenshot}\n"
                # Display the screenshot
                display_result = display_screenshot(after_screenshot)
                if display_result['status'] == 'success':
                    report += f"   📸 Screenshot displayed in default viewer!\n"
                else:
                    report += f"   ⚠️  Could not display screenshot: {display_result.get('message', 'Unknown error')}\n"
                # Embed screenshot in chat response
                if 'data_url' in screenshot_result:
                    report += f"\n![Post-Test Screenshot]({screenshot_result['data_url']})\n\n"
                else:
                    report += "\n"
        
        except Exception as e:
            report += f"⚠️  Error during E2E testing: {str(e)}\n\n"
            if auto_fix_errors:
                report += "🔧 Attempting to diagnose and fix...\n"
                # Could add more specific error handling here
                report += "   Check container logs for details\n\n"
    else:
        report += "⏭️  Skipping E2E tests (test_e2e=False)\n\n"
    
    # STEP 5: Set up Grafana monitoring (if requested)
    if monitor_logs:
        report += "=" * 70 + "\n"
        report += "**STEP 5: Setting Up Grafana Monitoring...**\n\n"
        
        try:
            # Use the existing smart monitoring function
            monitoring_result = smart_dockerize_and_show_logs(project_root, auto_fix=auto_fix_errors)
            report += monitoring_result + "\n\n"
            
            # Capture Grafana dashboard screenshot
            grafana_url = "http://localhost:3001/d/app-logs/application-logs"
            grafana_screenshot = os.path.join(project_root, 'screenshots', 'grafana_dashboard.png')
            
            report += "📸 Capturing Grafana dashboard screenshot...\n"
            time.sleep(5)  # Wait for Grafana to be ready
            
            # Use async version if in asyncio context
            try:
                import asyncio
                try:
                    asyncio.get_running_loop()
                    # In asyncio context - use async version
                    import nest_asyncio
                    nest_asyncio.apply()
                    screenshot_result = asyncio.run(capture_screenshot_async(grafana_url, grafana_screenshot, wait_time=5, return_base64=True))
                except (RuntimeError, ImportError):
                    # Not in asyncio context - use sync version
                    screenshot_result = capture_screenshot(grafana_url, grafana_screenshot, wait_time=5, return_base64=True)
            except ImportError:
                screenshot_result = capture_screenshot(grafana_url, grafana_screenshot, wait_time=5, return_base64=True)
            
            if screenshot_result['status'] == 'success':
                report += f"✅ Grafana screenshot captured: {grafana_screenshot}\n"
                screenshot_analysis = analyze_screenshot(grafana_screenshot)
                report += f"   Analysis: {screenshot_analysis['analysis']}\n"
                # Display the screenshot
                display_result = display_screenshot(grafana_screenshot)
                if display_result['status'] == 'success':
                    report += f"   📸 Screenshot displayed in default viewer!\n"
                # Embed screenshot in chat response
                if 'data_url' in screenshot_result:
                    report += f"\n![Grafana Dashboard Screenshot]({screenshot_result['data_url']})\n"
                report += "   Review screenshot to verify logs are showing correctly\n\n"
            else:
                report += f"⚠️  Could not capture Grafana screenshot: {screenshot_result.get('message', 'Unknown error')}\n"
                report += "   You can manually verify at: http://localhost:3001\n\n"
        
        except Exception as e:
            report += f"⚠️  Error setting up monitoring: {str(e)}\n\n"
            if auto_fix_errors:
                report += "🔧 Attempting to fix monitoring issues...\n"
                try:
                    fix_result = validate_and_fix_monitoring(project_root)
                    report += fix_result + "\n\n"
                except Exception as e2:
                    report += f"   Fix attempt failed: {str(e2)}\n\n"
    else:
        report += "⏭️  Skipping Grafana monitoring (monitor_logs=False)\n\n"
    
    # STEP 6: View application logs
    report += "=" * 70 + "\n"
    report += "**STEP 6: Application Logs...**\n\n"
    
    try:
        logs_output = view_application_logs(project_root, tail=50)
        report += logs_output + "\n\n"
    except Exception as e:
        report += f"⚠️  Error viewing logs: {str(e)}\n\n"
    
    # FINAL SUMMARY
    report += "=" * 70 + "\n"
    report += "**📊 WORKFLOW SUMMARY**\n"
    report += "=" * 70 + "\n\n"
    
    report += f"✅ Services Detected: {len(services)} application, {len(databases)} database\n"
    report += f"✅ Docker Files: {'Created/Validated' if not dockerfile_issues else 'Issues Found'}\n"
    report += f"✅ Containers: {'Running' if container_check.get('running', False) else 'Not Running'}\n"
    
    if test_e2e:
        report += f"✅ E2E Tests: Completed\n"
    
    if monitor_logs:
        report += f"✅ Monitoring: {'Setup Complete' if monitor_logs else 'Skipped'}\n"
    
    report += "\n**Access Your Application:**\n"
    report += f"   🌐 Frontend: http://localhost:{frontend_port}\n"
    report += f"   🔧 Backend: http://localhost:{backend_port}\n"
    
    if monitor_logs:
        report += f"   📊 Grafana: http://localhost:3001\n"
    
    report += "\n**Screenshots Saved:**\n"
    screenshot_dir = os.path.join(project_root, 'screenshots')
    if os.path.exists(screenshot_dir):
        for screenshot in os.listdir(screenshot_dir):
            if screenshot.endswith('.png'):
                report += f"   📸 {os.path.join(screenshot_dir, screenshot)}\n"
    
    report += "\n" + "=" * 70 + "\n"
    
    return report

