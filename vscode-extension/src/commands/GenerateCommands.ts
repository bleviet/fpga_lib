/**
 * VS Code Commands for VHDL Code Generation
 * 
 * Provides commands to generate VHDL files from IP core definitions.
 */

import * as vscode from 'vscode';
import * as path from 'path';
import { VHDLGenerator, BusType } from '../generator';

/**
 * Register all generator commands with VS Code
 */
export function registerGeneratorCommands(context: vscode.ExtensionContext): void {
    // Generate VHDL command
    context.subscriptions.push(
        vscode.commands.registerCommand('fpga-ip-core.generateVHDL', async () => {
            await generateVHDL(context);
        })
    );

    // Generate with specific bus type
    context.subscriptions.push(
        vscode.commands.registerCommand('fpga-ip-core.generateVHDLWithBus', async () => {
            const busType = await vscode.window.showQuickPick(['axil', 'avmm'], {
                placeHolder: 'Select bus interface type',
                title: 'Bus Type',
            });
            if (busType) {
                await generateVHDL(context, busType as BusType);
            }
        })
    );
}

/**
 * Get IP core data from active editor
 */
async function getIpCoreFromActiveEditor(): Promise<{ data: any; uri: vscode.Uri } | undefined> {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showErrorMessage('No active editor. Please open an IP core YAML file.');
        return undefined;
    }

    const document = editor.document;
    if (!document.fileName.endsWith('.yml') && !document.fileName.endsWith('.yaml')) {
        vscode.window.showErrorMessage('Active file is not a YAML file.');
        return undefined;
    }

    const yaml = await import('yaml');
    try {
        const content = document.getText();
        const data = yaml.parse(content);

        // Check if it's an IP core file
        if (!data.vlnv) {
            vscode.window.showErrorMessage('File does not appear to be an IP core definition (missing vlnv).');
            return undefined;
        }

        return { data, uri: document.uri };
    } catch (error) {
        vscode.window.showErrorMessage(`Failed to parse YAML: ${error}`);
        return undefined;
    }
}

/**
 * Main VHDL generation command
 */
async function generateVHDL(
    context: vscode.ExtensionContext,
    busType: BusType = 'axil'
): Promise<void> {
    // Get IP core from active editor
    const ipCore = await getIpCoreFromActiveEditor();
    if (!ipCore) {
        return;
    }

    // Determine output directory (same as IP core file)
    const sourceDir = path.dirname(ipCore.uri.fsPath);
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

    const outputDir = outputUri?.[0] || vscode.Uri.file(defaultOutputDir);

    // Get template directory from extension
    // Webpack copies templates to dist/templates
    const templateDir = path.join(context.extensionPath, 'dist', 'templates');

    try {
        // Show progress
        await vscode.window.withProgress(
            {
                location: vscode.ProgressLocation.Notification,
                title: 'Generating VHDL files...',
                cancellable: false,
            },
            async () => {
                const generator = new VHDLGenerator(templateDir);
                const written = await generator.writeFiles(ipCore.data, outputDir, busType);

                // Show success message with generated files
                const fileList = Array.from(written.keys()).join(', ');
                const result = await vscode.window.showInformationMessage(
                    `Generated ${written.size} VHDL files: ${fileList}`,
                    'Open Folder',
                    'Open First File'
                );

                if (result === 'Open Folder') {
                    await vscode.commands.executeCommand('vscode.openFolder', outputDir, { forceNewWindow: false });
                } else if (result === 'Open First File') {
                    const [, firstUri] = Array.from(written.entries())[0];
                    await vscode.window.showTextDocument(firstUri);
                }
            }
        );
    } catch (error) {
        vscode.window.showErrorMessage(`VHDL generation failed: ${error}`);
    }
}
