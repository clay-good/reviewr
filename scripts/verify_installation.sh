#!/bin/bash
# Verification script for reviewr installation

set -e

echo "======================================"
echo "reviewr Installation Verification"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track results
PASSED=0
FAILED=0

# Helper functions
pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASSED++))
}

fail() {
    echo -e "${RED}✗${NC} $1"
    ((FAILED++))
}

warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# 1. Check Python version
echo "1. Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    
    if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 9 ]; then
        pass "Python $PYTHON_VERSION (>= 3.9 required)"
    else
        fail "Python $PYTHON_VERSION (>= 3.9 required)"
    fi
else
    fail "Python 3 not found"
fi
echo ""

# 2. Check if reviewr is installed
echo "2. Checking reviewr installation..."
if python3 -c "import reviewr" 2>/dev/null; then
    pass "reviewr package is installed"
else
    fail "reviewr package not found"
    echo "   Run: pip install -e ."
fi
echo ""

# 3. Check CLI availability
echo "3. Checking CLI commands..."
if python3 -m reviewr --help &> /dev/null; then
    pass "reviewr CLI is accessible"
else
    fail "reviewr CLI not accessible"
fi

if command -v reviewr-pre-commit &> /dev/null || python3 -m reviewr.pre_commit_hook --help &> /dev/null 2>&1; then
    pass "reviewr-pre-commit is accessible"
else
    warn "reviewr-pre-commit not in PATH (may need to add to PATH)"
fi
echo ""

# 4. Check required dependencies
echo "4. Checking dependencies..."
DEPS=("click" "pydantic" "httpx" "rich" "pyyaml" "anthropic" "openai" "google.generativeai")
for dep in "${DEPS[@]}"; do
    if python3 -c "import ${dep//-/_}" 2>/dev/null; then
        pass "$dep is installed"
    else
        fail "$dep is missing"
    fi
done
echo ""

# 5. Check module structure
echo "5. Checking module structure..."
MODULES=("reviewr.cli" "reviewr.config" "reviewr.providers" "reviewr.review" "reviewr.utils")
for module in "${MODULES[@]}"; do
    if python3 -c "import $module" 2>/dev/null; then
        pass "$module module exists"
    else
        fail "$module module not found"
    fi
done
echo ""

# 6. Check specific components
echo "6. Checking specific components..."
if python3 -c "from reviewr.utils.secrets_scanner import SecretsScanner" 2>/dev/null; then
    pass "SecretsScanner is available"
else
    fail "SecretsScanner not found"
fi

if python3 -c "from reviewr.utils.formatters import SarifFormatter, HtmlFormatter, JunitFormatter" 2>/dev/null; then
    pass "All formatters are available"
else
    fail "Some formatters are missing"
fi

if python3 -c "from reviewr.providers import ProviderFactory" 2>/dev/null; then
    pass "ProviderFactory is available"
else
    fail "ProviderFactory not found"
fi
echo ""

# 7. Check configuration files
echo "7. Checking configuration templates..."
if python3 -c "from reviewr.config.defaults import DEFAULT_CONFIG_TEMPLATE_YAML, DEFAULT_CONFIG_TEMPLATE_TOML" 2>/dev/null; then
    pass "Configuration templates are available"
else
    fail "Configuration templates not found"
fi
echo ""

# 8. Check pre-commit hooks
echo "8. Checking pre-commit hooks..."
if [ -f ".pre-commit-hooks.yaml" ]; then
    pass ".pre-commit-hooks.yaml exists"
else
    fail ".pre-commit-hooks.yaml not found"
fi

if [ -f ".pre-commit-config.yaml.example" ]; then
    pass ".pre-commit-config.yaml.example exists"
else
    warn ".pre-commit-config.yaml.example not found"
fi
echo ""

# 9. Check VS Code extension
echo "9. Checking VS Code extension..."
if [ -d "vscode-extension" ]; then
    pass "vscode-extension directory exists"
    
    if [ -f "vscode-extension/package.json" ]; then
        pass "VS Code extension package.json exists"
    else
        fail "VS Code extension package.json not found"
    fi
    
    if [ -f "vscode-extension/src/extension.ts" ]; then
        pass "VS Code extension source exists"
    else
        fail "VS Code extension source not found"
    fi
else
    fail "vscode-extension directory not found"
fi
echo ""

# 10. Check documentation
echo "10. Checking documentation..."
DOCS=("README.md" "CONTRIBUTING.md" "LICENSE")
for doc in "${DOCS[@]}"; do
    if [ -f "$doc" ]; then
        pass "$doc exists"
    else
        warn "$doc not found"
    fi
done
echo ""

# 11. Test init command
echo "11. Testing init command..."
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"
if python3 -m reviewr --init 2>/dev/null; then
    if [ -f ".reviewr.yml" ]; then
        pass "Init command creates .reviewr.yml"
    else
        fail "Init command didn't create .reviewr.yml"
    fi
else
    fail "Init command failed"
fi
cd - > /dev/null
rm -rf "$TEMP_DIR"
echo ""

# 12. Check API key configuration
echo "12. Checking API key configuration..."
if [ -n "$ANTHROPIC_API_KEY" ]; then
    pass "ANTHROPIC_API_KEY is set"
elif [ -n "$OPENAI_API_KEY" ]; then
    pass "OPENAI_API_KEY is set"
elif [ -n "$GOOGLE_API_KEY" ]; then
    pass "GOOGLE_API_KEY is set"
else
    warn "No API keys configured (set ANTHROPIC_API_KEY, OPENAI_API_KEY, or GOOGLE_API_KEY)"
fi
echo ""

# Summary
echo "======================================"
echo "Summary"
echo "======================================"
echo -e "${GREEN}Passed: $PASSED${NC}"
if [ $FAILED -gt 0 ]; then
    echo -e "${RED}Failed: $FAILED${NC}"
fi
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed! reviewr is ready to use.${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Set an API key: export ANTHROPIC_API_KEY='your-key'"
    echo "2. Initialize config: reviewr --init"
    echo "3. Run a review: reviewr <path> --all --output-format sarif"
    exit 0
else
    echo -e "${RED}✗ Some checks failed. Please fix the issues above.${NC}"
    exit 1
fi

