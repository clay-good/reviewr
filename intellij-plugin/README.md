# Reviewr IntelliJ Plugin

AI-powered code review plugin for IntelliJ IDEA and other JetBrains IDEs.

## Features

- **Real-time Code Analysis** - Get instant feedback as you code
- **Multi-Language Support** - Python, JavaScript, TypeScript, Go, Rust, Java
- **Security Analysis** - Detect vulnerabilities and security issues
- **Performance Analysis** - Find performance bottlenecks
- **Quality Analysis** - Improve code quality and maintainability
- **Quick Fixes** - Apply suggested fixes with Alt+Enter
- **Tool Window** - View all findings in a dedicated panel

## Supported IDEs

- IntelliJ IDEA (Community & Ultimate)
- PyCharm (Community & Professional)
- WebStorm
- GoLand
- RustRover
- Android Studio

## Installation

### From JetBrains Marketplace (Coming Soon)

1. Open Settings/Preferences → Plugins
2. Search for "Reviewr"
3. Click Install
4. Restart IDE

### From Source

1. Clone the repository
2. Build the plugin:
   ```bash
   cd intellij-plugin
   ./gradlew buildPlugin
   ```
3. Install the plugin:
   - Open Settings/Preferences → Plugins
   - Click ⚙️ → Install Plugin from Disk
   - Select `build/distributions/reviewr-1.0.0.zip`
   - Restart IDE

## Configuration

### Prerequisites

Reviewr CLI must be installed:
```bash
pip install reviewr
```

### Plugin Settings

Open Settings/Preferences → Tools → Reviewr:

- **Enable Reviewr** - Turn analysis on/off
- **Reviewr Path** - Path to reviewr CLI (leave empty to use system python3 -m reviewr)
- **Use Local Analysis Only** - Faster analysis without API calls
- **Real-time Analysis** - Analyze code as you type
- **Analysis Delay** - Delay before running analysis (default: 1000ms)
- **Enable Security Analysis** - Detect security vulnerabilities
- **Enable Performance Analysis** - Find performance issues
- **Enable Quality Analysis** - Check code quality

### Severity Filters

Choose which severity levels to display:
- Critical (always recommended)
- High (recommended)
- Medium (recommended)
- Low
- Info

## Usage

### Analyze Current File

- **Keyboard Shortcut**: `Ctrl+Alt+R` (Windows/Linux) or `Cmd+Alt+R` (Mac)
- **Menu**: Tools → Reviewr → Analyze Current File
- **Context Menu**: Right-click in editor → Analyze with Reviewr

### Analyze Entire Project

- **Menu**: Tools → Reviewr → Analyze Entire Project

### View Results

Findings appear in three places:

1. **Inline in Editor** - Warnings and errors highlighted in code
2. **Tool Window** - Bottom panel showing all findings
3. **Problems Panel** - Integrated with IDE's problems view

### Apply Quick Fixes

1. Place cursor on a finding
2. Press `Alt+Enter` (Windows/Linux) or `Option+Enter` (Mac)
3. Select "Apply Reviewr fix"
4. Review and confirm the change

### Clear Cache

If analysis results seem stale:
- **Menu**: Tools → Reviewr → Clear Analysis Cache

## Architecture

### Core Components

- **ReviewrService** - Main service for running analysis
- **ReviewrAnnotator** - Real-time external annotator
- **ReviewrInspection** - On-demand local inspection
- **ReviewrToolWindow** - Results viewer
- **ReviewrSettings** - Configuration management
- **ApplyReviewrFixIntention** - Quick fix actions

### How It Works

1. Plugin detects file changes or user triggers analysis
2. Executes reviewr CLI: `python3 -m reviewr review <file> --format sarif --local-only`
3. Parses SARIF output
4. Displays findings in IDE
5. Provides quick fixes for applicable issues

## Development

### Build

```bash
./gradlew buildPlugin
```

### Run in IDE

```bash
./gradlew runIde
```

This launches a new IntelliJ IDEA instance with the plugin installed.

### Test

```bash
./gradlew test
```

### Publish

```bash
export PUBLISH_TOKEN="your-jetbrains-marketplace-token"
./gradlew publishPlugin
```

## Implementation Status

### ✅ Completed

- [x] Gradle build configuration
- [x] Plugin descriptor (plugin.xml)
- [x] Core service (ReviewrService.java)
- [x] Data models (ReviewFinding.java)
- [x] Settings (ReviewrSettings.java)
- [x] Documentation

### 📝 To Be Implemented

- [ ] ReviewrAnnotator.java - Real-time annotator
- [ ] ReviewrInspection.java - On-demand inspection
- [ ] ApplyReviewrFixIntention.java - Quick fixes
- [ ] ReviewrToolWindowFactory.java - Tool window
- [ ] ReviewrConfigurable.java - Settings UI
- [ ] Action classes (AnalyzeFileAction, etc.)
- [ ] Listener classes (FileEditorListener, etc.)
- [ ] Icons and resources
- [ ] Unit tests
- [ ] Integration tests

See `INTELLIJ_PLUGIN_IMPLEMENTATION.md` for detailed implementation templates.

## Troubleshooting

### Plugin Not Working

1. Check that reviewr CLI is installed: `python3 -m reviewr --help`
2. Check plugin settings: Settings → Tools → Reviewr
3. Check IDE logs: Help → Show Log in Finder/Explorer
4. Try clearing cache: Tools → Reviewr → Clear Analysis Cache

### Analysis Too Slow

1. Enable "Use Local Analysis Only" in settings
2. Increase "Analysis Delay" to reduce frequency
3. Disable "Real-time Analysis" and use manual triggers

### No Findings Shown

1. Check severity filters in settings
2. Verify file type is supported (Python, JS, TS, Go, Rust, Java)
3. Check that file has actual issues to report

## Contributing

Contributions welcome! See the main reviewr repository for contribution guidelines.

## License

Same as reviewr main project.

## Support

- GitHub Issues: https://github.com/yourusername/reviewr/issues
- Documentation: https://reviewr.dev/docs
- Email: support@reviewr.dev

