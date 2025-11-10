import os

def generate_dockerfile(app_path: str, app_type: str = "auto", 
                        python_version: str = "3.11", 
                        additional_packages: str = "") -> str:
    """Generate optimized Dockerfile based on app type."""
    
    if app_type == "auto":
        # Auto-detect from previous analysis
        if os.path.exists(os.path.join(app_path, "requirements.txt")):
            app_type = "python"
        elif os.path.exists(os.path.join(app_path, "package.json")):
            app_type = "node"
        else:
            app_type = "python"  # default
    
    dockerfiles = {
        "python": f"""FROM python:{python_version}-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    build-essential \\
    {additional_packages} \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \\
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Run application
CMD ["python", "app.py"]
""",
        
        "node": """FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install --production

# Copy application
COPY . .

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \\
    CMD node -e "require('http').get('http://localhost:3000', (r) => {if (r.statusCode !== 200) throw new Error(r.statusCode)})"

# Start application
CMD ["npm", "start"]
""",
        
        "static": """FROM nginx:alpine

COPY . /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s \\
    CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1
""",
        
        "java": """FROM openjdk:11-jre-slim

WORKDIR /app

COPY target/*.jar app.jar

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s \\
    CMD curl -f http://localhost:8080/health || exit 1

ENTRYPOINT ["java", "-jar", "app.jar"]
"""
    }
    
    return dockerfiles.get(app_type, dockerfiles["python"])
