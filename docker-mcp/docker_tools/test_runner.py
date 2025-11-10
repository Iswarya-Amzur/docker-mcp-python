import subprocess
import logging

logger = logging.getLogger(__name__)

def run_tests_in_container(image_name: str, test_command: str = "pytest",
                           container_name: str = "test-container") -> str:
    """Run tests inside the Docker container."""
    
    try:
        # Run container with test command
        cmd = [
            "docker", "run",
            "--name", container_name,
            "--rm",
            image_name,
            "sh", "-c", test_command
        ]
        
        logger.info(f"Running tests: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            return f"✅ Tests passed!\n\n{result.stdout}"
        else:
            return f"❌ Tests failed:\n{result.stdout}\n\nErrors:\n{result.stderr}"
    
    except subprocess.TimeoutExpired:
        return "❌ Tests timeout (exceeded 2 minutes)"
    except Exception as e:
        return f"❌ Error running tests: {str(e)}"
