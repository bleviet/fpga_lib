import React, { useEffect, useMemo, useRef, useState } from 'react';
import type { ReactNode, ErrorInfo } from 'react';
import { createRoot } from 'react-dom/client';
import jsyaml from 'js-yaml';
import { MemoryMap } from './types/memoryMap';
import Outline from './components/Outline';
import DetailsPanel from './components/DetailsPanel';
import { vscode } from './vscode';
import './index.css';

type YamlPath = Array<string | number>;

type Selection = {
    id: string;
    type: 'memoryMap' | 'block' | 'register' | 'array';
    object: any;
    breadcrumbs: string[];
    path: YamlPath;
};

type NormalizedRegister = {
    name: string;
    address_offset: number;
    size?: number;
    access?: string;
    reset_value?: number;
    description?: string;
    fields?: any[];
};

type NormalizedRegisterArray = {
    __kind: 'array';
    name: string;
    address_offset: number;
    count: number;
    stride: number;
    description?: string;
    registers: NormalizedRegister[];
};

const App = () => {
    const [memoryMap, setMemoryMap] = useState<MemoryMap | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [rawText, setRawText] = useState<string>('');
    const [fileName, setFileName] = useState<string>('');
    const [selectedId, setSelectedId] = useState<string | null>(null);
    const [selectedType, setSelectedType] = useState<'memoryMap' | 'block' | 'register' | 'array' | null>(null);
    const [selectedObject, setSelectedObject] = useState<any>(null);
    const [breadcrumbs, setBreadcrumbs] = useState<string[]>([]);
    const [activeTab, setActiveTab] = useState<'properties' | 'yaml'>('properties');

    const didInitSelectionRef = useRef(false);
    const selectionRef = useRef<Selection | null>(null);
    const rawTextRef = useRef<string>('');

    useEffect(() => {
        const handleMessage = (event: MessageEvent) => {
            const message = event.data;
            if (message.type === 'update') {
                try {
                    const nextRawText = String(message.text ?? '');
                    setRawText(nextRawText);
                    rawTextRef.current = nextRawText;
                    setFileName(String(message.fileName ?? ''));
                    const data = jsyaml.load(message.text) as any;

                    // Normalize the data structure
                    let map: any;
                    if (Array.isArray(data)) {
                        map = data[0];
                    } else if (data.memory_maps) {
                        map = data.memory_maps[0];
                    } else {
                        map = data;
                    }

                    // Normalize camelCase to snake_case for consistency with types
                    const normalized = normalizeMemoryMap(map);
                    setMemoryMap(normalized);
                    setError(null);

                    const resolveFromSelection = (sel: Selection | null): { type: Selection['type']; object: any; breadcrumbs: string[] } | null => {
                        if (!sel) return null;
                        if (sel.type === 'memoryMap') {
                            return { type: 'memoryMap', object: normalized, breadcrumbs: [normalized.name || 'Memory Map'] };
                        }

                        // Selection paths are YAML-style: ['addressBlocks', blockIndex, ...]
                        const blockIndex = typeof sel.path[1] === 'number' ? (sel.path[1] as number) : null;
                        if (blockIndex === null) return null;
                        const block = normalized.address_blocks?.[blockIndex];
                        if (!block) return null;

                        if (sel.type === 'block') {
                            return { type: 'block', object: block, breadcrumbs: [normalized.name || 'Memory Map', block.name] };
                        }

                        const blockRegs = ((block as any).registers ?? []) as Array<NormalizedRegister | NormalizedRegisterArray>;

                        if (sel.type === 'array') {
                            const regIndex = typeof sel.path[3] === 'number' ? (sel.path[3] as number) : null;
                            if (regIndex === null) return null;
                            const node = blockRegs[regIndex];
                            if (node && (node as any).__kind === 'array') {
                                const arr = node as NormalizedRegisterArray;
                                return { type: 'array', object: arr, breadcrumbs: [normalized.name || 'Memory Map', block.name, arr.name] };
                            }
                            return null;
                        }

                        if (sel.type === 'register') {
                            // Direct register: ['addressBlocks', b, 'registers', r]
                            // Nested register inside array: ['addressBlocks', b, 'registers', r, 'registers', rr]
                            if (sel.path.length === 4) {
                                const regIndex = typeof sel.path[3] === 'number' ? (sel.path[3] as number) : null;
                                if (regIndex === null) return null;
                                const node = blockRegs[regIndex];
                                if (!node || (node as any).__kind === 'array') return null;
                                const reg = node as NormalizedRegister;
                                return { type: 'register', object: reg, breadcrumbs: [normalized.name || 'Memory Map', block.name, reg.name] };
                            }

                            if (sel.path.length === 6) {
                                const arrIndex = typeof sel.path[3] === 'number' ? (sel.path[3] as number) : null;
                                const nestedIndex = typeof sel.path[5] === 'number' ? (sel.path[5] as number) : null;
                                if (arrIndex === null || nestedIndex === null) return null;
                                const node = blockRegs[arrIndex];
                                if (!node || (node as any).__kind !== 'array') return null;
                                const arr = node as NormalizedRegisterArray;
                                const reg = arr.registers?.[nestedIndex];
                                if (!reg) return null;
                                return { type: 'register', object: reg, breadcrumbs: [normalized.name || 'Memory Map', block.name, arr.name, reg.name] };
                            }

                            return null;
                        }

                        return null;
                    };

                    // Auto-select root on first load
                    if (!didInitSelectionRef.current) {
                        setSelectedId('root');
                        setSelectedType('memoryMap');
                        setSelectedObject(normalized);
                        setBreadcrumbs([normalized.name || 'Memory Map']);
                        selectionRef.current = {
                            id: 'root',
                            type: 'memoryMap',
                            object: normalized,
                            breadcrumbs: [normalized.name || 'Memory Map'],
                            path: [],
                        };
                        didInitSelectionRef.current = true;
                    } else {
                        const resolved = resolveFromSelection(selectionRef.current);
                        if (resolved) {
                            setSelectedId(selectionRef.current?.id ?? null);
                            setSelectedType(resolved.type);
                            setSelectedObject(resolved.object);
                            setBreadcrumbs(resolved.breadcrumbs);
                        }
                    }
                } catch (e: any) {
                    setError(e.message);
                }
            }
        };

        window.addEventListener('message', handleMessage);
        return () => window.removeEventListener('message', handleMessage);
    }, []);

    const parseNumber = (value: any, fallback = 0): number => {
        if (typeof value === 'number' && Number.isFinite(value)) return value;
        if (typeof value === 'string') {
            const s = value.trim();
            if (!s) return fallback;
            const n = Number.parseInt(s, 0);
            return Number.isFinite(n) ? n : fallback;
        }
        return fallback;
    };

    const getDefaultRegBytes = (block: any): number => {
        const bits = parseNumber(block.defaultRegWidth ?? block.default_reg_width ?? 32, 32);
        const bytes = Math.max(1, Math.floor(bits / 8));
        return bytes;
    };

    const normalizeRegisterList = (regs: any[], defaultRegBytes: number): Array<NormalizedRegister | NormalizedRegisterArray> => {
        const out: Array<NormalizedRegister | NormalizedRegisterArray> = [];
        let currentOffset = 0;

        for (const entry of regs ?? []) {
            const explicitOffset = entry.offset ?? entry.address_offset ?? entry.addressOffset;
            if (explicitOffset !== undefined) {
                currentOffset = parseNumber(explicitOffset, currentOffset);
            }

            const isArray = entry && typeof entry === 'object' && entry.count !== undefined && entry.stride !== undefined && Array.isArray(entry.registers);
            if (isArray) {
                const arrayOffset = currentOffset;
                const count = Math.max(1, parseNumber(entry.count, 1));
                const stride = Math.max(1, parseNumber(entry.stride, defaultRegBytes));
                const nested = normalizeRegisterList(entry.registers, defaultRegBytes) as NormalizedRegister[];
                out.push({
                    __kind: 'array',
                    name: entry.name,
                    address_offset: arrayOffset,
                    count,
                    stride,
                    description: entry.description,
                    registers: nested.filter((n) => (n as any).__kind !== 'array') as NormalizedRegister[],
                });
                currentOffset = arrayOffset + count * stride;
                continue;
            }

            const regOffset = currentOffset;
            const normalizedReg: NormalizedRegister = {
                name: entry.name,
                address_offset: regOffset,
                size: parseNumber(entry.size, 32),
                access: entry.access,
                reset_value: entry.reset_value,
                description: entry.description,
                fields: entry.fields?.map((field: any) => normalizeField(field)),
            };
            out.push(normalizedReg);
            currentOffset = regOffset + defaultRegBytes;
        }

        return out;
    };

    const normalizeMemoryMap = (data: any): MemoryMap => {
        const blocks = data.addressBlocks ?? data.address_blocks ?? [];
        return {
            name: data.name,
            description: data.description,
            address_blocks: (blocks ?? []).map((block: any) => {
                const defaultRegBytes = getDefaultRegBytes(block);
                const baseAddress = parseNumber(block.offset ?? block.base_address ?? block.baseAddress ?? 0, 0);

                const normalizedRegs = normalizeRegisterList(block.registers ?? [], defaultRegBytes);

                return {
                    name: block.name,
                    base_address: baseAddress,
                    range: block.range || '4K',
                    usage: block.usage || 'register',
                    access: block.access,
                    description: block.description,
                    // NOTE: this intentionally holds both registers and arrays; treated as "any" in consumers.
                    registers: normalizedRegs as any,
                    register_arrays: (block.register_arrays ?? []).map((arr: any) => ({
                        name: arr.name,
                        base_address: parseNumber(arr.base_address, 0),
                        count: parseNumber(arr.count, 1),
                        stride: parseNumber(arr.stride, defaultRegBytes),
                        template: normalizeRegister(arr.template || {}),
                        description: arr.description
                    }))
                };
            })
        };
    };

    const normalizeRegister = (reg: any): any => {
        return {
            name: reg.name,
            address_offset: reg.offset || reg.address_offset || 0,
            size: reg.size || 32,
            access: reg.access,
            reset_value: reg.reset_value,
            description: reg.description,
            fields: reg.fields?.map((field: any) => normalizeField(field))
        };
    };

    const normalizeField = (field: any): any => {
        // Parse bits field if it's a string like "[31:0]" or "[0:0]"
        let bit_offset = field.bit_offset || 0;
        let bit_width = field.bit_width || 1;

        if (field.bits && typeof field.bits === 'string') {
            const match = field.bits.match(/\[(\d+)(?::(\d+))?\]/);
            if (match) {
                const high = parseInt(match[1], 10);
                const low = match[2] ? parseInt(match[2], 10) : high;
                bit_offset = Math.min(low, high);
                bit_width = Math.abs(high - low) + 1;
            }
        }

        // Ensure numeric values are valid
        bit_offset = Number.isFinite(Number(bit_offset)) ? Number(bit_offset) : 0;
        bit_width = Number.isFinite(Number(bit_width)) && Number(bit_width) > 0 ? Number(bit_width) : 1;

        return {
            name: field.name,
            bit_offset,
            bit_width,
            access: field.access,
            reset_value: field.reset_value ?? field.resetValue ?? field.reset,
            description: field.description,
            enumerated_values: field.enumerated_values
        };
    };

    const handleSelect = (selection: Selection) => {
        selectionRef.current = selection;
        setSelectedId(selection.id);
        setSelectedType(selection.type);
        setSelectedObject(selection.object);
        setBreadcrumbs(selection.breadcrumbs);
    };

    const setAtPath = (root: any, path: YamlPath, value: any) => {
        if (!path.length) {
            throw new Error('Cannot set empty path');
        }
        let cursor = root;
        for (let i = 0; i < path.length - 1; i++) {
            const key = path[i];
            if (cursor == null) throw new Error(`Path not found at ${String(key)}`);
            cursor = cursor[key as any];
        }
        const last = path[path.length - 1];
        if (cursor == null) throw new Error(`Path not found at ${String(last)}`);
        cursor[last as any] = value;
    };

    const getAtPath = (root: any, path: YamlPath) => {
        let cursor = root;
        for (const key of path) {
            if (cursor == null) return undefined;
            cursor = cursor[key as any];
        }
        return cursor;
    };

    const deleteAtPath = (root: any, path: YamlPath) => {
        if (!path.length) return;
        let cursor = root;
        for (let i = 0; i < path.length - 1; i++) {
            const key = path[i];
            if (cursor == null) return;
            cursor = cursor[key as any];
        }
        const last = path[path.length - 1];
        if (cursor == null) return;
        if (Array.isArray(cursor) && typeof last === 'number') {
            cursor.splice(last, 1);
            return;
        }
        delete cursor[last as any];
    };

    const getMapRootInfo = (data: any): { root: any; mapPrefix: YamlPath; map: any } => {
        if (Array.isArray(data)) {
            return { root: data, mapPrefix: [0], map: data[0] };
        }
        if (data && typeof data === 'object' && Array.isArray(data.memory_maps)) {
            return { root: data, mapPrefix: ['memory_maps', 0], map: data.memory_maps[0] };
        }
        return { root: data, mapPrefix: [], map: data };
    };

    const dumpYaml = (data: any): string => {
        // NOTE: js-yaml will not preserve comments/formatting.
        return jsyaml.dump(data, { noRefs: true, sortKeys: false, lineWidth: -1 });
    };

    const handleUpdate = (path: YamlPath, value: any) => {
        const sel = selectionRef.current;
        if (!sel) return;

        const currentText = rawTextRef.current;
        let rootObj: any;
        try {
            rootObj = jsyaml.load(currentText) as any;
        } catch (err) {
            console.warn('Cannot apply update: YAML parse failed', err);
            return;
        }

        const { root, mapPrefix } = getMapRootInfo(rootObj);

        const parseBitsLike = (text: string): { bit_offset: number; bit_width: number } | null => {
            const trimmed = String(text ?? '').trim().replace(/\[|\]/g, '');
            if (!trimmed) return null;
            const parts = trimmed.split(':').map((p) => Number(String(p).trim()));
            if (parts.some((p) => Number.isNaN(p))) return null;
            let msb: number;
            let lsb: number;
            if (parts.length === 1) {
                msb = parts[0];
                lsb = parts[0];
            } else {
                msb = parts[0];
                lsb = parts[1];
            }
            if (!Number.isFinite(msb) || !Number.isFinite(lsb)) return null;
            if (msb < lsb) [msb, lsb] = [lsb, msb];
            return { bit_offset: lsb, bit_width: msb - lsb + 1 };
        };

        const formatBitsLike = (bit_offset: number, bit_width: number): string => {
            const lsb = Number(bit_offset);
            const width = Math.max(1, Number(bit_width));
            const msb = lsb + width - 1;
            return `[${msb}:${lsb}]`;
        };

        // Field operations (add/delete/move)
        if (path[0] === '__op' && sel.type === 'register') {
            const op = String(path[1] ?? '');
            const payload = value ?? {};
            const registerYamlPath: YamlPath = [...mapPrefix, ...sel.path];
            const fieldsPath: YamlPath = [...registerYamlPath, 'fields'];
            const current = getAtPath(root, fieldsPath);
            if (!Array.isArray(current)) {
                setAtPath(root, fieldsPath, []);
            }
            const fieldsArr = (getAtPath(root, fieldsPath) ?? []) as any[];
            if (!Array.isArray(fieldsArr)) return;

            if (op === 'field-add') {
                const afterIndex = typeof payload.afterIndex === 'number' ? payload.afterIndex : -1;
                const insertIndex = Math.max(0, Math.min(fieldsArr.length, afterIndex + 1));

                // Pick a free 1-bit slot in [0..31] as a starting point.
                const currentFields = (sel.object?.fields ?? []) as any[];
                const used = new Set<number>();
                for (const f of currentFields) {
                    const o = Number(f?.bit_offset ?? 0);
                    const w = Number(f?.bit_width ?? 1);
                    for (let b = o; b < o + w; b++) used.add(b);
                }
                let lsb = 0;
                while (used.has(lsb) && lsb < 32) lsb++;
                const bits = `[${lsb}:${lsb}]`;

                fieldsArr.splice(insertIndex, 0, {
                    name: payload.name ?? 'NEW_FIELD',
                    bits,
                    access: payload.access ?? 'read-write',
                    description: payload.description ?? '',
                });
            }

            if (op === 'field-delete') {
                const index = typeof payload.index === 'number' ? payload.index : -1;
                if (index >= 0 && index < fieldsArr.length) {
                    fieldsArr.splice(index, 1);
                }
            }

            if (op === 'field-move') {
                const index = typeof payload.index === 'number' ? payload.index : -1;
                const delta = typeof payload.delta === 'number' ? payload.delta : 0;
                const next = index + delta;
                if (index >= 0 && next >= 0 && index < fieldsArr.length && next < fieldsArr.length) {
                    const tmp = fieldsArr[index];
                    fieldsArr[index] = fieldsArr[next];
                    fieldsArr[next] = tmp;

                    // Re-pack bit offsets sequentially based on width (Python reference behavior).
                    let offset = 0;
                    for (const f of fieldsArr) {
                        let width = Number(f?.bit_width);
                        if (!Number.isFinite(width)) {
                            const parsed = parseBitsLike(f?.bits);
                            width = parsed?.bit_width ?? 1;
                        }
                        width = Math.max(1, Math.min(32, Math.trunc(width)));

                        f.bit_offset = offset;
                        f.bit_width = width;
                        // Keep legacy "bits" in sync if it exists.
                        if (typeof f?.bits === 'string') {
                            f.bits = formatBitsLike(offset, width);
                        }
                        offset += width;
                    }
                }
            }

            const newText = dumpYaml(root);
            rawTextRef.current = newText;
            setRawText(newText);
            vscode?.postMessage({ type: 'update', text: newText });
            return;
        }

        const field = path[0];
        if (!field || typeof field !== 'string') return;

        // Bit-field edits: ['fields', fieldIndex, key]
        if (field === 'fields' && typeof path[1] === 'number' && typeof path[2] === 'string') {
            const fieldIndex = path[1] as number;
            const fieldKey = path[2] as string;
            const registerYamlPath: YamlPath = [...mapPrefix, ...sel.path];

            const keyMap: Record<string, string> = {
                name: 'name',
                bits: 'bits',
                access: 'access',
                description: 'description',
                reset: 'reset',
                reset_value: 'reset',
            };
            const yamlKey = keyMap[fieldKey] ?? fieldKey;
            const fullPath: YamlPath = [...registerYamlPath, 'fields', fieldIndex, yamlKey];

            try {
                if (yamlKey === 'reset' && (value === '' || value === null || value === undefined)) {
                    deleteAtPath(root, fullPath);
                } else {
                    setAtPath(root, fullPath, value);
                }
            } catch (err) {
                console.warn('Failed to apply field update at path', fullPath, err);
                return;
            }

            const newText = dumpYaml(root);
            rawTextRef.current = newText;
            setRawText(newText);
            vscode?.postMessage({ type: 'update', text: newText });
            return;
        }

        const mapFieldToYamlKey = (): string => {
            // Root fields
            if (sel.type === 'memoryMap') {
                if (field === 'name') return 'name';
                if (field === 'description') return 'description';
            }
            if (sel.type === 'block') {
                if (field === 'name') return 'name';
                if (field === 'description') return 'description';
                // base address editing not implemented
            }
            if (sel.type === 'register') {
                if (field === 'name') return 'name';
                if (field === 'description') return 'description';
                if (field === 'access') return 'access';
                if (field === 'address_offset') return 'offset';
            }
            return field;
        };

        const yamlKey = mapFieldToYamlKey();
        const fullPath: YamlPath = [...mapPrefix, ...sel.path, yamlKey];

        try {
            setAtPath(root, fullPath, value);
        } catch (err) {
            console.warn('Failed to apply update at path', fullPath, err);
            return;
        }

        const newText = dumpYaml(root);
        rawTextRef.current = newText;
        setRawText(newText);
        vscode?.postMessage({ type: 'update', text: newText });
    };

    const headerTitle = useMemo(() => {
        if (fileName) return fileName;
        return 'Memory Map Editor';
    }, [fileName]);

    const sendCommand = (command: 'save' | 'validate') => {
        vscode?.postMessage({ type: 'command', command });
    };

    if (error) {
        return <div className="error-container">Error parsing YAML: {error}</div>;
    }

    if (!memoryMap) {
        return <div className="loading">Loading...</div>;
    }

    return (
        <>
            <header className="h-14 bg-white border-b border-gray-200 flex items-center justify-between px-4 shrink-0 z-20 shadow-sm">
                <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2 text-gray-700 font-semibold tracking-tight">
                        <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center text-white shadow-sm">
                            <span className="codicon codicon-chip text-[20px]"></span>
                        </div>
                        <span>RegEdit <span className="text-gray-400 font-normal">Pro</span></span>
                    </div>
                    <div className="h-6 w-px bg-gray-200 mx-2"></div>
                    <div className="flex items-center gap-2 text-sm text-gray-500">
                        <span className="hover:text-gray-800 cursor-pointer transition-colors">{headerTitle}</span>
                        {breadcrumbs.length > 1 && (
                            <>
                                <span className="codicon codicon-chevron-right text-[16px]"></span>
                                <span className="font-medium text-gray-900 bg-gray-100 px-2 py-0.5 rounded">{breadcrumbs[breadcrumbs.length - 1]}</span>
                            </>
                        )}
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <button
                        className="p-2 text-gray-500 hover:text-indigo-600 hover:bg-indigo-50 rounded-md transition-colors"
                        onClick={() => sendCommand('save')}
                        title="Save"
                    >
                        <span className="codicon codicon-save"></span>
                    </button>
                    <button
                        className="p-2 text-gray-500 hover:text-indigo-600 hover:bg-indigo-50 rounded-md transition-colors"
                        onClick={() => sendCommand('validate')}
                        title="Validate"
                    >
                        <span className="codicon codicon-check"></span>
                    </button>
                    <div className="h-6 w-px bg-gray-200 mx-1"></div>
                    <button className="p-2 text-gray-500 hover:text-indigo-600 hover:bg-indigo-50 rounded-md transition-colors" title="Export Header">
                        <span className="codicon codicon-code"></span>
                    </button>
                    <button className="p-2 text-gray-500 hover:text-indigo-600 hover:bg-indigo-50 rounded-md transition-colors" title="Documentation">
                        <span className="codicon codicon-book"></span>
                    </button>
                </div>
            </header>
            <main className="flex-1 flex overflow-hidden">
                <aside className="w-64 bg-white border-r border-gray-200 flex flex-col shrink-0">
                    <Outline
                        memoryMap={memoryMap}
                        selectedId={selectedId}
                        onSelect={handleSelect}
                    />
                </aside>
                {activeTab === 'yaml' ? (
                    <section className="flex-1 bg-white overflow-auto">
                        <div className="p-6">
                            <pre className="font-mono text-sm">{rawText}</pre>
                        </div>
                    </section>
                ) : (
                    <DetailsPanel
                        selectedType={selectedType}
                        selectedObject={selectedObject}
                        onUpdate={handleUpdate}
                    />
                )}
            </main>
        </>
    );
};


class ErrorBoundary extends React.Component<{ children: ReactNode }, { error: any, info: any }> {
    constructor(props: any) {
        super(props);
        this.state = { error: null, info: null };
    }
    static getDerivedStateFromError(error: any) {
        return { error, info: null };
    }
    componentDidCatch(error: any, info: ErrorInfo) {
        this.setState({ error, info });
    }
    render() {
        if (this.state.error) {
            return (
                <div style={{ background: '#fff0f0', color: '#b91c1c', padding: 32, fontFamily: 'monospace' }}>
                    <h2 style={{ fontWeight: 'bold' }}>UI Error</h2>
                    <div>{this.state.error?.message || String(this.state.error)}</div>
                    {this.state.info && <pre style={{ marginTop: 16, fontSize: 12 }}>{this.state.info.componentStack}</pre>}
                </div>
            );
        }
        return this.props.children;
    }
}

const rootElement = document.getElementById('root');
if (rootElement) {
    const root = createRoot(rootElement);
    root.render(
        <ErrorBoundary>
            <App />
        </ErrorBoundary>
    );
}
