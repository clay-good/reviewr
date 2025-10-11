import * as vscode from 'vscode';
import * as child_process from 'child_process';
import * as path from 'path';
import * as fs from 'fs';

// Diagnostic collection for reviewr findings
let diagnosticCollection: vscode.DiagnosticCollection;

export function activate(context: vscode.ExtensionContext) {
    console.log('reviewr extension is now active');

    // Create diagnostic collection
    diagnosticCollection = vscode.languages.createDiagnosticCollection('reviewr');
    context.subscriptions.push(diagnosticCollection);

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

    // Auto-review on save if enabled
    context.subscriptions.push(
        vscode.workspace.onDidSaveTextDocument((document) => {
            const config = vscode.workspace.getConfiguration('reviewr');
            if (config.get('autoReview')) {
                reviewFile(document.uri.fsPath);
            }
        })
    );
}

export function deactivate() {
    if (diagnosticCollection) {
        diagnosticCollection.dispose();
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

    // Clear previous diagnostics if configured
    if (clearProblems) {
        diagnosticCollection.clear();
    }

    // Create temporary directory for SARIF output
    const tempDir = path.join(require('os').tmpdir(), 'reviewr-vscode');
    if (!fs.existsSync(tempDir)) {
        fs.mkdirSync(tempDir, { recursive: true });
    }

    const sarifPath = path.join(tempDir, 'reviewr-report.sarif');

    // Build command
    let args = [targetPath];
    
    if (useAllTypes) {
        args.push('--all');
    } else {
        reviewTypes.forEach(type => args.push(`--${type}`));
    }
    
    args.push('--output-format', 'sarif');

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
                stdout += data.toString();
            });

            proc.stderr.on('data', (data) => {
                stderr += data.toString();
            });

            proc.on('close', (code) => {
                if (code !== 0 && code !== 1) {
                    // Code 1 is expected when issues are found
                    vscode.window.showErrorMessage(`reviewr failed: ${stderr}`);
                    reject(new Error(stderr));
                    return;
                }

                // Parse SARIF output
                try {
                    if (fs.existsSync(sarifPath)) {
                        const sarifContent = fs.readFileSync(sarifPath, 'utf-8');
                        const sarif = JSON.parse(sarifContent);
                        processSarifResults(sarif);
                        
                        vscode.window.showInformationMessage('reviewr analysis complete');
                    } else {
                        vscode.window.showWarningMessage('No SARIF output generated');
                    }
                } catch (error) {
                    vscode.window.showErrorMessage(`Failed to parse SARIF: ${error}`);
                }

                resolve();
            });

            proc.on('error', (error) => {
                vscode.window.showErrorMessage(`Failed to run reviewr: ${error.message}`);
                reject(error);
            });
        });
    });
}

function processSarifResults(sarif: any) {
    if (!sarif.runs || sarif.runs.length === 0) {
        return;
    }

    const run = sarif.runs[0];
    const results = run.results || [];

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

        // Add related information if available
        if (result.fixes && result.fixes.length > 0) {
            const fix = result.fixes[0];
            diagnostic.relatedInformation = [
                new vscode.DiagnosticRelatedInformation(
                    new vscode.Location(
                        vscode.Uri.file(filePath),
                        diagnostic.range
                    ),
                    `Suggestion: ${fix.description.text}`
                )
            ];
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

