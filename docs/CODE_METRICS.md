# Code Metrics Analysis

## Overview

The **Code Metrics** module provides comprehensive code quality analysis including:

- **Complexity Metrics**: Cyclomatic and cognitive complexity, Halstead metrics, maintainability index
- **Duplication Detection**: Token-based and AST-based code duplication detection
- **Technical Debt Estimation**: SQALE methodology-based debt calculation and prioritization

## Features

### 1. Complexity Analysis

Analyzes code complexity using multiple industry-standard metrics:

#### Cyclomatic Complexity (McCabe)
- Measures the number of linearly independent paths through code
- Thresholds:
  - **Low** (1-5): Simple, easy to test
  - **Moderate** (6-10): Acceptable complexity
  - **High** (11-20): Consider refactoring
  - **Very High** (21-50): Difficult to maintain
  - **Extreme** (50+): Critical refactoring needed

#### Cognitive Complexity (SonarSource)
- Measures how difficult code is to understand
- Accounts for nesting and control flow breaks
- Thresholds:
  - **Low** (1-5): Easy to understand
  - **Moderate** (6-10): Acceptable
  - **High** (11-15): Consider simplification
  - **Very High** (16-25): Hard to understand
  - **Extreme** (25+): Critical simplification needed

#### Halstead Metrics
- **Volume**: Size of the implementation
- **Difficulty**: How difficult to write/understand
- **Effort**: Mental effort required

#### Maintainability Index
- Composite metric combining:
  - Halstead Volume
  - Cyclomatic Complexity
  - Lines of Code
- Scale: 0-100 (higher is better)
- Thresholds:
  - **85-100**: Highly maintainable
  - **65-84**: Maintainable
  - **20-64**: Moderate maintainability
  - **0-19**: Difficult to maintain

### 2. Duplication Detection

Detects code duplication across your codebase:

#### Detection Types
- **Type 1 Clones**: Exact duplicates (ignoring whitespace/comments)
- **Type 2 Clones**: Structural duplicates (ignoring literals/identifiers)
- **Type 3 Clones**: Similar code with minor modifications

#### Configuration
- **Minimum Lines**: Default 6 lines (configurable)
- **Minimum Tokens**: Default 50 tokens
- **Scope**: Within files and across files

#### Metrics
- **Duplication Percentage**: % of code that is duplicated
- **Significant Duplicates**: Blocks >= 6 lines
- **Exact Duplicates**: 100% similarity

### 3. Technical Debt Estimation

Estimates technical debt using the SQALE methodology:

#### Debt Categories
- **Complexity**: High cyclomatic/cognitive complexity
- **Duplication**: Code duplication
- **Maintainability**: Low maintainability index
- **Security**: Security vulnerabilities
- **Reliability**: Potential bugs
- **Testability**: Hard to test code
- **Documentation**: Missing/poor documentation

#### Severity Levels
- **Blocker**: Must fix immediately
- **Critical**: Fix as soon as possible
- **Major**: Fix in current sprint
- **Minor**: Fix when convenient
- **Info**: Nice to fix

#### SQALE Rating
Based on debt ratio (debt / total development time):
- **A**: <= 5% (Excellent)
- **B**: <= 10% (Good)
- **C**: <= 20% (Fair)
- **D**: <= 50% (Poor)
- **E**: > 50% (Critical)

#### Remediation Time
Estimates time to fix each issue:
- **Complexity**: 5 min per complexity point above threshold
- **Duplication**: 2 min per duplicated line
- **Maintainability**: 30 min per unmaintainable function
- **Security**: 60 min per security issue

## Usage

### Enable All Metrics

```bash
reviewr /path/to/project --metrics --all --output-format sarif
```

### Selective Metrics

```bash
# Only complexity analysis
reviewr /path/to/project --metrics-complexity --all --output-format sarif

# Only duplication detection
reviewr /path/to/project --metrics-duplication --all --output-format sarif

# Only technical debt estimation
reviewr /path/to/project --metrics-debt --all --output-format sarif
```

### Custom Configuration

```bash
# Custom duplication threshold
reviewr /path/to/project --metrics-duplication --min-duplicate-lines 10 --all --output-format sarif

# With incremental analysis (faster)
reviewr /path/to/project --metrics --diff --all --output-format sarif
```

### Combined with Security Scanning

```bash
# Comprehensive analysis
reviewr /path/to/project --metrics --security-scan --all --output-format sarif
```

## Output Examples

### Complexity Finding

```json
{
  "type": "complexity",
  "severity": "high",
  "title": "High complexity in function process_data",
  "description": "Cyclomatic: 25, Cognitive: 20",
  "file": "src/processor.py",
  "line": 42,
  "recommendation": "Refactor to reduce complexity"
}
```

### Duplication Finding

```json
{
  "type": "duplication",
  "severity": "medium",
  "title": "Code duplication detected (30 lines)",
  "description": "Duplicate code between src/a.py:10 and src/b.py:50",
  "file": "src/a.py",
  "line": 10,
  "recommendation": "Extract common code into reusable function"
}
```

### Technical Debt Finding

```json
{
  "type": "debt",
  "severity": "critical",
  "title": "High complexity (cyclomatic: 35)",
  "description": "Difficult to understand, test, and maintain. Estimated remediation: 2.1 hours",
  "file": "function complex_algorithm",
  "line": 100,
  "recommendation": "Refactor into smaller functions, reduce branching"
}
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Code Quality

on: [push, pull_request]

jobs:
  metrics:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install reviewr
        run: pip install reviewr
      
      - name: Run metrics analysis
        run: reviewr . --metrics --all --output-format sarif > metrics.sarif
      
      - name: Upload SARIF
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: metrics.sarif
```

### GitLab CI

```yaml
code_metrics:
  stage: test
  script:
    - pip install reviewr
    - reviewr . --metrics --all --output-format sarif > metrics.sarif
  artifacts:
    reports:
      sast: metrics.sarif
```

### Bitbucket Pipelines

```yaml
pipelines:
  default:
    - step:
        name: Code Metrics
        script:
          - pip install reviewr
          - reviewr . --metrics --all --output-format sarif
```

## Performance

### Benchmark Results

**Small Project (10 files, 1,000 LOC):**
- Complexity: ~1 second
- Duplication: ~2 seconds
- Debt: ~1 second
- **Total: ~4 seconds**

**Medium Project (50 files, 5,000 LOC):**
- Complexity: ~3 seconds
- Duplication: ~8 seconds
- Debt: ~2 seconds
- **Total: ~13 seconds**

**Large Project (200 files, 20,000 LOC):**
- Complexity: ~10 seconds
- Duplication: ~30 seconds
- Debt: ~5 seconds
- **Total: ~45 seconds**

### With Incremental Analysis

**Changed Files Only (3 files, 300 LOC):**
- Complexity: ~0.5 seconds
- Duplication: ~1 second
- Debt: ~0.5 seconds
- **Total: ~2 seconds**
- **Improvement: 95% faster**

## Best Practices

### 1. Set Realistic Thresholds

```bash
# Adjust complexity thresholds for your team
reviewr . --metrics --cyclomatic-threshold 15 --cognitive-threshold 20 --all --output-format sarif
```

### 2. Focus on Critical Issues

```bash
# Only report high and critical issues
reviewr . --metrics --min-severity high --all --output-format sarif
```

### 3. Use Incremental Analysis

```bash
# Fast PR reviews
reviewr . --metrics --diff --all --output-format sarif
```

### 4. Combine with Security

```bash
# Comprehensive quality check
reviewr . --metrics --security-scan --all --output-format sarif
```

### 5. Track Trends

```bash
# Regular metrics collection
reviewr . --metrics --all --output-format sarif > metrics-$(date +%Y%m%d).sarif
```

## Integration with Other Tools

### SonarQube

The metrics module uses industry-standard metrics compatible with SonarQube:
- Cyclomatic Complexity
- Cognitive Complexity
- Code Duplication
- Technical Debt (SQALE)

### Code Climate

Compatible with Code Climate's maintainability metrics:
- Maintainability Index
- Complexity Scores
- Duplication Percentage

### CodeScene

Behavioral code analysis integration:
- Complexity Trends
- Hotspot Detection
- Refactoring Priorities

## API Usage

### Python API

```python
from reviewr.metrics.complexity import ComplexityAnalyzer
from reviewr.metrics.duplication import DuplicationDetector
from reviewr.metrics.debt import TechnicalDebtEstimator

# Analyze complexity
analyzer = ComplexityAnalyzer()
metrics = analyzer.analyze_file(Path("myfile.py"))

for metric in metrics:
    if metric.is_complex:
        print(f"{metric.name}: cyclomatic={metric.cyclomatic}")

# Detect duplication
detector = DuplicationDetector(min_lines=6)
report = detector.analyze_project(Path("myproject"))
print(f"Duplication: {report.duplication_percentage}%")

# Estimate debt
estimator = TechnicalDebtEstimator()
debt_report = estimator.estimate_from_metrics(
    complexity_metrics=metrics,
    duplication_report=report,
    total_loc=10000
)
print(f"Technical debt: {debt_report.total_debt_days:.1f} days")
print(f"SQALE rating: {debt_report.sqale_rating}")
```

## Roadmap

### Planned Enhancements

1. **Additional Languages**: JavaScript, TypeScript, Java, Go, Rust
2. **Custom Rules**: User-defined complexity thresholds
3. **Trend Analysis**: Historical metrics tracking
4. **Hotspot Detection**: Identify problematic areas
5. **Refactoring Suggestions**: AI-powered refactoring recommendations
6. **Team Metrics**: Aggregate metrics across teams
7. **Quality Gates**: Fail builds on threshold violations

## References

- [Cyclomatic Complexity (McCabe)](https://en.wikipedia.org/wiki/Cyclomatic_complexity)
- [Cognitive Complexity (SonarSource)](https://www.sonarsource.com/docs/CognitiveComplexity.pdf)
- [Halstead Metrics](https://en.wikipedia.org/wiki/Halstead_complexity_measures)
- [SQALE Methodology](https://www.sqale.org/)
- [Maintainability Index](https://docs.microsoft.com/en-us/visualstudio/code-quality/code-metrics-values)

## Support

For issues, questions, or feature requests, please visit:
- GitHub Issues: https://github.com/yourusername/reviewr/issues
- Documentation: https://reviewr.dev/docs/metrics

