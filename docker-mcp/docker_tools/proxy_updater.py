"""
Proxy Configuration Updater

Updates proxy targets in frontend configuration files to use Docker service names
instead of localhost for proper inter-container communication.
"""

import os
import json
import re
from typing import Dict, List, Optional


def update_proxy_configurations(project_root: str, services: dict) -> dict:
    """
    Update proxy configurations in frontend projects to use Docker service names.
    
    Scans common configuration files and updates localhost references to service names.
    
    Args:
        project_root: Root directory of the project
        services: Dictionary of detected services
        
    Returns:
        Dictionary with update results
    """
    results = {
        'updated_files': [],
        'errors': [],
        'backend_service': None,
        'backend_port': None
    }
    
    # Find backend service name and port
    backend_service = None
    backend_port = 8000
    
    for name, service_info in services.items():
        # Skip None service names
        if not name:
            continue
        if name.lower() in ['backend', 'api', 'server']:
            backend_service = name.lower().replace('_', '-').replace(' ', '-')
            backend_analysis = service_info.get('analysis', {})
            backend_port = backend_analysis.get('port', 8000)
            break
    
    if not backend_service:
        results['errors'].append("No backend service detected - skipping proxy updates")
        return results
    
    results['backend_service'] = backend_service
    results['backend_port'] = backend_port
    
    # Update configurations for each frontend service
    for name, service_info in services.items():
        if name.lower() in ['frontend', 'client', 'web']:
            service_path = service_info.get('path', '')
            
            # Update various config files
            _update_vite_config(service_path, backend_service, backend_port, results)
            _update_package_json_proxy(service_path, backend_service, backend_port, results)
            _update_next_config(service_path, backend_service, backend_port, results)
            _update_webpack_config(service_path, backend_service, backend_port, results)
            _update_setupproxy_js(service_path, backend_service, backend_port, results)
            _update_env_files(service_path, backend_service, backend_port, results)
    
    return results


def _update_vite_config(service_path: str, backend_service: str, backend_port: int, results: dict):
    """Update vite.config.js/ts to use Docker service name."""
    for config_file in ['vite.config.js', 'vite.config.ts']:
        config_path = os.path.join(service_path, config_file)
        if not os.path.exists(config_path):
            continue
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Update proxy target from localhost to service name
            # Pattern: target: 'http://localhost:8000' or target: "http://localhost:8000"
            content = re.sub(
                r"target:\s*['\"]http://localhost:(\d+)['\"]",
                f"target: 'http://{backend_service}:{backend_port}'",
                content
            )
            
            # Pattern: target: 'http://127.0.0.1:8000'
            content = re.sub(
                r"target:\s*['\"]http://127\.0\.0\.1:(\d+)['\"]",
                f"target: 'http://{backend_service}:{backend_port}'",
                content
            )
            
            if content != original_content:
                with open(config_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                results['updated_files'].append(config_path)
        
        except Exception as e:
            results['errors'].append(f"Error updating {config_path}: {str(e)}")


def _update_package_json_proxy(service_path: str, backend_service: str, backend_port: int, results: dict):
    """Update package.json proxy field to use Docker service name."""
    package_path = os.path.join(service_path, 'package.json')
    if not os.path.exists(package_path):
        return
    
    try:
        with open(package_path, 'r', encoding='utf-8') as f:
            package_data = json.load(f)
        
        # Check if proxy field exists
        if 'proxy' in package_data:
            old_proxy = package_data['proxy']
            
            # Update localhost references
            if 'localhost' in old_proxy or '127.0.0.1' in old_proxy:
                package_data['proxy'] = f"http://{backend_service}:{backend_port}"
                
                with open(package_path, 'w', encoding='utf-8') as f:
                    json.dump(package_data, f, indent=2)
                
                results['updated_files'].append(package_path)
    
    except Exception as e:
        results['errors'].append(f"Error updating {package_path}: {str(e)}")


def _update_next_config(service_path: str, backend_service: str, backend_port: int, results: dict):
    """Update next.config.js to use Docker service name."""
    for config_file in ['next.config.js', 'next.config.mjs']:
        config_path = os.path.join(service_path, config_file)
        if not os.path.exists(config_path):
            continue
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Update rewrites destination
            content = re.sub(
                r"destination:\s*['\"]http://localhost:(\d+)",
                f"destination: 'http://{backend_service}:{backend_port}",
                content
            )
            
            content = re.sub(
                r"destination:\s*['\"]http://127\.0\.0\.1:(\d+)",
                f"destination: 'http://{backend_service}:{backend_port}",
                content
            )
            
            if content != original_content:
                with open(config_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                results['updated_files'].append(config_path)
        
        except Exception as e:
            results['errors'].append(f"Error updating {config_path}: {str(e)}")


def _update_webpack_config(service_path: str, backend_service: str, backend_port: int, results: dict):
    """Update webpack config to use Docker service name."""
    for config_file in ['webpack.config.js', 'webpack.dev.js', 'webpack.prod.js']:
        config_path = os.path.join(service_path, config_file)
        if not os.path.exists(config_path):
            continue
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Update proxy target
            content = re.sub(
                r"target:\s*['\"]http://localhost:(\d+)['\"]",
                f"target: 'http://{backend_service}:{backend_port}'",
                content
            )
            
            content = re.sub(
                r"target:\s*['\"]http://127\.0\.0\.1:(\d+)['\"]",
                f"target: 'http://{backend_service}:{backend_port}'",
                content
            )
            
            if content != original_content:
                with open(config_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                results['updated_files'].append(config_path)
        
        except Exception as e:
            results['errors'].append(f"Error updating {config_path}: {str(e)}")


def _update_setupproxy_js(service_path: str, backend_service: str, backend_port: int, results: dict):
    """Update setupProxy.js (Create React App) to use Docker service name."""
    src_path = os.path.join(service_path, 'src')
    if not os.path.exists(src_path):
        return
    
    config_path = os.path.join(src_path, 'setupProxy.js')
    if not os.path.exists(config_path):
        return
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Update proxy target
        content = re.sub(
            r"target:\s*['\"]http://localhost:(\d+)['\"]",
            f"target: 'http://{backend_service}:{backend_port}'",
            content
        )
        
        content = re.sub(
            r"target:\s*['\"]http://127\.0\.0\.1:(\d+)['\"]",
            f"target: 'http://{backend_service}:{backend_port}'",
            content
        )
        
        if content != original_content:
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(content)
            results['updated_files'].append(config_path)
    
    except Exception as e:
        results['errors'].append(f"Error updating {config_path}: {str(e)}")


def _update_env_files(service_path: str, backend_service: str, backend_port: int, results: dict):
    """Update .env files to use Docker service name for API URLs."""
    for env_file in ['.env', '.env.local', '.env.development', '.env.production']:
        env_path = os.path.join(service_path, env_file)
        if not os.path.exists(env_path):
            continue
        
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Update API URL environment variables
            # REACT_APP_API_URL, VITE_API_URL, NEXT_PUBLIC_API_URL
            content = re.sub(
                r"(REACT_APP_API_URL|VITE_API_URL|NEXT_PUBLIC_API_URL|API_URL|BASE_URL)=http://localhost:(\d+)",
                f"\\1=http://{backend_service}:{backend_port}",
                content
            )
            
            content = re.sub(
                r"(REACT_APP_API_URL|VITE_API_URL|NEXT_PUBLIC_API_URL|API_URL|BASE_URL)=http://127\.0\.0\.1:(\d+)",
                f"\\1=http://{backend_service}:{backend_port}",
                content
            )
            
            if content != original_content:
                with open(env_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                results['updated_files'].append(env_path)
        
        except Exception as e:
            results['errors'].append(f"Error updating {env_path}: {str(e)}")
