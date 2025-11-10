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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP("Docker MCP", version="1.0.0")

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

if __name__ == "__main__":
    # Run MCP server with stdio transport (works with Claude Desktop, etc.)
    mcp.run(transport="stdio")
