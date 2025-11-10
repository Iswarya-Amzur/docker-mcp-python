import re

def fix_containerization_errors(app_path: str, error_message: str,
                                image_name: str = "my-app",
                                suggested_fix: str = "") -> str:
    """Analyze errors and suggest fixes with updated Dockerfile."""
    
    fixes = {}
    
    # Common error patterns and fixes
    error_patterns = {
        r"No such file or directory": {
            "issue": "File path is incorrect or missing",
            "fix": "Check file paths in COPY/ADD commands",
            "action": "Verify all files exist in the build context"
        },
        r"ModuleNotFoundError": {
            "issue": "Python module not found",
            "fix": "Add missing package to requirements.txt",
            "action": "Install package in Dockerfile before copying code"
        },
        r"npm ERR!": {
            "issue": "NPM installation failed",
            "fix": "Check package.json and package-lock.json",
            "action": "Ensure both files are in the directory"
        },
        r"permission denied": {
            "issue": "File permissions issue",
            "fix": "Add proper permission setup in Dockerfile",
            "action": "Use 'chmod' or run as correct user"
        },
        r"Port.*already in use": {
            "issue": "Port binding conflict",
            "fix": "Use different port or stop existing container",
            "action": "Change exposed port in Dockerfile"
        },
        r"out of memory": {
            "issue": "Container ran out of memory",
            "fix": "Increase memory limit or optimize code",
            "action": "Run with: docker run -m 2g <image>"
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
