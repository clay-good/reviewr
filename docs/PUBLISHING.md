# Publishing reviewr to PyPI

This guide explains how to publish reviewr to PyPI so developers can install it with `pip install reviewr`.

## Prerequisites

1. **PyPI Account**: Create accounts on both:
   - [PyPI](https://pypi.org/account/register/) (production)
   - [TestPyPI](https://test.pypi.org/account/register/) (testing)

2. **Install Build Tools**:
   ```bash
   pip install --upgrade pip setuptools wheel twine build
   ```

3. **API Tokens**: Generate API tokens for authentication:
   - PyPI: https://pypi.org/manage/account/token/
   - TestPyPI: https://test.pypi.org/manage/account/token/

4. **Configure PyPI Credentials**:
   Create `~/.pypirc`:
   ```ini
   [distutils]
   index-servers =
       pypi
       testpypi

   [pypi]
   username = __token__
   password = pypi-YOUR-API-TOKEN-HERE

   [testpypi]
   username = __token__
   password = pypi-YOUR-TESTPYPI-TOKEN-HERE
   ```

## Pre-Publishing Checklist

Before publishing, ensure:

- [ ] All tests pass: `python3 -m pytest`
- [ ] Version number updated in `setup.py` and `pyproject.toml`
- [ ] README.md is up-to-date
- [ ] CHANGELOG documented (if exists)
- [ ] LICENSE file present
- [ ] No sensitive data in code
- [ ] `.gitignore` excludes build artifacts
- [ ] Documentation is complete

## Publishing Steps

### Step 1: Clean Previous Builds

```bash
# Remove old build artifacts
rm -rf build/ dist/ *.egg-info
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null
```

### Step 2: Build Distribution Packages

```bash
# Build source distribution and wheel
python3 -m build

# This creates:
# - dist/reviewr-1.0.0.tar.gz (source distribution)
# - dist/reviewr-1.0.0-py3-none-any.whl (wheel)
```

### Step 3: Test on TestPyPI (Recommended)

```bash
# Upload to TestPyPI first
python3 -m twine upload --repository testpypi dist/*

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ reviewr

# Test the installation
reviewr --help
```

### Step 4: Publish to PyPI

```bash
# Upload to production PyPI
python3 -m twine upload dist/*

# You'll see output like:
# Uploading distributions to https://upload.pypi.org/legacy/
# Uploading reviewr-1.0.0-py3-none-any.whl
# Uploading reviewr-1.0.0.tar.gz
```

### Step 5: Verify Installation

```bash
# Install from PyPI
pip install reviewr

# Verify it works
reviewr --version
reviewr --help
```

## Installation Methods for Users

Once published, users can install reviewr in several ways:

### Basic Installation

```bash
pip install reviewr
```

### With Optional Dependencies

```bash
# GitHub integration
pip install reviewr[github]

# GitLab integration
pip install reviewr[gitlab]

# Dashboard features
pip install reviewr[dashboard]

# All optional features
pip install reviewr[all]

# Development dependencies
pip install reviewr[dev]
```

### Using Poetry

```bash
poetry add reviewr

# With extras
poetry add reviewr[all]
```

### Using pipx (Isolated Installation)

```bash
# Install as isolated CLI tool
pipx install reviewr

# With extras
pipx install reviewr[all]
```

### From Source (Development)

```bash
# Clone repository
git clone https://github.com/claygood/reviewr.git
cd reviewr

# Install in editable mode
pip install -e .

# Or with Poetry
poetry install
```

## Version Management

### Semantic Versioning

Follow [Semantic Versioning](https://semver.org/):
- **MAJOR** (1.x.x): Breaking changes
- **MINOR** (x.1.x): New features, backward compatible
- **PATCH** (x.x.1): Bug fixes, backward compatible

### Updating Version

Update version in both files:

1. **setup.py**:
   ```python
   version="1.0.0",
   ```

2. **pyproject.toml**:
   ```toml
   version = "1.0.0"
   ```

### Creating Git Tags

```bash
# Tag the release
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0

# Or create a GitHub release
gh release create v1.0.0 --title "v1.0.0" --notes "Release notes here"
```

## Continuous Deployment (Optional)

### GitHub Actions

Create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install build twine
      
      - name: Build package
        run: python -m build
      
      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: twine upload dist/*
```

Add `PYPI_API_TOKEN` to GitHub repository secrets.

## Troubleshooting

### Common Issues

1. **"File already exists" error**:
   - Version already published
   - Update version number in setup.py and pyproject.toml

2. **Authentication failed**:
   - Check API token is correct
   - Verify `~/.pypirc` configuration
   - Token must start with `pypi-`

3. **Missing dependencies**:
   - Ensure all dependencies listed in `install_requires`
   - Test in clean virtual environment

4. **Import errors after install**:
   - Check `packages=find_packages()` in setup.py
   - Verify `__init__.py` files exist in all packages

5. **README not displaying on PyPI**:
   - Ensure `long_description_content_type="text/markdown"`
   - Check README.md is valid Markdown

### Testing Locally

```bash
# Create clean virtual environment
python3 -m venv test_env
source test_env/bin/activate

# Install from local build
pip install dist/reviewr-1.0.0-py3-none-any.whl

# Test
reviewr --help

# Cleanup
deactivate
rm -rf test_env
```

## Post-Publishing

1. **Verify on PyPI**: Visit https://pypi.org/project/reviewr/
2. **Update Documentation**: Add installation instructions
3. **Announce Release**: Social media, blog, etc.
4. **Monitor Issues**: Watch for bug reports
5. **Plan Next Release**: Track feature requests

## Resources

- [PyPI Help](https://pypi.org/help/)
- [Python Packaging Guide](https://packaging.python.org/)
- [Twine Documentation](https://twine.readthedocs.io/)
- [Setuptools Documentation](https://setuptools.pypa.io/)

