# Reviewr Advanced Analysis - Usage Guide

## Quick Start

### Running the Demonstrations

```bash
# Run individual analyzer demonstrations
python3 demo_advanced_analysis.py

# Run complete analysis demonstration (all 6 analyzers)
python3 demo_complete_analysis.py
```

### Running the Tests

```bash
# Run all tests
python3 test_advanced_analysis.py

# Run with verbose output
python3 test_advanced_analysis.py -v

# Run specific test class
python3 -m unittest test_advanced_analysis.TestSecurityAnalyzer
```

---

## Using Individual Analyzers

### 1. Security Analyzer

Detects security vulnerabilities in Python code.

```python
from reviewr.analysis.security_analyzer import SecurityAnalyzer

# Initialize analyzer
analyzer = SecurityAnalyzer()

# Analyze code
code = """
def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)
"""

findings = analyzer.analyze('example.py', code)

# Process findings
for finding in findings:
    print(f"{finding.severity}: {finding.message}")
    print(f"  Line {finding.line_start}: {finding.suggestion}")
```

**Detects**:
- SQL injection (f-strings, .format(), % formatting, concatenation)
- Command injection (shell=True, eval/exec)
- Path traversal
- Insecure deserialization
- Weak cryptography
- Hardcoded secrets
- And more...

---

### 2. Data Flow Analyzer

Tracks tainted data from sources to dangerous sinks.

```python
from reviewr.analysis.dataflow_analyzer import DataFlowAnalyzer

analyzer = DataFlowAnalyzer()

code = """
from flask import request

def process_request():
    user_input = request.args.get('id')
    query = f"SELECT * FROM users WHERE id = {user_input}"
    cursor.execute(query)
"""

findings = analyzer.analyze('example.py', code)
```

**Tracks**:
- **Sources**: user input, web requests, files, network, environment
- **Sinks**: SQL, commands, file operations, network requests
- **Propagation**: through assignments, operations, f-strings

---

### 3. Complexity Analyzer

Calculates multiple complexity metrics.

```python
from reviewr.analysis.complexity_analyzer import ComplexityAnalyzer

analyzer = ComplexityAnalyzer()

code = """
def complex_function(x, y, z):
    if x > 0:
        if y > 0:
            if z > 0:
                return x + y + z
    return 0
"""

findings = analyzer.analyze('example.py', code)

# Check metrics
for finding in findings:
    if finding.metric_name:
        print(f"{finding.metric_name}: {finding.metric_value}")
```

**Calculates**:
- Cyclomatic complexity (McCabe)
- Cognitive complexity
- Halstead metrics (volume, difficulty, effort)
- Maintainability index
- Technical debt estimation

---

### 4. Type Safety Analyzer

Analyzes Python type hints and detects type-related issues.

```python
from reviewr.analysis.type_analyzer import TypeAnalyzer

analyzer = TypeAnalyzer()

code = """
def process_data(items=[]):  # Mutable default!
    result = ""
    for item in items:
        result += str(item)
    return result
"""

findings = analyzer.analyze('example.py', code)
```

**Detects**:
- Missing type annotations
- Mutable default arguments
- Incorrect None comparisons
- Inconsistent annotation styles
- Any type usage

---

### 5. Performance Analyzer

Detects performance anti-patterns.

```python
from reviewr.analysis.performance_analyzer import PerformanceAnalyzer

analyzer = PerformanceAnalyzer()

code = """
def get_user_posts(user_ids):
    posts = []
    for user_id in user_ids:
        # N+1 query pattern!
        user_posts = db.query("SELECT * FROM posts WHERE user_id = ?", user_id)
        posts.extend(user_posts)
    return posts
"""

findings = analyzer.analyze('example.py', code)
```

**Detects**:
- N+1 query patterns
- String concatenation in loops
- Inefficient data structures
- Network calls in loops
- Repeated computations

---

### 6. Semantic Analyzer

Understands code intent and detects logic errors.

```python
from reviewr.analysis.semantic_analyzer import SemanticAnalyzer

analyzer = SemanticAnalyzer()

code = """
def read_file(filename):
    f = open(filename, 'r')  # Resource leak!
    data = f.read()
    return data
"""

findings = analyzer.analyze('example.py', code)
```

**Detects**:
- Resource leaks
- Incorrect error handling
- Unreachable code
- Race conditions (TOCTOU)
- Inconsistent return types

---

## Using All Analyzers Together

```python
from reviewr.analysis.security_analyzer import SecurityAnalyzer
from reviewr.analysis.dataflow_analyzer import DataFlowAnalyzer
from reviewr.analysis.complexity_analyzer import ComplexityAnalyzer
from reviewr.analysis.type_analyzer import TypeAnalyzer
from reviewr.analysis.performance_analyzer import PerformanceAnalyzer
from reviewr.analysis.semantic_analyzer import SemanticAnalyzer

# Initialize all analyzers
analyzers = [
    SecurityAnalyzer(),
    DataFlowAnalyzer(),
    ComplexityAnalyzer(),
    TypeAnalyzer(),
    PerformanceAnalyzer(),
    SemanticAnalyzer()
]

# Read code to analyze
with open('mycode.py', 'r') as f:
    code = f.read()

# Run all analyzers
all_findings = []
for analyzer in analyzers:
    findings = analyzer.analyze('mycode.py', code)
    all_findings.extend(findings)

# Group by severity
by_severity = {}
for finding in all_findings:
    by_severity.setdefault(finding.severity, []).append(finding)

# Print summary
print(f"Total issues: {len(all_findings)}")
for severity in ['critical', 'high', 'medium', 'low', 'info']:
    if severity in by_severity:
        print(f"  {severity.upper()}: {len(by_severity[severity])}")
```

---

## Understanding Findings

### Finding Structure

Each finding has the following attributes:

```python
@dataclass
class LocalFinding:
    file_path: str              # Path to the file
    line_start: int             # Starting line number
    line_end: int               # Ending line number
    severity: str               # 'critical', 'high', 'medium', 'low', 'info'
    category: str               # 'security', 'dataflow', 'complexity', etc.
    message: str                # Description of the issue
    suggestion: Optional[str]   # How to fix it
    code_snippet: Optional[str] # Code excerpt
    metric_value: Optional[float]  # Numeric metric (if applicable)
    metric_name: Optional[str]     # Name of the metric
```

### Severity Levels

- **CRITICAL**: Immediate security risks (SQL injection, command injection)
- **HIGH**: Serious issues (resource leaks, N+1 queries, high complexity)
- **MEDIUM**: Important issues (weak crypto, timing attacks, inefficient code)
- **LOW**: Minor issues (missing type hints, style issues)
- **INFO**: Informational (technical debt, suggestions)

### Categories

- **security**: Security vulnerabilities
- **dataflow**: Data flow and taint tracking issues
- **complexity**: Code complexity metrics
- **type_safety**: Type annotation issues
- **performance**: Performance anti-patterns
- **semantic**: Logic errors and semantic issues
- **technical_debt**: Technical debt estimates

---

## Configuration

### Adjusting Thresholds

You can customize thresholds when initializing analyzers:

```python
from reviewr.analysis.complexity_analyzer import ComplexityAnalyzer

# Custom thresholds
analyzer = ComplexityAnalyzer()
analyzer.cyclomatic_threshold = 15  # Default: 10
analyzer.cognitive_threshold = 20   # Default: 15
analyzer.maintainability_threshold = 60  # Default: 65
```

### Filtering Findings

```python
# Filter by severity
critical_findings = [f for f in findings if f.severity == 'critical']

# Filter by category
security_findings = [f for f in findings if f.category == 'security']

# Filter by line number
findings_in_range = [f for f in findings if 10 <= f.line_start <= 50]
```

---

## Best Practices

### 1. Run Regularly
- Run analysis on every commit
- Integrate into CI/CD pipeline
- Use as pre-commit hook

### 2. Prioritize Findings
- Fix CRITICAL and HIGH severity first
- Address security issues immediately
- Plan refactoring for complexity issues

### 3. Learn from Suggestions
- Read the suggestions carefully
- Understand why the issue is problematic
- Apply the recommended fixes

### 4. Customize for Your Project
- Adjust thresholds based on your standards
- Filter out false positives
- Add project-specific patterns

### 5. Track Progress
- Monitor technical debt over time
- Measure improvement in metrics
- Celebrate wins!

---

## Integration Examples

### Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

python3 -c "
from reviewr.analysis.security_analyzer import SecurityAnalyzer
import sys

analyzer = SecurityAnalyzer()
# Analyze staged files
# Exit with error if critical issues found
"
```

### CI/CD Pipeline

```yaml
# .github/workflows/code-analysis.yml
name: Code Analysis

on: [push, pull_request]

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run reviewr analysis
        run: |
          python3 demo_complete_analysis.py
```

---

## Troubleshooting

### Issue: "Module not found"
**Solution**: Make sure you're in the reviewr directory and the package is installed:
```bash
cd reviewr
pip install -e .
```

### Issue: "Syntax error in analyzed code"
**Solution**: Analyzers skip files with syntax errors. Fix syntax first.

### Issue: "Too many findings"
**Solution**: 
- Start with CRITICAL and HIGH severity
- Adjust thresholds
- Focus on one category at a time

### Issue: "False positives"
**Solution**: 
- Review the suggestion to understand the issue
- If truly a false positive, add to ignore list
- Consider adjusting thresholds

---

## Getting Help

- **Documentation**: See `DEEP_ANALYSIS_SUMMARY.md` and `FINAL_SUMMARY.md`
- **Examples**: Run `demo_advanced_analysis.py` and `demo_complete_analysis.py`
- **Tests**: Check `test_advanced_analysis.py` for usage examples

---

## Next Steps

1. **Try the demos**: Run the demonstration scripts
2. **Run tests**: Verify everything works
3. **Analyze your code**: Use the analyzers on your own projects
4. **Integrate**: Add to your development workflow
5. **Customize**: Adjust thresholds and filters for your needs

Happy analyzing! 🚀

