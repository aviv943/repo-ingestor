import os
import tempfile
import shutil
from pathlib import Path


def create_sample_repo():
    """
    Creates a sample repository with different types of files for testing.
    """
    temp_dir = tempfile.mkdtemp()

    # Python files
    py_file1_path = os.path.join(temp_dir, "main.py")
    with open(py_file1_path, "w") as f:
        f.write("""
def main():
    print("Hello, world!")

if __name__ == "__main__":
    main()
""")

    py_file2_path = os.path.join(temp_dir, "utils.py")
    with open(py_file2_path, "w") as f:
        f.write("""
def helper_function():
    return "Helper function"
""")

    req_path = os.path.join(temp_dir, "requirements.txt")
    with open(req_path, "w") as f:
        f.write("""
pytest==7.3.1
click>=8.0.0
rich>=10.0.0
""")

    # C# files
    csharp_dir = os.path.join(temp_dir, "csharp")
    os.makedirs(csharp_dir, exist_ok=True)
    cs_file_path = os.path.join(csharp_dir, "Program.cs")
    with open(cs_file_path, "w") as f:
        f.write("""
using System;

namespace SampleApp
{
    class Program
    {
        static void Main(string[] args)
        {
            Console.WriteLine("Hello, world!");
        }
    }
}
""")

    # React files
    react_dir = os.path.join(temp_dir, "react")
    os.makedirs(react_dir, exist_ok=True)
    jsx_file_path = os.path.join(react_dir, "App.jsx")
    with open(jsx_file_path, "w") as f:
        f.write("""
import React from 'react';

function App() {
    return (
        <div>
            <h1>Hello, world!</h1>
        </div>
    );
}

export default App;
""")

    pkg_path = os.path.join(react_dir, "package.json")
    with open(pkg_path, "w") as f:
        f.write("""
{
  "name": "sample-app",
  "version": "1.0.0",
  "description": "A sample React app",
  "main": "index.js",
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test"
  },
  "author": "Test Author",
  "license": "MIT",
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "axios": "^1.3.4"
  },
  "devDependencies": {
    "jest": "^29.5.0",
    "eslint": "^8.36.0"
  }
}
""")

    # YAML files
    yaml_dir = os.path.join(temp_dir, "yaml")
    os.makedirs(yaml_dir, exist_ok=True)

    # Docker Compose file
    docker_compose_path = os.path.join(temp_dir, "docker-compose.yml")
    with open(docker_compose_path, "w") as f:
        f.write("""
version: '3'
services:
  web:
    image: nginx:latest
    ports:
      - "80:80"
  db:
    image: postgres:13
    volumes:
      - postgres_data:/var/lib/postgresql/data
volumes:
  postgres_data:
""")

    # Kubernetes manifest
    k8s_dir = os.path.join(temp_dir, "kubernetes")
    os.makedirs(k8s_dir, exist_ok=True)
    k8s_path = os.path.join(k8s_dir, "deployment.yaml")
    with open(k8s_path, "w") as f:
        f.write("""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
  labels:
    app: web
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
      - name: web
        image: nginx:latest
        ports:
        - containerPort: 80
""")

    # GitHub Actions workflow
    github_dir = os.path.join(temp_dir, ".github", "workflows")
    os.makedirs(github_dir, exist_ok=True)
    workflow_path = os.path.join(github_dir, "ci.yml")
    with open(workflow_path, "w") as f:
        f.write("""
name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      - name: Run tests
        run: |
          pytest
""")

    return temp_dir


def cleanup_sample_repo(repo_path):
    """
    Cleans up the sample repository
    """
    shutil.rmtree(repo_path)