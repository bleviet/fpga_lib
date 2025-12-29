/**
 * VHDL Code Generator Service
 * 
 * TypeScript implementation using Nunjucks templates.
 * Mirrors the Python VHDLGenerator for zero-dependency VS Code extension.
 */

import * as nunjucks from 'nunjucks';
import * as path from 'path';
import * as vscode from 'vscode';
import {
    TemplateContext,
    Register,
    RegisterField,
    Generic,
    UserPort,
    GeneratedFiles,
    BusType
} from './types';

// Import IP Core data type from webview types
import { IpCore, BitField, Parameter, Port } from '../webview/types/ipCore';

/**
 * Generation options for the generator
 */
export interface GenerationOptions {
    includeVhdl?: boolean;
    includeRegfile?: boolean;
    vendorFiles?: 'none' | 'intel' | 'xilinx' | 'both';
    includeTestbench?: boolean;
}

export class VHDLGenerator {
    private env: nunjucks.Environment;
    private readonly SUPPORTED_BUS_TYPES: BusType[] = ['axil', 'avmm'];

    constructor(extensionPath?: string) {
        // Templates are copied to dist/templates by webpack
        // __dirname in bundled code points to dist/
        let templatesPath: string;

        if (extensionPath) {
            // When called from extension with extensionPath, use dist/templates
            templatesPath = path.join(extensionPath, 'dist', 'templates');
        } else {
            // Fallback: relative to bundled file (__dirname = dist/)
            templatesPath = path.join(__dirname, 'templates');
        }

        this.env = nunjucks.configure(templatesPath, {
            autoescape: false,
            trimBlocks: false,
            lstripBlocks: false,
        });

        // Add format filter for hex strings (used in templates)
        this.env.addFilter('format', (str: string, ...args: any[]) => {
            let i = 0;
            return str.replace(/%([0-9]*)([A-Za-z])/g, (match, width, type) => {
                const val = args[i++];
                if (val === undefined) return match;

                if (type === 'X' || type === 'x') {
                    const numVal = typeof val === 'number' ? val : 0;
                    const hex = Math.abs(Math.floor(numVal)).toString(16);
                    const formatted = type === 'X' ? hex.toUpperCase() : hex;
                    const pad = width ? parseInt(width) : 0;
                    return formatted.padStart(pad, '0');
                }
                return String(val);
            });
        });
    }

    /**
     * Parse bit string [M:N]
     */
    private parseBits(bits: string): { offset: number; width: number } {
        if (!bits) return { offset: 0, width: 1 };
        // Handle [M:N]
        const matchRange = bits.match(/\[(\d+):(\d+)\]/);
        if (matchRange) {
            const high = parseInt(matchRange[1], 10);
            const low = parseInt(matchRange[2], 10);
            return { offset: low, width: Math.abs(high - low) + 1 };
        }
        // Handle [N]
        const matchSingle = bits.match(/\[(\d+)\]/);
        if (matchSingle) {
            const bit = parseInt(matchSingle[1], 10);
            return { offset: bit, width: 1 };
        }
        return { offset: 0, width: 1 };
    }

    /**
     * Extract registers from IP core memory maps (recursively)
     */
    private prepareRegisters(ipCore: IpCore): Register[] {
        const registers: Register[] = [];

        // Recursive helper to flatten register hierarchy
        const processRegister = (reg: any, baseOffset: number, prefix: string) => {
            const currentOffset = baseOffset + (reg.addressOffset || reg.offset || 0);
            const regName = reg.name || 'REG';

            // Check if this is a register group/array (has nested registers)
            if (reg.registers && Array.isArray(reg.registers) && reg.registers.length > 0) {
                const count = reg.count || 1;
                const stride = reg.stride || 0;

                for (let i = 0; i < count; i++) {
                    const instanceOffset = currentOffset + (i * stride);
                    // Use index suffix only if it's an array (count > 1) or to distinguish?
                    // Usually if count > 1 we need index. If count=1, maybe not?
                    // User might name group "TIMERS" count=4.
                    // Children: "CTRL".
                    // Result: TIMERS_0_CTRL.
                    const instancePrefix = count > 1 ? `${prefix}${regName}_${i}_` : `${prefix}${regName}_`;

                    for (const child of reg.registers) {
                        processRegister(child, instanceOffset, instancePrefix);
                    }
                }
                return;
            }

            // It is a leaf register
            const fields: RegisterField[] = (reg.fields || []).map((field: any) => {
                let offset = field.bitOffset || field.bit_offset;
                let width = field.bitWidth || field.bit_width;

                if (offset === undefined || width === undefined) {
                    const parsed = this.parseBits(field.bits);
                    offset = offset ?? parsed.offset;
                    width = width ?? parsed.width;
                }

                // Get access and normalize to lowercase
                const regAccess = typeof reg.access === 'string' ? reg.access.toLowerCase() : 'read-write';
                const fieldAccess = typeof field.access === 'string' ? field.access.toLowerCase() : regAccess;

                return {
                    name: field.name,
                    offset: offset || 0,
                    width: width || 1,
                    access: fieldAccess,
                    reset_value: field.resetValue || field.reset_value || 0,
                    description: field.description || '',
                };
            });

            // Add flat register
            const regAccess = typeof reg.access === 'string' ? reg.access.toLowerCase() : 'read-write';
            registers.push({
                name: prefix + regName,
                offset: currentOffset,
                access: regAccess,
                description: reg.description || '',
                fields,
            });
        };

        for (const mm of ipCore.memory_maps || []) {
            for (const block of mm.address_blocks || []) {
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                const b = block as any;
                const blockOffset = b.base_address || b.baseAddress || b.offset || 0;
                for (const reg of block.registers || []) {
                    processRegister(reg, blockOffset, "");
                }
            }
        }

        return registers.sort((a, b) => a.offset - b.offset);
    }

    /**
     * Extract generics/parameters from IP core
     */
    private prepareGenerics(ipCore: IpCore): Generic[] {
        return (ipCore.parameters || []).map((param: Parameter) => ({
            name: param.name,
            type: param.data_type || 'integer',
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            default_value: (param.value as any) ?? null,
        }));
    }

    /**
     * Extract user ports from IP core
     */
    private prepareUserPorts(ipCore: IpCore): UserPort[] {
        return (ipCore.ports || []).map((port: Port) => {
            const width = port.width || 1;
            const portType = width === 1
                ? 'std_logic'
                : `std_logic_vector(${width - 1} downto 0)`;

            return {
                name: port.name.toLowerCase(),
                direction: (port.direction || 'in').toLowerCase(),
                type: portType,
            };
        });
    }

    /**
     * Build template context from IP core data
     */
    private getTemplateContext(ipCore: IpCore, busType: BusType = 'axil'): TemplateContext {
        const registers = this.prepareRegisters(ipCore);
        const sw_access = ['read-write', 'write-only', 'rw', 'wo'];
        const hw_access = ['read-only', 'ro'];

        // Split registers for record generation
        const sw_registers = registers.filter(r => sw_access.includes(r.access));
        const hw_registers = registers.filter(r => hw_access.includes(r.access));

        return {
            entity_name: ipCore.vlnv.name.toLowerCase(),
            registers,
            sw_registers, // New pre-filtered lists
            hw_registers,
            generics: this.prepareGenerics(ipCore),
            user_ports: this.prepareUserPorts(ipCore),
            bus_type: busType,
            data_width: 32,
            addr_width: 8,
            reg_width: 4,
        } as any; // Cast to any to avoid strict TemplateContext check if interface not updated yet
    }

    /**
     * Generate VHDL package with register types
     */
    generatePackage(ipCore: IpCore): string {
        const context = this.getTemplateContext(ipCore);
        return this.env.render('package.vhdl.j2', context);
    }

    /**
     * Generate top-level entity
     */
    generateTop(ipCore: IpCore, busType: BusType = 'axil'): string {
        if (!this.SUPPORTED_BUS_TYPES.includes(busType)) {
            throw new Error(`Unsupported bus type: ${busType}`);
        }
        const context = this.getTemplateContext(ipCore, busType);
        return this.env.render('top.vhdl.j2', context);
    }

    /**
     * Generate core logic module
     */
    generateCore(ipCore: IpCore): string {
        const context = this.getTemplateContext(ipCore);
        return this.env.render('core.vhdl.j2', context);
    }

    /**
     * Generate bus wrapper
     */
    generateBusWrapper(ipCore: IpCore, busType: BusType): string {
        if (!this.SUPPORTED_BUS_TYPES.includes(busType)) {
            throw new Error(`Unsupported bus type: ${busType}`);
        }
        const context = this.getTemplateContext(ipCore, busType);
        return this.env.render(`bus_${busType}.vhdl.j2`, context);
    }

    /**
     * Generate register file
     */
    generateRegisterFile(ipCore: IpCore): string {
        const context = this.getTemplateContext(ipCore);
        return this.env.render('register_file.vhdl.j2', context);
    }

    /**
     * Generate Intel Platform Designer _hw.tcl
     */
    generateIntelHwTcl(ipCore: IpCore): string {
        const context = this.getTemplateContext(ipCore, 'avmm');
        return this.env.render('intel_hw_tcl.j2', context);
    }

    /**
     * Generate Xilinx Vivado component.xml
     */
    generateXilinxComponentXml(ipCore: IpCore): string {
        const context = this.getTemplateContext(ipCore, 'axil');
        return this.env.render('xilinx_component_xml.j2', context);
    }

    /**
     * Generate cocotb test file
     */
    generateCocotbTest(ipCore: IpCore, busType: BusType = 'axil'): string {
        const context = this.getTemplateContext(ipCore, busType);
        return this.env.render('cocotb_test.py.j2', context);
    }

    /**
     * Generate cocotb Makefile
     */
    generateCocotbMakefile(ipCore: IpCore, busType: BusType = 'axil'): string {
        const context = this.getTemplateContext(ipCore, busType);
        return this.env.render('cocotb_makefile.j2', context);
    }

    /**
     * Generate all files for an IP core based on options
     */
    generateAll(
        ipCore: IpCore,
        busType: BusType = 'axil',
        options: GenerationOptions = {}
    ): GeneratedFiles {
        const name = ipCore.vlnv.name.toLowerCase();
        const files: GeneratedFiles = new Map();

        // Default options
        const opts = {
            includeVhdl: options.includeVhdl !== false, // true by default
            includeRegfile: options.includeRegfile || false,
            vendorFiles: options.vendorFiles || 'none',
            includeTestbench: options.includeTestbench || false,
        };

        // Core VHDL files
        if (opts.includeVhdl) {
            files.set(`${name}_pkg.vhd`, this.generatePackage(ipCore));
            files.set(`${name}.vhd`, this.generateTop(ipCore, busType));
            files.set(`${name}_core.vhd`, this.generateCore(ipCore));
            files.set(`${name}_${busType}.vhd`, this.generateBusWrapper(ipCore, busType));
        }

        // Standalone register file
        if (opts.includeRegfile) {
            files.set(`${name}_regfile.vhd`, this.generateRegisterFile(ipCore));
        }

        // Vendor integration files
        if (opts.vendorFiles === 'intel' || opts.vendorFiles === 'both') {
            files.set(`${name}_hw.tcl`, this.generateIntelHwTcl(ipCore));
        }
        if (opts.vendorFiles === 'xilinx' || opts.vendorFiles === 'both') {
            files.set('component.xml', this.generateXilinxComponentXml(ipCore));
        }

        // Testbench files
        if (opts.includeTestbench) {
            files.set(`${name}_test.py`, this.generateCocotbTest(ipCore, busType));
            files.set('Makefile', this.generateCocotbMakefile(ipCore, busType));
        }

        return files;
    }

    /**
     * Write generated files to output directory
     */
    async writeFiles(
        ipCore: IpCore,
        outputDir: vscode.Uri,
        busType: BusType = 'axil'
    ): Promise<Map<string, vscode.Uri>> {
        const files = this.generateAll(ipCore, busType);
        const written = new Map<string, vscode.Uri>();

        // Create output directory if needed
        try {
            await vscode.workspace.fs.createDirectory(outputDir);
        } catch {
            // Directory may already exist
        }

        for (const [filename, content] of files) {
            const fileUri = vscode.Uri.joinPath(outputDir, filename);
            const encoder = new TextEncoder();
            await vscode.workspace.fs.writeFile(fileUri, encoder.encode(content));
            written.set(filename, fileUri);
        }

        return written;
    }
}

// Singleton instance
let generatorInstance: VHDLGenerator | null = null;

/**
 * Get or create the VHDL generator instance
 */
export function getVHDLGenerator(templateDir?: string): VHDLGenerator {
    if (!generatorInstance) {
        generatorInstance = new VHDLGenerator(templateDir);
    }
    return generatorInstance;
}
