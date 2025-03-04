"""
C# language handler.
"""
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any

from .base import BaseLanguageHandler
from ..config import LanguageConfig


class CSharpLanguageHandler(BaseLanguageHandler):
    """Handler for C# language repositories."""

    def __init__(self, config: LanguageConfig = None):
        """
        Initialize the C# language handler.

        Args:
            config: C# language configuration (optional)
        """
        from ..config import DEFAULT_CONFIG
        super().__init__(config or DEFAULT_CONFIG.languages["csharp"])

    def detect_language(self, repo_path: Path) -> bool:
        """
        Detect if this repository uses C#.

        Args:
            repo_path: Path to the repository

        Returns:
            True if C# is detected, False otherwise
        """
        # Check for C# files
        cs_files = list(repo_path.glob("**/*.cs"))
        if cs_files:
            return True

        # Check for C# project files
        csproj_files = list(repo_path.glob("**/*.csproj"))
        if csproj_files:
            return True

        # Check for solution files
        sln_files = list(repo_path.glob("**/*.sln"))
        if sln_files:
            return True

        return False

    def analyze_dependencies(self, files: Dict[str, str]) -> Dict[str, List[str]]:
        """
        Analyze dependencies between C# files.

        Args:
            files: Dictionary mapping file paths to their content

        Returns:
            Dictionary mapping file paths to their dependencies
        """
        dependencies = {}

        for file_path, content in files.items():
            if file_path.endswith(".cs"):
                file_deps = []

                # Get using statements
                using_matches = re.findall(r'^using\s+([\w.]+);', content, re.MULTILINE)
                file_deps.extend(using_matches)

                dependencies[file_path] = file_deps

            elif file_path.endswith(".csproj"):
                file_deps = []

                # Parse XML to get package references
                try:
                    root = ET.fromstring(content)
                    ns = {'': 'http://schemas.microsoft.com/developer/msbuild/2003'}

                    # Find PackageReference elements
                    for package_ref in root.findall(".//PackageReference", ns):
                        include = package_ref.get("Include")
                        if include:
                            file_deps.append(include)

                    # Find ProjectReference elements
                    for project_ref in root.findall(".//ProjectReference", ns):
                        include = project_ref.get("Include")
                        if include:
                            file_deps.append(os.path.basename(include).replace(".csproj", ""))
                except Exception:
                    # Fall back to regex if XML parsing fails
                    package_refs = re.findall(r'<PackageReference\s+Include="([^"]+)"', content)
                    file_deps.extend(package_refs)

                    project_refs = re.findall(r'<ProjectReference\s+Include="([^"]+)"', content)
                    for ref in project_refs:
                        file_deps.append(os.path.basename(ref).replace(".csproj", ""))

                dependencies[file_path] = file_deps

        return dependencies

    def extract_project_metadata(self, files: Dict[str, str]) -> Dict[str, Any]:
        """
        Extract C# project metadata from files.

        Args:
            files: Dictionary mapping file paths to their content

        Returns:
            Dictionary with project metadata
        """
        metadata = {
            "language": "C#",
            "projects": [],
            "solutions": [],
            "packages": []
        }

        for file_path, content in files.items():
            if file_path.endswith(".csproj"):
                metadata["projects"].append(os.path.basename(file_path))

                # Extract package references
                try:
                    root = ET.fromstring(content)
                    ns = {'': 'http://schemas.microsoft.com/developer/msbuild/2003'}

                    # Extract target framework
                    target_framework = root.find(".//TargetFramework", ns)
                    if target_framework is not None and target_framework.text:
                        project_metadata = {
                            "name": os.path.basename(file_path),
                            "framework": target_framework.text,
                            "packages": []
                        }

                        # Extract package references
                        for package_ref in root.findall(".//PackageReference", ns):
                            include = package_ref.get("Include")
                            version = package_ref.get("Version")
                            if include:
                                package = {"name": include}
                                if version:
                                    package["version"] = version
                                project_metadata["packages"].append(package)
                                metadata["packages"].append(include)

                        metadata["projects"].append(project_metadata)
                except Exception:
                    # Fall back to regex if XML parsing fails
                    package_refs = re.findall(r'<PackageReference\s+Include="([^"]+)"\s+Version="([^"]+)"', content)
                    for name, version in package_refs:
                        metadata["packages"].append(name)

            elif file_path.endswith(".sln"):
                metadata["solutions"].append(os.path.basename(file_path))

                # Extract project references from solution
                project_refs = re.findall(r'Project\([^)]+\)\s*=\s*"([^"]+)"', content)
                for ref in project_refs:
                    if ref not in metadata["projects"]:
                        metadata["projects"].append(ref)

        return metadata