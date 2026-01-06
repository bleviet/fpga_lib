/**
 * Python backend integration for VHDL generation.
 *
 * Calls the Python ipcore.py script with --json and --progress flags
 * to integrate with VS Code's progress notifications and output panel.
 */

import * as vscode from 'vscode';
import * as cp from 'child_process';
import * as path from 'path';

export interface GenerateResult {
    success: boolean;
    files?: Record<string, string>;
    count?: number;
    busType?: string;
    error?: string;
}

export interface GenerateOptions {
    vendor?: 'none' | 'intel' | 'xilinx' | 'both';
    includeTestbench?: boolean;
    includeRegs?: boolean;
    updateYaml?: boolean;
}

export class PythonBackend {
    private pythonPath: string;
    private projectRoot: string;
    private outputChannel: vscode.OutputChannel;

    constructor() {
        this.pythonPath = this.findPython();
        this.projectRoot = this.findProjectRoot();
        this.outputChannel = vscode.window.createOutputChannel('FPGA Generator');
    }

    private findPython(): string {
        // Check VS Code Python extension setting first
        const pythonConfig = vscode.workspace.getConfiguration('python');
        const configuredPath = pythonConfig.get<string>('defaultInterpreterPath');
        if (configuredPath) {
            return configuredPath;
        }
        // Default to python3 on Unix, python on Windows
        return process.platform === 'win32' ? 'python' : 'python3';
    }

    /**
     * Find the fpga_lib project root by looking for fpga_lib/ directory
     */
    private findProjectRoot(): string {
        const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || '';

        // Try to find fpga_lib directory by walking up from workspace root
        let current = workspaceRoot;
        for (let i = 0; i < 5; i++) {
            const fpgaLibDir = path.join(current, 'fpga_lib');
            const scriptsDir = path.join(current, 'scripts');
            try {
                // Check if both fpga_lib and scripts directories exist
                const fs = require('fs');
                if (fs.existsSync(fpgaLibDir) && fs.existsSync(scriptsDir)) {
                    return current;
                }
            } catch {
                // Ignore
            }
            const parent = path.dirname(current);
            if (parent === current) break;
            current = parent;
        }

        // Fallback to workspace root
        return workspaceRoot;
    }

    /**
     * Check if Python backend is available
     */
    async isAvailable(): Promise<boolean> {
        try {
            this.outputChannel.appendLine(`[DEBUG] Python: ${this.pythonPath}`);
            this.outputChannel.appendLine(`[DEBUG] Project root: ${this.projectRoot}`);

            const result = await this.runPython(['-c', 'import fpga_lib; print("ok")']);
            const available = result.stdout.includes('ok');

            if (!available) {
                this.outputChannel.appendLine(`[DEBUG] fpga_lib import failed. stdout: ${result.stdout}, stderr: ${result.stderr}`);
            }

            return available;
        } catch (error) {
            this.outputChannel.appendLine(`[DEBUG] isAvailable error: ${error}`);
            return false;
        }
    }

    /**
     * Generate VHDL using Python backend with progress streaming
     */
    async generateVHDL(
        inputPath: string,
        outputDir: string,
        options: GenerateOptions = {},
        progress?: vscode.Progress<{ message?: string; increment?: number }>
    ): Promise<GenerateResult> {
        // Call ipcore.py with generate subcommand
        const scriptPath = path.join(this.projectRoot, 'scripts', 'ipcore.py');
        const args = [
            scriptPath,
            'generate',
            inputPath,
            '--output', outputDir,
            '--vendor', options.vendor || 'both',
            '--json',
            '--progress',
        ];

        if (options.includeTestbench === false) {
            args.push('--no-testbench');
        }
        if (options.includeRegs === false) {
            args.push('--no-regs');
        }
        if (options.updateYaml === false) {
            args.push('--no-update-yaml');
        }

        const timestamp = new Date().toISOString();
        this.outputChannel.appendLine(`[${timestamp}] Running: ${this.pythonPath} ${args.join(' ')}`);
        this.outputChannel.show(true);

        try {
            const result = await this.runPythonWithProgress(args, progress);

            if (result.stderr) {
                this.outputChannel.appendLine('--- STDERR ---');
                this.outputChannel.appendLine(result.stderr);
            }

            const parsed = JSON.parse(result.stdout);
            this.outputChannel.appendLine(`✓ Generated ${parsed.count} files (bus: ${parsed.busType})`);
            return parsed;
        } catch (error) {
            this.outputChannel.appendLine(`✗ Error: ${error}`);
            return {
                success: false,
                error: `Python backend error: ${error}`
            };
        }
    }

    private runPython(args: string[]): Promise<{ stdout: string; stderr: string }> {
        return new Promise((resolve, reject) => {
            const proc = cp.spawn(this.pythonPath, args, {
                cwd: this.projectRoot,
                env: { ...process.env, PYTHONPATH: this.projectRoot }
            });

            let stdout = '';
            let stderr = '';

            proc.stdout.on('data', (data) => { stdout += data; });
            proc.stderr.on('data', (data) => { stderr += data; });

            proc.on('close', (code) => {
                if (code === 0) {
                    resolve({ stdout, stderr });
                } else {
                    reject(new Error(stderr || `Exit code ${code}`));
                }
            });

            proc.on('error', reject);
        });
    }

    /**
     * Run Python with progress streaming
     */
    private runPythonWithProgress(
        args: string[],
        progress?: vscode.Progress<{ message?: string; increment?: number }>
    ): Promise<{ stdout: string; stderr: string }> {
        return new Promise((resolve, reject) => {
            const proc = cp.spawn(this.pythonPath, args, {
                cwd: this.projectRoot,
                env: { ...process.env, PYTHONPATH: this.projectRoot }
            });

            let stdout = '';
            let stderr = '';

            proc.stdout.on('data', (data) => {
                const text = data.toString();
                stdout += text;

                // Parse progress lines (format: "PROGRESS: message")
                const lines = text.split('\n');
                for (const line of lines) {
                    if (line.startsWith('PROGRESS:')) {
                        const message = line.replace('PROGRESS:', '').trim();
                        progress?.report({ message, increment: 10 });
                        this.outputChannel.appendLine(`  ${message}`);
                    }
                }
            });

            proc.stderr.on('data', (data) => {
                stderr += data;
                this.outputChannel.appendLine(data.toString());
            });

            proc.on('close', (code) => {
                // Extract JSON from stdout (last line after PROGRESS lines)
                const jsonMatch = stdout.match(/\{[\s\S]*\}$/);
                const jsonOutput = jsonMatch ? jsonMatch[0] : stdout;

                if (code === 0) {
                    resolve({ stdout: jsonOutput, stderr });
                } else {
                    reject(new Error(stderr || `Exit code ${code}`));
                }
            });

            proc.on('error', reject);
        });
    }

    /**
     * Dispose resources
     */
    dispose(): void {
        this.outputChannel.dispose();
    }
}
