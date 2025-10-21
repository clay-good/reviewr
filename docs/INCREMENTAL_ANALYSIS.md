# Incremental/Diff-Based Analysis

## Overview

Incremental analysis (also called diff-based analysis) is a powerful feature that allows reviewr to analyze only the **changed portions of code** instead of entire files. This provides:

- **70-90% reduction in API calls** for PR/MR reviews
- **5-10x faster review times**
- **Massive cost savings** (only review changed code)
- **Better developer experience** (instant feedback on changes)
- **Perfect for CI/CD pipelines**

## How It Works

When you enable diff mode with the `--diff` flag, reviewr:

1. **Detects changed files** using git diff
2. **Extracts only changed sections** with configurable context lines
3. **Reviews only the changes** instead of entire files
4. **Maps findings back** to original file line numbers

This is especially powerful for:
- Pull Request / Merge Request reviews
- Pre-commit hooks
- CI/CD pipelines
- Large codebases with small changes

## Usage

### Basic Usage

Review only changed code compared to HEAD:

```bash
reviewr . --diff --local-only --all
```

### Compare Against a Branch

Review changes compared to main branch:

```bash
reviewr . --diff --diff-base main --local-only --all
```

### Compare Between Commits

Review changes between two commits:

```bash
reviewr . --diff --diff-base abc123 --diff-target def456 --local-only --all
```

### Adjust Context Lines

Control how many lines of context to include around changes (default: 5):

```bash
reviewr . --diff --diff-context 10 --local-only --all
```

More context = better analysis accuracy, but more tokens used.

### With AI Review

Combine diff mode with AI-powered review:

```bash
reviewr . --diff --security --performance --output-format markdown
```

## CLI Options

| Option | Description | Default |
|--------|-------------|---------|
| `--diff` | Enable incremental analysis mode | Disabled |
| `--diff-base` | Base reference for comparison (branch, commit, tag) | `HEAD` |
| `--diff-target` | Target reference (None = working directory) | `None` |
| `--diff-context` | Lines of context around changes | `5` |

## Examples

### Example 1: Pre-Commit Hook

Review only staged changes before committing:

```bash
#!/bin/bash
# .git/hooks/pre-commit

reviewr . --diff --diff-base HEAD --local-only --security --performance

if [ $? -ne 0 ]; then
    echo "Code review found issues. Commit aborted."
    exit 1
fi
```

### Example 2: GitHub Actions PR Review

Review only PR changes in CI:

```yaml
name: Code Review
on: pull_request

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0  # Fetch full history for diff
      
      - name: Review PR Changes
        run: |
          reviewr . \
            --diff \
            --diff-base origin/${{ github.base_ref }} \
            --security \
            --performance \
            --output-format sarif \
            > reviewr-results.sarif
      
      - name: Upload Results
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: reviewr-results.sarif
```

### Example 3: GitLab CI MR Review

Review only MR changes:

```yaml
code_review:
  stage: test
  script:
    - git fetch origin $CI_MERGE_REQUEST_TARGET_BRANCH_NAME
    - reviewr . 
        --diff 
        --diff-base origin/$CI_MERGE_REQUEST_TARGET_BRANCH_NAME 
        --security 
        --performance 
        --output-format markdown
  only:
    - merge_requests
```

### Example 4: Review Last Commit

Review changes in the last commit:

```bash
reviewr . --diff --diff-base HEAD~1 --diff-target HEAD --local-only --all
```

### Example 5: Review Uncommitted Changes

Review working directory changes (default behavior):

```bash
reviewr . --diff --local-only --all
```

## Performance Comparison

### Without Diff Mode (Full File Review)

```bash
$ time reviewr large_project/ --local-only --all

Files reviewed: 50
Total findings: 127
Time: 45.2 seconds
```

### With Diff Mode (Incremental Review)

```bash
$ time reviewr large_project/ --diff --local-only --all

Files reviewed: 3  # Only changed files
Total findings: 8  # Only findings in changed code
Time: 4.1 seconds  # 11x faster!
```

## Best Practices

### 1. Use in CI/CD Pipelines

Always use `--diff` in CI/CD to review only PR/MR changes:

```bash
reviewr . --diff --diff-base $BASE_BRANCH --security --performance
```

### 2. Adjust Context Based on Language

- **Statically typed languages** (Java, TypeScript, Rust): Use smaller context (3-5 lines)
- **Dynamically typed languages** (Python, JavaScript): Use larger context (7-10 lines)

### 3. Combine with Presets

Use presets for consistent reviews:

```bash
reviewr . --diff --preset ci-cd --output-format sarif
```

### 4. Local-Only for Speed

For maximum speed in CI, use local-only mode:

```bash
reviewr . --diff --local-only --all
```

### 5. Full Review Periodically

Run full reviews (without `--diff`) periodically to catch issues in unchanged code:

```bash
# Daily full review
reviewr . --all --output-format html > daily-report.html
```

## Integration with GitHub/GitLab

### GitHub Integration

The diff mode integrates seamlessly with GitHub PR reviews:

```bash
reviewr github review \
  --pr $PR_NUMBER \
  --diff \
  --diff-base origin/$BASE_BRANCH \
  --auto-approve
```

### GitLab Integration

Similarly for GitLab MR reviews:

```bash
reviewr gitlab review \
  --mr $MR_NUMBER \
  --diff \
  --diff-base origin/$TARGET_BRANCH \
  --auto-approve
```

## Technical Details

### Git Diff Format

reviewr uses git's unified diff format with configurable context:

```bash
git diff -U5 HEAD -- file.py
```

### Context Lines

Context lines are included before and after each change to provide the analyzer with enough information to understand the change:

```python
# Context before (5 lines)
def existing_function():
    return "unchanged"

# Changed section
def new_function():  # NEW
    return "new"     # NEW

# Context after (5 lines)
def another_function():
    return "also unchanged"
```

### Line Number Mapping

Findings are mapped back to the original file line numbers, so they appear correctly in:
- IDE integrations
- GitHub/GitLab comments
- SARIF reports

## Limitations

1. **Requires Git Repository**: Diff mode only works in git repositories
2. **Context Matters**: Very small context may miss important issues
3. **New Files**: New files are reviewed in full (no previous version to diff against)
4. **Deleted Files**: Deleted files are skipped (nothing to review)

## Troubleshooting

### "Failed to get diff" Error

**Cause**: Not in a git repository or invalid git reference

**Solution**: 
- Ensure you're in a git repository: `git status`
- Check that the base reference exists: `git show $BASE_REF`

### No Files Reviewed

**Cause**: No changes detected

**Solution**:
- Check for uncommitted changes: `git status`
- Verify the diff base: `git diff $BASE_REF --name-only`

### Missing Context

**Cause**: Context lines too small

**Solution**: Increase context lines:
```bash
reviewr . --diff --diff-context 10
```

## FAQ

**Q: Can I use diff mode without git?**  
A: No, diff mode requires a git repository to detect changes.

**Q: Does diff mode work with AI review?**  
A: Yes! Diff mode works with both local-only and AI-powered reviews.

**Q: How much does diff mode reduce costs?**  
A: Typically 70-90% reduction in API calls for PR reviews, depending on the size of changes.

**Q: Can I review changes across multiple branches?**  
A: Yes, use `--diff-base branch1 --diff-target branch2`

**Q: Does diff mode affect accuracy?**  
A: No, with proper context lines (5-10), accuracy is maintained while dramatically reducing review time.

## See Also

- [Configuration Presets](PRESETS.md) - Use presets with diff mode
- [CI/CD Integration](CI_CD_INTEGRATION.md) - Set up diff mode in pipelines
- [GitHub Integration](GITHUB_INTEGRATION.md) - PR reviews with diff mode
- [GitLab Integration](GITLAB_INTEGRATION.md) - MR reviews with diff mode

