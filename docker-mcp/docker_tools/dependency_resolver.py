"""Dependency Resolver for Automatic Dependency Management

This module handles:
- Automatic dependency detection from imports
- Version conflict resolution
- Missing dependency auto-addition
- Dependency graph analysis
- Package name mapping (import name -> package name)
"""

import re
import os
import json
import ast
import logging
from typing import Dict, List, Set, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class DependencyResolver:
    """Intelligent dependency detection and resolution."""
    
    # Mapping of import names to PyPI package names
    PYTHON_PACKAGE_MAPPING = {
        "PIL": "Pillow",
        "cv2": "opencv-python",
        "sklearn": "scikit-learn",
        "yaml": "pyyaml",
        "dotenv": "python-dotenv",
        "jwt": "PyJWT",
        "bs4": "beautifulsoup4",
        "psycopg2": "psycopg2-binary",
        "MySQLdb": "mysqlclient",
        "pymongo": "pymongo",
        "redis": "redis",
        "celery": "celery",
        "sqlalchemy": "SQLAlchemy",
        "flask": "Flask",
        "django": "Django",
        "fastapi": "fastapi",
        "tornado": "tornado",
        "aiohttp": "aiohttp",
        "requests": "requests",
        "numpy": "numpy",
        "pandas": "pandas",
        "matplotlib": "matplotlib",
        "scipy": "scipy",
        "tensorflow": "tensorflow",
        "torch": "torch",
        "keras": "keras",
    }
    
    # Common system dependencies for Python packages
    SYSTEM_DEPENDENCIES = {
        "psycopg2": ["libpq-dev"],
        "mysqlclient": ["default-libmysqlclient-dev"],
        "Pillow": ["libjpeg-dev", "zlib1g-dev"],
        "lxml": ["libxml2-dev", "libxslt1-dev"],
        "cryptography": ["libssl-dev", "libffi-dev"],
    }
    
    def __init__(self, project_root: str):
        """Initialize dependency resolver."""
        self.project_root = Path(project_root)
        self.detected_imports: Set[str] = set()
        self.detected_packages: Set[str] = set()
        self.system_deps: Set[str] = set()
        
    def analyze_project(self) -> Dict[str, any]:
        """
        Analyze project and detect all dependencies.
        
        Returns:
            Dict with detected dependencies and recommendations
        """
        result = {
            "python_packages": [],
            "npm_packages": [],
            "system_dependencies": [],
            "missing_in_requirements": [],
            "missing_in_package_json": [],
            "recommendations": []
        }
        
        # Detect Python dependencies
        if self._has_python_code():
            python_deps = self._analyze_python_dependencies()
            result["python_packages"] = python_deps["packages"]
            result["missing_in_requirements"] = python_deps["missing"]
            result["system_dependencies"] = python_deps["system_deps"]
        
        # Detect Node dependencies
        if self._has_node_code():
            node_deps = self._analyze_node_dependencies()
            result["npm_packages"] = node_deps["packages"]
            result["missing_in_package_json"] = node_deps["missing"]
        
        # Generate recommendations
        result["recommendations"] = self._generate_recommendations(result)
        
        return result
    
    def _has_python_code(self) -> bool:
        """Check if project has Python code."""
        return any(self.project_root.rglob("*.py"))
    
    def _has_node_code(self) -> bool:
        """Check if project has Node.js code."""
        return any(self.project_root.rglob("*.js")) or any(self.project_root.rglob("*.ts"))
    
    def _analyze_python_dependencies(self) -> Dict[str, any]:
        """Analyze Python dependencies."""
        # Find all imports
        imports = self._find_python_imports()
        
        # Map to package names
        packages = set()
        system_deps = set()
        
        for imp in imports:
            # Get base module name
            base_module = imp.split('.')[0]
            
            # Skip standard library
            if self._is_stdlib(base_module):
                continue
            
            # Map to package name
            package_name = self.PYTHON_PACKAGE_MAPPING.get(base_module, base_module)
            packages.add(package_name)
            
            # Check for system dependencies
            if package_name in self.SYSTEM_DEPENDENCIES:
                system_deps.update(self.SYSTEM_DEPENDENCIES[package_name])
        
        # Detect framework and ensure production server is included
        framework = self._detect_python_framework(imports)
        if framework:
            server_package = self._get_production_server_for_framework(framework)
            if server_package:
                packages.add(server_package)
        
        # Check what's missing from requirements.txt
        existing_packages = self._read_requirements_txt()
        missing = packages - existing_packages
        
        return {
            "packages": sorted(list(packages)),
            "missing": sorted(list(missing)),
            "system_deps": sorted(list(system_deps)),
            "framework": framework
        }
    
    def _find_python_imports(self) -> Set[str]:
        """Find all Python imports in the project."""
        imports = set()
        
        for py_file in self.project_root.rglob("*.py"):
            # Skip virtual environments and build directories
            if any(part in py_file.parts for part in ['venv', 'env', '.venv', 'build', 'dist', '__pycache__']):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse with AST
                tree = ast.parse(content, filename=str(py_file))
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.add(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            imports.add(node.module)
            
            except Exception as e:
                logger.debug(f"Could not parse {py_file}: {e}")
                # Fallback to regex
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Find import statements
                    import_pattern = r'^\\s*(?:from|import)\\s+([a-zA-Z0-9_]+)'
                    for match in re.finditer(import_pattern, content, re.MULTILINE):
                        imports.add(match.group(1))
                except:
                    pass
        
        return imports
    
    def _detect_python_framework(self, imports: Set[str]) -> Optional[str]:
        """Detect Python web framework from imports."""
        framework_indicators = {
            'fastapi': ['fastapi'],
            'django': ['django'],
            'flask': ['flask'],
            'sanic': ['sanic'],
            'quart': ['quart'],
            'aiohttp': ['aiohttp'],
            'tornado': ['tornado'],
            'starlette': ['starlette']
        }
        
        for framework, indicators in framework_indicators.items():
            for indicator in indicators:
                if indicator in imports or any(imp.startswith(f"{indicator}.") for imp in imports):
                    return framework
        
        return None
    
    def _get_production_server_for_framework(self, framework: str) -> Optional[str]:
        """Get the appropriate production server package for a framework."""
        # ASGI frameworks (async) use uvicorn
        asgi_frameworks = {'fastapi', 'starlette', 'sanic', 'quart', 'aiohttp'}
        # WSGI frameworks (sync) use gunicorn  
        wsgi_frameworks = {'django', 'flask'}
        
        if framework in asgi_frameworks:
            return 'uvicorn'
        elif framework in wsgi_frameworks:
            return 'gunicorn'
        elif framework == 'tornado':
            # Tornado has its own server
            return None
        
        return None
    
    def _is_stdlib(self, module_name: str) -> bool:
        """Check if module is part of Python standard library."""
        stdlib_modules = {
            'abc', 'aifc', 'argparse', 'array', 'ast', 'asynchat', 'asyncio', 'asyncore',
            'atexit', 'audioop', 'base64', 'bdb', 'binascii', 'binhex', 'bisect', 'builtins',
            'bz2', 'calendar', 'cgi', 'cgitb', 'chunk', 'cmath', 'cmd', 'code', 'codecs',
            'codeop', 'collections', 'colorsys', 'compileall', 'concurrent', 'configparser',
            'contextlib', 'contextvars', 'copy', 'copyreg', 'cProfile', 'crypt', 'csv',
            'ctypes', 'curses', 'dataclasses', 'datetime', 'dbm', 'decimal', 'difflib',
            'dis', 'distutils', 'doctest', 'email', 'encodings', 'enum', 'errno', 'faulthandler',
            'fcntl', 'filecmp', 'fileinput', 'fnmatch', 'formatter', 'fractions', 'ftplib',
            'functools', 'gc', 'getopt', 'getpass', 'gettext', 'glob', 'graphlib', 'grp',
            'gzip', 'hashlib', 'heapq', 'hmac', 'html', 'http', 'imaplib', 'imghdr', 'imp',
            'importlib', 'inspect', 'io', 'ipaddress', 'itertools', 'json', 'keyword',
            'lib2to3', 'linecache', 'locale', 'logging', 'lzma', 'mailbox', 'mailcap',
            'marshal', 'math', 'mimetypes', 'mmap', 'modulefinder', 'msilib', 'msvcrt',
            'multiprocessing', 'netrc', 'nis', 'nntplib', 'numbers', 'operator', 'optparse',
            'os', 'ossaudiodev', 'parser', 'pathlib', 'pdb', 'pickle', 'pickletools', 'pipes',
            'pkgutil', 'platform', 'plistlib', 'poplib', 'posix', 'posixpath', 'pprint',
            'profile', 'pstats', 'pty', 'pwd', 'py_compile', 'pyclbr', 'pydoc', 'queue',
            'quopri', 'random', 're', 'readline', 'reprlib', 'resource', 'rlcompleter',
            'runpy', 'sched', 'secrets', 'select', 'selectors', 'shelve', 'shlex', 'shutil',
            'signal', 'site', 'smtpd', 'smtplib', 'sndhdr', 'socket', 'socketserver', 'spwd',
            'sqlite3', 'ssl', 'stat', 'statistics', 'string', 'stringprep', 'struct',
            'subprocess', 'sunau', 'symbol', 'symtable', 'sys', 'sysconfig', 'syslog',
            'tabnanny', 'tarfile', 'telnetlib', 'tempfile', 'termios', 'test', 'textwrap',
            'threading', 'time', 'timeit', 'tkinter', 'token', 'tokenize', 'trace', 'traceback',
            'tracemalloc', 'tty', 'turtle', 'turtledemo', 'types', 'typing', 'unicodedata',
            'unittest', 'urllib', 'uu', 'uuid', 'venv', 'warnings', 'wave', 'weakref',
            'webbrowser', 'winreg', 'winsound', 'wsgiref', 'xdrlib', 'xml', 'xmlrpc', 'zipapp',
            'zipfile', 'zipimport', 'zlib', '_thread'
        }
        return module_name in stdlib_modules
    
    def _read_requirements_txt(self) -> Set[str]:
        """Read existing requirements.txt."""
        req_file = self.project_root / "requirements.txt"
        packages = set()
        
        if req_file.exists():
            try:
                with open(req_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            # Extract package name (before ==, >=, etc.)
                            package = re.split(r'[=<>!]', line)[0].strip()
                            packages.add(package.lower())
            except Exception as e:
                logger.error(f"Error reading requirements.txt: {e}")
        
        return packages
    
    def _analyze_node_dependencies(self) -> Dict[str, any]:
        """Analyze Node.js dependencies."""
        imports = self._find_node_imports()
        
        # Check what's in package.json
        existing_packages = self._read_package_json()
        
        # Find missing
        missing = imports - existing_packages
        
        return {
            "packages": sorted(list(imports)),
            "missing": sorted(list(missing))
        }
    
    def _find_node_imports(self) -> Set[str]:
        """Find all Node.js imports/requires."""
        imports = set()
        
        for js_file in list(self.project_root.rglob("*.js")) + list(self.project_root.rglob("*.ts")):
            # Skip node_modules and build directories
            if any(part in js_file.parts for part in ['node_modules', 'dist', 'build']):
                continue
            
            try:
                with open(js_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Find require() statements
                require_pattern = r"require\\s*\\(\\s*['\"]([^'\"]+)['\"]\\s*\\)"
                for match in re.finditer(require_pattern, content):
                    package = match.group(1)
                    # Skip relative imports
                    if not package.startswith('.'):
                        # Get base package name (before /)
                        base_package = package.split('/')[0]
                        # Handle @scoped packages
                        if base_package.startswith('@'):
                            base_package = '/'.join(package.split('/')[:2])
                        imports.add(base_package)
                
                # Find import statements
                import_pattern = r"import\\s+.*?from\\s+['\"]([^'\"]+)['\"]"
                for match in re.finditer(import_pattern, content):
                    package = match.group(1)
                    if not package.startswith('.'):
                        base_package = package.split('/')[0]
                        if base_package.startswith('@'):
                            base_package = '/'.join(package.split('/')[:2])
                        imports.add(base_package)
            
            except Exception as e:
                logger.debug(f"Could not parse {js_file}: {e}")
        
        return imports
    
    def _read_package_json(self) -> Set[str]:
        """Read existing package.json."""
        pkg_file = self.project_root / "package.json"
        packages = set()
        
        if pkg_file.exists():
            try:
                with open(pkg_file, 'r') as f:
                    data = json.load(f)
                
                # Get all dependencies
                for dep_type in ['dependencies', 'devDependencies']:
                    if dep_type in data:
                        packages.update(data[dep_type].keys())
            
            except Exception as e:
                logger.error(f"Error reading package.json: {e}")
        
        return packages
    
    def _generate_recommendations(self, analysis: Dict) -> List[str]:
        """Generate recommendations based on analysis."""
        recommendations = []
        
        if analysis["missing_in_requirements"]:
            recommendations.append(
                f"Add {len(analysis['missing_in_requirements'])} missing Python packages to requirements.txt: "
                f"{', '.join(analysis['missing_in_requirements'][:5])}"
                + ("..." if len(analysis['missing_in_requirements']) > 5 else "")
            )
        
        if analysis["missing_in_package_json"]:
            recommendations.append(
                f"Add {len(analysis['missing_in_package_json'])} missing npm packages to package.json: "
                f"{', '.join(analysis['missing_in_package_json'][:5])}"
                + ("..." if len(analysis['missing_in_package_json']) > 5 else "")
            )
        
        if analysis["system_dependencies"]:
            recommendations.append(
                f"Install system dependencies in Dockerfile: {', '.join(analysis['system_dependencies'])}"
            )
        
        return recommendations


def analyze_dependencies(project_root: str) -> Dict[str, any]:
    """
    Convenience function to analyze project dependencies.
    
    Args:
        project_root: Root directory of the project
        
    Returns:
        Dependency analysis results
    """
    resolver = DependencyResolver(project_root)
    return resolver.analyze_project()
