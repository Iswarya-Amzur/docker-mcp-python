"""
Setup configuration for Docker MCP Server
This allows the package to be installed via pip and used as a command
"""

from setuptools import setup, find_packages
import os

# Read the README for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="docker-mcp-server",
    version="1.0.0",
    author="Iswarya Amzur",
    author_email="your.email@example.com",
    description="MCP server for Docker containerization with intelligent monitoring",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Iswarya-Amzur/docker-mcp-python",
    packages=find_packages(where="docker-mcp"),
    package_dir={"": "docker-mcp"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "docker-mcp=server:main",
        ],
    },
    include_package_data=True,
    keywords="mcp docker containerization monitoring grafana loki",
)
