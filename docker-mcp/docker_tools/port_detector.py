"""
Dynamic Port Detection Utility

Scans application code to detect actual port configurations instead of using hardcoded defaults.
Supports multiple programming languages and frameworks.
"""

import os
import re
import json
from typing import Dict, List, Optional, Set
from pathlib import Path


def detect_ports_in_code(app_path: str, framework: str = None) -> Dict:
    """
    Dynamically detect ports used in application code.
    
    Args:
        app_path: Path to application root
        framework: Optional framework hint to optimize detection
        
    Returns:
        Dict with detected ports and confidence scores
    """
    app_path = Path(app_path)
    detected_ports = {}
    
    # Different strategies based on framework
    if framework:
        framework_lower = framework.lower()
        if framework_lower in ['django']:
            detected_ports.update(_detect_django_ports(app_path))
        elif framework_lower in ['flask']:
            detected_ports.update(_detect_flask_ports(app_path))
        elif framework_lower in ['fastapi']:
            detected_ports.update(_detect_fastapi_ports(app_path))
        elif framework_lower in ['express', 'nestjs', 'node']:
            detected_ports.update(_detect_node_ports(app_path))
        elif framework_lower in ['react', 'vue', 'angular', 'next', 'vite', 'svelte', 'gatsby', 'nuxt']:
            detected_ports.update(_detect_frontend_ports(app_path))
    
    # Generic port detection as fallback
    generic_ports = _detect_generic_ports(app_path)
    detected_ports.update(generic_ports)
    
    # Return the most likely port
    if detected_ports:
        # Sort by confidence score and return highest
        best_port = max(detected_ports.items(), key=lambda x: x[1]['confidence'])
        return {
            'port': best_port[0],
            'confidence': best_port[1]['confidence'],
            'source': best_port[1]['source'],
            'all_detected': detected_ports
        }
    
    return {'port': None, 'confidence': 0, 'source': None, 'all_detected': {}}


def _detect_django_ports(app_path: Path) -> Dict:
    """Detect Django application ports."""
    ports = {}
    
    # Check manage.py and settings files
    patterns = [
        r'runserver[^\d]*(\d+)',
        r'PORT\s*=\s*["\']?(\d+)',
        r'--port[=\s]+(\d+)',
        r'bind.*:(\d+)',
    ]
    
    # Look in manage.py, settings.py, wsgi.py, asgi.py
    files_to_check = ['manage.py', 'settings.py', 'wsgi.py', 'asgi.py', '*/settings.py', '*/wsgi.py']
    
    for file_pattern in files_to_check:
        for file_path in app_path.glob(f'**/{file_pattern}'):
            if file_path.is_file():
                found_ports = _scan_file_for_ports(file_path, patterns)
                for port, confidence in found_ports.items():
                    ports[port] = {
                        'confidence': confidence + 20,  # Django bonus
                        'source': f'Django:{file_path.name}'
                    }
    
    return ports


def _detect_flask_ports(app_path: Path) -> Dict:
    """Detect Flask application ports."""
    ports = {}
    
    patterns = [
        r'app\.run\([^)]*port\s*=\s*(\d+)',
        r'run\([^)]*port\s*=\s*(\d+)',
        r'PORT\s*=\s*["\']?(\d+)',
        r'--port[=\s]+(\d+)',
        r'host\s*=\s*["\'][^"\']*["\'],\s*port\s*=\s*(\d+)',
    ]
    
    # Check main app files
    files_to_check = ['app.py', 'main.py', 'application.py', 'run.py', 'server.py']
    
    for file_name in files_to_check:
        for file_path in app_path.glob(f'**/{file_name}'):
            if file_path.is_file():
                found_ports = _scan_file_for_ports(file_path, patterns)
                for port, confidence in found_ports.items():
                    ports[port] = {
                        'confidence': confidence + 15,  # Flask bonus
                        'source': f'Flask:{file_path.name}'
                    }
    
    return ports


def _detect_fastapi_ports(app_path: Path) -> Dict:
    """Detect FastAPI application ports."""
    ports = {}
    
    patterns = [
        r'uvicorn[^:]*:(\d+)',
        r'--port[=\s]+(\d+)',
        r'port\s*=\s*(\d+)',
        r'host=[^,]*,\s*port=(\d+)',
        r'run\([^)]*port\s*=\s*(\d+)',
    ]
    
    # Check main app files and uvicorn commands
    files_to_check = ['main.py', 'app.py', 'api.py', 'server.py', 'run.py', 'start.py']
    
    for file_name in files_to_check:
        for file_path in app_path.glob(f'**/{file_name}'):
            if file_path.is_file():
                found_ports = _scan_file_for_ports(file_path, patterns)
                for port, confidence in found_ports.items():
                    ports[port] = {
                        'confidence': confidence + 15,  # FastAPI bonus
                        'source': f'FastAPI:{file_path.name}'
                    }
    
    return ports


def _detect_node_ports(app_path: Path) -> Dict:
    """Detect Node.js application ports."""
    ports = {}
    
    # Check package.json first for scripts
    package_json = app_path / 'package.json'
    if package_json.exists():
        try:
            with open(package_json, 'r') as f:
                pkg_data = json.load(f)
                
            # Check scripts for port references
            scripts = pkg_data.get('scripts', {})
            for script_name, script_cmd in scripts.items():
                port_matches = re.findall(r'(?:--port|PORT=|:)[\s=]*(\d+)', script_cmd)
                for port in port_matches:
                    ports[int(port)] = {
                        'confidence': 25,
                        'source': f'package.json:{script_name}'
                    }
        except Exception:
            pass
    
    # Scan JavaScript/TypeScript files
    patterns = [
        r'listen\s*\(\s*(\d+)',
        r'port\s*[=:]\s*(\d+)',
        r'PORT\s*[=:]\s*(\d+)',
        r'process\.env\.PORT\s*\|\|\s*(\d+)',
        r'server\.listen\s*\(\s*(\d+)',
        r'app\.listen\s*\(\s*(\d+)',
    ]
    
    js_files = list(app_path.glob('**/*.js')) + list(app_path.glob('**/*.ts'))
    for file_path in js_files[:20]:  # Limit for performance
        if file_path.is_file() and 'node_modules' not in str(file_path):
            found_ports = _scan_file_for_ports(file_path, patterns)
            for port, confidence in found_ports.items():
                ports[port] = {
                    'confidence': confidence + 10,  # Node bonus
                    'source': f'Node:{file_path.name}'
                }
    
    return ports


def _detect_frontend_ports(app_path: Path) -> Dict:
    """Detect frontend application ports."""
    ports = {}
    
    # Check package.json for dev server configurations
    package_json = app_path / 'package.json'
    if package_json.exists():
        try:
            with open(package_json, 'r') as f:
                pkg_data = json.load(f)
            
            # Check scripts
            scripts = pkg_data.get('scripts', {})
            for script_name, script_cmd in scripts.items():
                if any(cmd in script_cmd for cmd in ['serve', 'dev', 'start', 'ng serve']):
                    port_matches = re.findall(r'(?:--port|PORT=|-p|:)[\s=]*(\d+)', script_cmd)
                    for port in port_matches:
                        ports[int(port)] = {
                            'confidence': 20,
                            'source': f'package.json:{script_name}'
                        }
        except Exception:
            pass
    
    # Check configuration files
    config_files = {
        'vite.config.js': r'port\s*:\s*(\d+)',
        'vite.config.ts': r'port\s*:\s*(\d+)',
        'webpack.config.js': r'port\s*:\s*(\d+)',
        'angular.json': r'"port"\s*:\s*(\d+)',
        'vue.config.js': r'port\s*:\s*(\d+)',
        'next.config.js': r'port\s*:\s*(\d+)',
    }
    
    for config_file, pattern in config_files.items():
        for file_path in app_path.glob(f'**/{config_file}'):
            if file_path.is_file():
                found_ports = _scan_file_for_ports(file_path, [pattern])
                for port, confidence in found_ports.items():
                    ports[port] = {
                        'confidence': confidence + 15,  # Config file bonus
                        'source': f'Config:{file_path.name}'
                    }
    
    return ports


def _detect_env_file_ports(app_path: Path) -> Dict:
    """Detect ports from .env files."""
    ports = {}
    
    # Check for .env files
    env_files = ['.env', '.env.local', '.env.development', '.env.production']
    
    for env_file in env_files:
        env_path = app_path / env_file
        if env_path.exists() and env_path.is_file():
            try:
                with open(env_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        line = line.strip()
                        # Skip comments and empty lines
                        if not line or line.startswith('#'):
                            continue
                        
                        # Match PORT=3000 or VITE_PORT=5173, etc.
                        if '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip().strip('"\'')
                            
                            # Check if key contains 'PORT'
                            if 'PORT' in key.upper() and value.isdigit():
                                port = int(value)
                                if 1000 <= port <= 65535:
                                    ports[port] = {
                                        'confidence': 30,  # High confidence for .env files
                                        'source': f'.env:{key}'
                                    }
            except Exception:
                pass
    
    return ports


def _detect_generic_ports(app_path: Path) -> Dict:
    """Generic port detection across all files."""
    ports = {}
    
    # First, check .env files (highest priority)
    env_ports = _detect_env_file_ports(app_path)
    ports.update(env_ports)
    
    # Common port patterns
    patterns = [
        r'listen\s*\(\s*(\d+)',
        r'bind\s*\([^)]*(\d+)',
        r'port\s*[=:]\s*(\d+)',
        r'PORT\s*[=:]\s*(\d+)',
        r'--port[=\s]+(\d+)',
        r':(\d+)(?:/|$|\s)',  # URLs with ports
    ]
    
    # Check main application files
    file_patterns = ['*.py', '*.js', '*.ts', '*.go', '*.java', '*.rb', '*.php']
    
    for pattern in file_patterns:
        for file_path in app_path.glob(f'**/{pattern}'):
            if (file_path.is_file() and 
                'node_modules' not in str(file_path) and 
                '__pycache__' not in str(file_path) and
                '.git' not in str(file_path)):
                
                found_ports = _scan_file_for_ports(file_path, patterns)
                for port, confidence in found_ports.items():
                    if port not in ports or ports[port]['confidence'] < confidence:
                        ports[port] = {
                            'confidence': confidence,
                            'source': f'Generic:{file_path.name}'
                        }
    
    return ports


def _scan_file_for_ports(file_path: Path, patterns: List[str]) -> Dict:
    """Scan a single file for port patterns."""
    ports = {}
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                try:
                    port = int(match)
                    # Filter out invalid ports
                    if 1024 <= port <= 65535:  # Valid port range
                        confidence = 10
                        
                        # Boost confidence for common development ports
                        if port in [3000, 3001, 4000, 5000, 8000, 8080, 8888, 9000]:
                            confidence += 5
                        
                        # Boost confidence for multiple occurrences
                        occurrences = len(re.findall(rf'\b{port}\b', content))
                        confidence += min(occurrences * 2, 10)
                        
                        ports[port] = confidence
                except ValueError:
                    continue
                    
    except Exception:
        pass
    
    return ports


def get_default_port_for_framework(framework: str) -> int:
    """Get default port for a framework if no port is detected."""
    defaults = {
        'django': 8000,
        'flask': 5000,
        'fastapi': 8000,
        'tornado': 8888,
        'pyramid': 6543,
        'express': 3000,
        'nestjs': 3000,
        'koa': 3000,
        'hapi': 3000,
        'react': 3000,
        'vue': 8080,
        'angular': 4200,
        'svelte': 5000,
        'next': 3000,
        'nuxt': 3000,
        'gatsby': 8000,
        'vite': 5173,  # Vite default dev server port
        'spring-boot': 8080,
        'quarkus': 8080,
        'rails': 3000,
        'laravel': 8000,
        'aspnetcore': 5000,
    }
    
    return defaults.get(framework.lower() if framework else '', 3000)


def detect_port_with_fallback(app_path: str, framework: str = None) -> int:
    """
    Detect port with fallback to framework defaults.
    
    Args:
        app_path: Path to application
        framework: Framework name
        
    Returns:
        Detected or default port number
    """
    detection_result = detect_ports_in_code(app_path, framework)
    
    if detection_result['port'] and detection_result['confidence'] > 5:
        return detection_result['port']
    
    # Fallback to framework default
    return get_default_port_for_framework(framework)