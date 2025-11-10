import subprocess
import logging
import sys

logger = logging.getLogger(__name__)

def build_docker_image(app_path: str, image_name: str = "my-app", 
                       tag: str = "latest", build_args: str = "") -> str:
    """Build Docker image using docker build command with real-time output."""
    
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
        
        # Use Popen for real-time streaming output
        process = subprocess.Popen(
            cmd,
            cwd=app_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding='utf-8',
            errors='replace',
            bufsize=1
        )
        
        output_lines = []
        # Stream output in real-time
        for line in process.stdout:
            try:
                print(line, end='', flush=True)  # Print to console immediately
            except UnicodeEncodeError:
                pass  # Skip if console can't handle the character
            output_lines.append(line)
        
        process.wait(timeout=300)  # 5 minute timeout
        
        full_output = ''.join(output_lines)
        
        if process.returncode == 0:
            return f"✅ Image built successfully: {image_name}:{tag}\n\n{full_output}"
        else:
            return f"❌ Build failed (exit code: {process.returncode}):\n\n{full_output}"
    
    except subprocess.TimeoutExpired:
        process.kill()
        return "❌ Build timeout (exceeded 5 minutes)"
    except Exception as e:
        return f"❌ Error: {str(e)}"
