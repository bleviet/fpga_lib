import React, { useMemo, useState } from 'react';
import { MemoryMap, AddressBlock, Register, RegisterArray } from '../types/memoryMap';

type YamlPath = Array<string | number>;

type RegisterArrayNode = {
    __kind: 'array';
    name: string;
    address_offset: number;
    count: number;
    stride: number;
    description?: string;
    registers: Register[];
};

const isArrayNode = (node: any): node is RegisterArrayNode => {
    return !!node && typeof node === 'object' && node.__kind === 'array' && typeof node.count === 'number' && typeof node.stride === 'number';
};

const toHex = (n: number) => `0x${Math.max(0, n).toString(16).toUpperCase()}`;

interface OutlineProps {
    memoryMap: MemoryMap;
    selectedId: string | null;
    onSelect: (selection: {
        id: string;
        type: 'memoryMap' | 'block' | 'register' | 'array';
        object: any;
        breadcrumbs: string[];
        path: YamlPath;
        meta?: {
            absoluteAddress?: number;
            relativeOffset?: number;
        };
    }) => void;
}

const Outline: React.FC<OutlineProps> = ({ memoryMap, selectedId, onSelect }) => {
    // By default, expand all blocks and registers
    const allIds = useMemo(() => {
        const ids = new Set<string>(['root']);
        (memoryMap.address_blocks ?? []).forEach((block, blockIdx) => {
            const blockId = `block-${blockIdx}`;
            ids.add(blockId);
            const regs = ((block as any).registers ?? []) as any[];
            regs.forEach((reg, regIdx) => {
                if (reg && reg.__kind === 'array') {
                    ids.add(`block-${blockIdx}-arrreg-${regIdx}`);
                }
            });
            ((block as any).register_arrays ?? []).forEach((arr: any, arrIdx: number) => {
                ids.add(`block-${blockIdx}-arr-${arrIdx}`);
            });
        });
        return ids;
    }, [memoryMap]);
    const [expanded, setExpanded] = useState<Set<string>>(allIds);
    const [query, setQuery] = useState('');

    const toggleExpand = (id: string, e: React.MouseEvent) => {
        e.stopPropagation();
        const newExpanded = new Set(expanded);
        if (newExpanded.has(id)) {
            newExpanded.delete(id);
        } else {
            newExpanded.add(id);
        }
        setExpanded(newExpanded);
    };

    const renderLeafRegister = (reg: Register, blockIndex: number, regIndex: number) => {
        const id = `block-${blockIndex}-reg-${regIndex}`;
        const isSelected = selectedId === id;
        const block = memoryMap.address_blocks?.[blockIndex];
        const absolute = (block?.base_address ?? 0) + (reg.address_offset ?? 0);
        return (
            <div
                key={id}
                className={`group flex items-center gap-2 px-3 py-1.5 text-sm cursor-pointer border-l-[3px] ${isSelected
                    ? 'bg-indigo-50 text-indigo-700 border-indigo-600 font-medium'
                    : 'text-gray-600 hover:bg-gray-50 border-transparent hover:border-gray-300'
                    }`}
                onClick={() =>
                    onSelect({
                        id,
                        type: 'register',
                        object: reg,
                        breadcrumbs: [memoryMap.name || 'Memory Map', memoryMap.address_blocks?.[blockIndex]?.name ?? '', reg.name],
                        path: ['addressBlocks', blockIndex, 'registers', regIndex],
                        meta: { absoluteAddress: absolute, relativeOffset: reg.address_offset ?? 0 },
                    })
                }
                style={{ paddingLeft: '40px' }}
            >
                <span className={`codicon codicon-symbol-variable text-[16px] ${isSelected ? 'text-indigo-500' : 'text-gray-400'}`}></span>
                <span className="flex-1">{reg.name}</span>
                <span className="text-[10px] text-gray-400 font-mono">{toHex(reg.address_offset)}</span>
            </div>
        );
    };

    const renderArrayRegister = (arr: RegisterArrayNode, block: AddressBlock, blockIndex: number, regIndex: number) => {
        const id = `block-${blockIndex}-arrreg-${regIndex}`;
        const isSelected = selectedId === id;
        const isExpanded = expanded.has(id);

        const start = (block.base_address ?? 0) + (arr.address_offset ?? 0);
        const end = start + Math.max(1, arr.count) * Math.max(1, arr.stride) - 1;

        return (
            <div key={id}>
                <div
                    className={`tree-item ${isSelected ? 'selected' : ''}`}
                    onClick={() =>
                        onSelect({
                            id,
                            type: 'array',
                            object: arr,
                            breadcrumbs: [memoryMap.name || 'Memory Map', block.name, arr.name],
                            path: ['addressBlocks', blockIndex, 'registers', regIndex],
                        })
                    }
                    style={{ paddingLeft: '40px' }}
                >
                    <span
                        className={`codicon codicon-chevron-${isExpanded ? 'down' : 'right'}`}
                        onClick={(e) => toggleExpand(id, e)}
                        style={{ marginRight: '6px', cursor: 'pointer' }}
                    ></span>
                    <span className="codicon codicon-symbol-array" style={{ marginRight: '6px' }}></span>
                    {arr.name} <span className="opacity-50">@ {toHex(start)}-{toHex(end)} [{arr.count}]</span>
                </div>

                {isExpanded && (
                    <div>
                        {Array.from({ length: arr.count }).map((_, elementIndex) => {
                            const elementId = `${id}-el-${elementIndex}`;
                            const elementBase = start + elementIndex * arr.stride;
                            const isElementSelected = selectedId === elementId;
                            return (
                                <div key={elementId}>
                                    <div
                                        className={`tree-item ${isElementSelected ? 'selected' : ''}`}
                                        onClick={() =>
                                            onSelect({
                                                id: elementId,
                                                type: 'array',
                                                object: { ...arr, __element_index: elementIndex, __element_base: elementBase },
                                                breadcrumbs: [memoryMap.name || 'Memory Map', block.name, `${arr.name}[${elementIndex}]`],
                                                path: ['addressBlocks', blockIndex, 'registers', regIndex],
                                            })
                                        }
                                        style={{ paddingLeft: '60px' }}
                                    >
                                        <span className="codicon codicon-symbol-namespace" style={{ marginRight: '6px' }}></span>
                                        {arr.name}[{elementIndex}] <span className="opacity-50">@ {toHex(elementBase)}</span>
                                    </div>

                                    {arr.registers?.map((reg, childIndex) => {
                                        const childId = `${elementId}-reg-${childIndex}`;
                                        const isChildSelected = selectedId === childId;
                                        const absolute = elementBase + (reg.address_offset ?? 0);
                                        return (
                                            <div
                                                key={childId}
                                                className={`tree-item ${isChildSelected ? 'selected' : ''}`}
                                                onClick={() =>
                                                    onSelect({
                                                        id: childId,
                                                        type: 'register',
                                                        object: reg,
                                                        breadcrumbs: [memoryMap.name || 'Memory Map', block.name, `${arr.name}[${elementIndex}]`, reg.name],
                                                        path: ['addressBlocks', blockIndex, 'registers', regIndex, 'registers', childIndex],
                                                        meta: { absoluteAddress: absolute, relativeOffset: reg.address_offset ?? 0 },
                                                    })
                                                }
                                                style={{ paddingLeft: '80px' }}
                                            >
                                                <span className="codicon codicon-symbol-variable" style={{ marginRight: '6px' }}></span>
                                                {reg.name} <span className="opacity-50">@ {toHex(absolute)}</span>
                                            </div>
                                        );
                                    })}
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>
        );
    };

    const renderArray = (arr: any, blockIndex: number, arrayIndex: number) => {
        const id = `block-${blockIndex}-arr-${arrayIndex}`;
        const isSelected = selectedId === id;
        const isExpanded = expanded.has(id);
        return (
            <div key={id}>
                <div
                    className={`tree-item ${isSelected ? 'selected' : ''}`}
                    onClick={() =>
                        onSelect({
                            id,
                            type: 'array',
                            object: arr,
                            breadcrumbs: [memoryMap.name || 'Memory Map', memoryMap.address_blocks?.[blockIndex]?.name ?? '', arr.name],
                            path: ['addressBlocks', blockIndex, 'register_arrays', arrayIndex],
                        })
                    }
                    style={{ paddingLeft: '40px' }}
                >
                    <span
                        className={`codicon codicon-chevron-${isExpanded ? 'down' : 'right'}`}
                        onClick={(e) => toggleExpand(id, e)}
                        style={{ marginRight: '6px', cursor: 'pointer' }}
                    ></span>
                    <span className="codicon codicon-symbol-array" style={{ marginRight: '6px' }}></span>
                    {arr.name} <span className="opacity-50">[{arr.count}]</span>
                </div>
                {isExpanded && Array.isArray(arr.children_registers) && (
                    <div>
                        {arr.children_registers.map((reg: Register, idx: number) => renderLeafRegister(reg, blockIndex, idx))}
                    </div>
                )}
            </div>
        );
    };

    const renderBlock = (block: AddressBlock, blockIndex: number) => {
        const id = `block-${blockIndex}`;
        const isExpanded = expanded.has(id);
        const isSelected = selectedId === id;

        const regsAny = ((block as any).registers ?? []) as any[];

        return (
            <div key={id}>
                <div
                    className={`tree-item ${isSelected ? 'selected' : ''}`}
                    onClick={() =>
                        onSelect({
                            id,
                            type: 'block',
                            object: block,
                            breadcrumbs: [memoryMap.name || 'Memory Map', block.name],
                            path: ['addressBlocks', blockIndex],
                        })
                    }
                    style={{ paddingLeft: '20px' }}
                >
                    <span
                        className={`codicon codicon-chevron-${isExpanded ? 'down' : 'right'}`}
                        onClick={(e) => toggleExpand(id, e)}
                        style={{ marginRight: '6px', cursor: 'pointer' }}
                    ></span>
                    <span className="codicon codicon-package" style={{ marginRight: '6px' }}></span>
                    {block.name} <span className="opacity-50">@ 0x{block.base_address.toString(16).toUpperCase()}</span>
                </div>
                {isExpanded && (
                    <div>
                        {regsAny.map((node, idx) => {
                            if (isArrayNode(node)) return renderArrayRegister(node, block, blockIndex, idx);
                            return renderLeafRegister(node as Register, blockIndex, idx);
                        })}
                        {(block as any).register_arrays?.map((arr: RegisterArray, idx: number) => renderArray(arr, blockIndex, idx))}
                    </div>
                )}
            </div>
        );
    };

    const rootId = 'root';
    const isRootExpanded = expanded.has(rootId);
    const isRootSelected = selectedId === rootId;

    const filteredBlocks = useMemo(() => {
        const q = query.trim().toLowerCase();
        const blocks = (memoryMap.address_blocks ?? []).map((block, index) => ({ block, index }));
        if (!q) return blocks;

        return blocks.filter(({ block }) => {
            if ((block.name ?? '').toLowerCase().includes(q)) return true;
            const regs = ((block as any).registers ?? []) as any[];
            if (
                regs.some((r) => {
                    if (!r) return false;
                    if (String(r.name ?? '').toLowerCase().includes(q)) return true;
                    if (isArrayNode(r)) {
                        return (r.registers ?? []).some((rr) => String(rr.name ?? '').toLowerCase().includes(q));
                    }
                    return false;
                })
            ) {
                return true;
            }
            const arrays = ((block as any).register_arrays ?? []) as any[];
            if (arrays.some((a) => (a.name ?? '').toLowerCase().includes(q))) return true;
            return false;
        });
    }, [memoryMap, query]);

    return (
        <>
            <div className="p-3 border-b border-gray-100 flex items-center gap-2">
                <div className="relative flex-1">
                    <span className="codicon codicon-search absolute left-2.5 top-2 text-gray-400 text-[18px]"></span>
                    <input
                        className="w-full pl-9 pr-3 py-1.5 text-sm border border-gray-200 rounded-md bg-gray-50 focus:bg-white focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none transition-all"
                        placeholder="Filter registers..."
                        type="text"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                    />
                </div>
                <button
                    className="ml-2 p-2 rounded bg-gray-100 hover:bg-gray-200 border border-gray-200 text-gray-600 flex items-center justify-center"
                    title={expanded.size === allIds.size ? 'Collapse All' : 'Expand All'}
                    onClick={() => {
                        if (expanded.size === allIds.size) {
                            setExpanded(new Set(['root']));
                        } else {
                            setExpanded(new Set(allIds));
                        }
                    }}
                >
                    {expanded.size === allIds.size ? (
                        // Collapse All SVG icon
                        <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <rect x="3" y="3" width="14" height="14" rx="3" fill="#fff" stroke="#888" strokeWidth="1.5" />
                            <rect x="6" y="9" width="8" height="2" rx="1" fill="#444" />
                        </svg>
                    ) : (
                        // Expand All SVG icon
                        <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <rect x="3" y="3" width="14" height="14" rx="3" fill="#fff" stroke="#888" strokeWidth="1.5" />
                            <rect x="6" y="9" width="8" height="2" rx="1" fill="#444" />
                            <rect x="9" y="6" width="2" height="8" rx="1" fill="#444" />
                        </svg>
                    )}
                </button>
            </div>
            <div className="flex-1 overflow-y-auto py-2">
                <div className="px-3 mb-2 text-xs font-bold text-gray-400 uppercase tracking-wider">Memory Map</div>
                <div
                    className={`group flex items-center gap-2 px-3 py-1.5 text-sm cursor-pointer border-l-[3px] ${isRootSelected
                        ? 'bg-indigo-50 text-indigo-700 border-indigo-600 font-medium'
                        : 'text-gray-600 hover:bg-gray-50 border-transparent hover:border-gray-300'
                        }`}
                    onClick={() =>
                        onSelect({
                            id: rootId,
                            type: 'memoryMap',
                            object: memoryMap,
                            breadcrumbs: [memoryMap.name || 'Memory Map'],
                            path: [],
                        })
                    }
                >
                    <span
                        className={`codicon codicon-chevron-${isRootExpanded ? 'down' : 'right'} text-[16px] ${isRootSelected ? 'text-indigo-500' : 'text-gray-400'}`}
                        onClick={(e) => toggleExpand(rootId, e)}
                    ></span>
                    <span className={`codicon codicon-map text-[16px] ${isRootSelected ? 'text-indigo-500' : 'text-gray-400'}`}></span>
                    <span className="flex-1">{memoryMap.name || 'Memory Map'}</span>
                </div>
                {isRootExpanded && filteredBlocks.map(({ block, index }) => renderBlock(block, index))}
            </div>
            <div className="p-3 bg-gray-50 border-t border-gray-200 text-xs text-gray-500 flex justify-between">
                <span>{filteredBlocks.length} Items</span>
                <span>Base: {toHex(memoryMap.address_blocks?.[0]?.base_address ?? 0)}</span>
            </div>
        </>
    );
};

export default Outline;
