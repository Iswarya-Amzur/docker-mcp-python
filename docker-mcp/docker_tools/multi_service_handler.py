import os
import json
from .analyzer import analyze_application
from .dockerfile_generator import generate_dockerfile

def detect_services(project_root: str) -> dict:
    """
    Detect all services (backend, frontend, etc.) in a project.
    
    Args:
        project_root: Root directory of the project
        
    Returns:
        Dictionary with detected services and their paths
    """
    services = {}
    
    # Common service directory names
    service_dirs = ['backend', 'frontend', 'api', 'client', 'server', 'web', 'app']
    
    # Check immediate subdirectories
    if os.path.exists(project_root):
        for item in os.listdir(project_root):
            item_path = os.path.join(project_root, item)
            if os.path.isdir(item_path) and item.lower() in service_dirs:
                # Analyze this directory
                analysis = analyze_application(item_path)
                if analysis['app_type'] and analysis['app_type'] != 'unknown':
                    services[item] = {
                        'path': item_path,
                        'type': analysis['app_type'],
                        'analysis': analysis
                    }
    
    return services


def generate_dockerfiles_for_services(services: dict) -> dict:
    """
    Generate Dockerfiles for all detected services.
    
    Args:
        services: Dictionary of services from detect_services()
        
    Returns:
        Dictionary with service names and their Dockerfile content
    """
    dockerfiles = {}
    
    for service_name, service_info in services.items():
        service_path = service_info['path']
        service_type = service_info['type']
        
        # Generate appropriate Dockerfile
        dockerfile_content = generate_dockerfile(
            service_path,
            app_type=service_type,
            python_version="3.11"
        )
        
        # Write Dockerfile to service directory
        dockerfile_path = os.path.join(service_path, 'Dockerfile')
        try:
            with open(dockerfile_path, 'w') as f:
                f.write(dockerfile_content)
            dockerfiles[service_name] = {
                'status': 'success',
                'path': dockerfile_path,
                'content': dockerfile_content
            }
        except Exception as e:
            dockerfiles[service_name] = {
                'status': 'error',
                'error': str(e)
            }
    
    return dockerfiles


def generate_docker_compose(project_root: str, services: dict) -> str:
    """
    Generate a unified docker-compose.yml for all services.
    
    Args:
        project_root: Root directory of the project
        services: Dictionary of services from detect_services()
        
    Returns:
        Docker Compose YAML content
    """
    compose_content = """version: '3.8'

services:
"""
    
    # Define port mappings based on service type
    port_mappings = {
        'backend': 8000,
        'api': 8000,
        'server': 8000,
        'frontend': 3000,
        'client': 3000,
        'web': 3000,
        'app': 3000
    }
    
    for service_name, service_info in services.items():
        service_type = service_info['type']
        container_port = 8000 if service_type == 'python' else 3000
        host_port = port_mappings.get(service_name.lower(), container_port)
        
        # Determine the CMD based on service type
        if service_type == 'python':
            # Check for common Python frameworks
            service_path = service_info['path']
            if os.path.exists(os.path.join(service_path, 'manage.py')):
                # Django
                command = 'python manage.py runserver 0.0.0.0:8000'
            elif os.path.exists(os.path.join(service_path, 'app.py')):
                command = 'python app.py'
            elif os.path.exists(os.path.join(service_path, 'main.py')):
                command = 'python main.py'
            else:
                command = 'python app.py'
        elif service_type == 'node':
            command = 'npm start'
        else:
            command = None
        
        compose_content += f"""  {service_name}:
    build:
      context: ./{service_name}
      dockerfile: Dockerfile
    container_name: {service_name}-container
    ports:
      - "{host_port}:{container_port}"
"""
        
        if command:
            compose_content += f"""    command: {command}
"""
        
        # Add environment variables for backend
        if service_name.lower() in ['backend', 'api', 'server']:
            compose_content += f"""    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/dbname
      - REDIS_URL=redis://redis:6379
      - NODE_ENV=development
"""
        
        # Add frontend environment variables and depends_on
        if service_name.lower() in ['frontend', 'client', 'web']:
            backend_service = None
            for svc in services.keys():
                if svc.lower() in ['backend', 'api', 'server']:
                    backend_service = svc
                    break
            
            if backend_service:
                compose_content += f"""    environment:
      - REACT_APP_API_URL=http://localhost:{port_mappings.get(backend_service.lower(), 8000)}
      - VITE_API_URL=http://localhost:{port_mappings.get(backend_service.lower(), 8000)}
      - NEXT_PUBLIC_API_URL=http://localhost:{port_mappings.get(backend_service.lower(), 8000)}
    depends_on:
      - {backend_service}
"""
        
        compose_content += f"""    volumes:
      - ./{service_name}:/app
      - /app/node_modules
    restart: unless-stopped
    networks:
      - app-network

"""
    
    # Add common services if backend exists
    has_backend = any(s.lower() in ['backend', 'api', 'server'] for s in services.keys())
    if has_backend:
        compose_content += """  # Uncomment below if you need a database
  # db:
  #   image: postgres:15-alpine
  #   container_name: postgres-db
  #   environment:
  #     - POSTGRES_USER=user
  #     - POSTGRES_PASSWORD=password
  #     - POSTGRES_DB=dbname
  #   ports:
  #     - "5432:5432"
  #   volumes:
  #     - postgres_data:/var/lib/postgresql/data
  #   networks:
  #     - app-network

  # redis:
  #   image: redis:7-alpine
  #   container_name: redis-cache
  #   ports:
  #     - "6379:6379"
  #   networks:
  #     - app-network

"""
    
    compose_content += """networks:
  app-network:
    driver: bridge

# Uncomment if using database
# volumes:
#   postgres_data:
"""
    
    # Write docker-compose.yml to project root
    compose_path = os.path.join(project_root, 'docker-compose.yml')
    try:
        with open(compose_path, 'w') as f:
            f.write(compose_content)
    except Exception as e:
        return f"Error writing docker-compose.yml: {str(e)}"
    
    return compose_content


def dockerize_full_project(project_root: str, auto_start: bool = True) -> str:
    """
    Complete workflow: detect services, generate Dockerfiles, create docker-compose.yml,
    and optionally build and start the containers.
    
    Args:
        project_root: Root directory of the project
        auto_start: Automatically build and start containers (default: True)
        
    Returns:
        Summary of all operations
    """
    result = f"🐳 **Dockerizing Project: {project_root}**\n\n"
    
    # Step 1: Detect services
    result += "**Step 1: Detecting Services...**\n"
    services = detect_services(project_root)
    
    if not services:
        return result + "❌ No services detected. Please ensure your project has backend/frontend directories."
    
    result += f"✅ Found {len(services)} service(s):\n"
    for name, info in services.items():
        result += f"  - {name}: {info['type']}\n"
    
    # Step 2: Generate Dockerfiles
    result += "\n**Step 2: Generating Dockerfiles...**\n"
    dockerfiles = generate_dockerfiles_for_services(services)
    
    dockerfile_success = True
    for name, info in dockerfiles.items():
        if info['status'] == 'success':
            result += f"✅ {name}: Dockerfile created at {info['path']}\n"
        else:
            result += f"❌ {name}: {info['error']}\n"
            dockerfile_success = False
    
    # Step 3: Generate docker-compose.yml
    result += "\n**Step 3: Generating docker-compose.yml...**\n"
    compose_content = generate_docker_compose(project_root, services)
    
    if "Error" not in compose_content:
        result += f"✅ docker-compose.yml created at {os.path.join(project_root, 'docker-compose.yml')}\n"
    else:
        result += f"❌ {compose_content}\n"
        dockerfile_success = False
    
    # Step 4: Build and start containers (NEW!)
    if auto_start and dockerfile_success:
        result += "\n**Step 4: Building and Starting Containers...**\n"
        result += "⏳ This may take a few minutes on first build...\n\n"
        
        try:
            # Import here to avoid circular dependency
            from .e2e_tester import start_docker_compose, wait_for_services
            
            # Start docker-compose with build
            start_result = start_docker_compose(project_root, detached=True)
            
            if start_result["status"] == "success":
                result += "✅ Containers built and started successfully!\n\n"
                
                # Wait for services to be ready
                result += "**Step 5: Waiting for Services to be Ready...**\n"
                
                # Determine ports from services
                backend_port = 8000
                frontend_port = 3000
                for name in services.keys():
                    if name.lower() in ['backend', 'api', 'server']:
                        backend_port = 8000
                    elif name.lower() in ['frontend', 'client', 'web']:
                        frontend_port = 3000
                
                wait_result = wait_for_services("localhost", backend_port, frontend_port, timeout=60)
                
                if wait_result["status"] in ["success", "partial"]:
                    result += f"✅ Services are ready!\n"
                    if wait_result.get("services"):
                        for svc, ready in wait_result["services"].items():
                            status = "✅" if ready else "⏳"
                            result += f"   {status} {svc}\n"
                    result += "\n"
                else:
                    result += f"⚠️  Some services may not be fully ready yet\n"
                    result += f"   They might still be starting up...\n\n"
                
                # Show access URLs
                result += "🚀 **Application is Running!**\n"
                result += "="*60 + "\n"
                for name in services.keys():
                    if name.lower() in ['backend', 'api', 'server']:
                        result += f"   🔧 Backend:  http://localhost:{backend_port}\n"
                    elif name.lower() in ['frontend', 'client', 'web']:
                        result += f"   🌐 Frontend: http://localhost:{frontend_port}\n"
                result += "="*60 + "\n\n"
                
                result += "✨ **Next Steps:**\n"
                result += f"   1. Test the application:\n"
                result += f"      test_application_e2e(project_root=\"{project_root}\")\n\n"
                result += f"   2. View logs:\n"
                result += f"      show_app_logs(project_root=\"{project_root}\")\n\n"
                result += f"   3. Open in browser manually:\n"
                result += f"      launch_app_in_browser()\n\n"
                
            else:
                result += f"❌ Failed to start containers\n"
                result += f"   Error: {start_result.get('error', start_result.get('message'))}\n\n"
                result += "🔧 **Manual Steps:**\n"
                result += f"   1. Check docker-compose.yml configuration\n"
                result += f"   2. Try manually: docker-compose up --build\n"
                result += f"   3. Check logs: docker-compose logs\n"
        
        except Exception as e:
            result += f"⚠️  Could not auto-start containers: {str(e)}\n\n"
            result += "🔧 **Manual Steps:**\n"
            result += f"   1. Build and run: docker-compose up --build\n"
            result += f"   2. Then test: test_application_e2e(project_root=\"{project_root}\")\n"
    
    elif not auto_start:
        # Step 4: Manual next steps (original behavior)
        result += "\n**Next Steps:**\n"
        result += f"1. Review the generated Dockerfiles in each service directory\n"
        result += f"2. Update environment variables in docker-compose.yml as needed\n"
        result += f"3. Build and run: `docker-compose up --build`\n"
        result += f"4. Access services:\n"
        
        for name in services.keys():
            if name.lower() in ['backend', 'api', 'server']:
                result += f"   - {name}: http://localhost:8000\n"
            elif name.lower() in ['frontend', 'client', 'web']:
                result += f"   - {name}: http://localhost:3000\n"
    
    return result
