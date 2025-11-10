from fastmcp import FastMCP
import subprocess
import os
import json
import logging
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
    app_type: str = "auto",
    python_version: str = "3.11",
    additional_packages: str = ""
) -> str:
    """
    Generate an optimized Dockerfile for the application.
    
    Args:
        app_path: Path to the application
        app_type: Type of app (python, node, java, static, auto-detect)
        python_version: Python version for Python apps (default: 3.11)
        additional_packages: Additional system packages to install
    
    Returns:
        Generated Dockerfile content
    """
    try:
        logger.info(f"Generating Dockerfile for {app_path}")
        dockerfile_content = generate_dockerfile(
            app_path, 
            app_type, 
            python_version, 
            additional_packages
        )
        return dockerfile_content
    except Exception as e:
        return f"Error generating Dockerfile: {str(e)}"

# Tool 3: Build Docker Image
@mcp.tool()
def build_image(
    app_path: str,
    image_name: str = "my-app",
    tag: str = "latest",
    build_args: str = ""
) -> str:
    """
    Build a Docker image from the application with Dockerfile.
    
    Args:
        app_path: Path to the application directory containing Dockerfile
        image_name: Name for the Docker image
        tag: Tag for the image (e.g., latest, v1.0)
        build_args: Additional build arguments (comma-separated key=value pairs)
    
    Returns:
        Build status and logs
    """
    try:
        logger.info(f"Building Docker image: {image_name}:{tag}")
        result = build_docker_image(app_path, image_name, tag, build_args)
        return result
    except Exception as e:
        return f"Error building image: {str(e)}"

# Tool 4: Run Tests in Container
@mcp.tool()
def test_container(
    image_name: str,
    test_command: str = "pytest",
    container_name: str = "test-container"
) -> str:
    """
    Run tests inside the Docker container to validate the build.
    
    Args:
        image_name: Name of the Docker image to test
        test_command: Command to run tests (e.g., pytest, npm test, mvn test)
        container_name: Name for the test container
    
    Returns:
        Test results and output
    """
    try:
        logger.info(f"Running tests in container: {image_name}")
        results = run_tests_in_container(image_name, test_command, container_name)
        return results
    except Exception as e:
        return f"Error running tests: {str(e)}"

# Tool 5: Fix Containerization Errors
@mcp.tool()
def fix_errors(
    app_path: str,
    error_message: str,
    image_name: str = "my-app",
    suggested_fix: str = ""
) -> str:
    """
    Analyze containerization errors and suggest/apply fixes automatically.
    
    Args:
        app_path: Path to the application
        error_message: The error message from build or test failure
        image_name: Name of the image that failed
        suggested_fix: Optional suggested fix approach
    
    Returns:
        Fixed Dockerfile content and explanation
    """
    try:
        logger.info(f"Analyzing and fixing errors for {image_name}")
        fix_result = fix_containerization_errors(
            app_path, 
            error_message, 
            image_name,
            suggested_fix
        )
        return fix_result
    except Exception as e:
        return f"Error fixing issues: {str(e)}"

# Tool 6: Get Container Logs
@mcp.tool()
def get_container_logs(container_name: str, tail: int = 50) -> str:
    """
    Retrieve logs from a running or stopped container for debugging.
    
    Args:
        container_name: Name of the container
        tail: Number of lines to retrieve (default: 50)
    
    Returns:
        Container logs
    """
    try:
        result = subprocess.run(
            ["docker", "logs", "--tail", str(tail), container_name],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"
    except Exception as e:
        return f"Error retrieving logs: {str(e)}"

if __name__ == "__main__":
    # Run MCP server with stdio transport (works with Claude Desktop, etc.)
    mcp.run(transport="stdio")
