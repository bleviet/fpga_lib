/**
 * VS Code Commands for VHDL Code Generation
 *
 * Provides commands to generate VHDL files from IP core definitions.
 * Uses Python backend (ipcore.py) when available, with TypeScript fallback.
 */

import * as vscode from 'vscode';
import * as path from 'path';
import { VHDLGenerator, BusType } from '../generator';
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
            await generateVHDL(context);
        })
    );

    // Generate with specific bus type (legacy, uses TypeScript only)
    context.subscriptions.push(
        vscode.commands.registerCommand('fpga-ip-core.generateVHDLWithBus', async () => {
            const busType = await vscode.window.showQuickPick(['axil', 'avmm'], {
                placeHolder: 'Select bus interface type',
                title: 'Bus Type',
            });
            if (busType) {
                await generateVHDLWithTypeScript(context, busType as BusType);
            }
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
 * Main VHDL generation command - uses Python backend with TypeScript fallback
 */
async function generateVHDL(context: vscode.ExtensionContext): Promise<void> {
    const ipCoreUri = getActiveIpCoreFile();
    if (!ipCoreUri) {
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

    // Check if Python backend is available
    const usePython = pythonBackend && await pythonBackend.isAvailable();

    await vscode.window.withProgress(
        {
            location: vscode.ProgressLocation.Notification,
            title: usePython
                ? 'Generating VHDL (Python backend)...'
                : 'Generating VHDL (TypeScript)...',
            cancellable: false,
        },
        async (progress) => {
            let result: { success: boolean; count?: number; error?: string };

            if (usePython && pythonBackend) {
                // Use Python backend
                result = await pythonBackend.generateVHDL(
                    ipCoreUri.fsPath,
                    outputDir,
                    { updateYaml: true },
                    progress
                );
            } else {
                // Fallback to TypeScript generator
                result = await generateWithTypeScript(context, ipCoreUri, outputDir);
            }

            if (result.success) {
                const backend = usePython ? '(Python)' : '(TypeScript)';
                const action = await vscode.window.showInformationMessage(
                    `✓ Generated ${result.count} files ${backend}`,
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
 * TypeScript-only generation (fallback)
 */
async function generateWithTypeScript(
    context: vscode.ExtensionContext,
    ipCoreUri: vscode.Uri,
    outputDir: string,
    busType: BusType = 'axil'
): Promise<{ success: boolean; count?: number; error?: string }> {
    try {
        const yaml = await import('yaml');
        const fs = await import('fs');
        const content = fs.readFileSync(ipCoreUri.fsPath, 'utf-8');
        const data = yaml.parse(content);

        const templateDir = path.join(context.extensionPath, 'dist', 'templates');
        const generator = new VHDLGenerator(templateDir);
        const written = await generator.writeFiles(data, vscode.Uri.file(outputDir), busType);

        return { success: true, count: written.size };
    } catch (error) {
        return { success: false, error: String(error) };
    }
}

/**
 * Legacy: Generate with specific bus type (TypeScript only)
 */
async function generateVHDLWithTypeScript(
    context: vscode.ExtensionContext,
    busType: BusType
): Promise<void> {
    const ipCoreUri = getActiveIpCoreFile();
    if (!ipCoreUri) {
        return;
    }

    const sourceDir = path.dirname(ipCoreUri.fsPath);
    const outputDir = path.join(sourceDir, 'generated');

    await vscode.window.withProgress(
        {
            location: vscode.ProgressLocation.Notification,
            title: `Generating VHDL (${busType})...`,
            cancellable: false,
        },
        async () => {
            const result = await generateWithTypeScript(context, ipCoreUri, outputDir, busType);

            if (result.success) {
                vscode.window.showInformationMessage(`✓ Generated ${result.count} files`);
            } else {
                vscode.window.showErrorMessage(`Generation failed: ${result.error}`);
            }
        }
    );
}
