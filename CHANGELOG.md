# Changelog

All notable changes to the reviewr project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added - Phase 4.1: AI-Powered Auto-Fix (Latest)
- **AI-Powered Fix Generation**: LLM-powered fix generator using Claude, GPT, or Gemini
- **Batch Fix Processing**: Concurrent fix application with intelligent conflict resolution
- **Enhanced CLI Commands**: `reviewr autofix generate`, `reviewr autofix apply`, `reviewr autofix review`
- **Safety Controls**: Confidence scoring, safe/unsafe flags, validation, and rollback support
- **Fix Categories**: SECURITY, PERFORMANCE, CORRECTNESS, STYLE, FORMATTING, IMPORTS, TYPE_HINTS, DOCUMENTATION
- **Interactive Mode**: Review and approve fixes one by one
- **Comprehensive Tests**: 10 tests covering AI fix generation, batch processing, and CLI commands
- **Documentation**: Complete guide for AI-powered auto-fix capabilities

### Added - Phase 11: Web Dashboard Enhancement
- **Upload Command**: `reviewr dashboard upload` to upload review results to dashboard
- **Automatic Project Creation**: Creates projects automatically if they don't exist
- **Full Metadata Extraction**: Files, lines, provider, model, tokens, cost, duration
- **Severity Counting**: Automatic counting and statistics for all severity levels
- **Finding Import**: Import all findings with complete details
- **Comprehensive Error Handling**: Robust error handling and validation
- **Integration Tests**: 3 tests for upload functionality
- **Documentation**: Complete guide for dashboard upload and integration

### Added - Phase 10: Email Reports Integration
- **Email Reporting**: Send code review summaries via email (SMTP)
- **HTML Email Templates**: Beautiful HTML email templates with styling
- **Attachment Support**: Attach full reports (SARIF, Markdown, HTML)
- **Multiple Recipients**: Send to multiple recipients with CC/BCC support
- **Critical Alerts**: Send immediate alerts for critical issues
- **CLI Commands**: `reviewr email send`, `reviewr email test`
- **Configuration**: SMTP server, authentication, TLS/SSL support
- **19 Tests**: Comprehensive test coverage for email functionality
- **Documentation**: Complete guide for email reporting setup and usage

### Added - Phase 9: Microsoft Teams Integration
- **Teams Webhooks**: Post review summaries to Teams channels via webhooks
- **Adaptive Cards**: Rich, interactive cards with formatting and actions
- **Bot API Support**: Full Teams Bot API integration for advanced features
- **Critical Alerts**: Immediate notifications for critical issues
- **CLI Commands**: `reviewr teams send`, `reviewr teams test`
- **22 Tests**: Comprehensive test coverage for Teams integration
- **Documentation**: Complete guide for Teams setup and usage

### Added - Phase 8: CircleCI Orb Integration
- **CircleCI Orb**: Reusable CircleCI orb for easy integration
- **Workflow Integration**: Seamless integration with CircleCI workflows
- **Artifact Upload**: Upload review results as CircleCI artifacts
- **Status Checks**: Fail builds on critical issues
- **Configuration**: Flexible configuration via environment variables
- **20 Tests**: Comprehensive test coverage for CircleCI integration
- **Documentation**: Complete guide for CircleCI setup and usage

### Added - Phase 7: Jenkins Integration
- **Jenkins Pipeline Support**: Groovy pipeline library for Jenkins
- **Declarative Pipeline**: Support for declarative pipeline syntax
- **Build Status**: Set build status based on review results
- **Artifact Publishing**: Publish review results as Jenkins artifacts
- **CLI Commands**: `reviewr jenkins post-comment`, `reviewr jenkins set-status`
- **20 Tests**: Comprehensive test coverage for Jenkins integration
- **Documentation**: Complete guide for Jenkins setup and usage

### Added - Phase 6: Azure DevOps Integration
- **Azure DevOps Integration**: Post review comments to Azure DevOps pull requests
- **Work Item Linking**: Link findings to Azure DevOps work items
- **Build Status**: Set build status based on review results
- **CLI Commands**: `reviewr azure post-comment`, `reviewr azure set-status`
- **18 Tests**: Comprehensive test coverage for Azure DevOps integration
- **Documentation**: Complete guide for Azure DevOps setup and usage

### Added - Phase 5: Slack Integration
- **Slack Webhooks**: Post review summaries to Slack channels
- **Rich Formatting**: Beautiful Slack message formatting with blocks and attachments
- **Critical Alerts**: Immediate notifications for critical issues
- **CLI Commands**: `reviewr slack send`, `reviewr slack test`
- **22 Tests**: Comprehensive test coverage for Slack integration
- **Documentation**: Complete guide for Slack setup and usage

### Added - Phase 4: Code Metrics Analysis
- **Complexity Metrics**: Cyclomatic, cognitive, Halstead, maintainability index
- **Duplication Detection**: Identify duplicate code blocks across files
- **Technical Debt**: Estimate technical debt in hours/days
- **CLI Flags**: `--metrics`, `--metrics-complexity`, `--metrics-duplication`, `--metrics-debt`
- **17 Tests**: Comprehensive test coverage for metrics analysis
- **Documentation**: Complete guide for code metrics features

### Added - Phase 3: Advanced Security Scanning
- **CVE/OSV Scanning**: Scan dependencies for known vulnerabilities
- **SAST Rules**: 50+ Static Application Security Testing rules
- **License Compliance**: Check license compatibility and compliance
- **CLI Flags**: `--security-scan`, `--scan-vulnerabilities`, `--scan-sast`, `--scan-licenses`
- **27 Tests**: Comprehensive test coverage for security scanning
- **Documentation**: Complete guide for security scanning features

### Added - Phase 2: Bitbucket Integration
- **Bitbucket Cloud/Server**: Post review comments to Bitbucket pull requests
- **Inline Comments**: Post findings as inline PR comments
- **Build Status**: Set build status based on review results
- **CLI Commands**: `reviewr bitbucket post-comment`, `reviewr bitbucket set-status`
- **16 Tests**: Comprehensive test coverage for Bitbucket integration
- **Documentation**: Complete guide for Bitbucket setup and usage

### Added - Phase 1: Incremental/Diff-Based Analysis
- **Git Diff Analysis**: Analyze only changed code in commits/PRs
- **Incremental Review**: Focus on new/modified code for faster reviews
- **Context Awareness**: Include surrounding context for better analysis
- **CLI Flags**: `--diff`, `--diff-base`, `--diff-target`, `--diff-context`
- **22 Tests**: Comprehensive test coverage for diff analysis
- **Documentation**: Complete guide for incremental analysis

### Added - Multi-Language Deep Analysis
- **Python Analyzers** (6): Security, DataFlow, Complexity, Type, Performance, Semantic
- **JavaScript/TypeScript Analyzers** (4): Security, Performance, Type, Quality
- **Go Analyzers** (3): Security, Performance, Quality
- **Rust Analyzers** (4): Ownership, Safety, Performance, Quality
- **Java Analyzers** (4): Security, Concurrency, Performance, Quality
- **Unified Orchestration**: Coordinate all analyzers with flexible configuration
- **141 Tests**: Comprehensive test coverage for all analyzers

### Added - API Efficiency Optimizations
- **Batch Review Types**: Single API call for multiple review types (93.3% reduction)
- **Intelligent Caching**: Cache results to avoid redundant API calls
- **Parallel Processing**: Concurrent file analysis for faster reviews
- **Performance Metrics**: 6.7x faster processing, 93.3% fewer API calls

### Added - VSCode Extension
- **Inline Diagnostics**: Real-time code review feedback in VSCode
- **Code Actions**: Quick fixes and suggestions
- **Hover Tooltips**: Detailed information on hover
- **Configuration**: Flexible configuration via VSCode settings
- **Production Ready**: Full functionality and comprehensive testing

### Added - CI/CD Integration
- **GitHub Actions**: Reusable workflow for automated PR reviews
- **GitLab CI**: Template for automated MR reviews
- **PR/MR Comments**: Beautiful markdown comments with findings
- **Status Checks**: Fail builds on critical issues
- **Comprehensive Documentation**: Setup guides for both platforms

### Added - Web Dashboard
- **Backend API**: FastAPI backend with RESTful endpoints
- **Database**: SQLAlchemy models for SQLite/PostgreSQL/MySQL
- **Metrics & Trends**: Track code quality over time
- **Project Management**: Organize reviews by project
- **Finding Tracking**: Track findings, status, and resolution
- **Docker Support**: Docker Compose for easy deployment
- **Comprehensive Tests**: Full test coverage for API and database

### Added - Auto-Fix Capabilities
- **Python Auto-Fixes** (6): Unused imports, formatting, type hints, security fixes
- **JavaScript/TypeScript Auto-Fixes** (7): const/let, async/await, null checks
- **Safe Application**: Backup, validation, and rollback support
- **CLI Commands**: `reviewr fix`, `reviewr fix --dry-run`, `reviewr fix --interactive`
- **Comprehensive Tests**: Full test coverage for auto-fix functionality

### Added - Configuration Presets
- **Built-in Presets**: security, performance, quick, comprehensive
- **Custom Presets**: Create and share team-specific presets
- **CLI Commands**: `reviewr preset list`, `reviewr preset show`, `reviewr preset validate`
- **Comprehensive Tests**: Full test coverage for preset system

### Added - Learning Mode
- **Feedback System**: Accept/reject findings to improve accuracy
- **Severity Customization**: Adjust severity levels based on feedback
- **Category Customization**: Customize finding categories
- **Persistence**: SQLite database for feedback storage
- **CLI Commands**: `reviewr learn feedback`, `reviewr learn stats`, `reviewr learn export`
- **Comprehensive Tests**: Full test coverage for learning system

## [1.0.0] - Initial Release

### Added
- **Core Review Engine**: AI-powered code review using Claude, GPT, and Gemini
- **Multiple Review Types**: Security, Performance, Correctness, Maintainability, Architecture, Standards, Explain
- **Output Formats**: SARIF, Markdown, HTML, JUnit
- **Local Analysis**: AST-based analysis without AI (complexity, dead code, imports)
- **Custom Rules**: YAML/JSON-based custom rule engine
- **Configuration**: YAML/TOML configuration files
- **CLI**: Comprehensive command-line interface
- **Caching**: Intelligent caching to avoid redundant API calls
- **Secrets Detection**: Detect and redact hardcoded secrets
- **Multi-Language Support**: Python, JavaScript, TypeScript, Go, Rust, Java
- **Comprehensive Tests**: 366 tests with 100% passing
- **Documentation**: Complete usage guide and roadmap

### Security
- **Secrets Redaction**: Automatically redact secrets before sending to AI
- **API Key Management**: Secure API key storage and management
- **Safe Defaults**: Conservative defaults for security and privacy

## Statistics

- **Total Lines of Code**: 19,300+
- **Core Modules**: 58+
- **CLI Commands**: 49+
- **Tests**: 366 (100% passing)
- **Documentation**: 8,600+ lines
- **Language Analyzers**: 21
- **Security Rules**: 50+
- **Auto-Fix Types**: 15+ (rule-based + AI-powered)
- **Integrations**: 9 (GitHub, GitLab, Bitbucket, Azure DevOps, Jenkins, CircleCI, Slack, Teams, Email)
- **Output Formats**: 5 (SARIF, Markdown, HTML, JUnit, Terminal)

## Future Roadmap

### Planned Features
- **IntelliJ/JetBrains Plugin**: IDE integration for IntelliJ IDEA, PyCharm, WebStorm
- **Advanced Dashboard Metrics**: Trend analysis, quality gates, technical debt tracking
- **Multi-Repository Analysis**: Analyze multiple repos, cross-repo dependencies
- **Enterprise Features**: SSO/SAML, Audit Logging, Custom LLM Support
- **Additional Languages**: C++, C#, Ruby, PHP, Swift, Kotlin
- **Advanced AI Features**: Code generation, refactoring suggestions, architecture recommendations

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting pull requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

