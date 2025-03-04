import os
import re
from pathlib import Path
from typing import Dict, List, Any

from .base import BaseLanguageHandler
from ..config import LanguageConfig


class YamlLanguageHandler(BaseLanguageHandler):
    """
    Language handler for YAML files, with special focus on Docker, Kubernetes,
    GitHub Actions, and other common YAML-based configurations.
    """

    def __init__(self, config: LanguageConfig = None):
        from ..config import DEFAULT_CONFIG
        super().__init__(config or DEFAULT_CONFIG.languages["yaml"])

    def detect_language(self, repo_path: Path) -> bool:
        """
        Detect if the repository contains YAML files
        """
        # Look for .yml and .yaml files
        yaml_files = list(repo_path.glob("**/*.yaml")) + list(repo_path.glob("**/*.yml"))
        if yaml_files:
            return True

        # Look for specific YAML files
        specific_files = [
            "docker-compose.yml",
            "docker-compose.yaml",
            ".github/workflows/*.yml",
            ".github/workflows/*.yaml",
            "kubernetes/*.yml",
            "kubernetes/*.yaml",
            "k8s/*.yml",
            "k8s/*.yaml",
            "helm/**/*.yaml",
            "helm/**/*.yml",
            ".gitlab-ci.yml",
            "cloudbuild.yaml",
            "appveyor.yml",
            "circle.yml",
            "travis.yml",
            ".travis.yml"
        ]

        for pattern in specific_files:
            if list(repo_path.glob(f"**/{pattern}")):
                return True

        return False

    def analyze_dependencies(self, files: Dict[str, str]) -> Dict[str, List[str]]:
        """
        Analyze YAML files for dependencies:
        - Docker images in docker-compose files
        - Base images in Dockerfiles
        - References to other resources in Kubernetes manifests
        - Actions in GitHub workflows
        """
        dependencies = {}

        for file_path, content in files.items():
            if not file_path.lower().endswith(('.yml', '.yaml')):
                continue

            file_deps = []

            # Docker compose image dependencies - improved regex to capture only the image name
            # This regex captures text after 'image:' until a whitespace, newline, or end of string
            image_matches = re.findall(r'^\s*image:\s*[\'"]?([^\s\'"]+)[\'"]?', content, re.MULTILINE)
            file_deps.extend([f"docker:image:{img}" for img in image_matches])

            # GitHub Actions - uses directives - improved to capture until newline
            action_matches = re.findall(r'^\s*uses:\s*([^\s\n]+)', content, re.MULTILINE)
            file_deps.extend([f"github:action:{action.strip()}" for action in action_matches])

            # Kubernetes references (apiVersion, kind, name)
            kubernetes_kinds = []
            api_version_matches = re.findall(r'apiVersion:\s*([^\s\n]+)', content)
            kind_matches = re.findall(r'kind:\s*([^\s\n]+)', content)
            name_matches = re.findall(r'name:\s*([^\s\n]+)', content)

            for i in range(min(len(api_version_matches), len(kind_matches))):
                kind = kind_matches[i].strip()
                api = api_version_matches[i].strip()
                kubernetes_kinds.append(f"k8s:{api}/{kind}")

            file_deps.extend(kubernetes_kinds)

            # Helm chart dependencies
            if "chart:" in content and "repository:" in content:
                chart_matches = re.findall(r'name:\s*([^\s\n]+)[\s\S]*?repository:\s*([^\s\n]+)', content)
                file_deps.extend([f"helm:chart:{name.strip()}" for name, _ in chart_matches])

            dependencies[file_path] = file_deps

        return dependencies

    def extract_project_metadata(self, files: Dict[str, str]) -> Dict[str, Any]:
        """
        Extract metadata from YAML files:
        - Docker compose services and volumes
        - Kubernetes resources
        - CI/CD pipeline configurations
        """
        metadata = {
            "language": "YAML",
            "docker_services": [],
            "kubernetes_resources": [],
            "github_workflows": [],
            "ci_cd_configs": []
        }

        for file_path, content in files.items():
            if not file_path.lower().endswith(('.yml', '.yaml')):
                continue

            file_name = os.path.basename(file_path)

            # Docker Compose
            if file_name.startswith("docker-compose"):
                service_matches = re.findall(r'^\s*(\w+):\s*$', content, re.MULTILINE)
                for service in service_matches:
                    if service != "services" and service != "volumes" and service != "networks":
                        metadata["docker_services"].append(service)

                # Find all volume definitions
                volume_matches = re.findall(r'volumes:\s*$[\s\S]*?^\S', content, re.MULTILINE)
                if volume_matches:
                    volume_defs = re.findall(r'^\s*-\s*([^\n]+)', volume_matches[0], re.MULTILINE)
                    if volume_defs:
                        if "volumes" not in metadata:
                            metadata["volumes"] = []
                        metadata["volumes"].extend([v.strip() for v in volume_defs])

            # Kubernetes
            if "apiVersion:" in content and "kind:" in content:
                kind_matches = re.findall(r'kind:\s*([^\s\n]+)', content)
                name_matches = re.findall(r'name:\s*([^\s\n]+)', content)

                for i in range(min(len(kind_matches), len(name_matches))):
                    metadata["kubernetes_resources"].append({
                        "kind": kind_matches[i].strip(),
                        "name": name_matches[i].strip()
                    })

            # GitHub Actions
            if ".github/workflows" in file_path:
                workflow_name_matches = re.findall(r'name:\s*([^\n]+)', content, re.MULTILINE)
                if workflow_name_matches:
                    metadata["github_workflows"].append({
                        "name": workflow_name_matches[0].strip(),
                        "file": file_path
                    })

                    # Extract jobs
                    job_matches = re.findall(r'jobs:\s*$[\s\S]*?^\S', content, re.MULTILINE)
                    if job_matches:
                        job_names = re.findall(r'^\s*(\w+):\s*$', job_matches[0], re.MULTILINE)
                        if "github_workflow_jobs" not in metadata:
                            metadata["github_workflow_jobs"] = []
                        metadata["github_workflow_jobs"].extend(job_names)

            # CI/CD configs
            ci_cd_files = [".gitlab-ci.yml", "appveyor.yml", "circle.yml", ".travis.yml", "travis.yml"]
            if file_name in ci_cd_files:
                metadata["ci_cd_configs"].append(file_name)

        return metadata