/**
 * VS Code Commands for VHDL Code Generation
 *
 * Provides commands to generate VHDL files from IP core definitions.
 * Requires Python backend (ipcore.py) with ipcore_lib installed.
 */

import * as vscode from 'vscode';
import * as path from 'path';
import { PythonBackend } from '../services/PythonBackend';

// Singleton backend instance
let pythonBackend: PythonBackend | undefined;

/**
 * Register all generator commands with VS Code
 */
export function registerGeneratorCommands(context: vscode.ExtensionContext): void {
    // Initialize Python backend
    pythonBackend = new PythonBackend();
    context.subscriptions.push({ dispose: () => pythonBackend?.dispose() });

    // Generate VHDL command (auto-detects bus from YAML)
    context.subscriptions.push(
        vscode.commands.registerCommand('fpga-ip-core.generateVHDL', async () => {
            await generateVHDL();
        })
    );

    // Legacy command - now just calls main generate
    context.subscriptions.push(
        vscode.commands.registerCommand('fpga-ip-core.generateVHDLWithBus', async () => {
            // Bus type is now auto-detected from YAML
            await generateVHDL();
        })
    );

    // Parse VHDL and create IP core YAML
    context.subscriptions.push(
        vscode.commands.registerCommand('fpga-ip-core.parseVHDL', async (uri?: vscode.Uri) => {
            await parseVHDL(uri);
        })
    );
}

/**
 * Get IP core file path from active editor
 */
function getActiveIpCoreFile(): vscode.Uri | undefined {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showErrorMessage('No active editor. Please open an IP core YAML file.');
        return undefined;
    }

    const document = editor.document;
    if (!document.fileName.endsWith('.ip.yml') && !document.fileName.endsWith('.ip.yaml')) {
        vscode.window.showErrorMessage('Active file is not an IP core file (*.ip.yml).');
        return undefined;
    }

    return document.uri;
}

/**
 * Main VHDL generation command - requires Python backend
 */
async function generateVHDL(): Promise<void> {
    const ipCoreUri = getActiveIpCoreFile();
    if (!ipCoreUri) {
        return;
    }

    // Check if Python backend is available
    if (!pythonBackend) {
        vscode.window.showErrorMessage('Python backend not initialized.');
        return;
    }

    const isAvailable = await pythonBackend.isAvailable();
    if (!isAvailable) {
        const action = await vscode.window.showErrorMessage(
            'Python backend not available. Please ensure Python and ipcore_lib are installed.',
            'Show Setup Instructions'
        );
        if (action === 'Show Setup Instructions') {
            vscode.env.openExternal(vscode.Uri.parse('https://github.com/bleviet/ipcore_lib#installation'));
        }
        return;
    }

    const sourceDir = path.dirname(ipCoreUri.fsPath);
    const defaultOutputDir = path.join(sourceDir, 'generated');

    // Ask user for output directory
    const outputUri = await vscode.window.showOpenDialog({
        defaultUri: vscode.Uri.file(defaultOutputDir),
        canSelectFiles: false,
        canSelectFolders: true,
        canSelectMany: false,
        openLabel: 'Select Output Directory',
        title: 'Select directory for generated VHDL files',
    });

    const outputDir = outputUri?.[0]?.fsPath || defaultOutputDir;

    await vscode.window.withProgress(
        {
            location: vscode.ProgressLocation.Notification,
            title: 'Generating VHDL files...',
            cancellable: false,
        },
        async (progress) => {
            const result = await pythonBackend!.generateVHDL(
                ipCoreUri.fsPath,
                outputDir,
                { updateYaml: true },
                progress
            );

            if (result.success) {
                const action = await vscode.window.showInformationMessage(
                    `✓ Generated ${result.count} files`,
                    'Open Folder'
                );

                if (action === 'Open Folder') {
                    await vscode.commands.executeCommand('revealFileInOS', vscode.Uri.file(outputDir));
                }
            } else {
                vscode.window.showErrorMessage(`Generation failed: ${result.error}`);
            }
        }
    );
}

/**
 * Parse VHDL file and generate IP core YAML
 */
async function parseVHDL(resourceUri?: vscode.Uri): Promise<void> {
    // Get VHDL file URI from context menu or active editor
    let vhdlUri = resourceUri;

    if (!vhdlUri) {
        const editor = vscode.window.activeTextEditor;
        if (editor && (editor.document.fileName.endsWith('.vhd') ||
            editor.document.fileName.endsWith('.vhdl'))) {
            vhdlUri = editor.document.uri;
        }
    }

    if (!vhdlUri) {
        // Show file picker
        const files = await vscode.window.showOpenDialog({
            canSelectFiles: true,
            canSelectFolders: false,
            filters: { 'VHDL Files': ['vhd', 'vhdl'] },
            title: 'Select VHDL file to parse',
        });
        vhdlUri = files?.[0];
    }

    if (!vhdlUri) {
        return;
    }

    // Check Python backend
    if (!pythonBackend) {
        vscode.window.showErrorMessage('Python backend not initialized.');
        return;
    }

    const isAvailable = await pythonBackend.isAvailable();
    if (!isAvailable) {
        const action = await vscode.window.showErrorMessage(
            'Python backend not available. Please ensure Python and ipcore_lib are installed.',
            'Show Setup Instructions'
        );
        if (action === 'Show Setup Instructions') {
            vscode.env.openExternal(vscode.Uri.parse('https://github.com/bleviet/ipcore_lib#installation'));
        }
        return;
    }

    // Generate output path (.ip.yml next to .vhd)
    const vhdlPath = vhdlUri.fsPath;
    const baseName = path.basename(vhdlPath, path.extname(vhdlPath));
    const outputDir = path.dirname(vhdlPath);
    const defaultOutput = path.join(outputDir, `${baseName}.ip.yml`);

    await vscode.window.withProgress(
        {
            location: vscode.ProgressLocation.Notification,
            title: 'Creating IP Core from VHDL...',
            cancellable: false,
        },
        async (progress) => {
            const result = await pythonBackend!.parseVHDL(
                vhdlPath,
                defaultOutput,
                { detectBus: true },
                progress
            );

            if (result.success && result.output) {
                const action = await vscode.window.showInformationMessage(
                    `✓ Created ${path.basename(result.output)}`,
                    'Open File'
                );

                if (action === 'Open File') {
                    const doc = await vscode.workspace.openTextDocument(result.output);
                    await vscode.window.showTextDocument(doc);
                }
            } else {
                vscode.window.showErrorMessage(`Parse failed: ${result.error}`);
            }
        }
    );
}

