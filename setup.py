from setuptools import setup, find_packages

setup(
    name="repo-ingestor",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "click>=8.0.0",
        "tqdm>=4.62.0",
        "rich>=10.0.0",
    ],
    entry_points={
        "console_scripts": [
            "repo-ingestor=repo_ingestor.cli:main",
        ],
    },
    author="Aviv",
    description="A professional tool that converts code repositories into a single file with code, dependencies, and structure",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    keywords="repository, code, ingest, documentation, llm, tokens",
    python_requires=">=3.7",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Documentation",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)