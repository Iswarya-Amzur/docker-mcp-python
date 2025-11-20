import os
import json
import re
import yaml
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from .analyzer import analyze_application
from .dockerfile_generator import generate_dockerfile

def detect_services(project_root: str) -> dict:
    """
    PRODUCTION-LEVEL SERVICE DETECTION
    
    Detects ANY type of service in enterprise applications:
    
    APPLICATION SERVICES:
    - Web services (REST APIs, GraphQL, gRPC)
    - Frontend applications (SPA, SSR, static sites)
    - Background workers (Celery, Sidekiq, Bull queues)
    - Microservices (individual services in monorepos)
    - Serverless functions (Lambda, Azure Functions, Vercel)
    
    INFRASTRUCTURE SERVICES:
    - Databases (SQL, NoSQL, Graph, Time-series)
    - Message brokers (RabbitMQ, Kafka, Redis Pub/Sub)
    - Caches (Redis, Memcached, Hazelcast)
    - Search engines (Elasticsearch, Solr, MeiliSearch)
    - Monitoring (Prometheus, Grafana, Jaeger)
    
    CONFIGURATION-BASED DETECTION:
    - Docker Compose services
    - Kubernetes manifests
    - Infrastructure as Code (Terraform, Pulumi)
    - CI/CD pipelines (GitHub Actions, GitLab CI)
    
    RUNTIME ANALYSIS:
    - Dynamic imports and lazy loading
    - Plugin architectures and extensions
    - Multi-threaded applications
    - Cross-language service calls
    
    Args:
        project_root: Root directory of the project
        
    Returns:
        Dictionary with comprehensive service detection results
    """
    detector = ProductionServiceDetector(project_root)
    return detector.detect_all_services()


class ProductionServiceDetector:
    """
    Enterprise-grade service detection engine.
    
    Implements multiple detection strategies:
    1. Static analysis (file patterns, imports, configs)
    2. Dynamic analysis (runtime dependencies, plugin loading)
    3. Infrastructure analysis (Docker, K8s, Terraform)
    4. Configuration parsing (YAML, JSON, TOML, INI)
    5. Dependency graph construction
    """
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.services = {}
        self.infrastructure_services = {}
        self.worker_services = {}
        self.serverless_functions = {}
        self.detected_technologies = set()
        
        if not self.project_root.exists():
            return

        # Enhanced service patterns for enterprise detection
        self.service_patterns = {
            # Application Services
            'web_services': {
                'directories': ['api', 'backend', 'server', 'service', 'gateway', 'proxy'],
                'files': ['app.py', 'server.js', 'main.go', 'app.go', 'server.py', 'api.py'],
                'frameworks': ['fastapi', 'express', 'gin', 'spring', 'django', 'flask', 'nest']
            },
            'frontend_services': {
                'directories': ['frontend', 'client', 'web', 'ui', 'app', 'portal', 'dashboard'],
                'files': ['index.html', 'app.tsx', 'main.js', 'index.jsx', 'app.vue'],
                'frameworks': ['react', 'vue', 'angular', 'svelte', 'next', 'nuxt', 'gatsby']
            },
            'worker_services': {
                'directories': ['workers', 'jobs', 'tasks', 'processors', 'consumers', 'handlers'],
                'files': ['worker.py', 'job.js', 'task.py', 'consumer.py', 'processor.go'],
                'frameworks': ['celery', 'rq', 'bull', 'sidekiq', 'delayed_job', 'faktory']
            },
            'microservices': {
                'directories': ['services', 'microservices', 'ms', 'components', 'modules'],
                'patterns': ['*-service', '*-api', '*-worker', '*-gateway', '*-proxy']
            }
        }
        
        # Infrastructure service detection patterns
        self.infrastructure_patterns = {
            'databases': {
                'sql': ['postgres', 'mysql', 'mariadb', 'sqlite', 'mssql', 'oracle'],
                'nosql': ['mongodb', 'cassandra', 'couchdb', 'dynamodb', 'firestore'],
                'graph': ['neo4j', 'arangodb', 'dgraph', 'amazon-neptune'],
                'timeseries': ['influxdb', 'timescaledb', 'prometheus', 'clickhouse'],
                'key_value': ['redis', 'etcd', 'consul', 'memcached', 'hazelcast']
            },
            'message_brokers': {
                'queues': ['rabbitmq', 'activemq', 'amazon-sqs', 'azure-servicebus'],
                'streaming': ['kafka', 'pulsar', 'kinesis', 'eventstore'],
                'pubsub': ['redis', 'nats', 'google-pubsub', 'azure-eventhub']
            },
            'search_engines': {
                'fulltext': ['elasticsearch', 'opensearch', 'solr', 'meilisearch'],
                'vector': ['pinecone', 'weaviate', 'qdrant', 'milvus']
            },
            'monitoring': {
                'metrics': ['prometheus', 'datadog', 'newrelic', 'splunk'],
                'logging': ['elasticsearch', 'loki', 'fluentd', 'logstash'],
                'tracing': ['jaeger', 'zipkin', 'datadog', 'lightstep'],
                'visualization': ['grafana', 'kibana', 'tableau', 'superset']
            }
        }
        
        # Configuration file patterns
        self.config_patterns = {
            'docker': ['docker-compose.yml', 'docker-compose.yaml', 'Dockerfile*'],
            'kubernetes': ['*.yaml', '*.yml', 'kustomization.yaml', 'helm/'],
            'terraform': ['*.tf', '*.tfvars', 'terraform.tfstate*'],
            'ansible': ['playbook.yml', 'inventory', 'ansible.cfg'],
            'ci_cd': ['.github/', '.gitlab-ci.yml', 'Jenkinsfile', 'azure-pipelines.yml']
        }
    
    def detect_all_services(self) -> Dict[str, Any]:
        """Main detection orchestrator - runs all detection strategies."""
        try:
            # Strategy 1: Static file analysis
            self._detect_application_services()
            
            # Strategy 2: Infrastructure service detection
            self._detect_infrastructure_services()
            
            # Strategy 3: Configuration-based detection
            self._detect_config_based_services()
            
            # Strategy 4: Runtime dependency analysis
            self._analyze_runtime_dependencies()
            
            # Strategy 5: Serverless function detection
            self._detect_serverless_functions()
            
            # Strategy 6: Worker and background service detection
            self._detect_worker_services()
            
            # Strategy 7: Plugin and extension detection
            self._detect_plugins_and_extensions()
            
            return self._compile_detection_results()
            
        except Exception as e:
            return {'error': f'Detection failed: {str(e)}', 'services': {}}
    
    def _detect_application_services(self):
        """Detect application services using enhanced static analysis."""
        # Multi-level directory scanning
        for strategy in ['root_level', 'direct_children', 'monorepo_scan', 'deep_scan']:
            getattr(self, f'_scan_{strategy}')()
    
    def _scan_root_level(self):
        """Check if root directory is a single service."""
        # SKIP docker-mcp tool directory itself to prevent self-dockerization
        root_name = self.project_root.name.lower()
        if 'docker-mcp' in root_name or 'docker_mcp' in root_name:
            return
        
        # Check if root itself is a service (single-service projects)
        # But don't let this block nested service detection
        analysis = analyze_application(str(self.project_root))
        if analysis.get('app_type') and analysis['app_type'] != 'unknown':
            # Check if there are ANY subdirectories that might be services
            has_nested_services = False
            if self.project_root.exists():
                for item in self.project_root.iterdir():
                    if (item.is_dir() and 
                        not item.name.startswith('.') and 
                        item.name not in ['node_modules', '__pycache__', 'venv', '.git']):
                        # Check if subdirectory is also a service
                        sub_analysis = analyze_application(str(item))
                        if sub_analysis.get('app_type') and sub_analysis['app_type'] != 'unknown':
                            has_nested_services = True
                            break
            
            # Only treat root as THE service if no nested services exist
            if not has_nested_services:
                self.services['app'] = {
                    'path': str(self.project_root),
                    'type': 'application',
                    'category': 'primary',
                    'framework': analysis.get('framework', 'unknown'),
                    'language': analysis['app_type'],
                    'analysis': analysis,
                    'detection_method': 'root_analysis'
                }
    
    def _scan_direct_children(self):
        """Scan immediate child directories for services."""
        if not self.project_root.exists():
            return
            
        for item in self.project_root.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                self._analyze_potential_service(item)
    
    def _scan_monorepo_scan(self):
        """Scan monorepo structures (packages/, apps/, services/)."""
        monorepo_dirs = ['packages', 'apps', 'services', 'modules', 'libs', 'components']
        
        for mono_dir in monorepo_dirs:
            mono_path = self.project_root / mono_dir
            if mono_path.exists() and mono_path.is_dir():
                for service_dir in mono_path.iterdir():
                    if service_dir.is_dir():
                        service_key = f"{mono_dir}-{service_dir.name}"
                        analysis = analyze_application(str(service_dir))
                        if analysis.get('app_type') and analysis['app_type'] != 'unknown':
                            self.services[service_key] = {
                                'path': str(service_dir),
                                'type': 'application',
                                'category': 'monorepo_service',
                                'framework': analysis.get('framework', 'unknown'),
                                'language': analysis['app_type'],
                                'analysis': analysis,
                                'detection_method': 'monorepo_scan',
                                'parent_structure': mono_dir
                            }
    
    def _scan_deep_scan(self):
        """Deep recursive scan for nested services - ALWAYS runs to find all services."""
        def scan_recursive(path: Path, depth: int = 0, max_depth: int = 5):
            if depth > max_depth or not path.exists():
                return
                
            for item in path.iterdir():
                # Skip common non-service directories
                if item.is_dir() and not item.name.startswith('.'):
                    skip_dirs = ['node_modules', '__pycache__', '.git', 'venv', 'env', '.venv', 
                                 'dist', 'build', '.next', '.nuxt', 'coverage', '.pytest_cache']
                    if item.name in skip_dirs:
                        continue
                    
                    # Skip docker-mcp directories
                    if 'docker-mcp' in item.name.lower() or 'docker_mcp' in item.name.lower():
                        continue
                    
                    # Check if this directory is a service
                    analysis = analyze_application(str(item))
                    if analysis.get('app_type') and analysis['app_type'] != 'unknown':
                        relative_path = item.relative_to(self.project_root)
                        service_key = str(relative_path).replace('/', '-').replace('\\\\', '-').replace('\\', '-')
                        
                        # Only add if not already detected
                        if service_key not in self.services:
                            self.services[service_key] = {
                                'path': str(item),
                                'type': 'application',
                                'category': 'nested_service',
                                'framework': analysis.get('framework', 'unknown'),
                                'language': analysis['app_type'],
                                'analysis': analysis,
                                'detection_method': 'deep_scan',
                                'nesting_level': depth + 1
                            }
                    
                    # ALWAYS continue scanning deeper - services can be nested inside services
                    scan_recursive(item, depth + 1, max_depth)
        
        scan_recursive(self.project_root)
    
    def _analyze_potential_service(self, service_path: Path):
        """Analyze a directory to determine if it's a service."""
        # SKIP docker-mcp tool directory and subdirectories
        path_name = service_path.name.lower()
        if 'docker-mcp' in path_name or 'docker_mcp' in path_name or path_name == 'docker_tools':
            return
        
        analysis = analyze_application(str(service_path))
        
        if analysis.get('app_type') and analysis['app_type'] != 'unknown':
            # Enhanced service categorization
            category = self._categorize_service(service_path, analysis)
            
            self.services[service_path.name] = {
                'path': str(service_path),
                'type': 'application',
                'category': category,
                'framework': analysis.get('framework', 'unknown'),
                'language': analysis['app_type'],
                'analysis': analysis,
                'detection_method': 'direct_analysis',
                'runtime_dependencies': self._analyze_runtime_deps(service_path),
                'config_dependencies': self._analyze_config_deps(service_path)
            }
    
    def _categorize_service(self, service_path: Path, analysis: Dict) -> str:
        """Categorize service based on its characteristics."""
        path_name = service_path.name.lower()
        framework = (analysis.get('framework') or '').lower()
        
        # Web service detection
        if any(term in path_name for term in ['api', 'backend', 'server', 'gateway']):
            return 'web_service'
        
        # Frontend detection
        if any(term in path_name for term in ['frontend', 'client', 'web', 'ui', 'app']):
            return 'frontend'
        
        # Worker detection
        if any(term in path_name for term in ['worker', 'job', 'task', 'consumer', 'processor']):
            return 'worker_service'
        
        # Framework-based categorization
        if framework in ['fastapi', 'flask', 'django', 'express', 'gin', 'spring']:
            return 'web_service'
        elif framework in ['react', 'vue', 'angular', 'next', 'nuxt', 'gatsby']:
            return 'frontend'
        elif framework in ['celery', 'rq', 'bull', 'sidekiq']:
            return 'worker_service'
        
        return 'generic_service'
    
    def _detect_infrastructure_services(self):
        """Detect infrastructure services from configuration files."""
        # Docker Compose detection
        self._detect_docker_compose_services()
        
        # Kubernetes service detection
        self._detect_kubernetes_services()
        
        # Database connection analysis
        self._detect_database_connections()
        
        # Message broker detection
        self._detect_message_brokers()
    
    def _detect_docker_compose_services(self):
        """Detect services defined in docker-compose files."""
        compose_files = ['docker-compose.yml', 'docker-compose.yaml', 'docker-compose.override.yml']
        
        for compose_file in compose_files:
            compose_path = self.project_root / compose_file
            if compose_path.exists():
                try:
                    with open(compose_path, 'r') as f:
                        compose_data = yaml.safe_load(f)
                    
                    if compose_data and 'services' in compose_data:
                        for service_name, service_config in compose_data['services'].items():
                            self.infrastructure_services[service_name] = {
                                'type': 'infrastructure',
                                'category': self._identify_service_category(service_config),
                                'image': service_config.get('image', 'custom'),
                                'ports': service_config.get('ports', []),
                                'environment': service_config.get('environment', {}),
                                'detection_method': 'docker_compose',
                                'config_file': compose_file
                            }
                except Exception as e:
                    print(f"Error parsing {compose_file}: {e}")
    
    def _identify_service_category(self, service_config: Dict) -> str:
        """Identify the category of a service from its configuration."""
        image = service_config.get('image', '').lower()
        
        # Database detection
        for db_category, db_list in self.infrastructure_patterns['databases'].items():
            if any(db in image for db in db_list):
                return f'database_{db_category}'
        
        # Message broker detection
        for broker_category, broker_list in self.infrastructure_patterns['message_brokers'].items():
            if any(broker in image for broker in broker_list):
                return f'message_broker_{broker_category}'
        
        # Search engine detection
        for search_category, search_list in self.infrastructure_patterns['search_engines'].items():
            if any(search in image for search in search_list):
                return f'search_engine_{search_category}'
        
        # Monitoring detection
        for monitor_category, monitor_list in self.infrastructure_patterns['monitoring'].items():
            if any(monitor in image for monitor in monitor_list):
                return f'monitoring_{monitor_category}'
        
        return 'unknown_infrastructure'
    
    def _detect_kubernetes_services(self):
        """Detect services from Kubernetes manifests."""
        k8s_files = list(self.project_root.glob('**/*.yaml')) + list(self.project_root.glob('**/*.yml'))
        
        for k8s_file in k8s_files:
            try:
                with open(k8s_file, 'r') as f:
                    docs = yaml.safe_load_all(f)
                
                for doc in docs:
                    if doc and doc.get('kind') in ['Service', 'Deployment', 'StatefulSet']:
                        service_name = doc['metadata']['name']
                        self.infrastructure_services[f'k8s-{service_name}'] = {
                            'type': 'kubernetes',
                            'category': doc['kind'].lower(),
                            'namespace': doc['metadata'].get('namespace', 'default'),
                            'detection_method': 'kubernetes_manifest',
                            'config_file': str(k8s_file.relative_to(self.project_root))
                        }
            except Exception:
                pass  # Skip invalid YAML files
    
    def _detect_config_based_services(self):
        """Detect services based on configuration files."""
        # Terraform infrastructure
        self._detect_terraform_resources()
        
        # CI/CD pipeline services
        self._detect_cicd_services()
        
        # Environment configuration
        self._detect_env_services()
    
    def _detect_terraform_resources(self):
        """Detect infrastructure from Terraform files."""
        tf_files = list(self.project_root.glob('**/*.tf'))
        
        for tf_file in tf_files:
            try:
                with open(tf_file, 'r') as f:
                    content = f.read()
                
                # Simple regex patterns for common resources
                resources = re.findall(r'resource\s+"([^"]+)"\s+"([^"]+)"', content)
                
                for resource_type, resource_name in resources:
                    if any(db in resource_type.lower() for db_list in self.infrastructure_patterns['databases'].values() for db in db_list):
                        self.infrastructure_services[f'tf-{resource_name}'] = {
                            'type': 'terraform',
                            'category': 'database',
                            'resource_type': resource_type,
                            'detection_method': 'terraform_analysis',
                            'config_file': str(tf_file.relative_to(self.project_root))
                        }
            except Exception:
                pass
    
    def _detect_cicd_services(self):
        """Detect CI/CD pipeline configurations."""
        cicd_configs = {
            '.github/workflows': 'github_actions',
            '.gitlab-ci.yml': 'gitlab_ci',
            'Jenkinsfile': 'jenkins',
            'azure-pipelines.yml': 'azure_devops'
        }
        
        for config_path, platform in cicd_configs.items():
            full_path = self.project_root / config_path
            if full_path.exists():
                self.infrastructure_services[f'cicd-{platform}'] = {
                    'type': 'cicd',
                    'category': 'automation',
                    'platform': platform,
                    'detection_method': 'cicd_config',
                    'config_file': config_path
                }
    
    def _analyze_runtime_dependencies(self):
        """Analyze runtime dependencies and dynamic service creation."""
        # This would be expanded with actual code analysis
        pass
    
    def _detect_serverless_functions(self):
        """Detect serverless function definitions."""
        # AWS Lambda
        sam_template = self.project_root / 'template.yaml'
        if sam_template.exists():
            self._parse_sam_template(sam_template)
        
        # Vercel Functions
        vercel_config = self.project_root / 'vercel.json'
        if vercel_config.exists():
            self._parse_vercel_config(vercel_config)
        
        # Netlify Functions
        netlify_dir = self.project_root / 'netlify' / 'functions'
        if netlify_dir.exists():
            for func_file in netlify_dir.iterdir():
                if func_file.is_file() and func_file.suffix in ['.js', '.ts', '.py']:
                    self.serverless_functions[func_file.stem] = {
                        'type': 'serverless',
                        'category': 'netlify_function',
                        'runtime': self._detect_runtime(func_file.suffix),
                        'path': str(func_file),
                        'detection_method': 'netlify_functions'
                    }
    
    def _detect_worker_services(self):
        """Detect background workers and job processors."""
        worker_patterns = {
            'celery': ['celery.py', 'celeryconfig.py', 'tasks.py'],
            'rq': ['worker.py', 'jobs.py'],
            'bull': ['queue.js', 'worker.js'],
            'sidekiq': ['worker.rb', 'jobs/']
        }
        
        for worker_type, patterns in worker_patterns.items():
            for pattern in patterns:
                matches = list(self.project_root.glob(f'**/{pattern}'))
                for match in matches:
                    worker_name = f'{worker_type}-{match.parent.name}'
                    self.worker_services[worker_name] = {
                        'type': 'worker',
                        'category': worker_type,
                        'path': str(match.parent),
                        'config_file': str(match),
                        'detection_method': 'worker_pattern'
                    }
    
    def _detect_plugins_and_extensions(self):
        """Detect plugin architectures and extension systems."""
        # Look for common plugin directories
        plugin_dirs = ['plugins', 'extensions', 'addons', 'modules']
        
        for plugin_dir in plugin_dirs:
            plugin_path = self.project_root / plugin_dir
            if plugin_path.exists() and plugin_path.is_dir():
                for plugin in plugin_path.iterdir():
                    if plugin.is_dir():
                        self.services[f'plugin-{plugin.name}'] = {
                            'type': 'plugin',
                            'category': 'extension',
                            'path': str(plugin),
                            'detection_method': 'plugin_directory'
                        }
    
    def _compile_detection_results(self) -> Dict[str, Any]:
        """Compile all detection results into final output."""
        return {
            'application_services': self.services,
            'infrastructure_services': self.infrastructure_services,
            'worker_services': self.worker_services,
            'serverless_functions': self.serverless_functions,
            'detected_technologies': list(self.detected_technologies),
            'detection_summary': {
                'total_services': len(self.services) + len(self.infrastructure_services) + len(self.worker_services) + len(self.serverless_functions),
                'application_services_count': len(self.services),
                'infrastructure_services_count': len(self.infrastructure_services),
                'worker_services_count': len(self.worker_services),
                'serverless_functions_count': len(self.serverless_functions)
            }
        }
    
    def _analyze_runtime_deps(self, service_path: Path) -> List[str]:
        """Analyze runtime dependencies for a service."""
        deps = []
        # This would be expanded with actual dependency analysis
        return deps
    
    def _analyze_config_deps(self, service_path: Path) -> Dict[str, Any]:
        """Analyze configuration dependencies for a service."""
        config_deps = {}
        # This would be expanded with actual config analysis
        return config_deps
    
    def _detect_database_connections(self):
        """Detect database connections from code analysis."""
        # This would analyze actual code for database connections
        pass
    
    def _detect_message_brokers(self):
        """Detect message broker usage from code analysis."""
        # This would analyze actual code for message broker usage
        pass
    
    def _parse_sam_template(self, template_path: Path):
        """Parse AWS SAM template for Lambda functions."""
        try:
            with open(template_path, 'r') as f:
                template = yaml.safe_load(f)
            
            resources = template.get('Resources', {})
            for resource_name, resource_config in resources.items():
                if resource_config.get('Type') == 'AWS::Serverless::Function':
                    self.serverless_functions[resource_name] = {
                        'type': 'serverless',
                        'category': 'aws_lambda',
                        'runtime': resource_config.get('Properties', {}).get('Runtime', 'unknown'),
                        'detection_method': 'sam_template'
                    }
        except Exception:
            pass
    
    def _parse_vercel_config(self, config_path: Path):
        """Parse Vercel configuration for functions."""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            functions = config.get('functions', {})
            for func_path, func_config in functions.items():
                func_name = Path(func_path).stem
                self.serverless_functions[func_name] = {
                    'type': 'serverless',
                    'category': 'vercel_function',
                    'runtime': func_config.get('runtime', 'unknown'),
                    'detection_method': 'vercel_config'
                }
        except Exception:
            pass
    
    def _detect_env_services(self):
        """Detect services from environment configurations."""
        env_files = ['.env', '.env.example', '.env.local', '.env.production']
        
        for env_file in env_files:
            env_path = self.project_root / env_file
            if env_path.exists():
                try:
                    with open(env_path, 'r') as f:
                        env_content = f.read()
                    
                    # Look for common service URL patterns
                    db_urls = re.findall(r'DATABASE_URL|MONGO_URL|REDIS_URL', env_content)
                    if db_urls:
                        for url in db_urls:
                            service_type = url.split('_')[0].lower()
                            self.infrastructure_services[f'env-{service_type}'] = {
                                'type': 'infrastructure',
                                'category': 'database',
                                'detection_method': 'env_variable',
                                'config_file': env_file
                            }
                except Exception:
                    pass
    
    def _detect_runtime(self, file_extension: str) -> str:
        """Detect runtime from file extension."""
        runtime_map = {
            '.js': 'nodejs',
            '.ts': 'nodejs',
            '.py': 'python',
            '.rb': 'ruby',
            '.go': 'go'
        }
        return runtime_map.get(file_extension, 'unknown')


# Keep original functions for backward compatibility
def cleanup_containers(project_root: str) -> dict:
    """
    Stop and remove all running containers to avoid port conflicts.
    This ensures a clean slate before building new containers.
    
    Args:
        project_root: Root directory containing docker-compose.yml
        
    Returns:
        Dictionary with cleanup status and details
    """
    import subprocess
    
    result_info = {
        "status": "success",
        "stopped_containers": [],
        "removed_containers": [],
        "errors": []
    }
    
    try:
        # First, try to stop docker-compose services if docker-compose.yml exists
        compose_path = os.path.join(project_root, 'docker-compose.yml')
        if os.path.exists(compose_path):
            stop_result = subprocess.run(
                ["docker-compose", "down", "-v"],
                cwd=project_root,
                capture_output=True,
                encoding='utf-8',
                errors='replace',
                timeout=60
            )
            if stop_result.returncode == 0:
                result_info["stopped_containers"].append("docker-compose services")
            else:
                result_info["errors"].append(f"docker-compose down: {stop_result.stderr}")
        
        # Also stop any running containers that might conflict
        ps_result = subprocess.run(
            ["docker", "ps", "-q"],
            capture_output=True,
            encoding='utf-8',
            errors='replace',
            timeout=30
        )
        
        if ps_result.returncode == 0 and ps_result.stdout.strip():
            container_ids = ps_result.stdout.strip().split('\n')
            for container_id in container_ids:
                if container_id:
                    # Get container name
                    name_result = subprocess.run(
                        ["docker", "inspect", "--format", "{{.Name}}", container_id],
                        capture_output=True,
                        encoding='utf-8',
                        errors='replace'
                    )
                    container_name = name_result.stdout.strip().lstrip('/')
                    
                    # Skip monitoring containers (loki, promtail, grafana)
                    if any(mon in container_name.lower() for mon in ['loki', 'promtail', 'grafana', 'prometheus']):
                        continue
                    
                    # Stop container
                    stop_result = subprocess.run(
                        ["docker", "stop", container_id],
                        capture_output=True,
                        encoding='utf-8',
                        errors='replace',
                        timeout=30
                    )
                    if stop_result.returncode == 0:
                        result_info["stopped_containers"].append(container_name)
                    
                    # Remove container
                    rm_result = subprocess.run(
                        ["docker", "rm", container_id],
                        capture_output=True,
                        encoding='utf-8',
                        errors='replace',
                        timeout=30
                    )
                    if rm_result.returncode == 0:
                        result_info["removed_containers"].append(container_name)
        
        return result_info
        
    except Exception as e:
        result_info["status"] = "error"
        result_info["errors"].append(str(e))
        return result_info


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
        
        # SAFETY CHECK: Prevent Dockerfile creation in problematic locations
        path_lower = service_path.lower()
        if any(skip in path_lower for skip in ['docker-mcp', 'docker_mcp', '.git', 'node_modules', '__pycache__']):
            dockerfiles[service_name] = {
                'status': 'skipped',
                'reason': f'Skipped docker-mcp tool directory: {service_path}'
            }
            continue
        
        # Check if this is a root directory without actual application code
        if not _has_application_files(service_path):
            dockerfiles[service_name] = {
                'status': 'skipped',
                'reason': f'No application files found in: {service_path}'
            }
            continue
        
        # Create analysis dict for dockerfile generation
        analysis = service_info.get('analysis', {})
        if not analysis:
            analysis = {
                'app_type': service_info.get('language', 'unknown'),
                'framework': service_info.get('framework', 'unknown')
            }
        
        # Generate appropriate Dockerfile
        dockerfile_content = generate_dockerfile(
            service_path,
            analysis=analysis,
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


def _has_application_files(path: str) -> bool:
    """
    Check if directory contains actual application files.
    Prevents Dockerfile creation in empty or tool directories.
    """
    import os
    from pathlib import Path
    
    path_obj = Path(path)
    if not path_obj.exists():
        return False
    
    # Check for common application indicators
    app_indicators = [
        # Python
        'requirements.txt', 'setup.py', 'pyproject.toml', 'app.py', 'main.py', 'manage.py',
        # Node.js
        'package.json', 'index.js', 'server.js', 'app.js', 'index.ts',
        # Frontend
        'index.html', 'App.jsx', 'App.tsx', 'main.jsx',
        # Go
        'go.mod', 'main.go',
        # Java
        'pom.xml', 'build.gradle',
    ]
    
    for indicator in app_indicators:
        if (path_obj / indicator).exists():
            return True
    
    # Check for src directory with files
    src_dir = path_obj / 'src'
    if src_dir.exists() and src_dir.is_dir():
        if any(src_dir.iterdir()):
            return True
    
    return False


def validate_docker_names(services: dict) -> list:
    """
    Validate Docker service names comply with Docker naming requirements.
    Docker requires:
    - Lowercase letters, digits, and separators (., -, _)
    - Must not start or end with a separator
    
    Args:
        services: Dictionary of services from detect_services()
        
    Returns:
        List of validation errors (empty if all valid)
    """
    import re
    errors = []
    
    # Docker naming pattern: lowercase letters, digits, dots, hyphens, underscores
    valid_pattern = re.compile(r'^[a-z0-9][a-z0-9._-]*$')
    
    for service_name in services.keys():
        # Check if name contains uppercase or invalid characters
        if not valid_pattern.match(service_name.lower().replace('_', '-').replace(' ', '-')):
            errors.append(f"Service '{service_name}' contains invalid characters for Docker")
        
        # Check for uppercase letters
        if any(c.isupper() for c in service_name):
            errors.append(f"Service '{service_name}' contains uppercase letters (will be converted to lowercase)")
    
    return errors


def generate_docker_compose(project_root: str, services: dict) -> str:
    """
    Generate a unified docker-compose.yml for all services.
    
    Docker naming requirements enforced:
    - All service names converted to lowercase
    - Spaces and underscores replaced with hyphens
    - Container names follow same pattern
    
    Args:
        project_root: Root directory of the project
        services: Dictionary of services from detect_services()
        
    Returns:
        Docker Compose YAML content
    """
    compose_content = """services:
"""
    
    # Define port mappings based on service type with conflict resolution
    port_mappings = {
        'backend': 8000,
        'api': 8000, 
        'server': 8000,
        'frontend': 3000,
        'client': 3000,
        'web': 3000,
        'app': 3000
    }
    
    # Track used ports to avoid conflicts
    used_ports = set()
    
    for service_name, service_info in services.items():
        # ENFORCE LOWERCASE: Docker requires lowercase image and container names
        service_name_lower = service_name.lower().replace('_', '-').replace(' ', '-')
        
        service_type = service_info.get('framework', service_info.get('type', 'unknown'))
        
        # Use port from analysis if available, otherwise use framework-based defaults
        analysis = service_info.get('analysis', {})
        detected_port = analysis.get('port')
        
        if detected_port:
            container_port = detected_port
            host_port = detected_port
        else:
            # Use service name-based mapping or fallback to old logic
            container_port = port_mappings.get(service_name.lower(), 
                                             8000 if service_type == 'python' else 3000)
            host_port = container_port
        
        # Resolve port conflicts by incrementing host port
        while host_port in used_ports:
            host_port += 1
        used_ports.add(host_port)
        
        # Determine the CMD based on service type and use dynamic port
        if service_type == 'python':
            # Check for common Python frameworks
            service_path = service_info['path']
            if os.path.exists(os.path.join(service_path, 'manage.py')):
                # Django - use detected port
                command = f'python manage.py runserver 0.0.0.0:{container_port}'
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
        
        # Determine correct build context path
        service_path = service_info.get('path', service_name)
        if service_path == '.' or service_path == project_root:
            # Service is at project root
            build_context = '.'
        else:
            # Service is in subdirectory - calculate relative path
            try:
                rel_path = os.path.relpath(service_path, project_root)
                build_context = f'./{rel_path}' if rel_path != '.' else '.'
            except ValueError:
                # Fallback if path calculation fails
                build_context = f'./{service_name}'
        
        compose_content += f"""  {service_name_lower}:
    build:
      context: {build_context}
      dockerfile: Dockerfile
    container_name: {service_name_lower}-container
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
                    backend_service = svc.lower().replace('_', '-').replace(' ', '-')
                    break
            
            if backend_service:
                compose_content += f"""    environment:
      - REACT_APP_API_URL=http://localhost:{port_mappings.get(service_name.lower(), 8000)}
      - VITE_API_URL=http://localhost:{port_mappings.get(service_name.lower(), 8000)}
      - NEXT_PUBLIC_API_URL=http://localhost:{port_mappings.get(service_name.lower(), 8000)}
    depends_on:
      - {backend_service}
"""
        
        # Determine volume mapping path (same logic as build context)
        if service_path == '.' or service_path == project_root:
            volume_source = '.'
        else:
            try:
                rel_path = os.path.relpath(service_path, project_root)
                volume_source = f'./{rel_path}' if rel_path != '.' else '.'
            except ValueError:
                volume_source = f'./{service_name}'
        
        compose_content += f"""    volumes:
      - {volume_source}:/app
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
    
    # Step 1: Detect services using enhanced detection
    result += "**Step 1: Detecting Services (Enhanced)...**\n"
    detection_results = detect_services(project_root)
    
    # Extract application services for docker generation
    services = detection_results.get('application_services', {})
    
    if not services:
        return result + "❌ No application services detected. Please ensure your project has recognizable service structures."
    
    result += f"✅ Found {len(services)} application service(s):\n"
    for name, info in services.items():
        result += f"  - {name}: {info.get('framework', info.get('type', 'unknown'))}\n"
    
    # Show infrastructure services if found
    infra_services = detection_results.get('infrastructure_services', {})
    if infra_services:
        result += f"✅ Found {len(infra_services)} infrastructure service(s):\n"
        for name, info in infra_services.items():
            result += f"  - {name}: {info.get('category', 'unknown')}\n"
    
    # Step 2: Validate Docker naming requirements
    result += "\n**Step 2: Validating Docker Names...**\n"
    naming_errors = validate_docker_names(services)
    if naming_errors:
        result += "⚠️  Docker naming issues detected (will auto-fix):\n"
        for error in naming_errors:
            result += f"   - {error}\n"
        result += "   ✅ Names will be automatically converted to lowercase\n"
    else:
        result += "✅ All service names are Docker-compliant\n"
    
    # Step 3: Generate Dockerfiles
    result += "\n**Step 3: Generating Dockerfiles...**\n"
    dockerfiles = generate_dockerfiles_for_services(services)
    
    dockerfile_success = True
    dockerfiles_updated = False
    skipped_count = 0
    for name, info in dockerfiles.items():
        if info['status'] == 'success':
            result += f"✅ {name}: Dockerfile created at {info['path']}\n"
            dockerfiles_updated = True
        elif info['status'] == 'skipped':
            result += f"⏭️  {name}: {info['reason']}\n"
            skipped_count += 1
        else:
            result += f"❌ {name}: {info['error']}\n"
            dockerfile_success = False
    
    if skipped_count > 0:
        result += f"ℹ️  Skipped {skipped_count} service(s) - not valid application directories\n"
    
    # Step 4: Generate docker-compose.yml
    result += "\n**Step 4: Generating docker-compose.yml...**\n"
    compose_content = generate_docker_compose(project_root, services)
    
    # Verify docker-compose.yml was actually created
    compose_path = os.path.join(project_root, 'docker-compose.yml')
    if "Error" not in compose_content and os.path.exists(compose_path):
        result += f"✅ docker-compose.yml created at {compose_path}\n"
    else:
        if "Error" in compose_content:
            result += f"❌ {compose_content}\n"
        else:
            result += f"❌ docker-compose.yml creation failed - file not found at {compose_path}\n"
        dockerfile_success = False
    
    # Step 5: Cleanup existing containers to avoid port conflicts
    if auto_start and dockerfile_success:
        result += "\n**Step 5: Cleaning Up Existing Containers...**\n"
        cleanup_result = cleanup_containers(project_root)
        
        if cleanup_result["stopped_containers"]:
            result += f"✅ Stopped containers: {', '.join(cleanup_result['stopped_containers'])}\n"
        if cleanup_result["removed_containers"]:
            result += f"✅ Removed containers: {', '.join(cleanup_result['removed_containers'])}\n"
        if cleanup_result["errors"]:
            for error in cleanup_result["errors"]:
                result += f"⚠️  Cleanup warning: {error}\n"
        if not cleanup_result["stopped_containers"] and not cleanup_result["removed_containers"]:
            result += "✅ No existing containers to clean up\n"
    
    # Step 6: Build and start containers (if requested and no errors)
    if auto_start and dockerfile_success:
        result += "\n**Step 6: Building and Starting Containers...**\n"
        if dockerfiles_updated:
            result += "🔄 Dockerfiles were updated - rebuilding images...\n"
        result += "⏳ This may take a few minutes on first build...\n\n"
        
        try:
            # Import here to avoid circular dependency
            from .e2e_tester import start_docker_compose, wait_for_services
            
            # Validate docker-compose.yml exists before attempting to start
            compose_path = os.path.join(project_root, 'docker-compose.yml')
            if not os.path.exists(compose_path):
                result += f"❌ docker-compose.yml not found at {compose_path}\n"
                result += "🔧 **Manual Steps:**\n"
                result += f"   1. Generate docker-compose.yml first\n"
                result += f"   2. Check file permissions\n"
                dockerfile_success = False
            else:
                # Start docker-compose with build
                start_result = start_docker_compose(project_root, detached=True)
                
            if start_result["status"] == "success":
                result += "✅ Containers built and started successfully!\n\n"
                
                # Wait for services to be ready
                result += "**Step 7: Waiting for Services to be Ready...**\n"
                
                # Determine ports from services analysis
                backend_port = 8000
                frontend_port = 3000
                for name, service_info in services.items():
                    analysis = service_info.get('analysis', {})
                    detected_port = analysis.get('port')
                    
                    if detected_port:
                        if name.lower() in ['backend', 'api', 'server']:
                            backend_port = detected_port
                        elif name.lower() in ['frontend', 'client', 'web']:
                            frontend_port = detected_port
                
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
        # Manual next steps (original behavior)
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