# reviewr VS Code Extension

AI-powered code review directly in VS Code. This extension wraps the reviewr CLI tool and displays findings in the Problems panel.

## Features

- **Review Current File**: Analyze the currently open file
- **Review Entire Workspace**: Analyze all files in your workspace
- **Problems Panel Integration**: View findings directly in VS Code's Problems panel
- **Auto-review on Save**: Optionally run reviews automatically when you save files
- **Configurable Review Types**: Choose which types of reviews to run

## Requirements

- reviewr CLI tool must be installed and accessible in your PATH
- API key for at least one LLM provider (Claude, OpenAI, or Gemini)

## Installation

### Install reviewr CLI

```bash
pip install -e /path/to/reviewr
```

### Install the Extension

1. Open VS Code
2. Go to Extensions (Ctrl+Shift+X / Cmd+Shift+X)
3. Search for "reviewr"
4. Click Install

Or install from VSIX:

```bash
cd vscode-extension
npm install
npm run compile
npm run package
code --install-extension reviewr-vscode-0.1.0.vsix
```

## Usage

### Command Palette

1. Open Command Palette (Ctrl+Shift+P / Cmd+Shift+P)
2. Type "reviewr"
3. Select:
   - **reviewr: Review Current File** - Analyze the active file
   - **reviewr: Review Entire Workspace** - Analyze all files in workspace

### Context Menu

- Right-click in the editor or on a file in the Explorer
- Select "Review Current File"

### Keyboard Shortcuts

You can add custom keyboard shortcuts in VS Code:

1. Open Keyboard Shortcuts (Ctrl+K Ctrl+S / Cmd+K Cmd+S)
2. Search for "reviewr"
3. Add your preferred shortcuts

## Configuration

Open VS Code Settings (Ctrl+, / Cmd+,) and search for "reviewr":

### `reviewr.cliPath`

Path to the reviewr CLI executable. Default: `"reviewr"`

```json
{
  "reviewr.cliPath": "/usr/local/bin/reviewr"
}
```

### `reviewr.useAllReviewTypes`

Use `--all` flag to run all review types. Default: `true`

```json
{
  "reviewr.useAllReviewTypes": true
}
```

### `reviewr.reviewTypes`

Default review types to run when `useAllReviewTypes` is false. Default: `["security", "performance", "correctness"]`

```json
{
  "reviewr.reviewTypes": ["security", "correctness"]
}
```

### `reviewr.autoReview`

Automatically review files on save. Default: `false`

```json
{
  "reviewr.autoReview": true
}
```

### `reviewr.clearProblemsOnReview`

Clear previous reviewr problems before running a new review. Default: `true`

```json
{
  "reviewr.clearProblemsOnReview": true
}
```

## Example Configuration

Add to your `.vscode/settings.json`:

```json
{
  "reviewr.cliPath": "reviewr",
  "reviewr.useAllReviewTypes": false,
  "reviewr.reviewTypes": ["security", "correctness"],
  "reviewr.autoReview": false,
  "reviewr.clearProblemsOnReview": true
}
```

## Viewing Results

After running a review:

1. Open the Problems panel (Ctrl+Shift+M / Cmd+Shift+M)
2. Filter by "reviewr" to see only reviewr findings
3. Click on any finding to jump to the relevant code
4. Hover over the problem for more details and suggestions

## Troubleshooting

### "reviewr command not found"

Make sure reviewr is installed and in your PATH:

```bash
which reviewr  # Unix/Mac
where reviewr  # Windows
```

If not in PATH, set the full path in settings:

```json
{
  "reviewr.cliPath": "/full/path/to/reviewr"
}
```

### "No API key configured"

Set your API key as an environment variable:

```bash
export ANTHROPIC_API_KEY="your-key"
export OPENAI_API_KEY="your-key"
export GOOGLE_API_KEY="your-key"
```

Or add to your shell profile (~/.bashrc, ~/.zshrc, etc.)

### Extension not activating

1. Check the Output panel (View > Output)
2. Select "reviewr" from the dropdown
3. Look for error messages

## Development

### Building from Source

```bash
cd vscode-extension
npm install
npm run compile
```

### Packaging

```bash
npm run package
```

This creates a `.vsix` file you can install manually.

### Testing

```bash
npm run watch  # Watch mode for development
<<<<<<< HEAD
```
=======
```

Then press F5 in VS Code to launch Extension Development Host.

## License

MIT

## Support

For issues and feature requests, please visit:
https://github.com/yourusername/reviewr/issues

>>>>>>> 9142a626e7c17e9750e46f0bd63dca202a22eff4
