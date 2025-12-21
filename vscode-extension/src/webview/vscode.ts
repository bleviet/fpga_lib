// Minimal VS Code API wrapper for the webview.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const vscode = (globalThis as any).acquireVsCodeApi ? (globalThis as any).acquireVsCodeApi() : undefined;
