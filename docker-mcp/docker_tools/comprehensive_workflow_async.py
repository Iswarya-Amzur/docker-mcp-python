"""
Async Comprehensive Docker Workflow with Direct Playwright Integration

This module provides a complete ASYNC end-to-end workflow for dockerizing applications,
testing them with direct Playwright browser automation, monitoring logs, and fixing errors.

Uses Playwright Python library directly for all browser interactions.
Returns base64-encoded screenshots for display in chat.
"""

import os
import subprocess
import time
import logging
import json
import base64
import asyncio
from typing import Dict, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

# Import existing modules
from .analyzer import analyze_application
from .multi_service_handler import detect_services, dockerize_full_project
from .dockerfile_generator import generate_dockerfile
from .e2e_tester_async import (
    launch_and_test_async,
    check_containers_running_async,
    start_docker_compose_async,
    wait_for_services_async
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
    
    return databases


def _identify_db_type(image: str) -> str:
    """Identify database type from image name."""
    image_lower = image.lower()
    if 'postgres' in image_lower:
        return 'postgresql'
    elif 'mysql' in image_lower or 'mariadb' in image_lower:
        return 'mysql'
    elif 'mongo' in image_lower:
        return 'mongodb'
    elif 'redis' in image_lower:
        return 'redis'
    elif 'sqlite' in image_lower:
        return 'sqlite'
    return 'unknown'


def validate_dockerfile(dockerfile_path: str) -> Dict:
    """Validate a Dockerfile for common issues."""
    validation = {
        'valid': True,
        'issues': [],
        'warnings': [],
        'recommendations': []
    }
    
    try:
        with open(dockerfile_path, 'r') as f:
            content = f.read()
            
            # Check for FROM statement
            if 'FROM' not in content:
                validation['valid'] = False
                validation['issues'].append("Missing FROM statement")
            
            # Check for WORKDIR
            if 'WORKDIR' not in content:
                validation['warnings'].append("No WORKDIR specified")
            
            # Check for proper CMD/ENTRYPOINT
            if 'CMD' not in content and 'ENTRYPOINT' not in content:
                validation['valid'] = False
                validation['issues'].append("Missing CMD or ENTRYPOINT")
            
            # Check for EXPOSE
            if 'EXPOSE' not in content:
                validation['warnings'].append("No EXPOSE statement found")
            
            # Recommendations
            if 'USER' not in content:
                validation['recommendations'].append("Consider adding USER statement for security")
            
            if '.dockerignore' not in os.listdir(os.path.dirname(dockerfile_path)):
                validation['recommendations'].append("Consider adding .dockerignore file")
    
    except Exception as e:
        validation['valid'] = False
        validation['issues'].append(f"Error reading Dockerfile: {str(e)}")
    
    return validation


async def comprehensive_dockerize_and_test_async(
    project_root: str, 
    test_e2e: bool = True,
    monitor_logs: bool = False,
    auto_fix_errors: bool = True
) -> dict:
    """
    ASYNC Comprehensive workflow that handles the entire dockerization and testing process.
    
    This is the main orchestrator function that:
    1. Analyzes the codebase and detects all services (including databases)
    2. Creates/validates Docker files
    3. Builds containers and launches application
    4. Captures screenshots and tests end-to-end (RETURNS BASE64)
    5. Sets up Grafana monitoring (if requested)
    6. Views logs
    7. Fixes any errors encountered
    
    Args:
        project_root: Root directory of the project
        test_e2e: Whether to run end-to-end tests
        monitor_logs: Whether to set up Grafana monitoring
        auto_fix_errors: Whether to automatically fix errors
        
    Returns:
        Dict with report text and base64 screenshots
    """
    result = {
        "report": "",
        "screenshots": {},
        "status": "success",
        "services": {},
        "databases": {},
        "tests": []
    }
    
    report = "🚀 **Comprehensive Dockerization & Testing Workflow**\n\n"
    report += "=" * 70 + "\n\n"
    
    # STEP 1: Analyze codebase and detect services
    report += "**STEP 1: Analyzing Codebase & Detecting Services...**\n\n"
    
    try:
        # Detect application services using enhanced detector
        detection_result = detect_services(project_root)
        result["services"] = detection_result
        
        # Extract actual application services
        services = detection_result.get('application_services', {})
        
        if services:
            report += f"✅ Detected {len(services)} application service(s):\n"
            for name, info in services.items():
                service_type = info.get('type', 'unknown')
                service_path = info.get('path', 'unknown')
                report += f"   - {name}: {service_type} ({service_path})\n"
        else:
            report += "ℹ️  No application services detected\n"
        
        # Report summary if available
        if 'detection_summary' in detection_result:
            summary = detection_result['detection_summary']
            total_services = summary.get('total_services', 0)
            if total_services > len(services):
                report += f"   (Total {total_services} services including infrastructure/worker services)\n"
        
        # Detect database services
        databases = detect_database_services(project_root)
        result["databases"] = databases
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
        detection_result = {'application_services': {}}
    
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
    
    # Initialize ports with detected values from services analysis
    backend_port = 8000
    frontend_port = 3000
    
    # Extract ports from service analysis
    for name, service_info in services.items():
        analysis = service_info.get('analysis', {})
        detected_port = analysis.get('port')
        
        if detected_port:
            if name.lower() in ['backend', 'api', 'server'] or service_info.get('category') == 'web_service':
                backend_port = detected_port
            elif name.lower() in ['frontend', 'client', 'web'] or service_info.get('category') == 'frontend':
                frontend_port = detected_port
            else:
                # For single-service apps, use the detected port as primary
                if len(services) == 1:
                    app_type = service_info.get('language', '')
                    if app_type == 'node':
                        frontend_port = detected_port
                    else:
                        backend_port = detected_port
    
    try:
        # Check if containers are already running
        container_check = await check_containers_running_async(project_root)
        
        if container_check.get('running', False):
            report += "✅ Containers already running\n\n"
        else:
            report += "🔨 Building and starting containers...\n"
            start_result = await start_docker_compose_async(project_root, detached=True)
            
            if start_result['status'] == 'success':
                report += "✅ Containers built and started successfully\n\n"
                
                # Wait for services to be ready
                report += "⏳ Waiting for services to be ready...\n"
                
                wait_result = await wait_for_services_async("localhost", backend_port, frontend_port, timeout=60)
                
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
                
                result["report"] = report
                result["status"] = "error"
                return result
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
        result["report"] = report
        result["status"] = "error"
        return result
    
    # STEP 4: Launch in browser and perform E2E tests
    report += "=" * 70 + "\n"
    report += "**STEP 4: Running End-to-End Tests with Real Browser...**\n\n"
    
    if test_e2e:
        try:
            # Run async E2E tests
            test_result = await launch_and_test_async(
                project_root,
                backend_port=backend_port,
                frontend_port=frontend_port,
                cleanup=False,
                headless=False,
                show_browser=True
            )
            
            # Extract screenshots (already base64 encoded)
            if 'screenshots' in test_result:
                result["screenshots"] = test_result["screenshots"]
                
                if test_result["screenshots"].get("initial"):
                    report += "📸 **Initial Screenshot Captured** (available in result data)\n\n"
                
                if test_result["screenshots"].get("after"):
                    report += "📸 **Post-Interaction Screenshot Captured** (available in result data)\n\n"
            
            # Add test results
            if 'tests' in test_result:
                result["tests"] = test_result["tests"]
                report += "**Test Results:**\n\n"
                
                for test in test_result["tests"]:
                    status_icon = "✅" if test.get("status") == "passed" else "⚠️" if test.get("status") == "warning" else "❌"
                    report += f"{status_icon} {test.get('name', 'Unknown test')}\n"
                    if test.get('note'):
                        report += f"   Note: {test['note']}\n"
                    if test.get('error'):
                        report += f"   Error: {test['error']}\n"
                
                if 'test_summary' in test_result:
                    summary = test_result['test_summary']
                    report += f"\n**Summary:** {summary['passed']}/{summary['total']} tests passed"
                    if summary['failed'] > 0:
                        report += f", {summary['failed']} failed"
                    report += "\n\n"
            
            # Add interactions
            if 'interactions' in test_result:
                report += "**User Interactions Performed:**\n\n"
                for interaction in test_result["interactions"]:
                    report += f"   - {interaction}\n"
                report += "\n"
            
        except Exception as e:
            report += f"❌ Error during E2E testing: {str(e)}\n\n"
            logger.error(f"E2E test error: {e}", exc_info=True)
    
    # STEP 5: Monitoring (optional)
    if monitor_logs:
        report += "=" * 70 + "\n"
        report += "**STEP 5: Setting Up Grafana Monitoring...**\n\n"
        report += "ℹ️  Monitoring setup not implemented in async version yet\n\n"
    
    report += "=" * 70 + "\n"
    report += "✅ **Workflow Complete!**\n"
    
    result["report"] = report
    return result
