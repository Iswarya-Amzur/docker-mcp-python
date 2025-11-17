import re

def fix_containerization_errors(app_path: str, error_message: str,
                                image_name: str = "my-app",
                                suggested_fix: str = "") -> str:
    """Analyze errors and suggest fixes with updated Dockerfile."""
    
    fixes = {}
    
    # Common error patterns and fixes (ENHANCED)
    error_patterns = {
        r"No such file or directory": {
            "issue": "File path is incorrect or missing",
            "fix": "Check file paths in COPY/ADD commands",
            "action": "Verify all files exist in the build context"
        },
        r"ModuleNotFoundError|ImportError": {
            "issue": "Python module not found",
            "fix": "Add missing package to requirements.txt",
            "action": "Install package in Dockerfile before copying code"
        },
        r"npm ERR!|npm ci.*exit code 1|npm.*failed": {
            "issue": "NPM installation failed",
            "fix": "Check package.json, package-lock.json, and network connectivity",
            "action": "1. Ensure package-lock.json exists and is valid, 2. Run 'npm install' locally to fix lockfile, 3. Check for conflicting dependencies"
        },
        r"permission denied": {
            "issue": "File permissions issue",
            "fix": "Add proper permission setup in Dockerfile",
            "action": "Use 'chmod' or run as correct user"
        },
        r"Port.*already in use|address already in use": {
            "issue": "Port binding conflict",
            "fix": "Use different port or stop existing container",
            "action": "Change exposed port in Dockerfile or docker-compose.yml"
        },
        r"out of memory|OOM": {
            "issue": "Container ran out of memory",
            "fix": "Increase memory limit or optimize code",
            "action": "Run with: docker run -m 2g <image> or add mem_limit in docker-compose.yml"
        },
        r"connection.*refused|connection.*timeout": {
            "issue": "Service connection failed",
            "fix": "Check if service is running and ports are correct",
            "action": "Verify docker-compose.yml port mappings and service dependencies"
        },
        r"playwright.*not installed|playwright.*not found": {
            "issue": "Playwright not installed",
            "fix": "Install Playwright and browsers",
            "action": "Run: pip install playwright && playwright install"
        },
        r"grafana.*not.*ready|loki.*not.*ready|promtail.*not.*ready": {
            "issue": "Monitoring service not ready",
            "fix": "Wait for services to start or check configuration",
            "action": "Check docker logs for grafana/loki/promtail and verify docker-compose.monitoring.yml"
        },
        r"no logs.*detected|logs.*not.*flowing": {
            "issue": "Logs not appearing in Grafana",
            "fix": "Check Promtail configuration and Docker socket access",
            "action": "Verify promtail-config.yml and ensure Docker socket is mounted correctly"
        },
        r"screenshot.*failed|capture.*error": {
            "issue": "Screenshot capture failed",
            "fix": "Check Playwright installation and URL accessibility",
            "action": "Verify URL is accessible and Playwright is installed: pip install playwright && playwright install"
        },
        r"docker.*build.*failed|build.*error": {
            "issue": "Docker build failed",
            "fix": "Check Dockerfile syntax and dependencies",
            "action": "Review Dockerfile, check base image, and verify all dependencies are available"
        },
        r"no configuration file provided|configuration.*not found": {
            "issue": "docker-compose.yml file missing",
            "fix": "Generate docker-compose.yml file first",
            "action": "Run dockerize_project() or manually create docker-compose.yml in project root"
        },
        r"npm ci.*exit code 1|npm.*failed.*production": {
            "issue": "NPM ci failed during Docker build",
            "fix": "Fix package-lock.json issues or missing dependencies",
            "action": "1. Delete package-lock.json and run 'npm install' locally, 2. Commit new package-lock.json, 3. Ensure all dependencies are available"
        },
        r"version.*is obsolete|version.*will be ignored": {
            "issue": "Docker Compose version field is obsolete",
            "fix": "Remove version field from docker-compose.yml",
            "action": "Edit docker-compose.yml and remove the 'version:' line at the top"
        },
        r"container.*exited|container.*stopped": {
            "issue": "Container exited unexpectedly",
            "fix": "Check container logs for errors",
            "action": "Run: docker logs <container_name> to see error details"
        },
        r"database.*connection.*failed|database.*error": {
            "issue": "Database connection failed",
            "fix": "Check database service is running and credentials are correct",
            "action": "Verify database container is running and environment variables are set correctly"
        }
    }
    
    detected_issues = []
    for pattern, fix_info in error_patterns.items():
        if re.search(pattern, error_message, re.IGNORECASE):
            detected_issues.append(fix_info)
    
    result = f"""
🔍 **Error Analysis for {image_name}**

**Error Message:**
{error_message}

**Detected Issues:**
"""
    
    for i, issue in enumerate(detected_issues, 1):
        result += f"""
{i}. **Issue**: {issue['issue']}
   **Fix**: {issue['fix']}
   **Action**: {issue['action']}
"""
    
    if suggested_fix:
        result += f"\n**Suggested Fix Applied:**\n{suggested_fix}"
    
    result += """

**Next Steps:**
1. Review the suggestions above
2. Update the Dockerfile accordingly
3. Rebuild the image: `docker build -t my-app:latest .`
4. Test again with: `docker run my-app:latest`
"""
    
    return result
