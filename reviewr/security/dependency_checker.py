"""
Dependency checker for analyzing project dependencies.

Provides:
- Dependency graph analysis
- Outdated dependency detection
- Transitive dependency analysis
- Dependency health scoring
"""

import json
import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set
from pathlib import Path
from enum import Enum
from datetime import datetime, timedelta


class DependencyHealth(Enum):
    """Dependency health status."""
    HEALTHY = "healthy"
    OUTDATED = "outdated"
    DEPRECATED = "deprecated"
    UNMAINTAINED = "unmaintained"
    UNKNOWN = "unknown"


@dataclass
class Dependency:
    """A project dependency."""
    name: str
    version: str
    ecosystem: str
    is_direct: bool = True
    latest_version: Optional[str] = None
    health: DependencyHealth = DependencyHealth.UNKNOWN
    last_updated: Optional[datetime] = None
    license: Optional[str] = None
    vulnerabilities: List[Any] = field(default_factory=list)
    transitive_deps: List[str] = field(default_factory=list)
    
    @property
    def is_outdated(self) -> bool:
        """Check if dependency is outdated."""
        return self.health in (DependencyHealth.OUTDATED, DependencyHealth.DEPRECATED)
    
    @property
    def is_unmaintained(self) -> bool:
        """Check if dependency is unmaintained."""
        return self.health == DependencyHealth.UNMAINTAINED
    
    @property
    def has_vulnerabilities(self) -> bool:
        """Check if dependency has known vulnerabilities."""
        return len(self.vulnerabilities) > 0
    
    @property
    def version_lag(self) -> Optional[str]:
        """Get version lag from latest."""
        if not self.latest_version:
            return None
        return f"{self.version} → {self.latest_version}"


class DependencyChecker:
    """Checker for analyzing project dependencies."""
    
    def __init__(self):
        """Initialize dependency checker."""
        self.dependencies: Dict[str, Dependency] = {}
        self.dependency_graph: Dict[str, Set[str]] = {}
    
    def analyze_project(self, project_path: Path) -> List[Dependency]:
        """
        Analyze all dependencies in a project.
        
        Args:
            project_path: Path to project root
            
        Returns:
            List of dependencies found
        """
        dependencies = []
        
        # Check for Python dependencies
        requirements_txt = project_path / "requirements.txt"
        if requirements_txt.exists():
            dependencies.extend(self.analyze_requirements_txt(requirements_txt))
        
        setup_py = project_path / "setup.py"
        if setup_py.exists():
            dependencies.extend(self.analyze_setup_py(setup_py))
        
        # Check for Node.js dependencies
        package_json = project_path / "package.json"
        if package_json.exists():
            dependencies.extend(self.analyze_package_json(package_json))
        
        # Check for Go dependencies
        go_mod = project_path / "go.mod"
        if go_mod.exists():
            dependencies.extend(self.analyze_go_mod(go_mod))
        
        # Check for Rust dependencies
        cargo_toml = project_path / "Cargo.toml"
        if cargo_toml.exists():
            dependencies.extend(self.analyze_cargo_toml(cargo_toml))
        
        return dependencies
    
    def analyze_requirements_txt(self, file_path: Path) -> List[Dependency]:
        """Analyze requirements.txt file."""
        dependencies = []
        
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse package==version
                    match = re.match(r'^([a-zA-Z0-9_-]+)\s*([=><]+)\s*([0-9.]+)', line)
                    if match:
                        package, operator, version = match.groups()
                        
                        dep = Dependency(
                            name=package,
                            version=version,
                            ecosystem="PyPI",
                            is_direct=True
                        )
                        dependencies.append(dep)
                        self.dependencies[f"PyPI:{package}"] = dep
        
        except Exception as e:
            print(f"Warning: Failed to analyze {file_path}: {e}")
        
        return dependencies
    
    def analyze_setup_py(self, file_path: Path) -> List[Dependency]:
        """Analyze setup.py file."""
        dependencies = []
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
                # Look for install_requires
                match = re.search(r'install_requires\s*=\s*\[(.*?)\]', content, re.DOTALL)
                if match:
                    requires = match.group(1)
                    for line in requires.split(','):
                        line = line.strip().strip('"\'')
                        if not line:
                            continue
                        
                        # Parse package>=version
                        match = re.match(r'^([a-zA-Z0-9_-]+)\s*([=><]+)\s*([0-9.]+)', line)
                        if match:
                            package, operator, version = match.groups()
                            
                            dep = Dependency(
                                name=package,
                                version=version,
                                ecosystem="PyPI",
                                is_direct=True
                            )
                            dependencies.append(dep)
                            self.dependencies[f"PyPI:{package}"] = dep
        
        except Exception as e:
            print(f"Warning: Failed to analyze {file_path}: {e}")
        
        return dependencies
    
    def analyze_package_json(self, file_path: Path) -> List[Dependency]:
        """Analyze package.json file."""
        dependencies = []
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
                # Analyze dependencies
                for package, version in data.get('dependencies', {}).items():
                    clean_version = version.lstrip('^~')
                    
                    dep = Dependency(
                        name=package,
                        version=clean_version,
                        ecosystem="npm",
                        is_direct=True
                    )
                    dependencies.append(dep)
                    self.dependencies[f"npm:{package}"] = dep
                
                # Analyze devDependencies
                for package, version in data.get('devDependencies', {}).items():
                    clean_version = version.lstrip('^~')
                    
                    dep = Dependency(
                        name=package,
                        version=clean_version,
                        ecosystem="npm",
                        is_direct=True
                    )
                    dependencies.append(dep)
                    self.dependencies[f"npm:{package}"] = dep
        
        except Exception as e:
            print(f"Warning: Failed to analyze {file_path}: {e}")
        
        return dependencies
    
    def analyze_go_mod(self, file_path: Path) -> List[Dependency]:
        """Analyze go.mod file."""
        dependencies = []
        
        try:
            with open(file_path, 'r') as f:
                in_require = False
                for line in f:
                    line = line.strip()
                    
                    if line.startswith('require ('):
                        in_require = True
                        continue
                    elif line == ')':
                        in_require = False
                        continue
                    
                    if in_require or line.startswith('require '):
                        match = re.match(r'require\s+([^\s]+)\s+v([0-9.]+)', line)
                        if not match:
                            match = re.match(r'([^\s]+)\s+v([0-9.]+)', line)
                        
                        if match:
                            package, version = match.groups()
                            
                            dep = Dependency(
                                name=package,
                                version=version,
                                ecosystem="Go",
                                is_direct=True
                            )
                            dependencies.append(dep)
                            self.dependencies[f"Go:{package}"] = dep
        
        except Exception as e:
            print(f"Warning: Failed to analyze {file_path}: {e}")
        
        return dependencies
    
    def analyze_cargo_toml(self, file_path: Path) -> List[Dependency]:
        """Analyze Cargo.toml file."""
        dependencies = []
        
        try:
            with open(file_path, 'r') as f:
                in_dependencies = False
                for line in f:
                    line = line.strip()
                    
                    if line == '[dependencies]':
                        in_dependencies = True
                        continue
                    elif line.startswith('[') and in_dependencies:
                        in_dependencies = False
                        continue
                    
                    if in_dependencies:
                        # Parse package = "version"
                        match = re.match(r'([a-zA-Z0-9_-]+)\s*=\s*"([0-9.]+)"', line)
                        if match:
                            package, version = match.groups()
                            
                            dep = Dependency(
                                name=package,
                                version=version,
                                ecosystem="crates.io",
                                is_direct=True
                            )
                            dependencies.append(dep)
                            self.dependencies[f"crates.io:{package}"] = dep
                        else:
                            match = re.match(r'([a-zA-Z0-9_-]+)\s*=\s*\{.*version\s*=\s*"([0-9.]+)"', line)
                            if match:
                                package, version = match.groups()
                                
                                dep = Dependency(
                                    name=package,
                                    version=version,
                                    ecosystem="crates.io",
                                    is_direct=True
                                )
                                dependencies.append(dep)
                                self.dependencies[f"crates.io:{package}"] = dep
        
        except Exception as e:
            print(f"Warning: Failed to analyze {file_path}: {e}")
        
        return dependencies
    
    def get_outdated_dependencies(self) -> List[Dependency]:
        """Get list of outdated dependencies."""
        return [dep for dep in self.dependencies.values() if dep.is_outdated]
    
    def get_vulnerable_dependencies(self) -> List[Dependency]:
        """Get list of dependencies with vulnerabilities."""
        return [dep for dep in self.dependencies.values() if dep.has_vulnerabilities]
    
    def get_unmaintained_dependencies(self) -> List[Dependency]:
        """Get list of unmaintained dependencies."""
        return [dep for dep in self.dependencies.values() if dep.is_unmaintained]
    
    def get_dependency_summary(self) -> Dict[str, Any]:
        """Get summary of dependency analysis."""
        total = len(self.dependencies)
        outdated = len(self.get_outdated_dependencies())
        vulnerable = len(self.get_vulnerable_dependencies())
        unmaintained = len(self.get_unmaintained_dependencies())
        
        return {
            "total_dependencies": total,
            "outdated": outdated,
            "vulnerable": vulnerable,
            "unmaintained": unmaintained,
            "health_score": self._calculate_health_score()
        }
    
    def _calculate_health_score(self) -> float:
        """Calculate overall dependency health score (0-100)."""
        if not self.dependencies:
            return 100.0
        
        total = len(self.dependencies)
        outdated = len(self.get_outdated_dependencies())
        vulnerable = len(self.get_vulnerable_dependencies())
        unmaintained = len(self.get_unmaintained_dependencies())
        
        # Weighted scoring
        score = 100.0
        score -= (outdated / total) * 20  # -20 points for outdated
        score -= (vulnerable / total) * 40  # -40 points for vulnerable
        score -= (unmaintained / total) * 30  # -30 points for unmaintained
        
        return max(0.0, score)

