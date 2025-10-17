from setuptools import setup, find_packages

setup(
    name="reviewr",
    version="0.1.0",
    description="AI-powered code review CLI tool supporting multiple LLM providers",
<<<<<<< HEAD
    author="Clay Good",
    author_email="hi@claygood.com",
=======
    author="Your Name",
    author_email="you@example.com",
>>>>>>> 9142a626e7c17e9750e46f0bd63dca202a22eff4
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
<<<<<<< HEAD
    extras_require={
        "github": ["requests>=2.28"],
        "all": ["requests>=2.28"],
    },
=======
>>>>>>> 9142a626e7c17e9750e46f0bd63dca202a22eff4
    entry_points={
        "console_scripts": [
            "reviewr=reviewr.cli:main",
            "reviewr-pre-commit=reviewr.pre_commit_hook:main",
<<<<<<< HEAD
            "reviewr-github=reviewr.cli_github:github_pr",
=======
>>>>>>> 9142a626e7c17e9750e46f0bd63dca202a22eff4
        ],
    },
    python_requires=">=3.9",
)

