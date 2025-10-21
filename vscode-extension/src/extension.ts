import * as vscode from 'vscode';
import * as child_process from 'child_process';
import * as path from 'path';
import * as fs from 'fs';

// Diagnostic collection for reviewr findings
let diagnosticCollection: vscode.DiagnosticCollection;
let statusBarItem: vscode.StatusBarItem;
let outputChannel: vscode.OutputChannel;

// Cache for SARIF results
interface CachedResult {
    sarif: any;
    timestamp: number;
    fileHash: string;
}
const resultCache = new Map<string, CachedResult>();

// Store findings for hover provider
const findingsByFile = new Map<string, any[]>();

export function activate(context: vscode.ExtensionContext) {
    console.log('reviewr extension is now active');

    // Create output channel
    outputChannel = vscode.window.createOutputChannel('reviewr');
    context.subscriptions.push(outputChannel);

    // Create diagnostic collection
    diagnosticCollection = vscode.languages.createDiagnosticCollection('reviewr');
    context.subscriptions.push(diagnosticCollection);

    // Create status bar item
    statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
    statusBarItem.command = 'reviewr.reviewCurrentFile';
    statusBarItem.text = '$(shield) reviewr';
    statusBarItem.tooltip = 'Click to review current file';
    statusBarItem.show();
    context.subscriptions.push(statusBarItem);

    // Register commands
    context.subscriptions.push(
        vscode.commands.registerCommand('reviewr.reviewCurrentFile', () => {
            reviewCurrentFile();
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('reviewr.reviewWorkspace', () => {
            reviewWorkspace();
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('reviewr.clearDiagnostics', () => {
            diagnosticCollection.clear();
            findingsByFile.clear();
            resultCache.clear();
            vscode.window.showInformationMessage('reviewr diagnostics cleared');
        })
    );

    // Register code action provider for quick fixes
    context.subscriptions.push(
        vscode.languages.registerCodeActionsProvider(
            { scheme: 'file' },
            new ReviewrCodeActionProvider(),
            {
                providedCodeActionKinds: ReviewrCodeActionProvider.providedCodeActionKinds
            }
        )
    );

    // Register hover provider for detailed information
    context.subscriptions.push(
        vscode.languages.registerHoverProvider(
            { scheme: 'file' },
            new ReviewrHoverProvider()
        )
    );

    // Auto-review on save if enabled
    context.subscriptions.push(
        vscode.workspace.onDidSaveTextDocument((document) => {
            const config = vscode.workspace.getConfiguration('reviewr');
            if (config.get('autoReview')) {
                reviewFile(document.uri.fsPath);
            }
        })
    );

    // Update status bar on active editor change
    context.subscriptions.push(
        vscode.window.onDidChangeActiveTextEditor((editor) => {
            updateStatusBar(editor);
        })
    );

    // Initial status bar update
    updateStatusBar(vscode.window.activeTextEditor);
}

export function deactivate() {
    if (diagnosticCollection) {
        diagnosticCollection.dispose();
    }
    if (statusBarItem) {
        statusBarItem.dispose();
    }
    if (outputChannel) {
        outputChannel.dispose();
    }
}

function updateStatusBar(editor: vscode.TextEditor | undefined) {
    if (!editor) {
        statusBarItem.text = '$(shield) reviewr';
        statusBarItem.tooltip = 'No active editor';
        return;
    }

    const filePath = editor.document.uri.fsPath;
    const diagnostics = diagnosticCollection.get(editor.document.uri);

    if (!diagnostics || diagnostics.length === 0) {
        statusBarItem.text = '$(shield-check) reviewr';
        statusBarItem.tooltip = 'No issues found';
        statusBarItem.backgroundColor = undefined;
        return;
    }

    // Count by severity
    let errors = 0;
    let warnings = 0;
    let infos = 0;

    for (const diag of diagnostics) {
        if (diag.severity === vscode.DiagnosticSeverity.Error) {
            errors++;
        } else if (diag.severity === vscode.DiagnosticSeverity.Warning) {
            warnings++;
        } else {
            infos++;
        }
    }

    // Update status bar
    if (errors > 0) {
        statusBarItem.text = `$(error) ${errors} $(warning) ${warnings}`;
        statusBarItem.tooltip = `reviewr: ${errors} errors, ${warnings} warnings, ${infos} infos`;
        statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.errorBackground');
    } else if (warnings > 0) {
        statusBarItem.text = `$(warning) ${warnings} $(info) ${infos}`;
        statusBarItem.tooltip = `reviewr: ${warnings} warnings, ${infos} infos`;
        statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
    } else {
        statusBarItem.text = `$(info) ${infos}`;
        statusBarItem.tooltip = `reviewr: ${infos} infos`;
        statusBarItem.backgroundColor = undefined;
    }
}

async function reviewCurrentFile() {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showErrorMessage('No active editor');
        return;
    }

    const filePath = editor.document.uri.fsPath;
    await reviewFile(filePath);
}

async function reviewWorkspace() {
    const workspaceFolders = vscode.workspace.workspaceFolders;
    if (!workspaceFolders || workspaceFolders.length === 0) {
        vscode.window.showErrorMessage('No workspace folder open');
        return;
    }

    const workspacePath = workspaceFolders[0].uri.fsPath;
    await reviewPath(workspacePath);
}

async function reviewFile(filePath: string) {
    await reviewPath(filePath);
}

async function reviewPath(targetPath: string) {
    const config = vscode.workspace.getConfiguration('reviewr');
    const cliPath = config.get<string>('cliPath', 'reviewr');
    const useAllTypes = config.get<boolean>('useAllReviewTypes', true);
    const reviewTypes = config.get<string[]>('reviewTypes', ['security', 'performance', 'correctness']);
    const clearProblems = config.get<boolean>('clearProblemsOnReview', true);

    // Check cache for single file reviews
    const isFile = fs.existsSync(targetPath) && fs.statSync(targetPath).isFile();
    if (isFile) {
        const fileHash = getFileHash(targetPath);
        const cached = resultCache.get(targetPath);

        if (cached && cached.fileHash === fileHash) {
            const age = Date.now() - cached.timestamp;
            if (age < 60000) { // Cache for 1 minute
                outputChannel.appendLine(`Using cached results for ${targetPath}`);
                processSarifResults(cached.sarif);
                updateStatusBar(vscode.window.activeTextEditor);
                return;
            }
        }
    }

    // Clear previous diagnostics if configured
    if (clearProblems) {
        diagnosticCollection.clear();
        findingsByFile.clear();
    }

    // Update status bar
    statusBarItem.text = '$(sync~spin) reviewr';
    statusBarItem.tooltip = 'Running analysis...';

    // Create temporary directory for SARIF output
    const tempDir = path.join(require('os').tmpdir(), 'reviewr-vscode');
    if (!fs.existsSync(tempDir)) {
        fs.mkdirSync(tempDir, { recursive: true });
    }

    const sarifPath = path.join(tempDir, 'reviewr-report.sarif');

    // Build command
    let args = ['analyze', targetPath];

    if (useAllTypes) {
        args.push('--all');
    } else {
        reviewTypes.forEach(type => args.push(`--${type}`));
    }

    args.push('--output-format', 'sarif');

    outputChannel.appendLine(`Running: ${cliPath} ${args.join(' ')}`);

    // Show progress
    await vscode.window.withProgress({
        location: vscode.ProgressLocation.Notification,
        title: 'Running reviewr...',
        cancellable: false
    }, async (progress) => {
        progress.report({ message: 'Analyzing code...' });

        return new Promise<void>((resolve, reject) => {
            // Change to temp directory to capture output
            const options = {
                cwd: tempDir,
                env: { ...process.env }
            };

            const proc = child_process.spawn(cliPath, args, options);

            let stdout = '';
            let stderr = '';

            proc.stdout.on('data', (data) => {
                const text = data.toString();
                stdout += text;
                outputChannel.append(text);
            });

            proc.stderr.on('data', (data) => {
                const text = data.toString();
                stderr += text;
                outputChannel.append(text);
            });

            proc.on('close', (code) => {
                outputChannel.appendLine(`reviewr exited with code ${code}`);

                if (code !== 0 && code !== 1) {
                    // Code 1 is expected when issues are found
                    vscode.window.showErrorMessage(`reviewr failed: ${stderr}`);
                    statusBarItem.text = '$(error) reviewr';
                    statusBarItem.tooltip = 'Analysis failed';
                    reject(new Error(stderr));
                    return;
                }

                // Parse SARIF output
                try {
                    if (fs.existsSync(sarifPath)) {
                        const sarifContent = fs.readFileSync(sarifPath, 'utf-8');
                        const sarif = JSON.parse(sarifContent);

                        // Cache results for single files
                        if (isFile) {
                            const fileHash = getFileHash(targetPath);
                            resultCache.set(targetPath, {
                                sarif,
                                timestamp: Date.now(),
                                fileHash
                            });
                        }

                        processSarifResults(sarif);

                        const issueCount = sarif.runs[0]?.results?.length || 0;
                        vscode.window.showInformationMessage(`reviewr: Found ${issueCount} issue(s)`);
                        outputChannel.appendLine(`Analysis complete: ${issueCount} issue(s) found`);
                    } else {
                        vscode.window.showWarningMessage('No SARIF output generated');
                        outputChannel.appendLine('Warning: No SARIF output generated');
                    }
                } catch (error) {
                    vscode.window.showErrorMessage(`Failed to parse SARIF: ${error}`);
                    outputChannel.appendLine(`Error parsing SARIF: ${error}`);
                }

                updateStatusBar(vscode.window.activeTextEditor);
                resolve();
            });

            proc.on('error', (error) => {
                vscode.window.showErrorMessage(`Failed to run reviewr: ${error.message}`);
                outputChannel.appendLine(`Error: ${error.message}`);
                statusBarItem.text = '$(error) reviewr';
                statusBarItem.tooltip = 'Failed to run reviewr';
                reject(error);
            });
        });
    });
}

function getFileHash(filePath: string): string {
    try {
        const content = fs.readFileSync(filePath, 'utf-8');
        const crypto = require('crypto');
        return crypto.createHash('md5').update(content).digest('hex');
    } catch (error) {
        return '';
    }
}

function processSarifResults(sarif: any) {
    if (!sarif.runs || sarif.runs.length === 0) {
        return;
    }

    const run = sarif.runs[0];
    const results = run.results || [];
    const rules = run.tool?.driver?.rules || [];

    // Create rule lookup
    const ruleMap = new Map<string, any>();
    for (const rule of rules) {
        ruleMap.set(rule.id, rule);
    }

    // Group diagnostics by file
    const diagnosticsByFile = new Map<string, vscode.Diagnostic[]>();

    for (const result of results) {
        const location = result.locations?.[0]?.physicalLocation;
        if (!location) continue;

        const filePath = location.artifactLocation.uri;
        const region = location.region;

        // Convert SARIF to VS Code diagnostic
        const diagnostic = new vscode.Diagnostic(
            new vscode.Range(
                region.startLine - 1,
                region.startColumn || 0,
                region.endLine - 1,
                region.endColumn || Number.MAX_SAFE_INTEGER
            ),
            result.message.text,
            mapSeverity(result.level)
        );

        diagnostic.source = 'reviewr';
        diagnostic.code = result.ruleId;

        // Store full result for hover provider
        if (!findingsByFile.has(filePath)) {
            findingsByFile.set(filePath, []);
        }
        findingsByFile.get(filePath)!.push({
            result,
            rule: ruleMap.get(result.ruleId),
            diagnostic
        });

        // Add related information if available
        if (result.fixes && result.fixes.length > 0) {
            const fix = result.fixes[0];
            diagnostic.relatedInformation = [
                new vscode.DiagnosticRelatedInformation(
                    new vscode.Location(
                        vscode.Uri.file(filePath),
                        diagnostic.range
                    ),
                    `💡 Suggestion: ${fix.description.text}`
                )
            ];
        }

        // Add tags based on rule properties
        const rule = ruleMap.get(result.ruleId);
        if (rule?.properties?.tags) {
            diagnostic.tags = [];
            if (rule.properties.tags.includes('deprecated')) {
                diagnostic.tags.push(vscode.DiagnosticTag.Deprecated);
            }
            if (rule.properties.tags.includes('unnecessary')) {
                diagnostic.tags.push(vscode.DiagnosticTag.Unnecessary);
            }
        }

        // Group by file
        if (!diagnosticsByFile.has(filePath)) {
            diagnosticsByFile.set(filePath, []);
        }
        diagnosticsByFile.get(filePath)!.push(diagnostic);
    }

    // Set diagnostics for each file
    for (const [filePath, diagnostics] of diagnosticsByFile) {
        const uri = vscode.Uri.file(filePath);
        diagnosticCollection.set(uri, diagnostics);
    }
}

function mapSeverity(sarifLevel: string): vscode.DiagnosticSeverity {
    switch (sarifLevel) {
        case 'error':
            return vscode.DiagnosticSeverity.Error;
        case 'warning':
            return vscode.DiagnosticSeverity.Warning;
        case 'note':
            return vscode.DiagnosticSeverity.Information;
        default:
            return vscode.DiagnosticSeverity.Hint;
    }
}

// Code Action Provider for quick fixes
class ReviewrCodeActionProvider implements vscode.CodeActionProvider {
    public static readonly providedCodeActionKinds = [
        vscode.CodeActionKind.QuickFix
    ];

    provideCodeActions(
        document: vscode.TextDocument,
        range: vscode.Range | vscode.Selection,
        context: vscode.CodeActionContext,
        token: vscode.CancellationToken
    ): vscode.CodeAction[] {
        const actions: vscode.CodeAction[] = [];

        // Get findings for this file
        const findings = findingsByFile.get(document.uri.fsPath);
        if (!findings) {
            return actions;
        }

        // Find findings that overlap with the current range
        for (const finding of findings) {
            const diagnostic = finding.diagnostic;

            if (!diagnostic.range.intersection(range)) {
                continue;
            }

            // Add "Show Details" action
            const showDetailsAction = new vscode.CodeAction(
                '📖 Show Details',
                vscode.CodeActionKind.QuickFix
            );
            showDetailsAction.command = {
                command: 'vscode.open',
                title: 'Show Details',
                arguments: [vscode.Uri.parse(`https://github.com/clay-good/reviewr#${finding.result.ruleId}`)]
            };
            showDetailsAction.diagnostics = [diagnostic];
            actions.push(showDetailsAction);

            // Add suggestion as quick fix if available
            if (finding.result.fixes && finding.result.fixes.length > 0) {
                const fix = finding.result.fixes[0];
                const fixAction = new vscode.CodeAction(
                    `💡 ${fix.description.text}`,
                    vscode.CodeActionKind.QuickFix
                );
                fixAction.diagnostics = [diagnostic];
                fixAction.isPreferred = true;

                // Note: Actual code edits would require more detailed fix information from SARIF
                // For now, we just show the suggestion
                actions.push(fixAction);
            }

            // Add "Ignore this issue" action
            const ignoreAction = new vscode.CodeAction(
                '🚫 Ignore this issue',
                vscode.CodeActionKind.QuickFix
            );
            ignoreAction.command = {
                command: 'reviewr.ignoreFinding',
                title: 'Ignore Finding',
                arguments: [document.uri, diagnostic]
            };
            ignoreAction.diagnostics = [diagnostic];
            actions.push(ignoreAction);
        }

        return actions;
    }
}

// Hover Provider for detailed information
class ReviewrHoverProvider implements vscode.HoverProvider {
    provideHover(
        document: vscode.TextDocument,
        position: vscode.Position,
        token: vscode.CancellationToken
    ): vscode.ProviderResult<vscode.Hover> {
        // Get findings for this file
        const findings = findingsByFile.get(document.uri.fsPath);
        if (!findings) {
            return null;
        }

        // Find finding at this position
        for (const finding of findings) {
            if (finding.diagnostic.range.contains(position)) {
                const markdown = new vscode.MarkdownString();
                markdown.isTrusted = true;
                markdown.supportHtml = true;

                // Title
                markdown.appendMarkdown(`### 🔍 reviewr: ${finding.result.ruleId}\n\n`);

                // Severity
                const severity = finding.result.level || 'note';
                const severityEmojiMap: { [key: string]: string } = {
                    'error': '🔴',
                    'warning': '🟡',
                    'note': '🔵',
                    'none': '⚪'
                };
                const severityEmoji = severityEmojiMap[severity] || '⚪';
                markdown.appendMarkdown(`**Severity**: ${severityEmoji} ${severity}\n\n`);

                // Message
                markdown.appendMarkdown(`**Issue**: ${finding.result.message.text}\n\n`);

                // Rule description
                if (finding.rule) {
                    if (finding.rule.shortDescription) {
                        markdown.appendMarkdown(`**Description**: ${finding.rule.shortDescription.text}\n\n`);
                    }
                    if (finding.rule.fullDescription) {
                        markdown.appendMarkdown(`${finding.rule.fullDescription.text}\n\n`);
                    }
                }

                // Suggestion
                if (finding.result.fixes && finding.result.fixes.length > 0) {
                    markdown.appendMarkdown(`---\n\n`);
                    markdown.appendMarkdown(`💡 **Suggestion**: ${finding.result.fixes[0].description.text}\n\n`);
                }

                // Tags
                if (finding.rule?.properties?.tags) {
                    const tags = finding.rule.properties.tags.join(', ');
                    markdown.appendMarkdown(`---\n\n`);
                    markdown.appendMarkdown(`**Tags**: ${tags}\n\n`);
                }

                // Confidence/Precision
                if (finding.rule?.properties?.precision) {
                    markdown.appendMarkdown(`**Precision**: ${finding.rule.properties.precision}\n\n`);
                }

                return new vscode.Hover(markdown, finding.diagnostic.range);
            }
        }

        return null;
    }
}

