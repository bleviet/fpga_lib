import React, { useEffect, useMemo, useState } from 'react';
import { VSCodeDropdown, VSCodeOption, VSCodeTextField, VSCodeTextArea } from '@vscode/webview-ui-toolkit/react';
import { Register } from '../types/memoryMap';
import BitFieldVisualizer from './BitFieldVisualizer';

interface DetailsPanelProps {
    selectedType: 'memoryMap' | 'block' | 'register' | 'array' | null;
    selectedObject: any;
    selectionMeta?: {
        absoluteAddress?: number;
        relativeOffset?: number;
    };
    onUpdate: (path: Array<string | number>, value: any) => void;
}

const ACCESS_OPTIONS = ['read-only', 'write-only', 'read-write', 'write-1-to-clear', 'read-write-1-to-clear'];

type EditKey = 'name' | 'bits' | 'access' | 'reset' | 'description';

const DetailsPanel: React.FC<DetailsPanelProps> = ({ selectedType, selectedObject, selectionMeta, onUpdate }) => {
    const [offsetText, setOffsetText] = useState<string>('');
    const [selectedFieldIndex, setSelectedFieldIndex] = useState<number>(-1);
    const [hoveredFieldIndex, setHoveredFieldIndex] = useState<number | null>(null);
    const [editingFieldIndex, setEditingFieldIndex] = useState<number | null>(null);
    const [editingKey, setEditingKey] = useState<EditKey>('name');

    // Exit edit mode on Escape
    useEffect(() => {
        const onKeyDown = (e: KeyboardEvent) => {
            if (e.key === 'Escape') setEditingFieldIndex(null);
        };
        window.addEventListener('keydown', onKeyDown);
        return () => window.removeEventListener('keydown', onKeyDown);
    }, []);

    // Auto-focus the editor on first click (no extra click needed)
    useEffect(() => {
        if (editingFieldIndex === null) return;
        const id = window.setTimeout(() => {
            const row = document.querySelector(`tr[data-field-idx="${editingFieldIndex}"]`) as HTMLElement | null;
            if (!row) return;
            const el = row.querySelector(`[data-edit-key="${editingKey}"]`) as HTMLElement | null;
            if (!el) return;
            try {
                el.focus();
            } catch {
                // ignore focus failures on custom elements
            }
        }, 0);
        return () => window.clearTimeout(id);
    }, [editingFieldIndex, editingKey]);

    const isRegister = selectedType === 'register' && !!selectedObject;
    const reg = isRegister ? (selectedObject as Register) : null;
    // Normalize fields for BitFieldVisualizer: always provide bit/bit_range
    const fields = useMemo(() => {
        if (!reg?.fields) return [];
        return reg.fields.map((f: any) => {
            if (f.bit_range) return f;
            if (f.bit_offset !== undefined && f.bit_width !== undefined) {
                const lo = Number(f.bit_offset);
                const width = Number(f.bit_width);
                const hi = lo + width - 1;
                return { ...f, bit_range: [hi, lo] };
            }
            if (f.bit !== undefined) return f;
            return f;
        });
    }, [reg?.fields]);

    const registerOffsetText = useMemo(() => {
        if (!isRegister || !reg) return '';
        const off = Number(reg.address_offset ?? 0);
        return `0x${off.toString(16).toUpperCase()}`;
    }, [isRegister, reg?.address_offset]);

    useEffect(() => {
        if (isRegister) {
            setOffsetText(registerOffsetText);
        } else {
            setOffsetText('');
        }
    }, [isRegister, registerOffsetText]);

    useEffect(() => {
        if (!isRegister) {
            setSelectedFieldIndex(-1);
            return;
        }
        if (!fields.length) {
            setSelectedFieldIndex(-1);
            return;
        }
        setSelectedFieldIndex((prev) => {
            if (prev < 0) return 0;
            if (prev >= fields.length) return fields.length - 1;
            return prev;
        });
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [isRegister, (reg as any)?.name, fields.length]);

    const commitRegisterOffset = () => {
        if (!isRegister) return;
        const parsed = Number.parseInt(offsetText.trim(), 0);
        if (Number.isNaN(parsed)) return;
        onUpdate(['address_offset'], parsed);
    };

    const toBits = (f: any) => {
        const o = Number(f?.bit_offset ?? 0);
        const w = Number(f?.bit_width ?? 1);
        if (!Number.isFinite(o) || !Number.isFinite(w)) {
            return '[?:?]';
        }
        const msb = o + w - 1;
        return `[${msb}:${o}]`;
    };

    const getFieldColor = (index: number): string => {
        const colors = ['blue', 'orange', 'emerald', 'pink', 'purple', 'cyan', 'amber', 'rose'];
        return colors[index % colors.length];
    };

    // Parse a bit string like "[7:4]" or "[3]" or "7:4" or "3".
    const parseBitsInput = (text: string) => {
        const trimmed = text.trim().replace(/[\[\]]/g, '');
        if (!trimmed) return null;
        const parts = trimmed.split(':').map((p) => Number(p.trim()));
        if (parts.some((p) => Number.isNaN(p))) return null;
        let msb: number;
        let lsb: number;
        if (parts.length === 1) {
            msb = parts[0];
            lsb = parts[0];
        } else {
            [msb, lsb] = parts as [number, number];
        }
        if (!Number.isFinite(msb) || !Number.isFinite(lsb)) return null;
        if (msb < lsb) {
            const tmp = msb;
            msb = lsb;
            lsb = tmp;
        }
        const width = msb - lsb + 1;
        return { bit_offset: lsb, bit_width: width, bit_range: [msb, lsb] as [number, number] };
    };

    const parseReset = (text: string): number | null => {
        const s = text.trim();
        if (!s) return null;
        const v = Number.parseInt(s, 0);
        return Number.isFinite(v) ? v : null;
    };

    if (!selectedObject) {
        return <div className="flex items-center justify-center h-full text-gray-500 text-sm">Select an item to view details</div>;
    }

    // Color map for field dots and BitFieldVisualizer
    const colorMap: Record<string, string> = {
        blue: '#3b82f6',
        orange: '#f97316',
        emerald: '#10b981',
        pink: '#ec4899',
        purple: '#a855f7',
        cyan: '#06b6d4',
        amber: '#f59e0b',
        rose: '#f43f5e',
        gray: '#e5e7eb',
    };
    if (selectedType === 'register') {
        const regObj = selectedObject as Register;

        const handleClickOutside = (e: React.MouseEvent) => {
            const target = e.target as HTMLElement | null;
            if (!target) return;
            const inRow = target.closest('tr[data-field-idx]');
            if (!inRow) setEditingFieldIndex(null);
        };

        const handleBlur = (idx: number) => (e: React.FocusEvent) => {
            const related = e.relatedTarget as HTMLElement | null;
            if (related && related.closest('tr[data-field-idx]')) return;
            setEditingFieldIndex(null);
        };

        const handleKeyDown = (idx: number) => (e: React.KeyboardEvent) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                setEditingFieldIndex(null);
            }
        };

        const startEdit = (idx: number, key: EditKey) => (e: React.MouseEvent) => {
            e.stopPropagation();
            setEditingFieldIndex(idx);
            setEditingKey(key);
        };

        return (
            <div className="flex flex-col w-full h-full" onClickCapture={handleClickOutside}>
                {/* --- Register Header and BitFieldVisualizer --- */}
                <div className="bg-gray-50/50 border-b border-gray-200 p-8 flex flex-col gap-6 shrink-0 relative overflow-hidden">
                    <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none"></div>
                    <div className="flex justify-between items-start relative z-10">
                        <div>
                            <h2 className="text-2xl font-bold text-gray-900 font-mono tracking-tight">{regObj.name}</h2>
                            <p className="text-gray-500 text-sm mt-1 max-w-2xl">{regObj.description}</p>
                        </div>
                        <div className="text-right">
                            <div className="text-sm font-mono text-gray-500 bg-white px-3 py-1 rounded-full border border-gray-200 shadow-sm inline-flex items-center gap-2">
                                <span className="w-2 h-2 rounded-full bg-emerald-500"></span> Width: <span className="text-gray-900 font-bold">32-bit</span>
                            </div>
                            <div className="mt-2 text-xs text-gray-400 font-mono">Reset: 0x{(regObj.reset_value ?? 0).toString(16).toUpperCase()}</div>
                        </div>
                    </div>
                    <div className="w-full relative z-10 mt-2 select-none">
                        <BitFieldVisualizer
                            fields={fields}
                            hoveredFieldIndex={hoveredFieldIndex}
                            setHoveredFieldIndex={setHoveredFieldIndex}
                            registerSize={32}
                            layout="pro"
                        />
                    </div>
                </div>
                {/* --- Main Content: Table and Properties --- */}
                <div className="flex-1 flex overflow-hidden">
                    <div className="flex-1 overflow-auto bg-white border-r border-gray-200">
                        <table className="w-full text-left border-collapse table-fixed">
                            <colgroup>
                                <col className="w-[32%] min-w-[240px]" />
                                <col className="w-[14%] min-w-[100px]" />
                                <col className="w-[14%] min-w-[120px]" />
                                <col className="w-[14%] min-w-[110px]" />
                                <col className="w-[26%]" />
                            </colgroup>
                            <thead className="bg-gray-50 text-xs font-semibold text-gray-500 uppercase tracking-wider sticky top-0 z-10 shadow-sm">
                                <tr className="h-12">
                                    <th className="px-6 py-3 border-b border-gray-200 align-middle">Name</th>
                                    <th className="px-4 py-3 border-b border-gray-200 align-middle">Bit(s)</th>
                                    <th className="px-4 py-3 border-b border-gray-200 align-middle">Access</th>
                                    <th className="px-4 py-3 border-b border-gray-200 align-middle">Reset</th>
                                    <th className="px-6 py-3 border-b border-gray-200 align-middle">Description</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100 text-sm">
                                {fields.map((field, idx) => {
                                    const isSelected = idx === hoveredFieldIndex;
                                    const highlightClass = isSelected ? 'bg-indigo-50/60' : '';
                                    const bits = toBits(field);
                                    const color = getFieldColor(idx);
                                    const resetDisplay =
                                        field.reset_value !== null && field.reset_value !== undefined
                                            ? `0x${Number(field.reset_value).toString(16).toUpperCase()}`
                                            : '';

                                    return (
                                        <tr
                                            key={idx}
                                            data-field-idx={idx}
                                            className={`group transition-colors border-l-4 border-transparent h-12 ${idx === hoveredFieldIndex ? 'border-indigo-600 bg-indigo-50/60' : ''}`}
                                            onMouseEnter={() => {
                                                setHoveredFieldIndex(idx);
                                                setSelectedFieldIndex(idx);
                                            }}
                                            onMouseLeave={() => setHoveredFieldIndex(null)}
                                            onClick={() => {
                                                setEditingFieldIndex(idx);
                                                setEditingKey('name');
                                            }}
                                            id={`row-${field.name?.toLowerCase().replace(/[^a-z0-9_]/g, '-')}`}
                                        >
                                            <td className="px-6 py-2 font-medium text-gray-900 align-middle" onClick={startEdit(idx, 'name')}>
                                                <div className="flex items-center gap-2 h-10">
                                                    <div className={`w-2.5 h-2.5 rounded-sm`} style={{ backgroundColor: color === 'gray' ? '#e5e7eb' : (colorMap && colorMap[color]) || color }}></div>
                                                    {editingFieldIndex === idx ? (
                                                        <VSCodeTextField
                                                            data-edit-key="name"
                                                            className="flex-1"
                                                            value={field.name || ''}
                                                            onInput={(e: any) => onUpdate(['fields', idx, 'name'], e.target.value)}
                                                            onBlur={handleBlur(idx)}
                                                            onKeyDown={handleKeyDown(idx)}
                                                        />
                                                    ) : (
                                                        field.name
                                                    )}
                                                </div>
                                            </td>
                                            <td className="px-4 py-2 font-mono text-gray-600 align-middle" onClick={startEdit(idx, 'bits')}>
                                                <div className="flex items-center h-10">
                                                    {editingFieldIndex === idx ? (
                                                        <VSCodeTextField
                                                            data-edit-key="bits"
                                                            className="w-full font-mono"
                                                            value={bits}
                                                            onInput={(e: any) => {
                                                                const parsed = parseBitsInput(e.target.value);
                                                                if (parsed) {
                                                                    onUpdate(['fields', idx, 'bit_offset'], parsed.bit_offset);
                                                                    onUpdate(['fields', idx, 'bit_width'], parsed.bit_width);
                                                                    onUpdate(['fields', idx, 'bit_range'], parsed.bit_range);
                                                                }
                                                            }}
                                                            onBlur={handleBlur(idx)}
                                                            onKeyDown={handleKeyDown(idx)}
                                                        />
                                                    ) : (
                                                        bits
                                                    )}
                                                </div>
                                            </td>
                                            <td className="px-4 py-2 align-middle" onClick={startEdit(idx, 'access')}>
                                                <div className="flex items-center h-10">
                                                    {editingFieldIndex === idx ? (
                                                        <VSCodeDropdown
                                                            data-edit-key="access"
                                                            value={field.access || 'read-write'}
                                                            className="w-full"
                                                            onInput={(e: any) => onUpdate(['fields', idx, 'access'], e.target.value)}
                                                            onBlur={handleBlur(idx)}
                                                            onKeyDown={handleKeyDown(idx)}
                                                        >
                                                            {ACCESS_OPTIONS.map((opt) => (
                                                                <VSCodeOption key={opt} value={opt}>{opt}</VSCodeOption>
                                                            ))}
                                                        </VSCodeDropdown>
                                                    ) : (
                                                        <div className="flex items-center justify-start">
                                                            <span className="px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800 border border-green-200 whitespace-nowrap">{field.access || 'RW'}</span>
                                                        </div>
                                                    )}
                                                </div>
                                            </td>
                                            <td className="px-4 py-2 font-mono text-gray-500 align-middle" onClick={startEdit(idx, 'reset')}>
                                                <div className="flex items-center h-10">
                                                    {editingFieldIndex === idx ? (
                                                        <VSCodeTextField
                                                            data-edit-key="reset"
                                                            className="w-full font-mono"
                                                            value={resetDisplay || '0x0'}
                                                            onInput={(e: any) => {
                                                                const raw = String(e.target.value ?? '');
                                                                const parsed = parseReset(raw);
                                                                if (parsed === null) {
                                                                    if (!raw.trim()) onUpdate(['fields', idx, 'reset_value'], null);
                                                                    return;
                                                                }
                                                                onUpdate(['fields', idx, 'reset_value'], parsed);
                                                            }}
                                                            onBlur={handleBlur(idx)}
                                                            onKeyDown={handleKeyDown(idx)}
                                                        />
                                                    ) : (
                                                        resetDisplay || '0x0'
                                                    )}
                                                </div>
                                            </td>
                                            <td className="px-6 py-2 text-gray-500 align-middle" onClick={startEdit(idx, 'description')}>
                                                <div className="flex items-center h-10">
                                                    {editingFieldIndex === idx ? (
                                                        <VSCodeTextArea
                                                            data-edit-key="description"
                                                            className="w-full"
                                                            rows={2}
                                                            value={field.description || ''}
                                                            onInput={(e: any) => onUpdate(['fields', idx, 'description'], e.target.value)}
                                                            onBlur={handleBlur(idx)}
                                                        />
                                                    ) : (
                                                        field.description || '-'
                                                    )}
                                                </div>
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        );
    }

    if (selectedType === 'memoryMap') {
        const map = selectedObject as any;
        return (
            <div className="p-6">
                <h2 className="text-lg font-bold text-gray-900 mb-4">Memory Map Overview</h2>
                <div className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1.5">Name</label>
                        <VSCodeTextField value={map.name || ''} onInput={(e: any) => onUpdate(['name'], e.target.value)} />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1.5">Description</label>
                        <VSCodeTextArea value={map.description || ''} rows={3} onInput={(e: any) => onUpdate(['description'], e.target.value)} />
                    </div>
                    <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                        <div className="flex justify-between items-center">
                            <span className="text-sm font-medium text-gray-700">Address Blocks:</span>
                            <span className="text-sm font-mono text-gray-900">{map.address_blocks?.length || 0}</span>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    if (selectedType === 'block') {
        const block = selectedObject as any;
        return (
            <div className="p-6">
                <h2 className="text-lg font-bold text-gray-900 mb-4">Address Block</h2>
                <div className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1.5">Name</label>
                        <VSCodeTextField value={block.name} onInput={(e: any) => onUpdate(['name'], e.target.value)} />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1.5">Base Address</label>
                        <VSCodeTextField
                            value={`0x${(block.base_address ?? 0).toString(16).toUpperCase()}`}
                            onInput={(e: any) => {
                                const val = Number.parseInt(e.target.value, 0);
                                if (!Number.isNaN(val)) onUpdate(['base_address'], val);
                            }}
                        />
                    </div>
                </div>
            </div>
        );
    }

    return <div className="p-6 text-gray-500">Select an item to view details</div>;
};

export default DetailsPanel;
