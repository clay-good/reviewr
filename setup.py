"""Setup script for reviewr."""

from setuptools import setup, find_packages

setup(
    name="reviewr",
    version="0.1.0",
    description="AI-powered code review CLI tool supporting multiple LLM providers",
    author="Your Name",
    author_email="you@example.com",
    packages=find_packages(),
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
    entry_points={
        "console_scripts": [
            "reviewr=reviewr.cli:main",
            "reviewr-pre-commit=reviewr.pre_commit_hook:main",
        ],
    },
    python_requires=">=3.9",
)

