import * as vscode from 'vscode';
import * as path from 'path';
import * as yaml from 'js-yaml';
import { Logger } from '../utils/Logger';
import { HtmlGenerator } from '../services/HtmlGenerator';
import { MessageHandler } from '../services/MessageHandler';
import { YamlValidator } from '../services/YamlValidator';
import { DocumentManager } from '../services/DocumentManager';
import { ImportResolver } from '../services/ImportResolver';

/**
 * Custom editor provider for FPGA IP core YAML files.
 *
 * Detects IP core files by checking for required keys: apiVersion + vlnv
 */
export class IpCoreEditorProvider implements vscode.CustomTextEditorProvider {
  private readonly logger = new Logger('IpCoreEditorProvider');
  private readonly htmlGenerator: HtmlGenerator;
  private readonly messageHandler: MessageHandler;
  private readonly documentManager: DocumentManager;
  private readonly importResolver: ImportResolver;

  constructor(private readonly context: vscode.ExtensionContext) {
    this.htmlGenerator = new HtmlGenerator(context);
    this.documentManager = new DocumentManager();
    const yamlValidator = new YamlValidator();
    this.messageHandler = new MessageHandler(yamlValidator, this.documentManager);
    this.importResolver = new ImportResolver(this.logger);

    this.logger.info('IpCoreEditorProvider initialized');
  }

  /**
   * Check if a document is an IP core YAML file.
   *
   * Detection strategy: Check for required keys (apiVersion + vlnv)
   * This allows *.yml files to work while avoiding false positives.
   */
  private async isIpCoreDocument(document: vscode.TextDocument): Promise<boolean> {
    try {
      const text = document.getText();
      const parsed = yaml.load(text);

      if (!parsed || typeof parsed !== 'object') {
        return false;
      }

      // Check for IP core signature: apiVersion + vlnv
      const data = parsed as any;
      // apiVersion can be string or number (YAML parses "1.0" as number)
      const hasApiVersion =
        'apiVersion' in data &&
        (typeof data.apiVersion === 'string' || typeof data.apiVersion === 'number');
      const hasVlnv = 'vlnv' in data && typeof data.vlnv === 'object';

      return hasApiVersion && hasVlnv;
    } catch (error) {
      // YAML parse error - not a valid IP core file
      return false;
    }
  }

  /**
   * Resolve the custom text editor for a document.
   */
  public async resolveCustomTextEditor(
    document: vscode.TextDocument,
    webviewPanel: vscode.WebviewPanel,
    _token: vscode.CancellationToken
  ): Promise<void> {
    this.logger.info('Resolving custom text editor for document', document.uri.toString());

    // Check if this is actually an IP core file
    const isIpCore = await this.isIpCoreDocument(document);
    if (!isIpCore) {
      this.logger.info('Document is not an IP core file, showing error in webview');
      // Show error in webview instead of disposing - disposing causes VS Code state issues
      webviewPanel.webview.options = { enableScripts: false };
      webviewPanel.webview.html = `
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <style>
                        body {
                            font-family: var(--vscode-font-family);
                            padding: 20px;
                            color: var(--vscode-foreground);
                            background: var(--vscode-editor-background);
                        }
                        .error-container {
                            display: flex;
                            flex-direction: column;
                            align-items: center;
                            justify-content: center;
                            height: 80vh;
                            text-align: center;
                        }
                        .error-icon { font-size: 48px; margin-bottom: 16px; }
                        .error-title { font-size: 18px; font-weight: bold; margin-bottom: 8px; }
                        .error-message { opacity: 0.7; }
                    </style>
                </head>
                <body>
                    <div class="error-container">
                        <div class="error-icon">⚠️</div>
                        <div class="error-title">Not an IP Core File</div>
                        <div class="error-message">
                            This file does not appear to be an IP core YAML file.<br>
                            Expected: <code>apiVersion</code> and <code>vlnv</code> fields.
                        </div>
                    </div>
                </body>
                </html>
            `;
      return;
    }

    this.logger.info('Document is an IP core file');

    // Configure webview
    webviewPanel.webview.options = {
      enableScripts: true,
    };

    // Set HTML content - use ipcore-specific HTML
    webviewPanel.webview.html = this.htmlGenerator.generateIpCoreHtml(webviewPanel.webview);

    // Track if webview is disposed
    let isDisposed = false;

    // Send initial update to webview with resolved imports
    const updateWebview = async () => {
      if (isDisposed) {
        this.logger.debug('Webview already disposed, skipping update');
        return;
      }
      try {
        this.logger.debug('updateWebview called');
        const text = document.getText();
        this.logger.debug(`Document text length: ${text.length}`);
        const parsed = yaml.load(text);
        this.logger.debug('YAML parsed successfully');

        // Resolve imports
        const baseDir = path.dirname(document.uri.fsPath);
        const imports = await this.importResolver.resolveImports(parsed as any, baseDir);
        this.logger.debug(`Imports resolved: ${Object.keys(imports).length} items`);

        // Check again after async operation
        if (isDisposed) {
          this.logger.debug('Webview disposed during import resolution, skipping update');
          return;
        }

        // Send to webview
        const message = {
          type: 'update',
          text: text,
          fileName: path.basename(document.uri.fsPath),
          imports: imports,
        };
        this.logger.info('Posting message to webview:', {
          type: message.type,
          fileName: message.fileName,
          textLength: text.length,
          importsCount: Object.keys(imports).length,
        });
        webviewPanel.webview.postMessage(message);
        this.logger.debug('Message posted successfully');
      } catch (error) {
        this.logger.error('Failed to update webview', error as Error);
      }
    };

    // Listen for document changes
    const changeDocumentSubscription = vscode.workspace.onDidChangeTextDocument((e) => {
      if (e.document.uri.toString() === document.uri.toString()) {
        void updateWebview();
      }
    });

    // Clean up subscriptions when webview is disposed
    webviewPanel.onDidDispose(() => {
      isDisposed = true;
      changeDocumentSubscription.dispose();
      this.logger.debug('Webview panel disposed');
    });

    // Handle messages from the webview
    webviewPanel.webview.onDidReceiveMessage(async (message) => {
      if (message.type === 'ready') {
        // Webview is ready, send initial update
        this.logger.info('Webview ready, sending initial update');
        void updateWebview();
      } else if (message.type === 'selectFiles') {
        // Handle file selection dialog
        this.logger.info('Opening file picker dialog');
        const options: vscode.OpenDialogOptions = {
          canSelectMany: message.multi !== undefined ? message.multi : true,
          openLabel: 'Select Files',
          canSelectFiles: true,
          canSelectFolders: false,
          filters: message.filters, // Support file filters
        };

        const fileUris = await vscode.window.showOpenDialog(options);
        if (fileUris && fileUris.length > 0) {
          // Get relative paths from the document directory
          const baseDir = path.dirname(document.uri.fsPath);
          const relativePaths = fileUris.map((uri) => {
            const filePath = uri.fsPath;
            return path.relative(baseDir, filePath);
          });

          // Send back to webview
          webviewPanel.webview.postMessage({
            type: 'filesSelected',
            files: relativePaths,
          });
          this.logger.info(`Selected ${relativePaths.length} file(s)`);
        }
      } else {
        void this.messageHandler.handleMessage(message, document);
      }
    });

    // Send initial content after a small delay to ensure webview is loaded
    // The webview will also send a 'ready' message when it's initialized
    setTimeout(() => {
      void updateWebview();
    }, 100);
  }
}
