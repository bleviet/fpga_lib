"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.vscode = void 0;
// Minimal VS Code API wrapper for the webview.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
exports.vscode = globalThis.acquireVsCodeApi ? globalThis.acquireVsCodeApi() : undefined;
//# sourceMappingURL=vscode.js.map