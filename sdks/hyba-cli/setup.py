#!/usr/bin/env python
"""
HYBA CLI Tool - Enterprise-grade command-line interface
Provision, manage, and execute computational intelligence services
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="hyba-cli",
    version="0.1.0",
    author="HYBA Team",
    author_email="engineering@hyba.ai",
    description="CLI tool for HYBA computational intelligence services",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hyba-ai/hyba-cli",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Topic :: Software Development :: Libraries",
        "Topic :: System :: Monitoring",
    ],
    python_requires=">=3.9",
    install_requires=[
        "click>=8.1.0",
        "rich>=13.0.0",
        "pyyaml>=6.0",
        "requests>=2.28.0",
        "pydantic>=1.10.0",
        "tabulate>=0.9.0",
        "pydantic-settings>=2.0.0",
        "hyba-sdk-py>=0.1.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "black>=23.0.0",
            "isort>=5.11.0",
            "flake8>=4.0.0",
            "mypy>=0.990",
        ],
    },
    entry_points={
        "console_scripts": [
            "hyba=hyba_cli.cli:main",
        ],
    },
)
