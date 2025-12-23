import * as vscode from 'vscode';
import { Logger, LogLevel } from './utils/Logger';
import { MemoryMapEditorProvider } from './providers/MemoryMapEditorProvider';

/**
 * Extension activation entry point
 */
export function activate(context: vscode.ExtensionContext): void {
    // Initialize logging
    Logger.initialize('FPGA Memory Map Editor', LogLevel.INFO);
    const logger = new Logger('Extension');
    logger.info('Extension activating');

    // Register the custom editor provider
    context.subscriptions.push(
        vscode.window.registerCustomEditorProvider(
            'fpgaMemoryMap.editor',
            new MemoryMapEditorProvider(context),
            {
                webviewOptions: {
                    retainContextWhenHidden: true,
                },
                supportsMultipleEditorsPerDocument: false,
            }
        )
    );

    logger.info('Extension activated successfully');
}

/**
 * Extension deactivation cleanup
 */
export function deactivate(): void {
    const logger = new Logger('Extension');
    logger.info('Extension deactivating');
    Logger.dispose();
}
