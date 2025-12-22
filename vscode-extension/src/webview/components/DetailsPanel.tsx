import React, { useEffect, useMemo, useRef, useState } from 'react';
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

type ActiveCell = { rowIndex: number; key: EditKey };

const COLUMN_ORDER: EditKey[] = ['name', 'bits', 'access', 'reset', 'description'];

const DetailsPanel: React.FC<DetailsPanelProps> = ({ selectedType, selectedObject, selectionMeta, onUpdate }) => {
    const [offsetText, setOffsetText] = useState<string>('');
    const [selectedFieldIndex, setSelectedFieldIndex] = useState<number>(-1);
    const [hoveredFieldIndex, setHoveredFieldIndex] = useState<number | null>(null);
    const [editingFieldIndex, setEditingFieldIndex] = useState<number | null>(null);
    const [editingKey, setEditingKey] = useState<EditKey>('name');
    const [selectedEditKey, setSelectedEditKey] = useState<EditKey>('name');
    const [activeCell, setActiveCell] = useState<ActiveCell>({ rowIndex: -1, key: 'name' });
    const [bitsDraft, setBitsDraft] = useState<string>('');
    const fieldsFocusRef = useRef<HTMLDivElement | null>(null);

    const refocusFieldsTableSoon = () => {
        window.setTimeout(() => {
            fieldsFocusRef.current?.focus();
        }, 0);
    };

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

    // When a register is selected, shift keyboard focus to the fields table.
    useEffect(() => {
        if (!isRegister) return;
        const id = window.setTimeout(() => {
            fieldsFocusRef.current?.focus();
        }, 0);
        return () => window.clearTimeout(id);
    }, [isRegister, reg?.name]);

    const beginEdit = (rowIndex: number, key: EditKey) => {
        if (rowIndex < 0 || rowIndex >= fields.length) return;
        setEditingKey(key);
        if (key === 'bits') {
            setBitsDraft(toBits(fields[rowIndex]));
        }
        setEditingFieldIndex(rowIndex);
    };

    // Exit edit mode on Escape and return focus to table
    useEffect(() => {
        const onKeyDown = (e: KeyboardEvent) => {
            if (e.key !== 'Escape') return;
            if (editingFieldIndex === null) return;
            e.preventDefault();
            e.stopPropagation();
            setEditingFieldIndex(null);
            refocusFieldsTableSoon();
        };
        window.addEventListener('keydown', onKeyDown);
        return () => window.removeEventListener('keydown', onKeyDown);
    }, [editingFieldIndex]);

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

    // Initialize draft text when entering Bits edit mode.
    useEffect(() => {
        if (editingFieldIndex === null) return;
        if (editingKey !== 'bits') return;
        const f = fields[editingFieldIndex];
        if (!f) return;
        setBitsDraft(toBits(f));
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [editingFieldIndex, editingKey]);


    // Keyboard shortcuts (when the fields table is focused):
    // - Arrow keys: move between cells
    // - Vim keys: h/j/k/l move between cells
    // - Alt+ArrowUp / Alt+ArrowDown: move selected field (repack offsets)
    // - F2 or e: edit active cell
    useEffect(() => {
        if (!isRegister) return;

        const onKeyDown = (e: KeyboardEvent) => {
            const keyLower = (e.key || '').toLowerCase();
            const vimToArrow: Record<string, 'ArrowLeft' | 'ArrowDown' | 'ArrowUp' | 'ArrowRight'> = {
                h: 'ArrowLeft',
                j: 'ArrowDown',
                k: 'ArrowUp',
                l: 'ArrowRight',
            };

            const mappedArrow = vimToArrow[keyLower];
            const normalizedKey: string = mappedArrow ?? e.key;

            const isArrow = normalizedKey === 'ArrowUp' || normalizedKey === 'ArrowDown' || normalizedKey === 'ArrowLeft' || normalizedKey === 'ArrowRight';
            const isEdit = normalizedKey === 'F2' || keyLower === 'e';
            if (!isArrow && !isEdit) return;

            // Avoid hijacking common editor chords.
            if (e.ctrlKey || e.metaKey) return;

            const activeEl = document.activeElement as HTMLElement | null;
            const isInFieldsArea = !!fieldsFocusRef.current && !!activeEl && (activeEl === fieldsFocusRef.current || fieldsFocusRef.current.contains(activeEl));
            if (!isInFieldsArea) return;

            const target = e.target as HTMLElement | null;
            const isTypingTarget = !!target?.closest(
                'input, textarea, select, [contenteditable="true"], vscode-text-field, vscode-text-area, vscode-dropdown'
            );
            // Don't steal arrow keys while editing/typing.
            if (editingFieldIndex !== null || isTypingTarget) return;

            const scrollToCell = (rowIndex: number, key: EditKey) => {
                window.setTimeout(() => {
                    const row = document.querySelector(`tr[data-field-idx="${rowIndex}"]`) as HTMLElement | null;
                    row?.scrollIntoView({ block: 'nearest' });
                    const cell = row?.querySelector(`td[data-col-key="${key}"]`) as HTMLElement | null;
                    cell?.scrollIntoView({ block: 'nearest', inline: 'nearest' });
                }, 0);
            };

            const currentRow = activeCell.rowIndex >= 0 ? activeCell.rowIndex : (selectedFieldIndex >= 0 ? selectedFieldIndex : 0);
            const currentKey: EditKey = COLUMN_ORDER.includes(activeCell.key) ? activeCell.key : selectedEditKey;

            if (isEdit) {
                if (currentRow < 0 || currentRow >= fields.length) return;
                e.preventDefault();
                e.stopPropagation();
                setSelectedFieldIndex(currentRow);
                setHoveredFieldIndex(currentRow);
                setSelectedEditKey(currentKey);
                setActiveCell({ rowIndex: currentRow, key: currentKey });
                beginEdit(currentRow, currentKey);
                return;
            }

            const isVertical = normalizedKey === 'ArrowUp' || normalizedKey === 'ArrowDown';
            const delta = normalizedKey === 'ArrowUp' || normalizedKey === 'ArrowLeft' ? -1 : 1;

            // Alt+Arrow moves fields.
            if (e.altKey && isVertical) {
                if (selectedFieldIndex < 0) return;
                const next = selectedFieldIndex + delta;
                if (next < 0 || next >= fields.length) return;

                e.preventDefault();
                e.stopPropagation();
                setEditingFieldIndex(null);
                onUpdate(['__op', 'field-move'], { index: selectedFieldIndex, delta });
                setSelectedFieldIndex(next);
                setHoveredFieldIndex(next);

                setActiveCell((prev) => ({ rowIndex: next, key: prev.key }));
                scrollToCell(next, currentKey);
                return;
            }

            // Plain arrows navigate cells.
            e.preventDefault();
            e.stopPropagation();

            if (isVertical) {
                const nextRow = Math.max(0, Math.min(fields.length - 1, currentRow + delta));
                setSelectedFieldIndex(nextRow);
                setHoveredFieldIndex(nextRow);
                setSelectedEditKey(currentKey);
                setActiveCell({ rowIndex: nextRow, key: currentKey });
                scrollToCell(nextRow, currentKey);
                return;
            }

            const currentCol = Math.max(0, COLUMN_ORDER.indexOf(currentKey));
            const nextCol = Math.max(0, Math.min(COLUMN_ORDER.length - 1, currentCol + delta));
            const nextKey = COLUMN_ORDER[nextCol] ?? 'name';
            setSelectedFieldIndex(currentRow);
            setHoveredFieldIndex(currentRow);
            setSelectedEditKey(nextKey);
            setActiveCell({ rowIndex: currentRow, key: nextKey });
            scrollToCell(currentRow, nextKey);
        };

        window.addEventListener('keydown', onKeyDown);
        return () => window.removeEventListener('keydown', onKeyDown);
    }, [isRegister, fields.length, selectedFieldIndex, selectedEditKey, activeCell, editingFieldIndex, onUpdate]);

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
            setActiveCell({ rowIndex: -1, key: 'name' });
            return;
        }
        if (!fields.length) {
            setSelectedFieldIndex(-1);
            setActiveCell({ rowIndex: -1, key: 'name' });
            return;
        }
        setSelectedFieldIndex((prev) => {
            if (prev < 0) return 0;
            if (prev >= fields.length) return fields.length - 1;
            return prev;
        });
        setActiveCell((prev) => {
            const rowIndex = prev.rowIndex < 0 ? 0 : Math.min(fields.length - 1, prev.rowIndex);
            const key = COLUMN_ORDER.includes(prev.key) ? prev.key : 'name';
            return { rowIndex, key };
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
                e.stopPropagation();
                setEditingFieldIndex(null);
                refocusFieldsTableSoon();
            }
        };

        const startEdit = (idx: number, key: EditKey) => (e: React.MouseEvent) => {
            e.stopPropagation();
            setEditingFieldIndex(idx);
            setEditingKey(key);
        };

        const startEditOnDoubleClick = (idx: number, key: EditKey) => (e: React.MouseEvent) => {
            // Use double-click to enter edit mode so single-click can be used for selection/move.
            e.stopPropagation();
            beginEdit(idx, key);
        };

        const moveSelectedField = (delta: -1 | 1) => {
            const idx = selectedFieldIndex;
            if (idx < 0) return;
            const next = idx + delta;
            if (next < 0 || next >= fields.length) return;
            setEditingFieldIndex(null);
            onUpdate(['__op', 'field-move'], { index: idx, delta });
            setSelectedFieldIndex(next);
            setHoveredFieldIndex(next);
        };

        return (
            <div className="flex flex-col w-full h-full min-h-0" onClickCapture={handleClickOutside}>
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
                <div className="flex-1 flex overflow-hidden min-h-0">
                    <div className="flex-1 bg-white border-r border-gray-200 min-h-0 flex flex-col">
                        <div className="shrink-0 px-4 py-2 border-b border-gray-200 bg-white flex items-center justify-end gap-1">
                            <button
                                className="p-2 text-gray-500 hover:text-indigo-600 hover:bg-indigo-50 rounded-md transition-colors disabled:opacity-40"
                                onClick={() => moveSelectedField(-1)}
                                disabled={selectedFieldIndex <= 0}
                                title="Move field up"
                                type="button"
                            >
                                <span className="codicon codicon-chevron-up"></span>
                            </button>
                            <button
                                className="p-2 text-gray-500 hover:text-indigo-600 hover:bg-indigo-50 rounded-md transition-colors disabled:opacity-40"
                                onClick={() => moveSelectedField(1)}
                                disabled={selectedFieldIndex < 0 || selectedFieldIndex >= fields.length - 1}
                                title="Move field down"
                                type="button"
                            >
                                <span className="codicon codicon-chevron-down"></span>
                            </button>
                        </div>
                        <div
                            ref={fieldsFocusRef}
                            tabIndex={0}
                            data-fields-table="true"
                            className="flex-1 overflow-auto min-h-0 outline-none focus:outline-none"
                        >
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
                                                className={`group transition-colors border-l-4 border-transparent h-12 ${idx === selectedFieldIndex ? 'border-indigo-600 bg-indigo-50/60' : idx === hoveredFieldIndex ? 'border-indigo-400 bg-indigo-50/40' : ''}`}
                                                onMouseEnter={() => {
                                                    setHoveredFieldIndex(idx);
                                                }}
                                                onMouseLeave={() => setHoveredFieldIndex(null)}
                                                onClick={() => {
                                                    setSelectedFieldIndex(idx);
                                                    setHoveredFieldIndex(idx);
                                                    setActiveCell((prev) => ({ rowIndex: idx, key: prev.key }));
                                                }}
                                                id={`row-${field.name?.toLowerCase().replace(/[^a-z0-9_]/g, '-')}`}
                                            >
                                                {(() => {
                                                    const isEditingRow = editingFieldIndex === idx;
                                                    const isEditingName = isEditingRow && editingKey === 'name';
                                                    const isEditingBits = isEditingRow && editingKey === 'bits';
                                                    const isEditingAccess = isEditingRow && editingKey === 'access';
                                                    const isEditingReset = isEditingRow && editingKey === 'reset';
                                                    const isEditingDescription = isEditingRow && editingKey === 'description';

                                                    return (
                                                        <>
                                                            <td
                                                                data-col-key="name"
                                                                className={`px-6 py-2 font-medium text-gray-900 align-middle ${activeCell.rowIndex === idx && activeCell.key === 'name' ? 'bg-indigo-100/70 ring-2 ring-indigo-600 ring-inset' : ''}`}
                                                                onClick={(e) => {
                                                                    e.stopPropagation();
                                                                    setSelectedFieldIndex(idx);
                                                                    setHoveredFieldIndex(idx);
                                                                    setSelectedEditKey('name');
                                                                    setActiveCell({ rowIndex: idx, key: 'name' });
                                                                }}
                                                                onDoubleClick={startEditOnDoubleClick(idx, 'name')}
                                                            >
                                                                <div className="flex items-center gap-2 h-10">
                                                                    <div className={`w-2.5 h-2.5 rounded-sm`} style={{ backgroundColor: color === 'gray' ? '#e5e7eb' : (colorMap && colorMap[color]) || color }}></div>
                                                                    {isEditingName ? (
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
                                                            <td
                                                                data-col-key="bits"
                                                                className={`px-4 py-2 font-mono text-gray-600 align-middle ${activeCell.rowIndex === idx && activeCell.key === 'bits' ? 'bg-indigo-100/70 ring-2 ring-indigo-600 ring-inset' : ''}`}
                                                                onClick={(e) => {
                                                                    e.stopPropagation();
                                                                    setSelectedFieldIndex(idx);
                                                                    setHoveredFieldIndex(idx);
                                                                    setSelectedEditKey('bits');
                                                                    setActiveCell({ rowIndex: idx, key: 'bits' });
                                                                }}
                                                                onDoubleClick={startEditOnDoubleClick(idx, 'bits')}
                                                            >
                                                                <div className="flex items-center h-10">
                                                                    {isEditingBits ? (
                                                                        <VSCodeTextField
                                                                            data-edit-key="bits"
                                                                            className="w-full font-mono"
                                                                            value={bitsDraft}
                                                                            onInput={(e: any) => {
                                                                                const next = String(e.target.value ?? '');
                                                                                setBitsDraft(next);
                                                                                const parsed = parseBitsInput(next);
                                                                                if (parsed) {
                                                                                    onUpdate(['fields', idx, 'bit_offset'], parsed.bit_offset);
                                                                                    onUpdate(['fields', idx, 'bit_width'], parsed.bit_width);
                                                                                    onUpdate(['fields', idx, 'bit_range'], parsed.bit_range);
                                                                                }
                                                                            }}
                                                                            onBlur={handleBlur(idx)}
                                                                            onKeyDown={(e: any) => {
                                                                                if (e.key !== 'Enter') return;
                                                                                const parsed = parseBitsInput(bitsDraft);
                                                                                if (parsed) {
                                                                                    onUpdate(['fields', idx, 'bit_offset'], parsed.bit_offset);
                                                                                    onUpdate(['fields', idx, 'bit_width'], parsed.bit_width);
                                                                                    onUpdate(['fields', idx, 'bit_range'], parsed.bit_range);
                                                                                }
                                                                                e.preventDefault();
                                                                                e.stopPropagation();
                                                                                setEditingFieldIndex(null);
                                                                                refocusFieldsTableSoon();
                                                                            }}
                                                                        />
                                                                    ) : (
                                                                        bits
                                                                    )}
                                                                </div>
                                                            </td>
                                                            <td
                                                                data-col-key="access"
                                                                className={`px-4 py-2 align-middle ${activeCell.rowIndex === idx && activeCell.key === 'access' ? 'bg-indigo-100/70 ring-2 ring-indigo-600 ring-inset' : ''}`}
                                                                onClick={(e) => {
                                                                    e.stopPropagation();
                                                                    setSelectedFieldIndex(idx);
                                                                    setHoveredFieldIndex(idx);
                                                                    setSelectedEditKey('access');
                                                                    setActiveCell({ rowIndex: idx, key: 'access' });
                                                                }}
                                                                onDoubleClick={startEditOnDoubleClick(idx, 'access')}
                                                            >
                                                                <div className="flex items-center h-10">
                                                                    {isEditingAccess ? (
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
                                                            <td
                                                                data-col-key="reset"
                                                                className={`px-4 py-2 font-mono text-gray-500 align-middle ${activeCell.rowIndex === idx && activeCell.key === 'reset' ? 'bg-indigo-100/70 ring-2 ring-indigo-600 ring-inset' : ''}`}
                                                                onClick={(e) => {
                                                                    e.stopPropagation();
                                                                    setSelectedFieldIndex(idx);
                                                                    setHoveredFieldIndex(idx);
                                                                    setSelectedEditKey('reset');
                                                                    setActiveCell({ rowIndex: idx, key: 'reset' });
                                                                }}
                                                                onDoubleClick={startEditOnDoubleClick(idx, 'reset')}
                                                            >
                                                                <div className="flex items-center h-10">
                                                                    {isEditingReset ? (
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
                                                            <td
                                                                data-col-key="description"
                                                                className={`px-6 py-2 text-gray-500 align-middle ${activeCell.rowIndex === idx && activeCell.key === 'description' ? 'bg-indigo-100/70 ring-2 ring-indigo-600 ring-inset' : ''}`}
                                                                onClick={(e) => {
                                                                    e.stopPropagation();
                                                                    setSelectedFieldIndex(idx);
                                                                    setHoveredFieldIndex(idx);
                                                                    setSelectedEditKey('description');
                                                                    setActiveCell({ rowIndex: idx, key: 'description' });
                                                                }}
                                                                onDoubleClick={startEditOnDoubleClick(idx, 'description')}
                                                            >
                                                                <div className="flex items-center h-10">
                                                                    {isEditingDescription ? (
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
                                                        </>
                                                    );
                                                })()}
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        </div>
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
