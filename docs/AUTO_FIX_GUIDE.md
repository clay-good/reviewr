# Auto-Fix Guide

Comprehensive guide to reviewr's automatic code fixing capabilities.

---

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Supported Fixes](#supported-fixes)
- [Usage](#usage)
- [Safety Guarantees](#safety-guarantees)
- [Advanced Usage](#advanced-usage)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

---

## Overview

reviewr can automatically fix many common code issues detected during analysis. The auto-fix system:

- **Safe by default** - Only applies fixes marked as safe
- **Backup & rollback** - Creates backups before making changes
- **Syntax validation** - Validates code after applying fixes
- **Interactive mode** - Ask for confirmation before each fix
- **Dry run mode** - Preview changes without applying them
- **Confidence scoring** - Each fix has a confidence score (0.0-1.0)

---

## Quick Start

### 1. Analyze and Fix in One Command

```bash
# Analyze code and apply safe fixes automatically
reviewr fix apply src/ --safe-only

# Preview what would be fixed (dry run)
reviewr fix apply src/ --dry-run

# Interactive mode - confirm each fix
reviewr fix apply src/ --interactive
```

### 2. Fix from Previous Analysis

```bash
# First, run analysis and save results
reviewr src/ --all --output-format json > results.json

# Then apply fixes from the results
reviewr fix apply src/ --findings-file results.json --safe-only
```

### 3. Rollback Changes

```bash
# Rollback all applied fixes
reviewr fix rollback
```

---

## Supported Fixes

### Python Fixes

| Issue | Fix | Confidence | Safe |
|-------|-----|------------|------|
| Unused imports | Remove import statement | 95% | |
| `== None` comparison | Replace with `is None` | 95% | |
| `!= None` comparison | Replace with `is not None` | 95% | |
| Bare `except:` | Replace with `except Exception:` | 90% | |
| `% formatting` | Convert to f-string | 80% | |
| `.format()` | Convert to f-string | 85% | |
| Mutable default args | Replace with `None` | 70% | |
| String concatenation in loops | Suggest list + join | 60% | |

### JavaScript/TypeScript Fixes

| Issue | Fix | Confidence | Safe |
|-------|-----|------------|------|
| `var` declaration | Replace with `const` | 90% | |
| `var` (reassigned) | Replace with `let` | 95% | |
| `==` comparison | Replace with `===` | 95% | |
| `!=` comparison | Replace with `!==` | 95% | |
| String concatenation | Convert to template literal | 85% | |
| Function expression | Convert to arrow function | 80% | |
| `obj && obj.prop` | Replace with `obj?.prop` | 90% | |
| `value \|\| default` | Replace with `value ?? default` | 75% | |

**Legend:**
- **Safe** - Can be applied automatically without risk
- **Requires Review** - May change behavior, review recommended

---

## Usage

### Basic Commands

#### Apply Fixes

```bash
reviewr fix apply <path> [OPTIONS]
```

**Options:**

- `--dry-run` - Show what would be fixed without applying changes
- `--interactive, -i` - Ask for confirmation before each fix
- `--safe-only` - Only apply fixes marked as safe
- `--category <cat>` - Only apply fixes in specific categories
- `--min-confidence <n>` - Minimum confidence threshold (0.0-1.0, default: 0.8)
- `--backup-dir <dir>` - Directory for backups (default: .reviewr_backups)
- `--no-validation` - Skip syntax validation after applying fixes
- `--verbose, -v` - Show detailed information
- `--findings-file <file>` - Use findings from previous analysis

**Categories:**
- `formatting` - Code formatting issues
- `imports` - Import statement issues
- `type_hints` - Type hint issues
- `security` - Security vulnerabilities
- `performance` - Performance issues
- `correctness` - Correctness issues
- `style` - Code style issues

#### Rollback Fixes

```bash
reviewr fix rollback [OPTIONS]
```

**Options:**

- `--backup-dir <dir>` - Directory containing backups (default: .reviewr_backups)

---

## Safety Guarantees

### 1. Backup System

Every file is backed up before applying fixes:

```
.reviewr_backups/
├── file.py_20241018_143022.backup
├── file.py_20241018_143022.meta
├── app.js_20241018_143025.backup
└── app.js_20241018_143025.meta
```

- `.backup` files contain the original content
- `.meta` files contain the original file path

### 2. Syntax Validation

After applying fixes, reviewr validates the syntax:

- **Python**: Uses `compile()` to check syntax
- **JavaScript/TypeScript**: Uses `node --check` to validate
- **Automatic rollback**: If validation fails, changes are rolled back

### 3. Confidence Scoring

Each fix has a confidence score:

- **0.90-1.00**: Very high confidence, safe to auto-apply
- **0.80-0.89**: High confidence, generally safe
- **0.70-0.79**: Medium confidence, review recommended
- **0.60-0.69**: Low confidence, manual review required
- **< 0.60**: Very low confidence, not recommended

### 4. Safe Flag

Each fix is marked as safe or unsafe:

- **Safe fixes**: Won't change program behavior
- **Unsafe fixes**: May change behavior, require review

---

## Advanced Usage

### Filter by Category

```bash
# Only fix import issues
reviewr fix apply src/ --category imports

# Fix imports and style issues
reviewr fix apply src/ --category imports --category style
```

### Adjust Confidence Threshold

```bash
# Only apply very high confidence fixes (>= 0.9)
reviewr fix apply src/ --min-confidence 0.9

# Apply all fixes with confidence >= 0.7
reviewr fix apply src/ --min-confidence 0.7
```

### Custom Backup Directory

```bash
# Use custom backup directory
reviewr fix apply src/ --backup-dir ~/my-backups/

# Rollback from custom directory
reviewr fix rollback --backup-dir ~/my-backups/
```

### Combine with Analysis

```bash
# Analyze with specific provider and apply fixes
reviewr fix apply src/ --provider claude --safe-only

# Use custom config
reviewr fix apply src/ --config reviewr.yaml --interactive
```

---

## Examples

### Example 1: Safe Auto-Fix

```bash
# Analyze and fix only safe issues
reviewr fix apply src/ --safe-only --verbose
```

**Output:**
```
 Analyzing code at src/...
 Found 15 issues
📖 Loading file contents...
 Generating fixes...
 Generated 8 fixes

Fix Summary
┏━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━┳━━━━━━━━━━━━━━━━┓
┃ Category ┃ Count ┃ Safe ┃ Avg Confidence ┃
┡━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━╇━━━━━━━━━━━━━━━━┩
│ imports │ 3 │ 3 │ 95% │
│ correctness │ 4 │ 4 │ 93% │
│ style │ 1 │ 1 │ 85% │
└─────────────┴───────┴──────┴────────────────┘

 Applying fixes...
 Remove unused import: Fix applied successfully
 Use 'is None': Fix applied successfully
 Replace bare except: Fix applied successfully
...

================================================================================
Results:
 Success: 8
 Failed: 0
 ⏭ Skipped: 0
================================================================================

💾 Backups saved to: .reviewr_backups
 To rollback: reviewr fix rollback --backup-dir .reviewr_backups
```

### Example 2: Interactive Mode

```bash
# Review each fix before applying
reviewr fix apply src/app.py --interactive
```

**Output:**
```
================================================================================
Fix: Remove unused import
File: src/app.py (lines 1-1)
Category: imports
Confidence: 95%

Old code:
import os

New code:

Explanation: Removing unused imports improves code clarity and reduces namespace pollution.

Apply this fix? [y/N]: y
 Remove unused import: Fix applied successfully

================================================================================
Fix: Use 'is None'
File: src/app.py (lines 15-15)
Category: correctness
Confidence: 95%

Old code:
if user == None:

New code:
if user is None:

Explanation: Use 'is' for singleton comparisons (None, True, False) instead of '=='.

Apply this fix? [y/N]: y
 Use 'is None': Fix applied successfully
```

### Example 3: Dry Run

```bash
# Preview changes without applying
reviewr fix apply src/ --dry-run --verbose
```

**Output:**
```
 Analyzing code at src/...
 Found 12 issues
 Generating fixes...
 Generated 6 fixes

Dry run mode - no changes will be made

Fix 1/6:
 File: src/app.py:1
 Category: imports
 Description: Remove unused import
 Confidence: 95%
 Safe: 
 Explanation: Removing unused imports improves code clarity

Fix 2/6:
 File: src/app.py:15
 Category: correctness
 Description: Use 'is None'
 Confidence: 95%
 Safe: 
 Explanation: Use 'is' for singleton comparisons
...
```

### Example 4: Fix from Previous Analysis

```bash
# Step 1: Run analysis and save results
reviewr src/ --all --output-format json > analysis.json

# Step 2: Review the results
cat analysis.json | jq '.findings[] | {file: .file_path, message: .message}'

# Step 3: Apply fixes
reviewr fix apply src/ --findings-file analysis.json --safe-only
```

---

## Troubleshooting

### Issue: "No fixable issues found"

**Cause:** No issues match the current filters (safe-only, category, confidence)

**Solution:**
```bash
# Try lowering confidence threshold
reviewr fix apply src/ --min-confidence 0.7

# Try without safe-only filter
reviewr fix apply src/ --interactive
```

### Issue: "Syntax validation failed"

**Cause:** Applied fix caused syntax errors

**Solution:**
- Fixes are automatically rolled back
- Check the error message for details
- Report the issue if it's a bug in the fix generator

### Issue: "Cannot find backup files"

**Cause:** Backup directory doesn't exist or was deleted

**Solution:**
```bash
# Check if backups exist
ls -la .reviewr_backups/

# If using custom directory, specify it
reviewr fix rollback --backup-dir /path/to/backups/
```

### Issue: "Fix not applied"

**Cause:** Code may have changed since analysis

**Solution:**
```bash
# Re-run analysis and apply fixes immediately
reviewr fix apply src/ --safe-only

# Or use --verbose to see detailed error messages
reviewr fix apply src/ --verbose
```

---

## Best Practices

1. **Start with dry run**: Always preview changes first
 ```bash
 reviewr fix apply src/ --dry-run
 ```

2. **Use safe-only for automation**: In CI/CD, only apply safe fixes
 ```bash
 reviewr fix apply src/ --safe-only --min-confidence 0.9
 ```

3. **Interactive for important code**: Use interactive mode for critical files
 ```bash
 reviewr fix apply src/core/ --interactive
 ```

4. **Keep backups**: Don't delete `.reviewr_backups/` until you're sure
 ```bash
 # Backups are safe to delete after verification
 rm -rf .reviewr_backups/
 ```

5. **Test after fixing**: Always run tests after applying fixes
 ```bash
 reviewr fix apply src/ --safe-only
 pytest # or your test command
 ```

---

## Integration with CI/CD

### GitHub Actions

```yaml
- name: Auto-fix code issues
 run: |
 reviewr fix apply src/ --safe-only --min-confidence 0.9
 
- name: Commit fixes
 run: |
 git config user.name "reviewr-bot"
 git config user.email "bot@reviewr.dev"
 git add -A
 git commit -m "Auto-fix: Apply safe code fixes" || true
 git push
```

### GitLab CI

```yaml
auto-fix:
 script:
 - reviewr fix apply src/ --safe-only --min-confidence 0.9
 - git config user.name "reviewr-bot"
 - git config user.email "bot@reviewr.dev"
 - git add -A
 - git commit -m "Auto-fix: Apply safe code fixes" || true
 - git push
```

---

**Built by world-class engineers** 

**Status:** Production Ready
