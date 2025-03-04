import os
import re
from pathlib import Path
from typing import Dict, List, Any

from repo_ingestor.language_handlers.base import BaseLanguageHandler
from repo_ingestor.config import LanguageConfig


class YamlLanguageHandler(BaseLanguageHandler):
    """
    Language handler for YAML files, with special focus on Docker, Kubernetes,
    GitHub Actions, and other common YAML-based configurations.
    """

    def __init__(self, config: LanguageConfig = None):
        from repo_ingestor.config import DEFAULT_CONFIG
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

            # Process the content to handle indentation better
            # Normalize content by removing leading whitespace from each line
            normalized_content = "\n".join(line.strip() for line in content.split("\n"))

            # Docker compose image dependencies
            image_matches = re.findall(r'image:\s*([^\s\n]+)', normalized_content)
            file_deps.extend([f"docker:image:{img}" for img in image_matches])

            # GitHub Actions - uses directives
            action_matches = re.findall(r'uses:\s*([^\s\n]+)', normalized_content)
            file_deps.extend([f"github:action:{action.strip()}" for action in action_matches])

            # Kubernetes references (apiVersion, kind, name)
            kubernetes_kinds = []
            api_version_matches = re.findall(r'apiVersion:\s*([^\s\n]+)', normalized_content)
            kind_matches = re.findall(r'kind:\s*([^\s\n]+)', normalized_content)

            for i in range(min(len(api_version_matches), len(kind_matches))):
                kind = kind_matches[i].strip()
                api = api_version_matches[i].strip()
                kubernetes_kinds.append(f"k8s:{api}/{kind}")

            file_deps.extend(kubernetes_kinds)

            # Helm chart dependencies
            if "chart:" in normalized_content and "repository:" in normalized_content:
                # This is a simplified approach; a more robust parser would be better for complex YAML
                chart_matches = re.findall(r'name:\s*([^\s\n]+)[\s\S]*?repository:\s*([^\s\n]+)', normalized_content)
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

            # Normalize content by removing leading whitespace from each line
            normalized_content = "\n".join(line.strip() for line in content.split("\n"))

            # Docker Compose
            if file_name.startswith("docker-compose"):
                # First extract service names - looking for pattern where service name is followed by colon
                # and it's not one of the common top-level keys
                service_lines = re.findall(r'(?:^|\n)(\w+):', normalized_content)
                for service in service_lines:
                    if service not in ["services", "volumes", "networks", "version"]:
                        metadata["docker_services"].append(service)

                # Find all volume definitions
                volume_section = re.search(r'volumes:(.*?)(?:^\S|\Z)', normalized_content, re.DOTALL | re.MULTILINE)
                if volume_section:
                    volume_defs = re.findall(r'-\s*([^\n]+)', volume_section.group(1))
                    if volume_defs:
                        if "volumes" not in metadata:
                            metadata["volumes"] = []
                        metadata["volumes"].extend([v.strip() for v in volume_defs])

            # Kubernetes
            if "apiVersion:" in normalized_content and "kind:" in normalized_content:
                kind_matches = re.findall(r'kind:\s*([^\s\n]+)', normalized_content)
                name_matches = re.findall(r'name:\s*([^\s\n]+)', normalized_content)

                for i in range(min(len(kind_matches), len(name_matches))):
                    metadata["kubernetes_resources"].append({
                        "kind": kind_matches[i].strip(),
                        "name": name_matches[i].strip()
                    })

            # GitHub Actions
            if ".github/workflows" in file_path:
                workflow_name_matches = re.findall(r'name:\s*([^\n]+)', normalized_content)
                if workflow_name_matches:
                    metadata["github_workflows"].append({
                        "name": workflow_name_matches[0].strip(),
                        "file": file_path
                    })

                    # Extract jobs
                    job_section = re.search(r'jobs:(.*?)(?:^\S|\Z)', normalized_content, re.DOTALL | re.MULTILINE)
                    if job_section:
                        job_names = re.findall(r'(?:^|\n)(\w+):', job_section.group(1))
                        if "github_workflow_jobs" not in metadata:
                            metadata["github_workflow_jobs"] = []
                        metadata["github_workflow_jobs"].extend(job_names)

            # CI/CD configs
            ci_cd_files = [".gitlab-ci.yml", "appveyor.yml", "circle.yml", ".travis.yml", "travis.yml"]
            if file_name in ci_cd_files:
                metadata["ci_cd_configs"].append(file_name)

        return metadata