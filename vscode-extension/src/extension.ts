import * as vscode from 'vscode';
import yaml from 'js-yaml';

export function activate(context: vscode.ExtensionContext) {
    console.log('FPGA Memory Map Editor is active');

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
}

class MemoryMapEditorProvider implements vscode.CustomTextEditorProvider {
    constructor(private readonly context: vscode.ExtensionContext) { }

    private static readonly viewType = 'fpgaMemoryMap.editor';

    public async resolveCustomTextEditor(
        document: vscode.TextDocument,
        webviewPanel: vscode.WebviewPanel,
        _token: vscode.CancellationToken
    ): Promise<void> {
        webviewPanel.webview.options = {
            enableScripts: true,
        };

        webviewPanel.webview.html = this.getHtmlForWebview(webviewPanel.webview);

        function updateWebview() {
            webviewPanel.webview.postMessage({
                type: 'update',
                text: document.getText(),
                fileName: vscode.workspace.asRelativePath(document.uri, false),
            });
        }

        const changeDocumentSubscription = vscode.workspace.onDidChangeTextDocument(e => {
            if (e.document.uri.toString() === document.uri.toString()) {
                updateWebview();
            }
        });

        webviewPanel.onDidDispose(() => {
            changeDocumentSubscription.dispose();
        });

        webviewPanel.webview.onDidReceiveMessage(e => {
            switch (e.type) {
                case 'update':
                    this.updateTextDocument(document, e.text);
                    return;
                case 'command':
                    if (e.command === 'save') {
                        void document.save();
                        return;
                    }
                    if (e.command === 'validate') {
                        try {
                            yaml.load(document.getText());
                            void vscode.window.showInformationMessage('YAML parsed successfully.');
                        } catch (err: any) {
                            void vscode.window.showErrorMessage(`YAML parse error: ${err?.message ?? String(err)}`);
                        }
                        return;
                    }
                    return;
            }
        });

        updateWebview();
    }

    private getHtmlForWebview(webview: vscode.Webview): string {
        const scriptUri = webview.asWebviewUri(
            vscode.Uri.joinPath(this.context.extensionUri, 'dist', 'webview.js')
        );

        const codiconsUri = webview.asWebviewUri(
            vscode.Uri.joinPath(this.context.extensionUri, 'node_modules', '@vscode/codicons', 'dist', 'codicon.css')
        );

        return `
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${webview.cspSource} 'unsafe-inline' https://cdn.tailwindcss.com https://fonts.googleapis.com; font-src ${webview.cspSource} https://fonts.gstatic.com; script-src ${webview.cspSource} 'unsafe-inline' https://cdn.tailwindcss.com;">
                <link href="${codiconsUri}" rel="stylesheet" />
                <script src="https://cdn.tailwindcss.com"></script>
                <script>
                    tailwind.config = {
                        theme: {
                            extend: {
                                fontFamily: {
                                    sans: ['var(--vscode-font-family)', 'sans-serif'],
                                    mono: ['var(--vscode-editor-font-family)', 'monospace'],
                                },
                                colors: {
                                    gray: {
                                        50: 'var(--vscode-editor-background)',
                                        100: 'var(--vscode-sideBar-background)',
                                        200: 'var(--vscode-panel-border)',
                                        300: 'var(--vscode-input-border)',
                                        400: 'var(--vscode-descriptionForeground)',
                                        500: 'var(--vscode-foreground)',
                                        600: 'var(--vscode-foreground)',
                                        700: 'var(--vscode-foreground)',
                                        800: 'var(--vscode-foreground)',
                                        900: 'var(--vscode-foreground)',
                                        950: 'var(--vscode-editor-background)',
                                    }
                                }
                            }
                        }
                    }
                </script>
                <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" rel="stylesheet" />
                <style>
                    ::-webkit-scrollbar { width: 6px; height: 6px; }
                    ::-webkit-scrollbar-track { background: transparent; }
                    ::-webkit-scrollbar-thumb { background: var(--vscode-scrollbarSlider-background); border-radius: 3px; }
                    ::-webkit-scrollbar-thumb:hover { background: var(--vscode-scrollbarSlider-hoverBackground); }
                    .bit-cell { transition: all 0.2s ease; }
                    .bit-cell:hover { transform: translateY(-2px); box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); z-index: 10; }
                    .highlight-row { background-color: var(--vscode-list-hoverBackground); border-left-color: var(--vscode-focusBorder); }
                    .highlight-bit { opacity: 1 !important; transform: scale(1.05); z-index: 20; box-shadow: 0 0 0 2px var(--vscode-focusBorder); }
                    .dim-bit { opacity: 0.4; }
                </style>
                <title>Memory Map Editor</title>
            </head>
            <body class="bg-gray-50 text-gray-900 font-sans h-screen flex flex-col overflow-hidden">
                <div id="root"></div>
                <script src="${scriptUri}"></script>
            </body>
            </html>
        `;
    }

    private updateTextDocument(document: vscode.TextDocument, text: string) {
        const edit = new vscode.WorkspaceEdit();
        const lastLine = document.lineAt(Math.max(0, document.lineCount - 1));
        edit.replace(
            document.uri,
            new vscode.Range(0, 0, lastLine.lineNumber, lastLine.text.length),
            text
        );
        return vscode.workspace.applyEdit(edit);
    }
}
