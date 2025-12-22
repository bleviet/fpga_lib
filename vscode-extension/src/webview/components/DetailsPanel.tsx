import React, { useEffect, useImperativeHandle, useMemo, useRef, useState } from 'react';
import { VSCodeDropdown, VSCodeOption, VSCodeTextField, VSCodeTextArea } from '@vscode/webview-ui-toolkit/react';
import { Register } from '../types/memoryMap';
import BitFieldVisualizer from './BitFieldVisualizer';
import AddressMapVisualizer from './AddressMapVisualizer';
import RegisterMapVisualizer from './RegisterMapVisualizer';

interface DetailsPanelProps {
    selectedType: 'memoryMap' | 'block' | 'register' | 'array' | null;
    selectedObject: any;
    selectionMeta?: {
        absoluteAddress?: number;
        relativeOffset?: number;
        focusDetails?: boolean;
    };
    onUpdate: (path: Array<string | number>, value: any) => void;
}

export type DetailsPanelHandle = {
    focus: () => void;
};

const ACCESS_OPTIONS = ['read-only', 'write-only', 'read-write', 'write-1-to-clear', 'read-write-1-to-clear'];

type EditKey = 'name' | 'bits' | 'access' | 'reset' | 'description';

type ActiveCell = { rowIndex: number; key: EditKey };

const COLUMN_ORDER: EditKey[] = ['name', 'bits', 'access', 'reset', 'description'];

type BlockEditKey = 'name' | 'base' | 'size' | 'usage' | 'description';
type BlockActiveCell = { rowIndex: number; key: BlockEditKey };
const BLOCK_COLUMN_ORDER: BlockEditKey[] = ['name', 'base', 'size', 'usage', 'description'];

type RegEditKey = 'name' | 'offset' | 'access' | 'description';
type RegActiveCell = { rowIndex: number; key: RegEditKey };
const REG_COLUMN_ORDER: RegEditKey[] = ['name', 'offset', 'access', 'description'];

const DetailsPanel = React.forwardRef<DetailsPanelHandle, DetailsPanelProps>(({ selectedType, selectedObject, selectionMeta, onUpdate }, ref) => {
    const [offsetText, setOffsetText] = useState<string>('');
    const [selectedFieldIndex, setSelectedFieldIndex] = useState<number>(-1);
    const [hoveredFieldIndex, setHoveredFieldIndex] = useState<number | null>(null);
    const [selectedEditKey, setSelectedEditKey] = useState<EditKey>('name');
    const [activeCell, setActiveCell] = useState<ActiveCell>({ rowIndex: -1, key: 'name' });
    const [blockActiveCell, setBlockActiveCell] = useState<BlockActiveCell>({ rowIndex: -1, key: 'name' });
    const [regActiveCell, setRegActiveCell] = useState<RegActiveCell>({ rowIndex: -1, key: 'name' });
    // Use unique key per register (e.g. blockIdx-regIdx or field name)
    const [nameDrafts, setNameDrafts] = useState<Record<string, string>>({});
    const [nameErrors, setNameErrors] = useState<Record<string, string | null>>({});
    const [bitsDrafts, setBitsDrafts] = useState<Record<number, string>>({});
    const [bitsErrors, setBitsErrors] = useState<Record<number, string | null>>({});

    // Helper: get bit width from [N:M] or [N]
    const parseBitsWidth = (bits: string): number | null => {
        const match = bits.trim().match(/^\[(\d+)(?::(\d+))?\]$/);
        if (!match) return null;
        const n = parseInt(match[1], 10);
        const m = match[2] ? parseInt(match[2], 10) : n;
        return Math.abs(n - m) + 1;
    };
    // Validate bits string: must be [N:M] or [N], N, M >= 0, N >= M
    const validateBitsString = (bits: string): string | null => {
        const trimmed = bits.trim();
        if (!/^\[\d+(?::\d+)?\]$/.test(trimmed)) {
            return 'Format must be [N:M] or [N]';
        }
        const match = trimmed.match(/\[(\d+)(?::(\d+))?\]/);
        if (!match) return 'Invalid format';
        const n = parseInt(match[1], 10);
        const m = match[2] ? parseInt(match[2], 10) : n;
        if (n < 0 || m < 0) return 'Bit indices must be >= 0';
        if (n < m) return 'MSB must be >= LSB';
        return null;
    };
    const [resetDrafts, setResetDrafts] = useState<Record<number, string>>({});
    const [resetErrors, setResetErrors] = useState<Record<number, string | null>>({});
    // Memory map states
    const [selectedBlockIndex, setSelectedBlockIndex] = useState<number>(-1);
    const [hoveredBlockIndex, setHoveredBlockIndex] = useState<number | null>(null);
    // Address block states
    const [selectedRegIndex, setSelectedRegIndex] = useState<number>(-1);
    const [hoveredRegIndex, setHoveredRegIndex] = useState<number | null>(null);
    const fieldsFocusRef = useRef<HTMLDivElement | null>(null);
    const blocksFocusRef = useRef<HTMLDivElement | null>(null);
    const regsFocusRef = useRef<HTMLDivElement | null>(null);

    useImperativeHandle(
        ref,
        () => ({
            focus: () => {
                if (selectedType === 'register') {
                    fieldsFocusRef.current?.focus();
                    return;
                }
                if (selectedType === 'memoryMap') {
                    blocksFocusRef.current?.focus();
                    return;
                }
                if (selectedType === 'block') {
                    regsFocusRef.current?.focus();
                    return;
                }
                // Fallback: focus whichever exists.
                fieldsFocusRef.current?.focus();
                blocksFocusRef.current?.focus();
                regsFocusRef.current?.focus();
            },
        }),
        [selectedType]
    );

    const refocusFieldsTableSoon = () => {
        window.setTimeout(() => {
            fieldsFocusRef.current?.focus();
        }, 0);
    };

    const refocusBlocksTableSoon = () => {
        window.setTimeout(() => {
            blocksFocusRef.current?.focus();
        }, 0);
    };

    const refocusRegsTableSoon = () => {
        window.setTimeout(() => {
            regsFocusRef.current?.focus();
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

    // Only shift focus into this panel when explicitly requested (e.g. Outline Enter/Right/l).
    useEffect(() => {
        if (!selectionMeta?.focusDetails) return;
        const id = window.setTimeout(() => {
            if (selectedType === 'register') fieldsFocusRef.current?.focus();
            if (selectedType === 'memoryMap') blocksFocusRef.current?.focus();
            if (selectedType === 'block') regsFocusRef.current?.focus();
        }, 0);
        return () => window.clearTimeout(id);
    }, [selectionMeta?.focusDetails, selectedType, (selectedObject as any)?.name]);

    const focusFieldEditor = (rowIndex: number, key: EditKey) => {
        window.setTimeout(() => {
            const row = document.querySelector(`tr[data-field-idx="${rowIndex}"]`) as HTMLElement | null;
            const el = row?.querySelector(`[data-edit-key="${key}"]`) as HTMLElement | null;
            try {
                el?.focus();
            } catch {
                // ignore
            }
        }, 0);
    };

    // Escape should return focus from an inline editor back to its table container.
    useEffect(() => {
        const onKeyDown = (e: KeyboardEvent) => {
            if (e.key !== 'Escape') return;

            const activeEl = document.activeElement as HTMLElement | null;
            if (!activeEl) return;

            const inFields = !!fieldsFocusRef.current && fieldsFocusRef.current.contains(activeEl) && activeEl !== fieldsFocusRef.current;
            const inBlocks = !!blocksFocusRef.current && blocksFocusRef.current.contains(activeEl) && activeEl !== blocksFocusRef.current;
            const inRegs = !!regsFocusRef.current && regsFocusRef.current.contains(activeEl) && activeEl !== regsFocusRef.current;
            if (!inFields && !inBlocks && !inRegs) return;

            e.preventDefault();
            e.stopPropagation();
            try {
                (activeEl as any).blur?.();
            } catch {
                // ignore
            }
            if (inFields) refocusFieldsTableSoon();
            if (inBlocks) refocusBlocksTableSoon();
            if (inRegs) refocusRegsTableSoon();
        };
        window.addEventListener('keydown', onKeyDown);
        return () => window.removeEventListener('keydown', onKeyDown);
    }, []);


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
            const isDelete = keyLower === 'd' || e.key === 'Delete';
            if (!isArrow && !isEdit && !isDelete) return;

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
            if (isTypingTarget) return;

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
                focusFieldEditor(currentRow, currentKey);
                return;
            }

            if (isDelete) {
                if (currentRow < 0 || currentRow >= fields.length) return;
                e.preventDefault();
                e.stopPropagation();
                // Remove the field at currentRow and ensure fields is a valid array
                const newFields = fields.filter((_, idx) => idx !== currentRow);
                onUpdate(['fields'], newFields);
                // Move selection to previous or next field
                const nextRow = currentRow > 0 ? currentRow - 1 : (newFields.length > 0 ? 0 : -1);
                setSelectedFieldIndex(nextRow);
                setHoveredFieldIndex(nextRow);
                setActiveCell({ rowIndex: nextRow, key: currentKey });
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
    }, [isRegister, fields.length, selectedFieldIndex, selectedEditKey, activeCell, onUpdate]);

    // Keyboard shortcuts for Memory Map blocks table (when focused):
    // - Arrow keys or Vim h/j/k/l to move active cell
    // - F2 or e focuses the editor for the active cell
    useEffect(() => {
        if (selectedType !== 'memoryMap') return;

        const blocks = (selectedObject as any)?.address_blocks || (selectedObject as any)?.addressBlocks || [];
        if (!Array.isArray(blocks) || blocks.length === 0) return;

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
            const isDelete = keyLower === 'd' || e.key === 'Delete';
            if (!isArrow && !isEdit && !isDelete) return;

            if (e.ctrlKey || e.metaKey) return;

            const activeEl = document.activeElement as HTMLElement | null;
            const isInBlocksArea = !!blocksFocusRef.current && !!activeEl && (activeEl === blocksFocusRef.current || blocksFocusRef.current.contains(activeEl));
            if (!isInBlocksArea) return;

            const target = e.target as HTMLElement | null;
            const isTypingTarget = !!target?.closest(
                'input, textarea, select, [contenteditable="true"], vscode-text-field, vscode-text-area, vscode-dropdown'
            );
            if (isTypingTarget) return;

            const scrollToCell = (rowIndex: number, key: BlockEditKey) => {
                window.setTimeout(() => {
                    const row = document.querySelector(`tr[data-block-idx="${rowIndex}"]`) as HTMLElement | null;
                    row?.scrollIntoView({ block: 'nearest' });
                    const cell = row?.querySelector(`td[data-col-key="${key}"]`) as HTMLElement | null;
                    cell?.scrollIntoView({ block: 'nearest', inline: 'nearest' });
                }, 0);
            };

            const focusEditor = (rowIndex: number, key: BlockEditKey) => {
                window.setTimeout(() => {
                    const row = document.querySelector(`tr[data-block-idx="${rowIndex}"]`) as HTMLElement | null;
                    const editor = row?.querySelector(`[data-edit-key="${key}"]`) as HTMLElement | null;
                    editor?.focus?.();
                }, 0);
            };

            const currentRow = blockActiveCell.rowIndex >= 0 ? blockActiveCell.rowIndex : (selectedBlockIndex >= 0 ? selectedBlockIndex : 0);
            const currentKey: BlockEditKey = BLOCK_COLUMN_ORDER.includes(blockActiveCell.key) ? blockActiveCell.key : 'name';

            if (isEdit) {
                if (currentRow < 0 || currentRow >= blocks.length) return;
                e.preventDefault();
                e.stopPropagation();
                setSelectedBlockIndex(currentRow);
                setHoveredBlockIndex(currentRow);
                setBlockActiveCell({ rowIndex: currentRow, key: currentKey });
                focusEditor(currentRow, currentKey);
                return;
            }

            if (isDelete) {
                if (currentRow < 0 || currentRow >= blocks.length) return;
                e.preventDefault();
                e.stopPropagation();
                // Remove the block at currentRow and ensure addressBlocks is a valid array
                const newBlocks = blocks.filter((_, idx) => idx !== currentRow);
                onUpdate(['addressBlocks'], newBlocks);
                // Move selection to previous or next block
                const nextRow = currentRow > 0 ? currentRow - 1 : (newBlocks.length > 0 ? 0 : -1);
                setSelectedBlockIndex(nextRow);
                setHoveredBlockIndex(nextRow);
                setBlockActiveCell({ rowIndex: nextRow, key: currentKey });
                return;
            }

            e.preventDefault();
            e.stopPropagation();

            const isVertical = normalizedKey === 'ArrowUp' || normalizedKey === 'ArrowDown';
            const delta = normalizedKey === 'ArrowUp' || normalizedKey === 'ArrowLeft' ? -1 : 1;

            if (isVertical) {
                const nextRow = Math.max(0, Math.min(blocks.length - 1, currentRow + delta));
                setSelectedBlockIndex(nextRow);
                setHoveredBlockIndex(nextRow);
                setBlockActiveCell({ rowIndex: nextRow, key: currentKey });
                scrollToCell(nextRow, currentKey);
                return;
            }

            const currentCol = Math.max(0, BLOCK_COLUMN_ORDER.indexOf(currentKey));
            const nextCol = Math.max(0, Math.min(BLOCK_COLUMN_ORDER.length - 1, currentCol + delta));
            const nextKey = BLOCK_COLUMN_ORDER[nextCol] ?? 'name';
            setSelectedBlockIndex(currentRow);
            setHoveredBlockIndex(currentRow);
            setBlockActiveCell({ rowIndex: currentRow, key: nextKey });
            scrollToCell(currentRow, nextKey);
        };

        window.addEventListener('keydown', onKeyDown);
        return () => window.removeEventListener('keydown', onKeyDown);
    }, [selectedType, selectedObject, selectedBlockIndex, hoveredBlockIndex, blockActiveCell]);

    // Keyboard shortcuts for Address Block registers table (when focused):
    // - Arrow keys or Vim h/j/k/l to move active cell
    // - F2 or e focuses the editor for the active cell
    useEffect(() => {
        if (selectedType !== 'block') return;

        const registers = (selectedObject as any)?.registers || [];
        if (!Array.isArray(registers) || registers.length === 0) return;

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
            const isDelete = keyLower === 'd' || e.key === 'Delete';
            if (!isArrow && !isEdit && !isDelete) return;

            if (e.ctrlKey || e.metaKey) return;

            const activeEl = document.activeElement as HTMLElement | null;
            const isInRegsArea = !!regsFocusRef.current && !!activeEl && (activeEl === regsFocusRef.current || regsFocusRef.current.contains(activeEl));
            if (!isInRegsArea) return;

            const target = e.target as HTMLElement | null;
            const isTypingTarget = !!target?.closest(
                'input, textarea, select, [contenteditable="true"], vscode-text-field, vscode-text-area, vscode-dropdown'
            );
            if (isTypingTarget) return;

            const scrollToCell = (rowIndex: number, key: RegEditKey) => {
                window.setTimeout(() => {
                    const row = document.querySelector(`tr[data-reg-idx="${rowIndex}"]`) as HTMLElement | null;
                    row?.scrollIntoView({ block: 'nearest' });
                    const cell = row?.querySelector(`td[data-col-key="${key}"]`) as HTMLElement | null;
                    cell?.scrollIntoView({ block: 'nearest', inline: 'nearest' });
                }, 0);
            };

            const focusEditor = (rowIndex: number, key: RegEditKey) => {
                window.setTimeout(() => {
                    const row = document.querySelector(`tr[data-reg-idx="${rowIndex}"]`) as HTMLElement | null;
                    const editor = row?.querySelector(`[data-edit-key="${key}"]`) as HTMLElement | null;
                    editor?.focus?.();
                }, 0);
            };

            const currentRow = regActiveCell.rowIndex >= 0 ? regActiveCell.rowIndex : (selectedRegIndex >= 0 ? selectedRegIndex : 0);
            const currentKey: RegEditKey = REG_COLUMN_ORDER.includes(regActiveCell.key) ? regActiveCell.key : 'name';

            if (isEdit) {
                if (currentRow < 0 || currentRow >= registers.length) return;
                e.preventDefault();
                e.stopPropagation();
                setSelectedRegIndex(currentRow);
                setHoveredRegIndex(currentRow);
                setRegActiveCell({ rowIndex: currentRow, key: currentKey });
                focusEditor(currentRow, currentKey);
                return;
            }

            if (isDelete) {
                if (currentRow < 0 || currentRow >= registers.length) return;
                e.preventDefault();
                e.stopPropagation();
                // Remove the register at currentRow and ensure registers is a valid array
                const newRegs = registers.filter((_, idx) => idx !== currentRow);
                onUpdate(['registers'], newRegs);
                // Move selection to previous or next register
                const nextRow = currentRow > 0 ? currentRow - 1 : (newRegs.length > 0 ? 0 : -1);
                setSelectedRegIndex(nextRow);
                setHoveredRegIndex(nextRow);
                setRegActiveCell({ rowIndex: nextRow, key: currentKey });
                return;
            }

            e.preventDefault();
            e.stopPropagation();

            const isVertical = normalizedKey === 'ArrowUp' || normalizedKey === 'ArrowDown';
            const delta = normalizedKey === 'ArrowUp' || normalizedKey === 'ArrowLeft' ? -1 : 1;

            if (isVertical) {
                const nextRow = Math.max(0, Math.min(registers.length - 1, currentRow + delta));
                setSelectedRegIndex(nextRow);
                setHoveredRegIndex(nextRow);
                setRegActiveCell({ rowIndex: nextRow, key: currentKey });
                scrollToCell(nextRow, currentKey);
                return;
            }

            const currentCol = Math.max(0, REG_COLUMN_ORDER.indexOf(currentKey));
            const nextCol = Math.max(0, Math.min(REG_COLUMN_ORDER.length - 1, currentCol + delta));
            const nextKey = REG_COLUMN_ORDER[nextCol] ?? 'name';
            setSelectedRegIndex(currentRow);
            setHoveredRegIndex(currentRow);
            setRegActiveCell({ rowIndex: currentRow, key: nextKey });
            scrollToCell(currentRow, nextKey);
        };

        window.addEventListener('keydown', onKeyDown);
        return () => window.removeEventListener('keydown', onKeyDown);
    }, [selectedType, selectedObject, selectedRegIndex, hoveredRegIndex, regActiveCell]);

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

    // Clamp selection/active cell for Memory Map blocks.
    useEffect(() => {
        if (selectedType !== 'memoryMap') {
            setSelectedBlockIndex(-1);
            setBlockActiveCell({ rowIndex: -1, key: 'name' });
            return;
        }
        const blocks = (selectedObject as any)?.address_blocks || (selectedObject as any)?.addressBlocks || [];
        if (!Array.isArray(blocks) || blocks.length === 0) {
            setSelectedBlockIndex(-1);
            setBlockActiveCell({ rowIndex: -1, key: 'name' });
            return;
        }
        setSelectedBlockIndex((prev) => {
            if (prev < 0) return 0;
            if (prev >= blocks.length) return blocks.length - 1;
            return prev;
        });
        setBlockActiveCell((prev) => {
            const rowIndex = prev.rowIndex < 0 ? 0 : Math.min(blocks.length - 1, prev.rowIndex);
            const key = BLOCK_COLUMN_ORDER.includes(prev.key) ? prev.key : 'name';
            return { rowIndex, key };
        });
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [selectedType, (selectedObject as any)?.name, ((selectedObject as any)?.address_blocks || (selectedObject as any)?.addressBlocks || []).length]);

    // Clamp selection/active cell for Address Block registers.
    useEffect(() => {
        if (selectedType !== 'block') {
            setSelectedRegIndex(-1);
            setRegActiveCell({ rowIndex: -1, key: 'name' });
            return;
        }
        const registers = (selectedObject as any)?.registers || [];
        if (!Array.isArray(registers) || registers.length === 0) {
            setSelectedRegIndex(-1);
            setRegActiveCell({ rowIndex: -1, key: 'name' });
            return;
        }
        setSelectedRegIndex((prev) => {
            if (prev < 0) return 0;
            if (prev >= registers.length) return registers.length - 1;
            return prev;
        });
        setRegActiveCell((prev) => {
            const rowIndex = prev.rowIndex < 0 ? 0 : Math.min(registers.length - 1, prev.rowIndex);
            const key = REG_COLUMN_ORDER.includes(prev.key) ? prev.key : 'name';
            return { rowIndex, key };
        });
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [selectedType, (selectedObject as any)?.name, ((selectedObject as any)?.registers || []).length]);

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

    const validateVhdlIdentifier = (name: string): string | null => {
        const trimmed = name.trim();
        if (!trimmed) return 'Name is required';
        // VHDL basic identifier (common convention):
        // - starts with a letter
        // - contains only letters, digits, and underscores
        // - no consecutive underscores
        // - no trailing underscore
        const re = /^[A-Za-z](?:[A-Za-z0-9]*(_[A-Za-z0-9]+)*)?$/;
        if (!re.test(trimmed)) {
            return 'VHDL name must start with a letter and contain only letters, digits, and single underscores';
        }
        return null;
    };

    const getFieldBitWidth = (f: any): number => {
        const w = Number(f?.bit_width);
        if (Number.isFinite(w) && w > 0) return w;
        const br = f?.bit_range;
        if (Array.isArray(br) && br.length === 2) {
            const msb = Number(br[0]);
            const lsb = Number(br[1]);
            if (Number.isFinite(msb) && Number.isFinite(lsb)) return Math.abs(msb - lsb) + 1;
        }
        return 1;
    };

    const validateResetForField = (f: any, value: number | null): string | null => {
        if (value === null) return null;
        if (!Number.isFinite(value)) return 'Invalid number';
        if (value < 0) return 'Reset must be >= 0';
        const width = getFieldBitWidth(f);
        // Avoid overflow in shifts; for typical widths (<=32) this is safe.
        const max = width >= 53 ? Number.MAX_SAFE_INTEGER : Math.pow(2, width) - 1;
        if (value > max) return `Reset too large for ${width} bit(s)`;
        return null;
    };

    if (!selectedObject) {
        return <div className="flex items-center justify-center h-full vscode-muted text-sm">Select an item to view details</div>;
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

        const getFieldKey = (field: any, idx: number) => {
            // Prefer a unique name if available, else fallback to index
            return field && field.name ? `${field.name}` : `idx-${idx}`;
        };
        const ensureDraftsInitialized = (idx: number) => {
            const f = fields[idx];
            if (!f) return;
            const key = getFieldKey(f, idx);
            setNameDrafts((prev) => (prev[key] !== undefined ? prev : { ...prev, [key]: String(f.name ?? '') }));
            setBitsDrafts((prev) => (prev[idx] !== undefined ? prev : { ...prev, [idx]: toBits(f) }));
            setResetDrafts((prev) => {
                if (prev[idx] !== undefined) return prev;
                const v = f?.reset_value;
                const display = v !== null && v !== undefined ? `0x${Number(v).toString(16).toUpperCase()}` : '0x0';
                return { ...prev, [idx]: display };
            });
        };

        const moveSelectedField = (delta: -1 | 1) => {
            const idx = selectedFieldIndex;
            if (idx < 0) return;
            const next = idx + delta;
            if (next < 0 || next >= fields.length) return;
            onUpdate(['__op', 'field-move'], { index: idx, delta });
            setSelectedFieldIndex(next);
            setHoveredFieldIndex(next);
        };

        return (
            <div className="flex flex-col w-full h-full min-h-0">
                {/* --- Register Header and BitFieldVisualizer --- */}
                <div className="vscode-surface border-b vscode-border p-8 flex flex-col gap-6 shrink-0 relative overflow-hidden">
                    <div className="absolute inset-0 fpga-grid-bg bg-[size:24px_24px] pointer-events-none"></div>
                    <div className="flex justify-between items-start relative z-10">
                        <div>
                            <h2 className="text-2xl font-bold font-mono tracking-tight">{regObj.name}</h2>
                            <p className="vscode-muted text-sm mt-1 max-w-2xl">{regObj.description}</p>
                        </div>
                    </div>
                    <div className="w-full relative z-10 mt-2 select-none">
                        <BitFieldVisualizer
                            fields={fields}
                            hoveredFieldIndex={hoveredFieldIndex}
                            setHoveredFieldIndex={setHoveredFieldIndex}
                            registerSize={32}
                            layout="pro"
                            onUpdateFieldReset={(fieldIndex, resetValue) => {
                                onUpdate(['fields', fieldIndex, 'reset_value'], resetValue);
                            }}
                        />
                    </div>
                </div>
                {/* --- Main Content: Table and Properties --- */}
                <div className="flex-1 flex overflow-hidden min-h-0">
                    <div className="flex-1 vscode-surface border-r vscode-border min-h-0 flex flex-col">
                        <div className="shrink-0 px-4 py-2 border-b vscode-border vscode-surface flex items-center justify-end gap-1">
                            <button
                                className="p-2 rounded-md transition-colors disabled:opacity-40 vscode-icon-button"
                                onClick={() => moveSelectedField(-1)}
                                disabled={selectedFieldIndex <= 0}
                                title="Move field up"
                                type="button"
                            >
                                <span className="codicon codicon-chevron-up"></span>
                            </button>
                            <button
                                className="p-2 rounded-md transition-colors disabled:opacity-40 vscode-icon-button"
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
                                <thead className="vscode-surface-alt text-xs font-semibold vscode-muted uppercase tracking-wider sticky top-0 z-10 shadow-sm">
                                    <tr className="h-12">
                                        <th className="px-6 py-3 border-b vscode-border align-middle">Name</th>
                                        <th className="px-4 py-3 border-b vscode-border align-middle">Bit(s)</th>
                                        <th className="px-4 py-3 border-b vscode-border align-middle">Access</th>
                                        <th className="px-4 py-3 border-b vscode-border align-middle">Reset</th>
                                        <th className="px-6 py-3 border-b vscode-border align-middle">Description</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y vscode-border text-sm">
                                    {fields.map((field, idx) => {
                                        const bits = toBits(field);
                                        const color = getFieldColor(idx);
                                        const resetDisplay =
                                            field.reset_value !== null && field.reset_value !== undefined
                                                ? `0x${Number(field.reset_value).toString(16).toUpperCase()}`
                                                : '';

                                        // Helper to get a unique key for this field
                                        const fieldKey = field && field.name ? `${field.name}` : `idx-${idx}`;
                                        const nameValue = nameDrafts[fieldKey] ?? String(field.name ?? '');
                                        const nameErr = nameErrors[fieldKey] ?? null;
                                        const bitsValue = bitsDrafts[idx] ?? bits;
                                        const bitsErr = bitsErrors[idx] ?? null;
                                        const resetValue = resetDrafts[idx] ?? (resetDisplay || '0x0');
                                        const resetErr = resetErrors[idx] ?? null;

                                        return (
                                            <tr
                                                key={idx}
                                                data-field-idx={idx}
                                                className={`group transition-colors border-l-4 border-transparent h-12 ${idx === selectedFieldIndex ? 'vscode-focus-border vscode-row-selected' : idx === hoveredFieldIndex ? 'vscode-focus-border vscode-row-hover' : ''}`}
                                                onMouseEnter={() => {
                                                    setHoveredFieldIndex(idx);
                                                }}
                                                onMouseLeave={() => setHoveredFieldIndex(null)}
                                                onClick={() => {
                                                    setSelectedFieldIndex(idx);
                                                    setHoveredFieldIndex(idx);
                                                    setActiveCell((prev) => ({ rowIndex: idx, key: prev.key }));
                                                    ensureDraftsInitialized(idx);
                                                }}
                                                id={`row-${field.name?.toLowerCase().replace(/[^a-z0-9_]/g, '-')}`}
                                            >
                                                <>
                                                    <td
                                                        data-col-key="name"
                                                        className={`px-6 py-2 font-medium align-middle ${activeCell.rowIndex === idx && activeCell.key === 'name' ? 'vscode-cell-active' : ''}`}
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            ensureDraftsInitialized(idx);
                                                            setSelectedFieldIndex(idx);
                                                            setHoveredFieldIndex(idx);
                                                            setSelectedEditKey('name');
                                                            setActiveCell({ rowIndex: idx, key: 'name' });
                                                        }}
                                                    >
                                                        <div className="flex flex-col justify-center">
                                                            <div className="flex items-center gap-2 h-10">
                                                                <div
                                                                    className={`w-2.5 h-2.5 rounded-sm`}
                                                                    style={{ backgroundColor: color === 'gray' ? '#e5e7eb' : (colorMap && colorMap[color]) || color }}
                                                                ></div>
                                                                <VSCodeTextField
                                                                    data-edit-key="name"
                                                                    className="flex-1"
                                                                    value={nameValue}
                                                                    onFocus={() => {
                                                                        ensureDraftsInitialized(idx);
                                                                        setSelectedFieldIndex(idx);
                                                                        setHoveredFieldIndex(idx);
                                                                        setSelectedEditKey('name');
                                                                        setActiveCell({ rowIndex: idx, key: 'name' });
                                                                    }}
                                                                    onInput={(e: any) => {
                                                                        const next = String(e.target.value ?? '');
                                                                        setNameDrafts((prev) => ({ ...prev, [fieldKey]: next }));
                                                                        const err = validateVhdlIdentifier(next);
                                                                        setNameErrors((prev) => ({ ...prev, [fieldKey]: err }));
                                                                        if (!err) onUpdate(['fields', idx, 'name'], next.trim());
                                                                    }}
                                                                />
                                                            </div>
                                                            {nameErr ? <div className="text-xs vscode-error mt-1">{nameErr}</div> : null}
                                                        </div>
                                                    </td>
                                                    <td
                                                        data-col-key="bits"
                                                        className={`px-4 py-2 font-mono vscode-muted align-middle ${activeCell.rowIndex === idx && activeCell.key === 'bits' ? 'vscode-cell-active' : ''}`}
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            ensureDraftsInitialized(idx);
                                                            setSelectedFieldIndex(idx);
                                                            setHoveredFieldIndex(idx);
                                                            setSelectedEditKey('bits');
                                                            setActiveCell({ rowIndex: idx, key: 'bits' });
                                                        }}
                                                    >
                                                        <div className="flex items-center h-10">
                                                            <div className="flex flex-col w-full">
                                                                <VSCodeTextField
                                                                    data-edit-key="bits"
                                                                    className="w-full font-mono"
                                                                    value={bitsValue}
                                                                    onFocus={() => {
                                                                        ensureDraftsInitialized(idx);
                                                                        setSelectedFieldIndex(idx);
                                                                        setHoveredFieldIndex(idx);
                                                                        setSelectedEditKey('bits');
                                                                        setActiveCell({ rowIndex: idx, key: 'bits' });
                                                                    }}
                                                                    onInput={(e: any) => {
                                                                        const next = String(e.target.value ?? '');
                                                                        setBitsDrafts((prev) => ({ ...prev, [idx]: next }));
                                                                        let err = validateBitsString(next);
                                                                        // Overfill validation
                                                                        if (!err) {
                                                                            const thisWidth = parseBitsWidth(next);
                                                                            if (thisWidth !== null) {
                                                                                // Calculate total bits used if this field is set to new value
                                                                                let total = 0;
                                                                                for (let i = 0; i < fields.length; ++i) {
                                                                                    if (i === idx) {
                                                                                        total += thisWidth;
                                                                                    } else {
                                                                                        // Use draft if present, else current
                                                                                        const b = bitsDrafts[i] ?? toBits(fields[i]);
                                                                                        const w = parseBitsWidth(b);
                                                                                        if (w) total += w;
                                                                                    }
                                                                                }
                                                                                const regSize = reg?.size || 32;
                                                                                if (total > regSize) {
                                                                                    err = `Bit fields overflow register (${total} > ${regSize})`;
                                                                                }
                                                                            }
                                                                        }
                                                                        setBitsErrors((prev) => ({ ...prev, [idx]: err }));
                                                                        if (!err) {
                                                                            const parsed = parseBitsInput(next);
                                                                            if (parsed) {
                                                                                onUpdate(['fields', idx, 'bit_offset'], parsed.bit_offset);
                                                                                onUpdate(['fields', idx, 'bit_width'], parsed.bit_width);
                                                                                onUpdate(['fields', idx, 'bit_range'], parsed.bit_range);
                                                                            }
                                                                        }
                                                                    }}
                                                                />
                                                                {bitsErr ? <div className="text-xs vscode-error mt-1">{bitsErr}</div> : null}
                                                            </div>
                                                        </div>
                                                    </td>
                                                    <td
                                                        data-col-key="access"
                                                        className={`px-4 py-2 align-middle ${activeCell.rowIndex === idx && activeCell.key === 'access' ? 'vscode-cell-active' : ''}`}
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            ensureDraftsInitialized(idx);
                                                            setSelectedFieldIndex(idx);
                                                            setHoveredFieldIndex(idx);
                                                            setSelectedEditKey('access');
                                                            setActiveCell({ rowIndex: idx, key: 'access' });
                                                        }}
                                                    >
                                                        <div className="flex items-center h-10">
                                                            <VSCodeDropdown
                                                                data-edit-key="access"
                                                                value={field.access || 'read-write'}
                                                                className="w-full"
                                                                onFocus={() => {
                                                                    setSelectedFieldIndex(idx);
                                                                    setHoveredFieldIndex(idx);
                                                                    setSelectedEditKey('access');
                                                                    setActiveCell({ rowIndex: idx, key: 'access' });
                                                                }}
                                                                onInput={(e: any) => onUpdate(['fields', idx, 'access'], e.target.value)}
                                                            >
                                                                {ACCESS_OPTIONS.map((opt) => (
                                                                    <VSCodeOption key={opt} value={opt}>
                                                                        {opt}
                                                                    </VSCodeOption>
                                                                ))}
                                                            </VSCodeDropdown>
                                                        </div>
                                                    </td>
                                                    <td
                                                        data-col-key="reset"
                                                        className={`px-4 py-2 font-mono vscode-muted align-middle ${activeCell.rowIndex === idx && activeCell.key === 'reset' ? 'vscode-cell-active' : ''}`}
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            ensureDraftsInitialized(idx);
                                                            setSelectedFieldIndex(idx);
                                                            setHoveredFieldIndex(idx);
                                                            setSelectedEditKey('reset');
                                                            setActiveCell({ rowIndex: idx, key: 'reset' });
                                                        }}
                                                    >
                                                        <div className="flex flex-col justify-center h-10">
                                                            <VSCodeTextField
                                                                data-edit-key="reset"
                                                                className="w-full font-mono"
                                                                value={resetValue}
                                                                onFocus={() => {
                                                                    ensureDraftsInitialized(idx);
                                                                    setSelectedFieldIndex(idx);
                                                                    setHoveredFieldIndex(idx);
                                                                    setSelectedEditKey('reset');
                                                                    setActiveCell({ rowIndex: idx, key: 'reset' });
                                                                }}
                                                                onInput={(e: any) => {
                                                                    const raw = String(e.target.value ?? '');
                                                                    setResetDrafts((prev) => ({ ...prev, [idx]: raw }));

                                                                    const trimmed = raw.trim();
                                                                    if (!trimmed) {
                                                                        setResetErrors((prev) => ({ ...prev, [idx]: null }));
                                                                        onUpdate(['fields', idx, 'reset_value'], null);
                                                                        return;
                                                                    }

                                                                    const parsed = parseReset(raw);
                                                                    const err = validateResetForField(field, parsed);
                                                                    setResetErrors((prev) => ({ ...prev, [idx]: err }));
                                                                    if (err) return;
                                                                    if (parsed !== null) onUpdate(['fields', idx, 'reset_value'], parsed);
                                                                }}
                                                            />
                                                            {resetErr ? <div className="text-xs vscode-error mt-1">{resetErr}</div> : null}
                                                        </div>
                                                    </td>
                                                    <td
                                                        data-col-key="description"
                                                        className={`px-6 py-2 vscode-muted align-middle ${activeCell.rowIndex === idx && activeCell.key === 'description' ? 'vscode-cell-active' : ''}`}
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            ensureDraftsInitialized(idx);
                                                            setSelectedFieldIndex(idx);
                                                            setHoveredFieldIndex(idx);
                                                            setSelectedEditKey('description');
                                                            setActiveCell({ rowIndex: idx, key: 'description' });
                                                        }}
                                                    >
                                                        <div className="flex items-center h-10">
                                                            <VSCodeTextArea
                                                                data-edit-key="description"
                                                                className="w-full"
                                                                rows={2}
                                                                value={field.description || ''}
                                                                onFocus={() => {
                                                                    setSelectedFieldIndex(idx);
                                                                    setHoveredFieldIndex(idx);
                                                                    setSelectedEditKey('description');
                                                                    setActiveCell({ rowIndex: idx, key: 'description' });
                                                                }}
                                                                onInput={(e: any) => onUpdate(['fields', idx, 'description'], e.target.value)}
                                                            />
                                                        </div>
                                                    </td>
                                                </>
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
        const blocks = map.address_blocks || map.addressBlocks || [];

        const toHex = (n: number) => `0x${Math.max(0, n).toString(16).toUpperCase()}`;

        const getBlockColor = (idx: number) => {
            const colorKeys = ['blue', 'orange', 'emerald', 'pink', 'purple', 'cyan', 'amber', 'rose'];
            return colorKeys[idx % colorKeys.length];
        };

        return (
            <div className="flex flex-col w-full h-full min-h-0">
                {/* Memory Map Header and Address Visualizer */}
                <div className="vscode-surface border-b vscode-border p-8 flex flex-col gap-6 shrink-0 relative overflow-hidden">
                    {/* <div className="absolute inset-0 fpga-grid-bg bg-[size:24px_24px] pointer-events-none"></div> */}
                    <div className="flex justify-between items-start relative z-10">
                        <div>
                            <h2 className="text-2xl font-bold font-mono tracking-tight">{map.name || 'Memory Map'}</h2>
                            <p className="vscode-muted text-sm mt-1 max-w-2xl">{map.description || 'Address space layout'}</p>
                        </div>
                    </div>
                    <div className="w-full relative z-10 mt-2 select-none">
                        <AddressMapVisualizer
                            blocks={blocks}
                            hoveredBlockIndex={hoveredBlockIndex}
                            setHoveredBlockIndex={setHoveredBlockIndex}
                        />
                    </div>
                </div>
                {/* Address Blocks Table */}
                <div className="flex-1 flex overflow-hidden min-h-0">
                    <div className="flex-1 vscode-surface min-h-0 flex flex-col">
                        <div
                            ref={blocksFocusRef}
                            tabIndex={0}
                            data-blocks-table="true"
                            className="flex-1 overflow-auto min-h-0 outline-none focus:outline-none"
                        >
                            <table className="w-full text-left border-collapse table-fixed">
                                <colgroup>
                                    <col className="w-[25%] min-w-[200px]" />
                                    <col className="w-[20%] min-w-[120px]" />
                                    <col className="w-[15%] min-w-[100px]" />
                                    <col className="w-[15%] min-w-[100px]" />
                                    <col className="w-[25%]" />
                                </colgroup>
                                <thead className="vscode-surface-alt text-xs font-semibold vscode-muted uppercase tracking-wider sticky top-0 z-10 shadow-sm">
                                    <tr className="h-12">
                                        <th className="px-6 py-3 border-b vscode-border align-middle">Name</th>
                                        <th className="px-4 py-3 border-b vscode-border align-middle">Base Address</th>
                                        <th className="px-4 py-3 border-b vscode-border align-middle">Size</th>
                                        <th className="px-4 py-3 border-b vscode-border align-middle">Usage</th>
                                        <th className="px-6 py-3 border-b vscode-border align-middle">Description</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y vscode-border text-sm">
                                    {blocks.map((block: any, idx: number) => {
                                        const color = getBlockColor(idx);
                                        const base = block.base_address ?? block.offset ?? 0;
                                        const size = block.size ?? block.range ?? 4096;
                                        const colorMap: Record<string, string> = {
                                            blue: '#3b82f6',
                                            orange: '#f97316',
                                            emerald: '#10b981',
                                            pink: '#ec4899',
                                            purple: '#a855f7',
                                            cyan: '#06b6d4',
                                            amber: '#f59e0b',
                                            rose: '#f43f5e',
                                        };

                                        return (
                                            <tr
                                                key={idx}
                                                data-block-idx={idx}
                                                className={`group transition-colors border-l-4 border-transparent h-12 ${idx === selectedBlockIndex ? 'vscode-focus-border vscode-row-selected' :
                                                    idx === hoveredBlockIndex ? 'vscode-focus-border vscode-row-hover' : ''
                                                    }`}
                                                onMouseEnter={() => setHoveredBlockIndex(idx)}
                                                onMouseLeave={() => setHoveredBlockIndex(null)}
                                                onClick={() => {
                                                    setSelectedBlockIndex(idx);
                                                    setHoveredBlockIndex(idx);
                                                    setBlockActiveCell((prev) => ({ rowIndex: idx, key: prev.key }));
                                                }}
                                            >
                                                <td
                                                    data-col-key="name"
                                                    className={`px-6 py-2 font-medium align-middle ${blockActiveCell.rowIndex === idx && blockActiveCell.key === 'name' ? 'vscode-cell-active' : ''}`}
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        setSelectedBlockIndex(idx);
                                                        setHoveredBlockIndex(idx);
                                                        setBlockActiveCell({ rowIndex: idx, key: 'name' });
                                                    }}
                                                >
                                                    <div className="flex items-center gap-2">
                                                        <div className="w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: colorMap[color] || color }}></div>
                                                        <VSCodeTextField
                                                            data-edit-key="name"
                                                            className="flex-1"
                                                            value={block.name || ''}
                                                            onInput={(e: any) => onUpdate(['addressBlocks', idx, 'name'], e.target.value)}
                                                        />
                                                    </div>
                                                </td>
                                                <td
                                                    data-col-key="base"
                                                    className={`px-4 py-2 font-mono vscode-muted align-middle ${blockActiveCell.rowIndex === idx && blockActiveCell.key === 'base' ? 'vscode-cell-active' : ''}`}
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        setSelectedBlockIndex(idx);
                                                        setHoveredBlockIndex(idx);
                                                        setBlockActiveCell({ rowIndex: idx, key: 'base' });
                                                    }}
                                                >
                                                    <VSCodeTextField
                                                        data-edit-key="base"
                                                        className="w-full font-mono"
                                                        value={toHex(base)}
                                                        onInput={(e: any) => {
                                                            const val = Number.parseInt(e.target.value, 0);
                                                            if (!Number.isNaN(val)) {
                                                                onUpdate(['addressBlocks', idx, 'offset'], val);
                                                            }
                                                        }}
                                                    />
                                                </td>
                                                <td
                                                    data-col-key="size"
                                                    className={`px-4 py-2 font-mono vscode-muted align-middle ${blockActiveCell.rowIndex === idx && blockActiveCell.key === 'size' ? 'vscode-cell-active' : ''}`}
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        setSelectedBlockIndex(idx);
                                                        setHoveredBlockIndex(idx);
                                                        setBlockActiveCell({ rowIndex: idx, key: 'size' });
                                                    }}
                                                >
                                                    {size < 1024 ? `${size}B` : `${(size / 1024).toFixed(1)}KB`}
                                                </td>
                                                <td
                                                    data-col-key="usage"
                                                    className={`px-4 py-2 align-middle ${blockActiveCell.rowIndex === idx && blockActiveCell.key === 'usage' ? 'vscode-cell-active' : ''}`}
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        setSelectedBlockIndex(idx);
                                                        setHoveredBlockIndex(idx);
                                                        setBlockActiveCell({ rowIndex: idx, key: 'usage' });
                                                    }}
                                                >
                                                    <span className="px-2 py-0.5 rounded text-xs font-medium vscode-badge whitespace-nowrap">
                                                        {block.usage || 'register'}
                                                    </span>
                                                </td>
                                                <td
                                                    data-col-key="description"
                                                    className={`px-6 py-2 vscode-muted align-middle ${blockActiveCell.rowIndex === idx && blockActiveCell.key === 'description' ? 'vscode-cell-active' : ''}`}
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        setSelectedBlockIndex(idx);
                                                        setHoveredBlockIndex(idx);
                                                        setBlockActiveCell({ rowIndex: idx, key: 'description' });
                                                    }}
                                                >
                                                    <VSCodeTextArea
                                                        data-edit-key="description"
                                                        className="w-full"
                                                        rows={1}
                                                        value={block.description || ''}
                                                        onInput={(e: any) => onUpdate(['addressBlocks', idx, 'description'], e.target.value)}
                                                    />
                                                </td>
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

    if (selectedType === 'block') {
        const block = selectedObject as any;
        const registers = block.registers || [];
        const baseAddress = block.base_address ?? block.offset ?? 0;

        const toHex = (n: number) => `0x${Math.max(0, n).toString(16).toUpperCase()}`;

        const getRegColor = (idx: number) => {
            const colorKeys = ['blue', 'orange', 'emerald', 'pink', 'purple', 'cyan', 'amber', 'rose'];
            return colorKeys[idx % colorKeys.length];
        };

        return (
            <div className="flex flex-col w-full h-full min-h-0">
                {/* Address Block Header and Register Visualizer */}
                <div className="vscode-surface border-b vscode-border p-8 flex flex-col gap-6 shrink-0 relative overflow-hidden">
                    <div className="absolute inset-0 fpga-grid-bg bg-[size:24px_24px] pointer-events-none"></div>
                    <div className="flex justify-between items-start relative z-10">
                        <div>
                            <h2 className="text-2xl font-bold font-mono tracking-tight">{block.name || 'Address Block'}</h2>
                            <p className="vscode-muted text-sm mt-1 max-w-2xl">
                                {block.description || `Base: ${toHex(baseAddress)}`} • {block.usage || 'register'}
                            </p>
                        </div>
                    </div>
                    <div className="w-full relative z-10 mt-2 select-none">
                        <RegisterMapVisualizer
                            registers={registers}
                            hoveredRegIndex={hoveredRegIndex}
                            setHoveredRegIndex={setHoveredRegIndex}
                            baseAddress={baseAddress}
                        />
                    </div>
                </div>
                {/* Registers Table */}
                <div className="flex-1 flex overflow-hidden min-h-0">
                    <div className="flex-1 vscode-surface min-h-0 flex flex-col">
                        <div
                            ref={regsFocusRef}
                            tabIndex={0}
                            data-regs-table="true"
                            className="flex-1 overflow-auto min-h-0 outline-none focus:outline-none"
                        >
                            <table className="w-full text-left border-collapse table-fixed">
                                <colgroup>
                                    <col className="w-[30%] min-w-[200px]" />
                                    <col className="w-[20%] min-w-[120px]" />
                                    <col className="w-[15%] min-w-[100px]" />
                                    <col className="w-[35%]" />
                                </colgroup>
                                <thead className="vscode-surface-alt text-xs font-semibold vscode-muted uppercase tracking-wider sticky top-0 z-10 shadow-sm">
                                    <tr className="h-12">
                                        <th className="px-6 py-3 border-b vscode-border align-middle">Name</th>
                                        <th className="px-4 py-3 border-b vscode-border align-middle">Offset</th>
                                        <th className="px-4 py-3 border-b vscode-border align-middle">Access</th>
                                        <th className="px-6 py-3 border-b vscode-border align-middle">Description</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y vscode-border text-sm">
                                    {registers.map((reg: any, idx: number) => {
                                        const color = getRegColor(idx);
                                        const offset = reg.address_offset ?? reg.offset ?? (idx * 4);
                                        const colorMap: Record<string, string> = {
                                            blue: '#3b82f6',
                                            orange: '#f97316',
                                            emerald: '#10b981',
                                            pink: '#ec4899',
                                            purple: '#a855f7',
                                            cyan: '#06b6d4',
                                            amber: '#f59e0b',
                                            rose: '#f43f5e',
                                        };

                                        return (
                                            <tr
                                                key={idx}
                                                data-reg-idx={idx}
                                                className={`group transition-colors border-l-4 border-transparent h-12 ${idx === selectedRegIndex ? 'vscode-focus-border vscode-row-selected' :
                                                    idx === hoveredRegIndex ? 'vscode-focus-border vscode-row-hover' : ''
                                                    }`}
                                                onMouseEnter={() => setHoveredRegIndex(idx)}
                                                onMouseLeave={() => setHoveredRegIndex(null)}
                                                onClick={() => {
                                                    setSelectedRegIndex(idx);
                                                    setHoveredRegIndex(idx);
                                                    setRegActiveCell((prev) => ({ rowIndex: idx, key: prev.key }));
                                                }}
                                            >
                                                <td
                                                    data-col-key="name"
                                                    className={`px-6 py-2 font-medium align-middle ${regActiveCell.rowIndex === idx && regActiveCell.key === 'name' ? 'vscode-cell-active' : ''}`}
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        setSelectedRegIndex(idx);
                                                        setHoveredRegIndex(idx);
                                                        setRegActiveCell({ rowIndex: idx, key: 'name' });
                                                    }}
                                                >
                                                    <div className="flex items-center gap-2">
                                                        <div className="w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: colorMap[color] || color }}></div>
                                                        <VSCodeTextField
                                                            data-edit-key="name"
                                                            className="flex-1"
                                                            value={reg.name || ''}
                                                            onInput={(e: any) => onUpdate(['registers', idx, 'name'], e.target.value)}
                                                        />
                                                    </div>
                                                </td>
                                                <td
                                                    data-col-key="offset"
                                                    className={`px-4 py-2 font-mono vscode-muted align-middle ${regActiveCell.rowIndex === idx && regActiveCell.key === 'offset' ? 'vscode-cell-active' : ''}`}
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        setSelectedRegIndex(idx);
                                                        setHoveredRegIndex(idx);
                                                        setRegActiveCell({ rowIndex: idx, key: 'offset' });
                                                    }}
                                                >
                                                    <VSCodeTextField
                                                        data-edit-key="offset"
                                                        className="w-full font-mono"
                                                        value={toHex(offset)}
                                                        onInput={(e: any) => {
                                                            const val = Number.parseInt(e.target.value, 0);
                                                            if (!Number.isNaN(val)) {
                                                                onUpdate(['registers', idx, 'offset'], val);
                                                            }
                                                        }}
                                                    />
                                                </td>
                                                <td
                                                    data-col-key="access"
                                                    className={`px-4 py-2 align-middle ${regActiveCell.rowIndex === idx && regActiveCell.key === 'access' ? 'vscode-cell-active' : ''}`}
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        setSelectedRegIndex(idx);
                                                        setHoveredRegIndex(idx);
                                                        setRegActiveCell({ rowIndex: idx, key: 'access' });
                                                    }}
                                                >
                                                    <VSCodeDropdown
                                                        data-edit-key="access"
                                                        className="w-full"
                                                        value={reg.access || 'read-write'}
                                                        onInput={(e: any) => onUpdate(['registers', idx, 'access'], e.target.value)}
                                                    >
                                                        {ACCESS_OPTIONS.map((opt) => (
                                                            <VSCodeOption key={opt} value={opt}>{opt}</VSCodeOption>
                                                        ))}
                                                    </VSCodeDropdown>
                                                </td>
                                                <td
                                                    data-col-key="description"
                                                    className={`px-6 py-2 vscode-muted align-middle ${regActiveCell.rowIndex === idx && regActiveCell.key === 'description' ? 'vscode-cell-active' : ''}`}
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        setSelectedRegIndex(idx);
                                                        setHoveredRegIndex(idx);
                                                        setRegActiveCell({ rowIndex: idx, key: 'description' });
                                                    }}
                                                >
                                                    <VSCodeTextArea
                                                        data-edit-key="description"
                                                        className="w-full"
                                                        rows={1}
                                                        value={reg.description || ''}
                                                        onInput={(e: any) => onUpdate(['registers', idx, 'description'], e.target.value)}
                                                    />
                                                </td>
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

    return <div className="p-6 vscode-muted">Select an item to view details</div>;
});

export default DetailsPanel;
