import subprocess
import logging

logger = logging.getLogger(__name__)

def build_docker_image(app_path: str, image_name: str = "my-app", 
                       tag: str = "latest", build_args: str = "") -> str:
    """Build Docker image using docker build command."""
    
    try:
        # Parse build args
        args = []
        if build_args:
            for arg in build_args.split(","):
                args.extend(["--build-arg", arg.strip()])
        
        cmd = [
            "docker", "build",
            "-t", f"{image_name}:{tag}",
            *args,
            "."
        ]
        
        logger.info(f"Running: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            cwd=app_path,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            return f"✅ Image built successfully: {image_name}:{tag}\n\n{result.stdout}"
        else:
            return f"❌ Build failed:\n{result.stderr}\n\nSTDOUT:\n{result.stdout}"
    
    except subprocess.TimeoutExpired:
        return "❌ Build timeout (exceeded 5 minutes)"
    except Exception as e:
        return f"❌ Error: {str(e)}"
