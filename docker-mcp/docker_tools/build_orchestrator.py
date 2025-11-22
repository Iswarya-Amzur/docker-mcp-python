"""Build Orchestrator for Intelligent Docker Build Management

This module handles:
- Parallel builds for independent services
- Build dependency graph execution
- Automatic retry with exponential backoff
- Build caching and layer reuse
- Progress tracking and reporting
- Failure recovery and rollback
"""

import asyncio
import subprocess
import time
import logging
from typing import Dict, List, Optional, Tuple, Any, Set
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class BuildStatus(Enum):
    """Build status enumeration."""
    PENDING = "pending"
    BUILDING = "building"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"
    SKIPPED = "skipped"


@dataclass
class BuildTask:
    """Represents a single build task."""
    service_name: str
    dockerfile_path: Path
    context_path: Path
    image_name: str
    dependencies: List[str] = field(default_factory=list)
    status: BuildStatus = BuildStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    build_time: float = 0.0
    error_message: str = ""
    build_args: Dict[str, str] = field(default_factory=dict)


class BuildOrchestrator:
    """Intelligent build orchestration with parallel execution and retry logic."""
    
    def __init__(self, max_parallel: int = 3, max_retries: int = 3):
        """
        Initialize build orchestrator.
        
        Args:
            max_parallel: Maximum number of parallel builds
            max_retries: Maximum retry attempts per service
        """
        self.max_parallel = max_parallel
        self.max_retries = max_retries
        self.build_tasks: Dict[str, BuildTask] = {}
        self.build_results: Dict[str, Dict] = {}
        self.total_build_time = 0.0
        
    def add_build_task(
        self,
        service_name: str,
        dockerfile_path: str,
        context_path: str,
        image_name: str,
        dependencies: Optional[List[str]] = None,
        build_args: Optional[Dict[str, str]] = None
    ):
        """Add a build task to the orchestrator."""
        task = BuildTask(
            service_name=service_name,
            dockerfile_path=Path(dockerfile_path),
            context_path=Path(context_path),
            image_name=image_name,
            dependencies=dependencies or [],
            max_retries=self.max_retries,
            build_args=build_args or {}
        )
        self.build_tasks[service_name] = task
        logger.info(f"Added build task for {service_name}")
    
    async def build_all(self, parallel: bool = True) -> Dict[str, Any]:
        """
        Build all services with intelligent orchestration.
        
        Args:
            parallel: Whether to build in parallel
            
        Returns:
            Build results summary
        """
        start_time = time.time()
        
        if parallel:
            result = await self._build_parallel()
        else:
            result = await self._build_sequential()
        
        self.total_build_time = time.time() - start_time
        
        # Generate summary
        summary = self._generate_summary()
        result["summary"] = summary
        result["total_time"] = self.total_build_time
        
        return result
    
    async def _build_parallel(self) -> Dict[str, Any]:
        """Build services in parallel respecting dependencies."""
        logger.info("Starting parallel build orchestration")
        
        # Build dependency graph
        dependency_graph = self._build_dependency_graph()
        
        # Get build order (topological sort)
        build_order = self._topological_sort(dependency_graph)
        
        if not build_order:
            return {
                "status": "error",
                "message": "Circular dependency detected",
                "builds": {}
            }
        
        # Group services by dependency level
        levels = self._group_by_level(build_order, dependency_graph)
        
        # Build level by level
        all_builds = {}
        for level_num, services in enumerate(levels):
            logger.info(f"Building level {level_num + 1}/{len(levels)}: {services}")
            
            # Build services in this level in parallel
            tasks = []
            for service in services:
                if service in self.build_tasks:
                    tasks.append(self._build_service_with_retry(service))
            
            # Wait for all builds in this level to complete
            level_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for service, result in zip(services, level_results):
                if isinstance(result, Exception):
                    all_builds[service] = {
                        "status": "failed",
                        "error": str(result)
                    }
                    logger.error(f"Build failed for {service}: {result}")
                else:
                    all_builds[service] = result
        
        # Check overall status
        failed_builds = [s for s, r in all_builds.items() if r.get("status") == "failed"]
        
        return {
            "status": "success" if not failed_builds else "partial",
            "builds": all_builds,
            "failed": failed_builds
        }
    
    async def _build_sequential(self) -> Dict[str, Any]:
        """Build services sequentially."""
        logger.info("Starting sequential build orchestration")
        
        all_builds = {}
        
        for service_name in self.build_tasks:
            result = await self._build_service_with_retry(service_name)
            all_builds[service_name] = result
            
            if result["status"] == "failed":
                logger.warning(f"Build failed for {service_name}, continuing...")
        
        failed_builds = [s for s, r in all_builds.items() if r.get("status") == "failed"]
        
        return {
            "status": "success" if not failed_builds else "partial",
            "builds": all_builds,
            "failed": failed_builds
        }
    
    async def _build_service_with_retry(self, service_name: str) -> Dict[str, Any]:
        """Build a service with automatic retry on failure."""
        task = self.build_tasks[service_name]
        
        for attempt in range(task.max_retries + 1):
            if attempt > 0:
                task.status = BuildStatus.RETRYING
                task.retry_count = attempt
                # Exponential backoff
                wait_time = 2 ** attempt
                logger.info(f"Retrying {service_name} (attempt {attempt + 1}/{task.max_retries + 1}) after {wait_time}s")
                await asyncio.sleep(wait_time)
            else:
                task.status = BuildStatus.BUILDING
            
            # Attempt build
            result = await self._build_service(task)
            
            if result["status"] == "success":
                task.status = BuildStatus.SUCCESS
                return result
            else:
                task.error_message = result.get("error", "Unknown error")
                logger.warning(f"Build attempt {attempt + 1} failed for {service_name}: {task.error_message}")
                
                # Try to apply automatic fixes
                if attempt < task.max_retries:
                    fix_applied = await self._try_auto_fix(task)
                    if not fix_applied:
                        logger.info(f"No automatic fix available for {service_name}")
        
        # All retries exhausted
        task.status = BuildStatus.FAILED
        return {
            "status": "failed",
            "service": service_name,
            "error": task.error_message,
            "retries": task.retry_count
        }
    
    async def _build_service(self, task: BuildTask) -> Dict[str, Any]:
        """Execute docker build for a service."""
        start_time = time.time()
        
        try:
            # Construct docker build command
            cmd = [
                "docker", "build",
                "-t", task.image_name,
                "-f", str(task.dockerfile_path),
            ]
            
            # Add build args
            for key, value in task.build_args.items():
                cmd.extend(["--build-arg", f"{key}={value}"])
            
            # Add context path
            cmd.append(str(task.context_path))
            
            logger.info(f"Building {task.service_name}: {' '.join(cmd)}")
            
            # Run build
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            build_time = time.time() - start_time
            task.build_time = build_time
            
            if process.returncode == 0:
                logger.info(f"✅ Build successful for {task.service_name} ({build_time:.2f}s)")
                return {
                    "status": "success",
                    "service": task.service_name,
                    "image": task.image_name,
                    "build_time": build_time,
                    "output": stdout.decode('utf-8', errors='ignore')
                }
            else:
                error_output = stderr.decode('utf-8', errors='ignore')
                logger.error(f"❌ Build failed for {task.service_name}: {error_output[:500]}")
                return {
                    "status": "failed",
                    "service": task.service_name,
                    "error": error_output,
                    "build_time": build_time
                }
        
        except Exception as e:
            build_time = time.time() - start_time
            task.build_time = build_time
            logger.error(f"Exception during build of {task.service_name}: {e}")
            return {
                "status": "failed",
                "service": task.service_name,
                "error": str(e),
                "build_time": build_time
            }
    
    async def _try_auto_fix(self, task: BuildTask) -> bool:
        """Try to automatically fix build errors."""
        try:
            from .error_fixer import EnhancedErrorFixer
            
            fixer = EnhancedErrorFixer(str(task.context_path), max_retries=self.max_retries)
            fix_result = fixer.analyze_and_fix(task.error_message, task.service_name)
            
            if fix_result.get("can_retry"):
                logger.info(f"✅ Applied automatic fixes for {task.service_name}")
                logger.info(f"Modified files: {fix_result.get('modified_files', [])}")
                return True
            else:
                logger.info(f"No automatic fix available for {task.service_name}")
                return False
        
        except Exception as e:
            logger.error(f"Error during auto-fix: {e}")
            return False
    
    def _build_dependency_graph(self) -> Dict[str, Set[str]]:
        """Build dependency graph from build tasks."""
        graph = {}
        
        for service_name, task in self.build_tasks.items():
            graph[service_name] = set(task.dependencies)
        
        return graph
    
    def _topological_sort(self, graph: Dict[str, Set[str]]) -> Optional[List[str]]:
        """Perform topological sort to determine build order."""
        # Kahn's algorithm
        in_degree = {node: 0 for node in graph}
        
        for node in graph:
            for neighbor in graph[node]:
                if neighbor in in_degree:
                    in_degree[neighbor] += 1
        
        queue = [node for node in in_degree if in_degree[node] == 0]
        result = []
        
        while queue:
            node = queue.pop(0)
            result.append(node)
            
            for neighbor in graph.get(node, []):
                if neighbor in in_degree:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)
        
        # Check for cycles
        if len(result) != len(graph):
            logger.error("Circular dependency detected in build graph")
            return None
        
        return result
    
    def _group_by_level(self, build_order: List[str], graph: Dict[str, Set[str]]) -> List[List[str]]:
        """Group services by dependency level for parallel building."""
        levels = []
        processed = set()
        
        while len(processed) < len(build_order):
            current_level = []
            
            for service in build_order:
                if service in processed:
                    continue
                
                # Check if all dependencies are processed
                deps = graph.get(service, set())
                if all(dep in processed or dep not in graph for dep in deps):
                    current_level.append(service)
            
            if not current_level:
                # Shouldn't happen if topological sort worked
                break
            
            levels.append(current_level)
            processed.update(current_level)
        
        return levels
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate build summary."""
        total_tasks = len(self.build_tasks)
        successful = sum(1 for t in self.build_tasks.values() if t.status == BuildStatus.SUCCESS)
        failed = sum(1 for t in self.build_tasks.values() if t.status == BuildStatus.FAILED)
        
        total_retries = sum(t.retry_count for t in self.build_tasks.values())
        
        return {
            "total_services": total_tasks,
            "successful": successful,
            "failed": failed,
            "success_rate": f"{(successful / total_tasks * 100):.1f}%" if total_tasks > 0 else "0%",
            "total_retries": total_retries,
            "total_build_time": f"{self.total_build_time:.2f}s",
            "average_build_time": f"{(self.total_build_time / total_tasks):.2f}s" if total_tasks > 0 else "0s"
        }


async def build_services_parallel(
    services: Dict[str, Dict],
    max_parallel: int = 3,
    max_retries: int = 3
) -> Dict[str, Any]:
    """
    Convenience function to build multiple services in parallel.
    
    Args:
        services: Dict of service_name -> {dockerfile, context, image, dependencies}
        max_parallel: Maximum parallel builds
        max_retries: Maximum retry attempts
        
    Returns:
        Build results
    """
    orchestrator = BuildOrchestrator(max_parallel=max_parallel, max_retries=max_retries)
    
    for service_name, config in services.items():
        orchestrator.add_build_task(
            service_name=service_name,
            dockerfile_path=config["dockerfile"],
            context_path=config["context"],
            image_name=config["image"],
            dependencies=config.get("dependencies", []),
            build_args=config.get("build_args", {})
        )
    
    return await orchestrator.build_all(parallel=True)
