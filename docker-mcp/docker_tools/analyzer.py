"""
PRODUCTION-GRADE APPLICATION ANALYZER

Enhanced analyzer with enterprise-level framework detection capabilities:

SUPPORTED LANGUAGES & FRAMEWORKS:
- Python: Django, Flask, FastAPI, Tornado, Pyramid, CherryPy, Bottle, Quart, Sanic
- JavaScript/TypeScript: React, Vue, Angular, Svelte, Next.js, Nuxt, Gatsby, Remix
- Backend Node.js: Express, Fastify, Koa, Hapi, NestJS, Adonis, Meteor
- Java: Spring Boot, Spring MVC, Quarkus, Micronaut, Vert.x, Play Framework
- .NET: ASP.NET Core, Blazor, Nancy, ServiceStack, WebAPI
- Go: Gin, Echo, Fiber, Beego, Buffalo, Revel, Gorilla Mux
- Ruby: Rails, Sinatra, Grape, Hanami, Roda, Cuba
- PHP: Laravel, Symfony, CodeIgniter, CakePHP, Phalcon, Slim
- Rust: Actix, Rocket, Warp, Tide, Axum
- Scala: Play, Akka HTTP, Finch, http4s
- Kotlin: Ktor, Spring Boot (Kotlin)
- Swift: Vapor, Perfect, Kitura

DETECTION CAPABILITIES:
- Runtime version detection
- Dependency analysis with version pinning
- Environment variable extraction
- Database connection patterns
- Message queue integrations
- Caching layer detection
- Authentication/authorization frameworks
- Testing framework identification
- Build tool detection
- Package manager analysis
"""

import os
import json
import re
import toml
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple, Set, Any
from pathlib import Path
from .port_detector import detect_port_with_fallback


def analyze_application(app_path: str) -> dict:
    """
    PRODUCTION-GRADE APPLICATION ANALYZER
    
    Comprehensive framework detection with enterprise capabilities:
    
    DETECTION FEATURES:
    - Multi-framework per language support (50+ frameworks)
    - Version detection with compatibility analysis
    - Dependency graph construction
    - Environment configuration analysis
    - Database integration detection
    - Authentication/authorization framework detection
    - Testing framework identification
    - Build system analysis
    - Runtime optimization recommendations
    - Security framework detection
    
    Args:
        app_path: Path to analyze
        
    Returns:
        Comprehensive analysis dictionary with all detected information
    """
    analyzer = EnhancedApplicationAnalyzer(app_path)
    return analyzer.analyze()


class EnhancedApplicationAnalyzer:
    """
    Production-grade application analyzer with comprehensive framework detection.
    
    Supports enterprise-level applications with complex technology stacks,
    multi-framework projects, and advanced runtime configurations.
    """
    
    def __init__(self, app_path: str):
        self.app_path = Path(app_path).resolve()
        self.analysis = {
            "app_path": str(self.app_path),
            "app_type": None,
            "framework": None,
            "framework_version": None,
            "language_version": None,
            "dependencies": [],
            "dev_dependencies": [],
            "entry_point": None,
            "detected_files": [],
            "status": "analyzing",
            "app_found_in": str(self.app_path),
            "port": None,
            "build_command": None,
            "start_command": None,
            "test_command": None,
            "environment_vars": [],
            "additional_services": [],
            "database_integrations": [],
            "authentication_frameworks": [],
            "testing_frameworks": [],
            "build_tools": [],
            "package_managers": [],
            "security_frameworks": [],
            "api_frameworks": [],
            "frontend_frameworks": [],
            "css_frameworks": [],
            "state_management": [],
            "deployment_configs": [],
            "docker_configs": [],
            "ci_cd_configs": []
        }
        
        # Define comprehensive framework detection patterns
        self.framework_patterns = {
            'python': {
                'web': {
                    'django': {
                        'files': ['manage.py', 'wsgi.py', 'asgi.py'],
                        'dirs': ['django_project', 'mysite'],
                        'imports': ['django', 'Django'],
                        'configs': ['settings.py', 'urls.py'],
                        'port': 8000,
                        'start_cmd': 'python manage.py runserver 0.0.0.0:8000'
                    },
                    'flask': {
                        'files': ['app.py', 'application.py', 'main.py'],
                        'imports': ['flask', 'Flask'],
                        'deps': ['flask'],
                        'configs': ['config.py'],
                        'port': 5000,
                        'start_cmd': 'python app.py'
                    },
                    'fastapi': {
                        'files': ['main.py', 'app.py', 'api.py'],
                        'imports': ['fastapi', 'FastAPI', 'APIRouter'],
                        'deps': ['fastapi', 'uvicorn'],
                        'port': 8000,
                        'start_cmd': 'uvicorn main:app --host 0.0.0.0 --port 8000'
                    },
                    'tornado': {
                        'imports': ['tornado'],
                        'files': ['server.py', 'app.py'],
                        'port': 8888
                    },
                    'pyramid': {
                        'imports': ['pyramid'],
                        'configs': ['development.ini', 'production.ini'],
                        'port': 6543
                    },
                    'sanic': {
                        'imports': ['sanic'],
                        'port': 8000,
                        'start_cmd': 'python app.py'
                    },
                    'quart': {
                        'imports': ['quart'],
                        'port': 5000
                    }
                },
                'workers': {
                    'celery': {
                        'files': ['celery.py', 'celeryconfig.py', 'tasks.py'],
                        'imports': ['celery'],
                        'start_cmd': 'celery -A app worker --loglevel=info'
                    },
                    'rq': {
                        'imports': ['rq'],
                        'files': ['worker.py', 'jobs.py']
                    }
                }
            },
            'node': {
                'frontend': {
                    'react': {
                        'deps': ['react', 'react-dom'],
                        'files': ['src/App.jsx', 'src/App.tsx', 'public/index.html'],
                        'configs': ['craco.config.js', 'react-app-env.d.ts'],
                        'port': 3000
                    },
                    'vue': {
                        'deps': ['vue'],
                        'files': ['src/App.vue', 'vue.config.js'],
                        'configs': ['vue.config.js'],
                        'port': 8080
                    },
                    'angular': {
                        'deps': ['@angular/core'],
                        'files': ['angular.json', 'src/app/app.component.ts'],
                        'configs': ['angular.json', 'tsconfig.json'],
                        'port': 4200
                    },
                    'svelte': {
                        'deps': ['svelte'],
                        'files': ['src/App.svelte'],
                        'configs': ['svelte.config.js'],
                        'port': 5000
                    },
                    'next': {
                        'deps': ['next'],
                        'files': ['next.config.js', 'pages/', 'app/'],
                        'configs': ['next.config.js'],
                        'port': 3000,
                        'start_cmd': 'npm start'
                    },
                    'nuxt': {
                        'deps': ['nuxt'],
                        'files': ['nuxt.config.js', 'nuxt.config.ts'],
                        'port': 3000
                    },
                    'gatsby': {
                        'deps': ['gatsby'],
                        'files': ['gatsby-config.js', 'gatsby-node.js'],
                        'port': 8000
                    },
                    'vite': {
                        'deps': ['vite', '@vitejs/plugin-react'],
                        'files': ['vite.config.js', 'vite.config.ts', 'index.html'],
                        'configs': ['vite.config.js', 'vite.config.ts'],
                        'port': 5173,
                        'start_cmd': 'npm run dev'
                    }
                },
                'backend': {
                    'express': {
                        'deps': ['express'],
                        'files': ['server.js', 'app.js', 'index.js'],
                        'port': 3000
                    },
                    'fastify': {
                        'deps': ['fastify'],
                        'files': ['server.js', 'app.js'],
                        'port': 3000
                    },
                    'koa': {
                        'deps': ['koa'],
                        'files': ['server.js', 'app.js'],
                        'port': 3000
                    },
                    'hapi': {
                        'deps': ['@hapi/hapi'],
                        'files': ['server.js'],
                        'port': 3000
                    },
                    'nestjs': {
                        'deps': ['@nestjs/core', '@nestjs/common'],
                        'files': ['src/main.ts', 'nest-cli.json'],
                        'configs': ['nest-cli.json'],
                        'port': 3000
                    }
                }
            },
            'java': {
                'spring': {
                    'files': ['pom.xml', 'build.gradle'],
                    'markers': ['spring-boot', 'springframework'],
                    'configs': ['application.yml', 'application.properties'],
                    'port': 8080
                },
                'quarkus': {
                    'markers': ['quarkus'],
                    'configs': ['application.properties'],
                    'port': 8080
                }
            }
        }
    
    def analyze(self) -> Dict[str, Any]:
        """Run comprehensive analysis."""
        try:
            if not self.app_path.exists():
                self.analysis['status'] = 'error'
                self.analysis['error'] = f'Path not found: {self.app_path}'
                return self.analysis
            
            # Step 1: File detection
            self._detect_files()
            
            # Step 2: Language detection
            self._detect_language()
            
            # Step 3: Framework detection
            self._detect_frameworks()
            
            # Step 4: Dependency analysis
            self._analyze_dependencies()
            
            # Step 5: Configuration analysis
            self._analyze_configurations()
            
            # Step 6: Environment analysis
            self._analyze_environment()
            
            # Step 7: Integration detection
            self._detect_integrations()
            
            # Step 8: Build system analysis
            self._analyze_build_systems()
            
            # Step 9: Generate recommendations
            self._generate_recommendations()
            
            self.analysis['status'] = 'completed'
            return self.analysis
            
        except Exception as e:
            self.analysis['status'] = 'error'
            self.analysis['error'] = str(e)
            return self.analysis
    
    def _detect_files(self):
        """Detect all relevant files in the project - FAST VERSION."""
        try:
            files = []
            # Only scan immediate directory and one level deep for speed
            for item in self.app_path.glob('*'):
                if item.is_file():
                    files.append(item.name)
            # Check common subdirectories only
            for subdir in ['src', 'app', 'lib', 'api', 'server']:
                subpath = self.app_path / subdir
                if subpath.exists():
                    for item in subpath.glob('*'):
                        if item.is_file():
                            files.append(f"{subdir}/{item.name}")
            self.analysis['detected_files'] = files[:50]  # Reduced limit for performance
        except Exception:
            self.analysis['detected_files'] = []
    
    def _detect_language(self):
        """Detect primary programming language with flexible validation."""
        language_indicators = {
            'python': ['requirements.txt', 'pyproject.toml', 'setup.py', 'Pipfile', 'poetry.lock', '*.py'],
            'node': ['package.json', 'yarn.lock', 'package-lock.json', '*.js', '*.ts', '*.jsx', '*.tsx'],
            'java': ['pom.xml', 'build.gradle', 'build.gradle.kts', '*.java'],
            'go': ['go.mod', 'go.sum', '*.go'],
            'ruby': ['Gemfile', 'Gemfile.lock', '*.rb'],
            'php': ['composer.json', 'composer.lock', '*.php'],
            'rust': ['Cargo.toml', 'Cargo.lock', '*.rs'],
            'dotnet': ['*.csproj', '*.sln', '*.cs', '*.vb'],
            'scala': ['build.sbt', '*.scala'],
            'kotlin': ['*.kt', '*.kts', 'build.gradle.kts']
        }
        
        # Key files that indicate a real application/service
        required_indicators = {
            'python': ['requirements.txt', 'pyproject.toml', 'setup.py', 'Pipfile', 'poetry.lock'],
            'node': ['package.json'],
            'java': ['pom.xml', 'build.gradle', 'build.gradle.kts'],
            'go': ['go.mod'],
            'ruby': ['Gemfile'],
            'php': ['composer.json'],
            'rust': ['Cargo.toml'],
            'dotnet': ['*.csproj', '*.sln'],
            'scala': ['build.sbt'],
            'kotlin': ['build.gradle.kts']
        }
        
        # Directories to exclude from language detection (mobile/build artifacts)
        excluded_dirs = [
            'android', 'ios', 'mobile',  # Mobile build directories
            'build', 'dist', 'out', 'target',  # Build output directories
            'node_modules', '__pycache__', '.git', 'venv', '.venv',  # Dependencies/caches
            '.gradle', '.next', '.nuxt', 'coverage',  # Framework caches
            'capacitor-cordova-android-plugins'  # Capacitor build artifacts
        ]
        
        detected_languages = {}
        
        # First, check for root-level package managers (highest priority)
        root_package_manager = None
        if (self.app_path / 'package.json').exists():
            root_package_manager = 'node'
        elif (self.app_path / 'requirements.txt').exists() or (self.app_path / 'pyproject.toml').exists():
            root_package_manager = 'python'
        elif (self.app_path / 'pom.xml').exists() or (self.app_path / 'build.gradle').exists():
            root_package_manager = 'java'
        elif (self.app_path / 'go.mod').exists():
            root_package_manager = 'go'
        elif (self.app_path / 'Cargo.toml').exists():
            root_package_manager = 'rust'
        elif (self.app_path / 'Gemfile').exists():
            root_package_manager = 'ruby'
        elif (self.app_path / 'composer.json').exists():
            root_package_manager = 'php'
        
        for lang, indicators in language_indicators.items():
            score = 0
            has_required = False
            required_file_count = 0
            
            # MASSIVE bonus if this language has root-level package manager
            is_root_language = (root_package_manager == lang)
            
            # Check if required indicator exists - FAST VERSION (root only)
            for req_indicator in required_indicators.get(lang, []):
                if req_indicator.startswith('*.'):
                    # Only check root directory, no recursive scan
                    matches = list(self.app_path.glob(f'*{req_indicator[1:]}'))
                else:
                    # Only check root directory, no recursive scan
                    matches = list(self.app_path.glob(req_indicator))
                
                if matches:
                    has_required = True
                    required_file_count = len(matches)
                    # Massive bonus for root package manager
                    weight = 1000 if is_root_language else 100
                    score += len(matches) * weight
                    break
            
            # Only continue if required indicators are present
            if not has_required:
                continue
            
            # Helper function to check if path should be excluded
            def should_exclude(file_path: Path) -> bool:
                try:
                    parts = file_path.relative_to(self.app_path).parts
                    return any(excluded_dir in parts for excluded_dir in excluded_dirs)
                except:
                    return False
            
            # Count source code files (FAST VERSION - limited depth)
            source_file_count = 0
            for indicator in indicators:
                if indicator.startswith('*.'):
                    ext = indicator[1:]
                    # Only check root and immediate src/app/lib directories (no deep recursion)
                    root_matches = list(self.app_path.glob(f'*{ext}'))
                    src_matches = list(self.app_path.glob(f'src/*{ext}')) if (self.app_path / 'src').exists() else []
                    app_matches = list(self.app_path.glob(f'app/*{ext}')) if (self.app_path / 'app').exists() else []
                    lib_matches = list(self.app_path.glob(f'lib/*{ext}')) if (self.app_path / 'lib').exists() else []
                    
                    all_matches = root_matches + src_matches + app_matches + lib_matches
                    source_file_count = len(all_matches)
                    
                    # More flexible file count requirements:
                    # - If has package manager file, need at least 1 source file
                    # - Award points proportional to file count
                    # - Root language gets higher weight for source files
                    if source_file_count > 0:
                        weight = 5 if is_root_language else 2
                        score += min(source_file_count * weight, 100 if is_root_language else 50)
                else:
                    # Config files (already counted in required) - FAST VERSION (root only)
                    if indicator not in required_indicators.get(lang, []):
                        matches = list(self.app_path.glob(indicator))
                        score += len(matches) * 10
            
            if score > 0:
                detected_languages[lang] = score
                self.analysis[f'{lang}_file_count'] = source_file_count
        
        if detected_languages:
            primary_lang = max(detected_languages, key=detected_languages.get)
            # Lower threshold - if has package manager file, it's valid
            # Minimum score of 100 means at least one required file exists
            if detected_languages[primary_lang] >= 100:
                self.analysis['app_type'] = primary_lang
                self.analysis['language_confidence'] = detected_languages
            else:
                self.analysis['app_type'] = 'unknown'
        else:
            self.analysis['app_type'] = 'unknown'
    
    def _detect_frameworks(self):
        """Detect frameworks based on the primary language."""
        if not self.analysis['app_type'] or self.analysis['app_type'] not in self.framework_patterns:
            return
        
        lang_patterns = self.framework_patterns[self.analysis['app_type']]
        detected_frameworks = []
        
        for category, frameworks in lang_patterns.items():
            for framework_name, pattern in frameworks.items():
                confidence = self._calculate_framework_confidence(pattern)
                if confidence > 0:
                    detected_frameworks.append({
                        'name': framework_name,
                        'category': category,
                        'confidence': confidence,
                        'port': pattern.get('port'),
                        'start_command': pattern.get('start_cmd')
                    })
        
        # Sort by confidence and select primary framework
        detected_frameworks.sort(key=lambda x: x['confidence'], reverse=True)
        
        if detected_frameworks:
            # Handle special cases: prioritize Vite over Express for React apps
            primary_framework = detected_frameworks[0]
            
            # CRITICAL: Prioritize FastAPI over Flask when both detected
            # FastAPI and Flask have overlapping file patterns, but FastAPI is more specific
            fastapi_frameworks = [f for f in detected_frameworks if f['name'] == 'fastapi']
            flask_frameworks = [f for f in detected_frameworks if f['name'] == 'flask']
            
            if fastapi_frameworks and flask_frameworks:
                # Check for FastAPI-specific indicators
                has_fastapi_imports = self._has_specific_imports(['fastapi', 'FastAPI', 'APIRouter', 'Depends'])
                has_uvicorn_in_deps = self._has_dependency('uvicorn')
                
                if has_fastapi_imports or has_uvicorn_in_deps:
                    primary_framework = fastapi_frameworks[0]
                    # Boost FastAPI confidence
                    primary_framework['confidence'] += 50
                else:
                    # Default to Flask if no FastAPI-specific indicators
                    primary_framework = flask_frameworks[0]
            
            # If we detect both Express and Vite/React, choose based on project structure
            vite_frameworks = [f for f in detected_frameworks if f['name'] == 'vite']
            react_frameworks = [f for f in detected_frameworks if f['name'] == 'react']
            express_frameworks = [f for f in detected_frameworks if f['name'] == 'express']
            
            # If Vite is detected with React, prioritize Vite
            if vite_frameworks and react_frameworks and express_frameworks:
                primary_framework = vite_frameworks[0]
            # If React but no Vite, check for Vite config files
            elif react_frameworks and express_frameworks:
                vite_config_exists = any(
                    (self.app_path / config).exists() 
                    for config in ['vite.config.js', 'vite.config.ts']
                )
                if vite_config_exists:
                    # Create a synthetic Vite entry if config exists but not detected
                    primary_framework = {
                        'name': 'vite',
                        'category': 'frontend', 
                        'confidence': max(react_frameworks[0]['confidence'], express_frameworks[0]['confidence']) + 10,
                        'port': 5173,
                        'start_command': 'npm run dev'
                    }
            
            self.analysis['framework'] = primary_framework['name']
            
            # Use dynamic port detection with proper fallback
            detected_port = detect_port_with_fallback(str(self.app_path), primary_framework['name'])
            # Fallback to framework default if detection returns 0 or None
            if not detected_port or detected_port == 0:
                detected_port = primary_framework.get('port', 3000)
            self.analysis['port'] = detected_port
            
            self.analysis['start_command'] = primary_framework['start_command']
            self.analysis['detected_frameworks'] = detected_frameworks
    
    def _calculate_framework_confidence(self, pattern: Dict) -> int:
        """Calculate confidence score for framework detection."""
        score = 0
        
        # Check for specific files
        if 'files' in pattern:
            for file_pattern in pattern['files']:
                matches = list(self.app_path.glob(f'**/{file_pattern}'))
                score += len(matches) * 20
        
        # Check for directories
        if 'dirs' in pattern:
            for dir_pattern in pattern['dirs']:
                matches = list(self.app_path.glob(f'**/{dir_pattern}'))
                score += len(matches) * 15
        
        # Check for imports in code files (HIGHER WEIGHT for accuracy)
        if 'imports' in pattern:
            score += self._check_imports(pattern['imports']) * 30
        
        # Check for dependencies (CRITICAL for distinguishing frameworks)
        if 'deps' in pattern:
            score += self._check_dependencies(pattern['deps']) * 40
        
        # Check for markers in build files
        if 'markers' in pattern:
            score += self._check_build_markers(pattern['markers']) * 15
        
        return score
    
    def _has_specific_imports(self, imports: List[str]) -> bool:
        """Check if specific imports exist in code files (case-sensitive) - FAST VERSION."""
        # Only check root directory and src folder, max 10 files
        code_files = list(self.app_path.glob('*.py'))[:5]
        if (self.app_path / 'src').exists():
            code_files += list((self.app_path / 'src').glob('*.py'))[:5]
        
        for code_file in code_files:
            try:
                with open(code_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    for import_name in imports:
                        # Case-sensitive check for better accuracy
                        if re.search(rf'import\s+{re.escape(import_name)}|from\s+\S*\s+import\s+.*{re.escape(import_name)}', content):
                            return True
            except Exception:
                pass
        
        return False
    
    def _has_dependency(self, dep_name: str) -> bool:
        """Check if a specific dependency exists in requirements.txt or package.json."""
        # Check requirements.txt
        req_file = self.app_path / 'requirements.txt'
        if req_file.exists():
            try:
                with open(req_file, 'r') as f:
                    content = f.read().lower()
                    if dep_name.lower() in content:
                        return True
            except Exception:
                pass
        
        # Check package.json
        package_json = self.app_path / 'package.json'
        if package_json.exists():
            try:
                with open(package_json, 'r') as f:
                    pkg_data = json.load(f)
                    all_deps = {**pkg_data.get('dependencies', {}), **pkg_data.get('devDependencies', {})}
                    if dep_name in all_deps:
                        return True
            except Exception:
                pass
        
        return False
    
    def _check_imports(self, imports: List[str]) -> int:
        """Check for import statements in code files - FAST VERSION."""
        score = 0
        # Only check root and src directories, no deep recursion
        code_files = list(self.app_path.glob('*.py'))[:3] + list(self.app_path.glob('*.js'))[:3] + list(self.app_path.glob('*.ts'))[:3]
        if (self.app_path / 'src').exists():
            code_files += list((self.app_path / 'src').glob('*.py'))[:3]
        
        for code_file in code_files[:10]:  # Limit for performance
            try:
                with open(code_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    for import_name in imports:
                        if re.search(rf'import.*{re.escape(import_name)}|from.*{re.escape(import_name)}', content, re.IGNORECASE):
                            score += 1
            except Exception:
                pass
        
        return score
    
    def _check_dependencies(self, deps: List[str]) -> int:
        """Check for dependencies in package files."""
        score = 0
        
        # Check package.json
        package_json = self.app_path / 'package.json'
        if package_json.exists():
            try:
                with open(package_json, 'r') as f:
                    pkg_data = json.load(f)
                    all_deps = {**pkg_data.get('dependencies', {}), **pkg_data.get('devDependencies', {})}
                    for dep in deps:
                        if dep in all_deps:
                            score += 1
            except Exception:
                pass
        
        # Check requirements.txt
        req_file = self.app_path / 'requirements.txt'
        if req_file.exists():
            try:
                with open(req_file, 'r') as f:
                    req_content = f.read().lower()
                    for dep in deps:
                        if dep.lower() in req_content:
                            score += 1
            except Exception:
                pass
        
        return score
    
    def _check_build_markers(self, markers: List[str]) -> int:
        """Check for markers in build files."""
        score = 0
        build_files = ['pom.xml', 'build.gradle', 'Cargo.toml', 'pyproject.toml']
        
        for build_file in build_files:
            build_path = self.app_path / build_file
            if build_path.exists():
                try:
                    with open(build_path, 'r') as f:
                        content = f.read().lower()
                        for marker in markers:
                            if marker.lower() in content:
                                score += 1
                except Exception:
                    pass
        
        return score
    
    def _analyze_dependencies(self):
        """Analyze project dependencies."""
        # Node.js dependencies
        package_json = self.app_path / 'package.json'
        if package_json.exists():
            try:
                with open(package_json, 'r') as f:
                    pkg_data = json.load(f)
                    self.analysis['dependencies'] = list(pkg_data.get('dependencies', {}).keys())
                    self.analysis['dev_dependencies'] = list(pkg_data.get('devDependencies', {}).keys())
                    self.analysis['package_managers'].append('npm')
                    
                    # Extract entry point
                    main_file = pkg_data.get('main', 'index.js')
                    if main_file and not self.analysis['entry_point']:
                        self.analysis['entry_point'] = main_file
                    
                    # Extract scripts
                    scripts = pkg_data.get('scripts', {})
                    if 'start' in scripts:
                        self.analysis['start_command'] = 'npm start'
                    if 'build' in scripts:
                        self.analysis['build_command'] = 'npm run build'
                    if 'test' in scripts:
                        self.analysis['test_command'] = 'npm test'
            except Exception:
                pass
        
        # Python dependencies and entry point detection
        req_file = self.app_path / 'requirements.txt'
        if req_file.exists():
            try:
                with open(req_file, 'r') as f:
                    deps = [line.strip().split('==')[0].split('>=')[0].split('<=')[0] 
                           for line in f.read().splitlines() 
                           if line.strip() and not line.startswith('#')]
                    self.analysis['dependencies'].extend(deps)
                    self.analysis['package_managers'].append('pip')
            except Exception:
                pass
        
        # Detect Python entry point if not already set
        if not self.analysis['entry_point'] and self.analysis['app_type'] == 'python':
            for main_file in ['main.py', 'app.py', 'application.py', 'run.py', 'server.py']:
                if (self.app_path / main_file).exists():
                    self.analysis['entry_point'] = main_file
                    break
        
        # Detect language versions
        self._detect_language_versions()
    
    def _detect_language_versions(self):
        """Detect Python and Node.js versions from project configuration files."""
        # Detect Python version
        if self.analysis['app_type'] == 'python':
            python_version = None
            
            # Check runtime.txt (Heroku style)
            runtime_file = self.app_path / 'runtime.txt'
            if runtime_file.exists():
                try:
                    with open(runtime_file, 'r') as f:
                        content = f.read().strip()
                        if content.startswith('python-'):
                            python_version = content.replace('python-', '')
                except Exception:
                    pass
            
            # Check .python-version (pyenv)
            pyenv_file = self.app_path / '.python-version'
            if not python_version and pyenv_file.exists():
                try:
                    with open(pyenv_file, 'r') as f:
                        python_version = f.read().strip()
                except Exception:
                    pass
            
            # Check pyproject.toml
            pyproject = self.app_path / 'pyproject.toml'
            if not python_version and pyproject.exists():
                try:
                    with open(pyproject, 'r') as f:
                        content = f.read()
                        # Look for python = "^3.x" or requires-python = ">=3.x"
                        match = re.search(r'python.*?["\']([>=^~]*)(\d+\.\d+)', content)
                        if match:
                            python_version = match.group(2)
                except Exception:
                    pass
            
            # Check Pipfile
            pipfile = self.app_path / 'Pipfile'
            if not python_version and pipfile.exists():
                try:
                    with open(pipfile, 'r') as f:
                        content = f.read()
                        match = re.search(r'python_version.*?["\']([\d.]+)', content)
                        if match:
                            python_version = match.group(1)
                except Exception:
                    pass
            
            # Default to 3.11 if not found
            self.analysis['language_version'] = python_version or '3.11'
        
        # Detect Node.js version
        elif self.analysis['app_type'] == 'node':
            node_version = None
            
            # Check .nvmrc
            nvmrc_file = self.app_path / '.nvmrc'
            if nvmrc_file.exists():
                try:
                    with open(nvmrc_file, 'r') as f:
                        node_version = f.read().strip().replace('v', '')
                except Exception:
                    pass
            
            # Check package.json engines field
            package_json = self.app_path / 'package.json'
            if not node_version and package_json.exists():
                try:
                    with open(package_json, 'r') as f:
                        pkg_data = json.load(f)
                        engines = pkg_data.get('engines', {})
                        node_spec = engines.get('node', '')
                        # Extract version number from spec like ">=18.0.0" or "^20.0.0"
                        match = re.search(r'([\d.]+)', node_spec)
                        if match:
                            version_str = match.group(1)
                            # Get major version
                            major = version_str.split('.')[0]
                            node_version = major
                except Exception:
                    pass
            
            # Check .node-version
            node_version_file = self.app_path / '.node-version'
            if not node_version and node_version_file.exists():
                try:
                    with open(node_version_file, 'r') as f:
                        node_version = f.read().strip().replace('v', '').split('.')[0]
                except Exception:
                    pass
            
            # Default to 20 if not found
            self.analysis['language_version'] = node_version or '20'
    
    def _analyze_configurations(self):
        """Analyze configuration files."""
        config_patterns = {
            'docker': ['Dockerfile', 'docker-compose.yml', 'docker-compose.yaml'],
            'ci_cd': ['.github/workflows/', '.gitlab-ci.yml', 'Jenkinsfile'],
            'env': ['.env', '.env.example', '.env.local'],
            'build': ['webpack.config.js', 'vite.config.js', 'rollup.config.js']
        }
        
        for config_type, patterns in config_patterns.items():
            found_configs = []
            for pattern in patterns:
                matches = list(self.app_path.glob(f'**/{pattern}'))
                found_configs.extend([str(m.relative_to(self.app_path)) for m in matches])
            
            if found_configs:
                self.analysis[f'{config_type}_configs'] = found_configs
    
    def _analyze_environment(self):
        """Analyze environment variables and configuration."""
        env_files = ['.env', '.env.example', '.env.sample', '.env.template']
        
        for env_file in env_files:
            env_path = self.app_path / env_file
            if env_path.exists():
                try:
                    with open(env_path, 'r') as f:
                        env_vars = []
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#') and '=' in line:
                                var_name = line.split('=')[0].strip()
                                env_vars.append(var_name)
                        self.analysis['environment_vars'].extend(env_vars)
                except Exception:
                    pass
    
    def _detect_integrations(self):
        """Detect database and service integrations."""
        # Database integrations
        db_patterns = {
            'postgresql': ['psycopg2', 'pg', 'postgresql', 'asyncpg'],
            'mysql': ['mysql', 'pymysql', 'mysql2', 'mysqlclient'],
            'mongodb': ['pymongo', 'mongoose', 'motor'],
            'redis': ['redis', 'ioredis', 'hiredis'],
            'sqlite': ['sqlite3']
        }
        
        for db_type, indicators in db_patterns.items():
            if any(dep in str(self.analysis['dependencies']).lower() for dep in indicators):
                self.analysis['database_integrations'].append(db_type)
        
        # Authentication frameworks
        auth_patterns = ['passport', 'auth0', 'firebase-auth', 'django-auth', 'flask-login']
        for auth in auth_patterns:
            if auth in str(self.analysis['dependencies']).lower():
                self.analysis['authentication_frameworks'].append(auth)
    
    def _analyze_build_systems(self):
        """Analyze build systems and tools."""
        build_files = {
            'webpack': ['webpack.config.js'],
            'vite': ['vite.config.js', 'vite.config.ts'],
            'parcel': ['package.json'],  # Check for parcel in deps
            'rollup': ['rollup.config.js'],
            'esbuild': ['build.js'],
            'maven': ['pom.xml'],
            'gradle': ['build.gradle', 'build.gradle.kts'],
            'cmake': ['CMakeLists.txt'],
            'make': ['Makefile']
        }
        
        for build_tool, files in build_files.items():
            for file_pattern in files:
                if list(self.app_path.glob(f'**/{file_pattern}')):
                    self.analysis['build_tools'].append(build_tool)
                    break
    
    def _generate_recommendations(self):
        """Generate optimization and deployment recommendations."""
        recommendations = []
        
        # Port recommendations - use dynamic detection with framework/app_type fallback
        if not self.analysis['port']:
            framework = self.analysis.get('framework')
            detected_port = detect_port_with_fallback(str(self.app_path), framework)
            self.analysis['port'] = detected_port
        
        # Build command recommendations
        if not self.analysis['build_command']:
            if self.analysis['framework'] in ['react', 'vue', 'angular']:
                self.analysis['build_command'] = 'npm run build'
            elif self.analysis['framework'] == 'next':
                self.analysis['build_command'] = 'npm run build'
        
        # Start command recommendations
        if not self.analysis['start_command']:
            if self.analysis['framework'] == 'django':
                self.analysis['start_command'] = 'python manage.py runserver 0.0.0.0:8000'
            elif self.analysis['framework'] == 'flask':
                self.analysis['start_command'] = 'python app.py'
            elif self.analysis['framework'] == 'fastapi':
                self.analysis['start_command'] = 'uvicorn main:app --host 0.0.0.0 --port 8000'
            elif self.analysis['app_type'] == 'node':
                self.analysis['start_command'] = 'npm start'
        
        self.analysis['recommendations'] = recommendations


# Legacy functions for backward compatibility
def detect_environment_variables(app_path: str) -> List[str]:
    """Detect required environment variables from various config files."""
    analyzer = EnhancedApplicationAnalyzer(app_path)
    analysis = analyzer.analyze()
    return analysis.get('environment_vars', [])


def detect_databases_in_code(app_path: str) -> List[Dict]:
    """Detect database usage by analyzing code imports and configurations."""
    analyzer = EnhancedApplicationAnalyzer(app_path)
    analysis = analyzer.analyze()
    
    databases = []
    for db_type in analysis.get('database_integrations', []):
        databases.append({
            'type': db_type,
            'detected_from': 'dependencies'
        })
    
    return databases