from setuptools import setup, find_packages
import os

# Read the long description from README
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="reviewr",
    version="1.0.0",
    description="Enterprise-grade AI-powered code review platform for pre-commit validation, CI/CD integration, and comprehensive code quality enforcement",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Clay Good",
    author_email="hi@claygood.com",
    url="https://github.com/claygood/reviewr",
    project_urls={
        "Bug Tracker": "https://github.com/claygood/reviewr/issues",
        "Documentation": "https://github.com/claygood/reviewr/blob/main/README.md",
        "Source Code": "https://github.com/claygood/reviewr",
    },
    packages=find_packages(exclude=["tests", "tests.*", "test_*", "demo_*"]),
    install_requires=[
        "click>=8.0",
        "pydantic>=2.0",
        "httpx>=0.24",
        "rich>=13.0",
        "pyyaml>=6.0",
        "python-dotenv>=1.0",
        "tenacity>=8.0",
        "diskcache>=5.0",
        "anthropic>=0.18",
        "openai>=1.0",
        "google-generativeai>=0.3",
        "tomli>=2.0.0;python_version<'3.11'",
    ],
    extras_require={
        "github": ["requests>=2.28"],
        "gitlab": ["requests>=2.28"],
        "dashboard": ["fastapi>=0.100", "uvicorn>=0.23", "sqlalchemy>=2.0"],
        "all": ["requests>=2.28", "fastapi>=0.100", "uvicorn>=0.23", "sqlalchemy>=2.0"],
        "dev": [
            "pytest>=7.0",
            "pytest-asyncio>=0.21",
            "pytest-cov>=4.0",
            "black>=23.0",
            "ruff>=0.1",
            "mypy>=1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "reviewr=reviewr.cli:main",
            "reviewr-pre-commit=reviewr.pre_commit_hook:main",
            "reviewr-github=reviewr.cli_github:github_pr",
            "reviewr-gitlab=reviewr.cli_gitlab:gitlab_mr",
        ],
    },
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Testing",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Environment :: Console",
    ],
    keywords="code-review ai llm static-analysis security linting quality ci-cd",
    license="MIT",
    include_package_data=True,
)
