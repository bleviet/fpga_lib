"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const react_1 = __importStar(require("react"));
const react_2 = require("@vscode/webview-ui-toolkit/react");
const BitFieldVisualizer_1 = __importDefault(require("./BitFieldVisualizer"));
const AddressMapVisualizer_1 = __importDefault(require("./AddressMapVisualizer"));
const RegisterMapVisualizer_1 = __importDefault(require("./RegisterMapVisualizer"));
const ACCESS_OPTIONS = ['read-only', 'write-only', 'read-write', 'write-1-to-clear', 'read-write-1-to-clear'];
const COLUMN_ORDER = ['name', 'bits', 'access', 'reset', 'description'];
const BLOCK_COLUMN_ORDER = ['name', 'base', 'size', 'usage', 'description'];
const REG_COLUMN_ORDER = ['name', 'offset', 'access', 'description'];
const DetailsPanel = ({ selectedType, selectedObject, selectionMeta, onUpdate }) => {
    var _a, _b;
    const [offsetText, setOffsetText] = (0, react_1.useState)('');
    const [selectedFieldIndex, setSelectedFieldIndex] = (0, react_1.useState)(-1);
    const [hoveredFieldIndex, setHoveredFieldIndex] = (0, react_1.useState)(null);
    const [editingFieldIndex, setEditingFieldIndex] = (0, react_1.useState)(null);
    const [editingKey, setEditingKey] = (0, react_1.useState)('name');
    const [selectedEditKey, setSelectedEditKey] = (0, react_1.useState)('name');
    const [activeCell, setActiveCell] = (0, react_1.useState)({ rowIndex: -1, key: 'name' });
    const [blockActiveCell, setBlockActiveCell] = (0, react_1.useState)({ rowIndex: -1, key: 'name' });
    const [regActiveCell, setRegActiveCell] = (0, react_1.useState)({ rowIndex: -1, key: 'name' });
    const [nameDraft, setNameDraft] = (0, react_1.useState)('');
    const [nameError, setNameError] = (0, react_1.useState)(null);
    const [bitsDraft, setBitsDraft] = (0, react_1.useState)('');
    const [resetDraft, setResetDraft] = (0, react_1.useState)('');
    const [resetError, setResetError] = (0, react_1.useState)(null);
    // Memory map states
    const [selectedBlockIndex, setSelectedBlockIndex] = (0, react_1.useState)(-1);
    const [hoveredBlockIndex, setHoveredBlockIndex] = (0, react_1.useState)(null);
    // Address block states
    const [selectedRegIndex, setSelectedRegIndex] = (0, react_1.useState)(-1);
    const [hoveredRegIndex, setHoveredRegIndex] = (0, react_1.useState)(null);
    const fieldsFocusRef = (0, react_1.useRef)(null);
    const blocksFocusRef = (0, react_1.useRef)(null);
    const regsFocusRef = (0, react_1.useRef)(null);
    const refocusFieldsTableSoon = () => {
        window.setTimeout(() => {
            var _a;
            (_a = fieldsFocusRef.current) === null || _a === void 0 ? void 0 : _a.focus();
        }, 0);
    };
    const refocusBlocksTableSoon = () => {
        window.setTimeout(() => {
            var _a;
            (_a = blocksFocusRef.current) === null || _a === void 0 ? void 0 : _a.focus();
        }, 0);
    };
    const refocusRegsTableSoon = () => {
        window.setTimeout(() => {
            var _a;
            (_a = regsFocusRef.current) === null || _a === void 0 ? void 0 : _a.focus();
        }, 0);
    };
    const isRegister = selectedType === 'register' && !!selectedObject;
    const reg = isRegister ? selectedObject : null;
    // Normalize fields for BitFieldVisualizer: always provide bit/bit_range
    const fields = (0, react_1.useMemo)(() => {
        if (!(reg === null || reg === void 0 ? void 0 : reg.fields))
            return [];
        return reg.fields.map((f) => {
            if (f.bit_range)
                return f;
            if (f.bit_offset !== undefined && f.bit_width !== undefined) {
                const lo = Number(f.bit_offset);
                const width = Number(f.bit_width);
                const hi = lo + width - 1;
                return Object.assign(Object.assign({}, f), { bit_range: [hi, lo] });
            }
            if (f.bit !== undefined)
                return f;
            return f;
        });
    }, [reg === null || reg === void 0 ? void 0 : reg.fields]);
    // When a register is selected, shift keyboard focus to the fields table.
    (0, react_1.useEffect)(() => {
        if (!isRegister)
            return;
        const id = window.setTimeout(() => {
            var _a;
            (_a = fieldsFocusRef.current) === null || _a === void 0 ? void 0 : _a.focus();
        }, 0);
        return () => window.clearTimeout(id);
    }, [isRegister, reg === null || reg === void 0 ? void 0 : reg.name]);
    const beginEdit = (rowIndex, key) => {
        var _a, _b;
        if (rowIndex < 0 || rowIndex >= fields.length)
            return;
        setEditingKey(key);
        if (key === 'name') {
            const current = String((_b = (_a = fields[rowIndex]) === null || _a === void 0 ? void 0 : _a.name) !== null && _b !== void 0 ? _b : '');
            setNameDraft(current);
            setNameError(null);
        }
        if (key === 'bits') {
            setBitsDraft(toBits(fields[rowIndex]));
        }
        if (key === 'reset') {
            const f = fields[rowIndex];
            const v = f === null || f === void 0 ? void 0 : f.reset_value;
            const display = v !== null && v !== undefined ? `0x${Number(v).toString(16).toUpperCase()}` : '0x0';
            setResetDraft(display);
            setResetError(null);
        }
        setEditingFieldIndex(rowIndex);
    };
    // Exit edit mode on Escape and return focus to table
    (0, react_1.useEffect)(() => {
        const onKeyDown = (e) => {
            if (e.key !== 'Escape')
                return;
            if (editingFieldIndex === null)
                return;
            e.preventDefault();
            e.stopPropagation();
            setEditingFieldIndex(null);
            refocusFieldsTableSoon();
        };
        window.addEventListener('keydown', onKeyDown);
        return () => window.removeEventListener('keydown', onKeyDown);
    }, [editingFieldIndex]);
    // Escape should exit focus from inline editors in blocks/register tables back to their table container.
    (0, react_1.useEffect)(() => {
        const onKeyDown = (e) => {
            var _a, _b;
            if (e.key !== 'Escape')
                return;
            // If we're editing fields, let the field handler above handle it.
            if (editingFieldIndex !== null)
                return;
            const activeEl = document.activeElement;
            if (!activeEl)
                return;
            const inBlocks = !!blocksFocusRef.current && blocksFocusRef.current.contains(activeEl);
            const inRegs = !!regsFocusRef.current && regsFocusRef.current.contains(activeEl);
            if (!inBlocks && !inRegs)
                return;
            e.preventDefault();
            e.stopPropagation();
            try {
                (_b = (_a = activeEl).blur) === null || _b === void 0 ? void 0 : _b.call(_a);
            }
            catch (_c) {
                // ignore
            }
            if (inBlocks)
                refocusBlocksTableSoon();
            if (inRegs)
                refocusRegsTableSoon();
        };
        window.addEventListener('keydown', onKeyDown);
        return () => window.removeEventListener('keydown', onKeyDown);
    }, [editingFieldIndex]);
    // Auto-focus the editor on first click (no extra click needed)
    (0, react_1.useEffect)(() => {
        if (editingFieldIndex === null)
            return;
        const id = window.setTimeout(() => {
            const row = document.querySelector(`tr[data-field-idx="${editingFieldIndex}"]`);
            if (!row)
                return;
            const el = row.querySelector(`[data-edit-key="${editingKey}"]`);
            if (!el)
                return;
            try {
                el.focus();
            }
            catch (_a) {
                // ignore focus failures on custom elements
            }
        }, 0);
        return () => window.clearTimeout(id);
    }, [editingFieldIndex, editingKey]);
    // Initialize draft text when entering Bits edit mode.
    (0, react_1.useEffect)(() => {
        if (editingFieldIndex === null)
            return;
        if (editingKey !== 'bits')
            return;
        const f = fields[editingFieldIndex];
        if (!f)
            return;
        setBitsDraft(toBits(f));
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [editingFieldIndex, editingKey]);
    // Keyboard shortcuts (when the fields table is focused):
    // - Arrow keys: move between cells
    // - Vim keys: h/j/k/l move between cells
    // - Alt+ArrowUp / Alt+ArrowDown: move selected field (repack offsets)
    // - F2 or e: edit active cell
    (0, react_1.useEffect)(() => {
        if (!isRegister)
            return;
        const onKeyDown = (e) => {
            var _a;
            const keyLower = (e.key || '').toLowerCase();
            const vimToArrow = {
                h: 'ArrowLeft',
                j: 'ArrowDown',
                k: 'ArrowUp',
                l: 'ArrowRight',
            };
            const mappedArrow = vimToArrow[keyLower];
            const normalizedKey = mappedArrow !== null && mappedArrow !== void 0 ? mappedArrow : e.key;
            const isArrow = normalizedKey === 'ArrowUp' || normalizedKey === 'ArrowDown' || normalizedKey === 'ArrowLeft' || normalizedKey === 'ArrowRight';
            const isEdit = normalizedKey === 'F2' || keyLower === 'e';
            if (!isArrow && !isEdit)
                return;
            // Avoid hijacking common editor chords.
            if (e.ctrlKey || e.metaKey)
                return;
            const activeEl = document.activeElement;
            const isInFieldsArea = !!fieldsFocusRef.current && !!activeEl && (activeEl === fieldsFocusRef.current || fieldsFocusRef.current.contains(activeEl));
            if (!isInFieldsArea)
                return;
            const target = e.target;
            const isTypingTarget = !!(target === null || target === void 0 ? void 0 : target.closest('input, textarea, select, [contenteditable="true"], vscode-text-field, vscode-text-area, vscode-dropdown'));
            // Don't steal arrow keys while editing/typing.
            if (editingFieldIndex !== null || isTypingTarget)
                return;
            const scrollToCell = (rowIndex, key) => {
                window.setTimeout(() => {
                    const row = document.querySelector(`tr[data-field-idx="${rowIndex}"]`);
                    row === null || row === void 0 ? void 0 : row.scrollIntoView({ block: 'nearest' });
                    const cell = row === null || row === void 0 ? void 0 : row.querySelector(`td[data-col-key="${key}"]`);
                    cell === null || cell === void 0 ? void 0 : cell.scrollIntoView({ block: 'nearest', inline: 'nearest' });
                }, 0);
            };
            const currentRow = activeCell.rowIndex >= 0 ? activeCell.rowIndex : (selectedFieldIndex >= 0 ? selectedFieldIndex : 0);
            const currentKey = COLUMN_ORDER.includes(activeCell.key) ? activeCell.key : selectedEditKey;
            if (isEdit) {
                if (currentRow < 0 || currentRow >= fields.length)
                    return;
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
                if (selectedFieldIndex < 0)
                    return;
                const next = selectedFieldIndex + delta;
                if (next < 0 || next >= fields.length)
                    return;
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
            const nextKey = (_a = COLUMN_ORDER[nextCol]) !== null && _a !== void 0 ? _a : 'name';
            setSelectedFieldIndex(currentRow);
            setHoveredFieldIndex(currentRow);
            setSelectedEditKey(nextKey);
            setActiveCell({ rowIndex: currentRow, key: nextKey });
            scrollToCell(currentRow, nextKey);
        };
        window.addEventListener('keydown', onKeyDown);
        return () => window.removeEventListener('keydown', onKeyDown);
    }, [isRegister, fields.length, selectedFieldIndex, selectedEditKey, activeCell, editingFieldIndex, onUpdate]);
    // Keyboard shortcuts for Memory Map blocks table (when focused):
    // - Arrow keys or Vim h/j/k/l to move active cell
    // - F2 or e focuses the editor for the active cell
    (0, react_1.useEffect)(() => {
        if (selectedType !== 'memoryMap')
            return;
        const blocks = (selectedObject === null || selectedObject === void 0 ? void 0 : selectedObject.address_blocks) || (selectedObject === null || selectedObject === void 0 ? void 0 : selectedObject.addressBlocks) || [];
        if (!Array.isArray(blocks) || blocks.length === 0)
            return;
        const onKeyDown = (e) => {
            var _a;
            const keyLower = (e.key || '').toLowerCase();
            const vimToArrow = {
                h: 'ArrowLeft',
                j: 'ArrowDown',
                k: 'ArrowUp',
                l: 'ArrowRight',
            };
            const mappedArrow = vimToArrow[keyLower];
            const normalizedKey = mappedArrow !== null && mappedArrow !== void 0 ? mappedArrow : e.key;
            const isArrow = normalizedKey === 'ArrowUp' || normalizedKey === 'ArrowDown' || normalizedKey === 'ArrowLeft' || normalizedKey === 'ArrowRight';
            const isEdit = normalizedKey === 'F2' || keyLower === 'e';
            if (!isArrow && !isEdit)
                return;
            if (e.ctrlKey || e.metaKey)
                return;
            const activeEl = document.activeElement;
            const isInBlocksArea = !!blocksFocusRef.current && !!activeEl && (activeEl === blocksFocusRef.current || blocksFocusRef.current.contains(activeEl));
            if (!isInBlocksArea)
                return;
            const target = e.target;
            const isTypingTarget = !!(target === null || target === void 0 ? void 0 : target.closest('input, textarea, select, [contenteditable="true"], vscode-text-field, vscode-text-area, vscode-dropdown'));
            if (isTypingTarget)
                return;
            const scrollToCell = (rowIndex, key) => {
                window.setTimeout(() => {
                    const row = document.querySelector(`tr[data-block-idx="${rowIndex}"]`);
                    row === null || row === void 0 ? void 0 : row.scrollIntoView({ block: 'nearest' });
                    const cell = row === null || row === void 0 ? void 0 : row.querySelector(`td[data-col-key="${key}"]`);
                    cell === null || cell === void 0 ? void 0 : cell.scrollIntoView({ block: 'nearest', inline: 'nearest' });
                }, 0);
            };
            const focusEditor = (rowIndex, key) => {
                window.setTimeout(() => {
                    var _a;
                    const row = document.querySelector(`tr[data-block-idx="${rowIndex}"]`);
                    const editor = row === null || row === void 0 ? void 0 : row.querySelector(`[data-edit-key="${key}"]`);
                    (_a = editor === null || editor === void 0 ? void 0 : editor.focus) === null || _a === void 0 ? void 0 : _a.call(editor);
                }, 0);
            };
            const currentRow = blockActiveCell.rowIndex >= 0 ? blockActiveCell.rowIndex : (selectedBlockIndex >= 0 ? selectedBlockIndex : 0);
            const currentKey = BLOCK_COLUMN_ORDER.includes(blockActiveCell.key) ? blockActiveCell.key : 'name';
            if (isEdit) {
                if (currentRow < 0 || currentRow >= blocks.length)
                    return;
                e.preventDefault();
                e.stopPropagation();
                setSelectedBlockIndex(currentRow);
                setHoveredBlockIndex(currentRow);
                setBlockActiveCell({ rowIndex: currentRow, key: currentKey });
                focusEditor(currentRow, currentKey);
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
            const nextKey = (_a = BLOCK_COLUMN_ORDER[nextCol]) !== null && _a !== void 0 ? _a : 'name';
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
    (0, react_1.useEffect)(() => {
        if (selectedType !== 'block')
            return;
        const registers = (selectedObject === null || selectedObject === void 0 ? void 0 : selectedObject.registers) || [];
        if (!Array.isArray(registers) || registers.length === 0)
            return;
        const onKeyDown = (e) => {
            var _a;
            const keyLower = (e.key || '').toLowerCase();
            const vimToArrow = {
                h: 'ArrowLeft',
                j: 'ArrowDown',
                k: 'ArrowUp',
                l: 'ArrowRight',
            };
            const mappedArrow = vimToArrow[keyLower];
            const normalizedKey = mappedArrow !== null && mappedArrow !== void 0 ? mappedArrow : e.key;
            const isArrow = normalizedKey === 'ArrowUp' || normalizedKey === 'ArrowDown' || normalizedKey === 'ArrowLeft' || normalizedKey === 'ArrowRight';
            const isEdit = normalizedKey === 'F2' || keyLower === 'e';
            if (!isArrow && !isEdit)
                return;
            if (e.ctrlKey || e.metaKey)
                return;
            const activeEl = document.activeElement;
            const isInRegsArea = !!regsFocusRef.current && !!activeEl && (activeEl === regsFocusRef.current || regsFocusRef.current.contains(activeEl));
            if (!isInRegsArea)
                return;
            const target = e.target;
            const isTypingTarget = !!(target === null || target === void 0 ? void 0 : target.closest('input, textarea, select, [contenteditable="true"], vscode-text-field, vscode-text-area, vscode-dropdown'));
            if (isTypingTarget)
                return;
            const scrollToCell = (rowIndex, key) => {
                window.setTimeout(() => {
                    const row = document.querySelector(`tr[data-reg-idx="${rowIndex}"]`);
                    row === null || row === void 0 ? void 0 : row.scrollIntoView({ block: 'nearest' });
                    const cell = row === null || row === void 0 ? void 0 : row.querySelector(`td[data-col-key="${key}"]`);
                    cell === null || cell === void 0 ? void 0 : cell.scrollIntoView({ block: 'nearest', inline: 'nearest' });
                }, 0);
            };
            const focusEditor = (rowIndex, key) => {
                window.setTimeout(() => {
                    var _a;
                    const row = document.querySelector(`tr[data-reg-idx="${rowIndex}"]`);
                    const editor = row === null || row === void 0 ? void 0 : row.querySelector(`[data-edit-key="${key}"]`);
                    (_a = editor === null || editor === void 0 ? void 0 : editor.focus) === null || _a === void 0 ? void 0 : _a.call(editor);
                }, 0);
            };
            const currentRow = regActiveCell.rowIndex >= 0 ? regActiveCell.rowIndex : (selectedRegIndex >= 0 ? selectedRegIndex : 0);
            const currentKey = REG_COLUMN_ORDER.includes(regActiveCell.key) ? regActiveCell.key : 'name';
            if (isEdit) {
                if (currentRow < 0 || currentRow >= registers.length)
                    return;
                e.preventDefault();
                e.stopPropagation();
                setSelectedRegIndex(currentRow);
                setHoveredRegIndex(currentRow);
                setRegActiveCell({ rowIndex: currentRow, key: currentKey });
                focusEditor(currentRow, currentKey);
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
            const nextKey = (_a = REG_COLUMN_ORDER[nextCol]) !== null && _a !== void 0 ? _a : 'name';
            setSelectedRegIndex(currentRow);
            setHoveredRegIndex(currentRow);
            setRegActiveCell({ rowIndex: currentRow, key: nextKey });
            scrollToCell(currentRow, nextKey);
        };
        window.addEventListener('keydown', onKeyDown);
        return () => window.removeEventListener('keydown', onKeyDown);
    }, [selectedType, selectedObject, selectedRegIndex, hoveredRegIndex, regActiveCell]);
    const registerOffsetText = (0, react_1.useMemo)(() => {
        var _a;
        if (!isRegister || !reg)
            return '';
        const off = Number((_a = reg.address_offset) !== null && _a !== void 0 ? _a : 0);
        return `0x${off.toString(16).toUpperCase()}`;
    }, [isRegister, reg === null || reg === void 0 ? void 0 : reg.address_offset]);
    (0, react_1.useEffect)(() => {
        if (isRegister) {
            setOffsetText(registerOffsetText);
        }
        else {
            setOffsetText('');
        }
    }, [isRegister, registerOffsetText]);
    (0, react_1.useEffect)(() => {
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
            if (prev < 0)
                return 0;
            if (prev >= fields.length)
                return fields.length - 1;
            return prev;
        });
        setActiveCell((prev) => {
            const rowIndex = prev.rowIndex < 0 ? 0 : Math.min(fields.length - 1, prev.rowIndex);
            const key = COLUMN_ORDER.includes(prev.key) ? prev.key : 'name';
            return { rowIndex, key };
        });
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [isRegister, reg === null || reg === void 0 ? void 0 : reg.name, fields.length]);
    // Clamp selection/active cell for Memory Map blocks.
    (0, react_1.useEffect)(() => {
        if (selectedType !== 'memoryMap') {
            setSelectedBlockIndex(-1);
            setBlockActiveCell({ rowIndex: -1, key: 'name' });
            return;
        }
        const blocks = (selectedObject === null || selectedObject === void 0 ? void 0 : selectedObject.address_blocks) || (selectedObject === null || selectedObject === void 0 ? void 0 : selectedObject.addressBlocks) || [];
        if (!Array.isArray(blocks) || blocks.length === 0) {
            setSelectedBlockIndex(-1);
            setBlockActiveCell({ rowIndex: -1, key: 'name' });
            return;
        }
        setSelectedBlockIndex((prev) => {
            if (prev < 0)
                return 0;
            if (prev >= blocks.length)
                return blocks.length - 1;
            return prev;
        });
        setBlockActiveCell((prev) => {
            const rowIndex = prev.rowIndex < 0 ? 0 : Math.min(blocks.length - 1, prev.rowIndex);
            const key = BLOCK_COLUMN_ORDER.includes(prev.key) ? prev.key : 'name';
            return { rowIndex, key };
        });
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [selectedType, selectedObject === null || selectedObject === void 0 ? void 0 : selectedObject.name, ((selectedObject === null || selectedObject === void 0 ? void 0 : selectedObject.address_blocks) || (selectedObject === null || selectedObject === void 0 ? void 0 : selectedObject.addressBlocks) || []).length]);
    // Clamp selection/active cell for Address Block registers.
    (0, react_1.useEffect)(() => {
        if (selectedType !== 'block') {
            setSelectedRegIndex(-1);
            setRegActiveCell({ rowIndex: -1, key: 'name' });
            return;
        }
        const registers = (selectedObject === null || selectedObject === void 0 ? void 0 : selectedObject.registers) || [];
        if (!Array.isArray(registers) || registers.length === 0) {
            setSelectedRegIndex(-1);
            setRegActiveCell({ rowIndex: -1, key: 'name' });
            return;
        }
        setSelectedRegIndex((prev) => {
            if (prev < 0)
                return 0;
            if (prev >= registers.length)
                return registers.length - 1;
            return prev;
        });
        setRegActiveCell((prev) => {
            const rowIndex = prev.rowIndex < 0 ? 0 : Math.min(registers.length - 1, prev.rowIndex);
            const key = REG_COLUMN_ORDER.includes(prev.key) ? prev.key : 'name';
            return { rowIndex, key };
        });
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [selectedType, selectedObject === null || selectedObject === void 0 ? void 0 : selectedObject.name, ((selectedObject === null || selectedObject === void 0 ? void 0 : selectedObject.registers) || []).length]);
    const commitRegisterOffset = () => {
        if (!isRegister)
            return;
        const parsed = Number.parseInt(offsetText.trim(), 0);
        if (Number.isNaN(parsed))
            return;
        onUpdate(['address_offset'], parsed);
    };
    const toBits = (f) => {
        var _a, _b;
        const o = Number((_a = f === null || f === void 0 ? void 0 : f.bit_offset) !== null && _a !== void 0 ? _a : 0);
        const w = Number((_b = f === null || f === void 0 ? void 0 : f.bit_width) !== null && _b !== void 0 ? _b : 1);
        if (!Number.isFinite(o) || !Number.isFinite(w)) {
            return '[?:?]';
        }
        const msb = o + w - 1;
        return `[${msb}:${o}]`;
    };
    const getFieldColor = (index) => {
        const colors = ['blue', 'orange', 'emerald', 'pink', 'purple', 'cyan', 'amber', 'rose'];
        return colors[index % colors.length];
    };
    // Parse a bit string like "[7:4]" or "[3]" or "7:4" or "3".
    const parseBitsInput = (text) => {
        const trimmed = text.trim().replace(/[\[\]]/g, '');
        if (!trimmed)
            return null;
        const parts = trimmed.split(':').map((p) => Number(p.trim()));
        if (parts.some((p) => Number.isNaN(p)))
            return null;
        let msb;
        let lsb;
        if (parts.length === 1) {
            msb = parts[0];
            lsb = parts[0];
        }
        else {
            [msb, lsb] = parts;
        }
        if (!Number.isFinite(msb) || !Number.isFinite(lsb))
            return null;
        if (msb < lsb) {
            const tmp = msb;
            msb = lsb;
            lsb = tmp;
        }
        const width = msb - lsb + 1;
        return { bit_offset: lsb, bit_width: width, bit_range: [msb, lsb] };
    };
    const parseReset = (text) => {
        const s = text.trim();
        if (!s)
            return null;
        const v = Number.parseInt(s, 0);
        return Number.isFinite(v) ? v : null;
    };
    const validateVhdlIdentifier = (name) => {
        const trimmed = name.trim();
        if (!trimmed)
            return 'Name is required';
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
    const getFieldBitWidth = (f) => {
        const w = Number(f === null || f === void 0 ? void 0 : f.bit_width);
        if (Number.isFinite(w) && w > 0)
            return w;
        const br = f === null || f === void 0 ? void 0 : f.bit_range;
        if (Array.isArray(br) && br.length === 2) {
            const msb = Number(br[0]);
            const lsb = Number(br[1]);
            if (Number.isFinite(msb) && Number.isFinite(lsb))
                return Math.abs(msb - lsb) + 1;
        }
        return 1;
    };
    const validateResetForField = (f, value) => {
        if (value === null)
            return null;
        if (!Number.isFinite(value))
            return 'Invalid number';
        if (value < 0)
            return 'Reset must be >= 0';
        const width = getFieldBitWidth(f);
        // Avoid overflow in shifts; for typical widths (<=32) this is safe.
        const max = width >= 53 ? Number.MAX_SAFE_INTEGER : Math.pow(2, width) - 1;
        if (value > max)
            return `Reset too large for ${width} bit(s)`;
        return null;
    };
    if (!selectedObject) {
        return react_1.default.createElement("div", { className: "flex items-center justify-center h-full vscode-muted text-sm" }, "Select an item to view details");
    }
    // Color map for field dots and BitFieldVisualizer
    const colorMap = {
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
        const regObj = selectedObject;
        const handleClickOutside = (e) => {
            const target = e.target;
            if (!target)
                return;
            const inRow = target.closest('tr[data-field-idx]');
            if (!inRow)
                setEditingFieldIndex(null);
        };
        const handleBlur = (idx) => (e) => {
            const related = e.relatedTarget;
            if (related && related.closest('tr[data-field-idx]'))
                return;
            setEditingFieldIndex(null);
        };
        const handleKeyDown = (idx) => (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                e.stopPropagation();
                if (editingFieldIndex === idx && editingKey === 'name' && nameError) {
                    return;
                }
                if (editingFieldIndex === idx && editingKey === 'reset' && resetError) {
                    return;
                }
                setEditingFieldIndex(null);
                refocusFieldsTableSoon();
            }
        };
        const startEdit = (idx, key) => (e) => {
            e.stopPropagation();
            setEditingFieldIndex(idx);
            setEditingKey(key);
        };
        const startEditOnDoubleClick = (idx, key) => (e) => {
            // Use double-click to enter edit mode so single-click can be used for selection/move.
            e.stopPropagation();
            beginEdit(idx, key);
        };
        const moveSelectedField = (delta) => {
            const idx = selectedFieldIndex;
            if (idx < 0)
                return;
            const next = idx + delta;
            if (next < 0 || next >= fields.length)
                return;
            setEditingFieldIndex(null);
            onUpdate(['__op', 'field-move'], { index: idx, delta });
            setSelectedFieldIndex(next);
            setHoveredFieldIndex(next);
        };
        return (react_1.default.createElement("div", { className: "flex flex-col w-full h-full min-h-0", onClickCapture: handleClickOutside },
            react_1.default.createElement("div", { className: "vscode-surface border-b vscode-border p-8 flex flex-col gap-6 shrink-0 relative overflow-hidden" },
                react_1.default.createElement("div", { className: "absolute inset-0 fpga-grid-bg bg-[size:24px_24px] pointer-events-none" }),
                react_1.default.createElement("div", { className: "flex justify-between items-start relative z-10" },
                    react_1.default.createElement("div", null,
                        react_1.default.createElement("h2", { className: "text-2xl font-bold font-mono tracking-tight" }, regObj.name),
                        react_1.default.createElement("p", { className: "vscode-muted text-sm mt-1 max-w-2xl" }, regObj.description))),
                react_1.default.createElement("div", { className: "w-full relative z-10 mt-2 select-none" },
                    react_1.default.createElement(BitFieldVisualizer_1.default, { fields: fields, hoveredFieldIndex: hoveredFieldIndex, setHoveredFieldIndex: setHoveredFieldIndex, registerSize: 32, layout: "pro", onUpdateFieldReset: (fieldIndex, resetValue) => {
                            onUpdate(['fields', fieldIndex, 'reset_value'], resetValue);
                        } }))),
            react_1.default.createElement("div", { className: "flex-1 flex overflow-hidden min-h-0" },
                react_1.default.createElement("div", { className: "flex-1 vscode-surface border-r vscode-border min-h-0 flex flex-col" },
                    react_1.default.createElement("div", { className: "shrink-0 px-4 py-2 border-b vscode-border vscode-surface flex items-center justify-end gap-1" },
                        react_1.default.createElement("button", { className: "p-2 rounded-md transition-colors disabled:opacity-40 vscode-icon-button", onClick: () => moveSelectedField(-1), disabled: selectedFieldIndex <= 0, title: "Move field up", type: "button" },
                            react_1.default.createElement("span", { className: "codicon codicon-chevron-up" })),
                        react_1.default.createElement("button", { className: "p-2 rounded-md transition-colors disabled:opacity-40 vscode-icon-button", onClick: () => moveSelectedField(1), disabled: selectedFieldIndex < 0 || selectedFieldIndex >= fields.length - 1, title: "Move field down", type: "button" },
                            react_1.default.createElement("span", { className: "codicon codicon-chevron-down" }))),
                    react_1.default.createElement("div", { ref: fieldsFocusRef, tabIndex: 0, "data-fields-table": "true", className: "flex-1 overflow-auto min-h-0 outline-none focus:outline-none" },
                        react_1.default.createElement("table", { className: "w-full text-left border-collapse table-fixed" },
                            react_1.default.createElement("colgroup", null,
                                react_1.default.createElement("col", { className: "w-[32%] min-w-[240px]" }),
                                react_1.default.createElement("col", { className: "w-[14%] min-w-[100px]" }),
                                react_1.default.createElement("col", { className: "w-[14%] min-w-[120px]" }),
                                react_1.default.createElement("col", { className: "w-[14%] min-w-[110px]" }),
                                react_1.default.createElement("col", { className: "w-[26%]" })),
                            react_1.default.createElement("thead", { className: "vscode-surface-alt text-xs font-semibold vscode-muted uppercase tracking-wider sticky top-0 z-10 shadow-sm" },
                                react_1.default.createElement("tr", { className: "h-12" },
                                    react_1.default.createElement("th", { className: "px-6 py-3 border-b vscode-border align-middle" }, "Name"),
                                    react_1.default.createElement("th", { className: "px-4 py-3 border-b vscode-border align-middle" }, "Bit(s)"),
                                    react_1.default.createElement("th", { className: "px-4 py-3 border-b vscode-border align-middle" }, "Access"),
                                    react_1.default.createElement("th", { className: "px-4 py-3 border-b vscode-border align-middle" }, "Reset"),
                                    react_1.default.createElement("th", { className: "px-6 py-3 border-b vscode-border align-middle" }, "Description"))),
                            react_1.default.createElement("tbody", { className: "divide-y vscode-border text-sm" }, fields.map((field, idx) => {
                                var _a;
                                const bits = toBits(field);
                                const color = getFieldColor(idx);
                                const resetDisplay = field.reset_value !== null && field.reset_value !== undefined
                                    ? `0x${Number(field.reset_value).toString(16).toUpperCase()}`
                                    : '';
                                return (react_1.default.createElement("tr", { key: idx, "data-field-idx": idx, className: `group transition-colors border-l-4 border-transparent h-12 ${idx === selectedFieldIndex ? 'vscode-focus-border vscode-row-selected' : idx === hoveredFieldIndex ? 'vscode-focus-border vscode-row-hover' : ''}`, onMouseEnter: () => {
                                        setHoveredFieldIndex(idx);
                                    }, onMouseLeave: () => setHoveredFieldIndex(null), onClick: () => {
                                        setSelectedFieldIndex(idx);
                                        setHoveredFieldIndex(idx);
                                        setActiveCell((prev) => ({ rowIndex: idx, key: prev.key }));
                                    }, id: `row-${(_a = field.name) === null || _a === void 0 ? void 0 : _a.toLowerCase().replace(/[^a-z0-9_]/g, '-')}` }, (() => {
                                    const isEditingRow = editingFieldIndex === idx;
                                    const isEditingName = isEditingRow && editingKey === 'name';
                                    const isEditingBits = isEditingRow && editingKey === 'bits';
                                    const isEditingAccess = isEditingRow && editingKey === 'access';
                                    const isEditingReset = isEditingRow && editingKey === 'reset';
                                    const isEditingDescription = isEditingRow && editingKey === 'description';
                                    return (react_1.default.createElement(react_1.default.Fragment, null,
                                        react_1.default.createElement("td", { "data-col-key": "name", className: `px-6 py-2 font-medium align-middle ${activeCell.rowIndex === idx && activeCell.key === 'name' ? 'vscode-cell-active' : ''}`, onClick: (e) => {
                                                e.stopPropagation();
                                                setSelectedFieldIndex(idx);
                                                setHoveredFieldIndex(idx);
                                                setSelectedEditKey('name');
                                                setActiveCell({ rowIndex: idx, key: 'name' });
                                            }, onDoubleClick: startEditOnDoubleClick(idx, 'name') },
                                            react_1.default.createElement("div", { className: "flex flex-col justify-center" },
                                                react_1.default.createElement("div", { className: "flex items-center gap-2 h-10" },
                                                    react_1.default.createElement("div", { className: `w-2.5 h-2.5 rounded-sm`, style: { backgroundColor: color === 'gray' ? '#e5e7eb' : (colorMap && colorMap[color]) || color } }),
                                                    isEditingName ? (react_1.default.createElement(react_2.VSCodeTextField, { "data-edit-key": "name", className: "flex-1", value: nameDraft, onInput: (e) => {
                                                            var _a;
                                                            const next = String((_a = e.target.value) !== null && _a !== void 0 ? _a : '');
                                                            setNameDraft(next);
                                                            const err = validateVhdlIdentifier(next);
                                                            setNameError(err);
                                                            if (!err)
                                                                onUpdate(['fields', idx, 'name'], next.trim());
                                                        }, onBlur: handleBlur(idx), onKeyDown: handleKeyDown(idx) })) : (field.name)),
                                                isEditingName && nameError ? (react_1.default.createElement("div", { className: "text-xs vscode-error mt-1" }, nameError)) : null)),
                                        react_1.default.createElement("td", { "data-col-key": "bits", className: `px-4 py-2 font-mono vscode-muted align-middle ${activeCell.rowIndex === idx && activeCell.key === 'bits' ? 'vscode-cell-active' : ''}`, onClick: (e) => {
                                                e.stopPropagation();
                                                setSelectedFieldIndex(idx);
                                                setHoveredFieldIndex(idx);
                                                setSelectedEditKey('bits');
                                                setActiveCell({ rowIndex: idx, key: 'bits' });
                                            }, onDoubleClick: startEditOnDoubleClick(idx, 'bits') },
                                            react_1.default.createElement("div", { className: "flex items-center h-10" }, isEditingBits ? (react_1.default.createElement(react_2.VSCodeTextField, { "data-edit-key": "bits", className: "w-full font-mono", value: bitsDraft, onInput: (e) => {
                                                    var _a;
                                                    const next = String((_a = e.target.value) !== null && _a !== void 0 ? _a : '');
                                                    setBitsDraft(next);
                                                    const parsed = parseBitsInput(next);
                                                    if (parsed) {
                                                        onUpdate(['fields', idx, 'bit_offset'], parsed.bit_offset);
                                                        onUpdate(['fields', idx, 'bit_width'], parsed.bit_width);
                                                        onUpdate(['fields', idx, 'bit_range'], parsed.bit_range);
                                                    }
                                                }, onBlur: handleBlur(idx), onKeyDown: (e) => {
                                                    if (e.key !== 'Enter')
                                                        return;
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
                                                } })) : (bits))),
                                        react_1.default.createElement("td", { "data-col-key": "access", className: `px-4 py-2 align-middle ${activeCell.rowIndex === idx && activeCell.key === 'access' ? 'vscode-cell-active' : ''}`, onClick: (e) => {
                                                e.stopPropagation();
                                                setSelectedFieldIndex(idx);
                                                setHoveredFieldIndex(idx);
                                                setSelectedEditKey('access');
                                                setActiveCell({ rowIndex: idx, key: 'access' });
                                            }, onDoubleClick: startEditOnDoubleClick(idx, 'access') },
                                            react_1.default.createElement("div", { className: "flex items-center h-10" }, isEditingAccess ? (react_1.default.createElement(react_2.VSCodeDropdown, { "data-edit-key": "access", value: field.access || 'read-write', className: "w-full", onInput: (e) => onUpdate(['fields', idx, 'access'], e.target.value), onBlur: handleBlur(idx), onKeyDown: handleKeyDown(idx) }, ACCESS_OPTIONS.map((opt) => (react_1.default.createElement(react_2.VSCodeOption, { key: opt, value: opt }, opt))))) : (react_1.default.createElement("div", { className: "flex items-center justify-start" },
                                                react_1.default.createElement("span", { className: "px-2 py-0.5 rounded text-xs font-medium vscode-badge whitespace-nowrap" }, field.access || 'RW'))))),
                                        react_1.default.createElement("td", { "data-col-key": "reset", className: `px-4 py-2 font-mono vscode-muted align-middle ${activeCell.rowIndex === idx && activeCell.key === 'reset' ? 'vscode-cell-active' : ''}`, onClick: (e) => {
                                                e.stopPropagation();
                                                setSelectedFieldIndex(idx);
                                                setHoveredFieldIndex(idx);
                                                setSelectedEditKey('reset');
                                                setActiveCell({ rowIndex: idx, key: 'reset' });
                                            }, onDoubleClick: startEditOnDoubleClick(idx, 'reset') },
                                            react_1.default.createElement("div", { className: "flex flex-col justify-center h-10" },
                                                isEditingReset ? (react_1.default.createElement(react_2.VSCodeTextField, { "data-edit-key": "reset", className: "w-full font-mono", value: resetDraft, onInput: (e) => {
                                                        var _a;
                                                        const raw = String((_a = e.target.value) !== null && _a !== void 0 ? _a : '');
                                                        setResetDraft(raw);
                                                        const trimmed = raw.trim();
                                                        if (!trimmed) {
                                                            setResetError(null);
                                                            onUpdate(['fields', idx, 'reset_value'], null);
                                                            return;
                                                        }
                                                        const parsed = parseReset(raw);
                                                        const err = validateResetForField(field, parsed);
                                                        setResetError(err);
                                                        if (err)
                                                            return;
                                                        if (parsed !== null)
                                                            onUpdate(['fields', idx, 'reset_value'], parsed);
                                                    }, onBlur: handleBlur(idx), onKeyDown: handleKeyDown(idx) })) : (resetDisplay || '0x0'),
                                                isEditingReset && resetError ? (react_1.default.createElement("div", { className: "text-xs vscode-error mt-1" }, resetError)) : null)),
                                        react_1.default.createElement("td", { "data-col-key": "description", className: `px-6 py-2 vscode-muted align-middle ${activeCell.rowIndex === idx && activeCell.key === 'description' ? 'vscode-cell-active' : ''}`, onClick: (e) => {
                                                e.stopPropagation();
                                                setSelectedFieldIndex(idx);
                                                setHoveredFieldIndex(idx);
                                                setSelectedEditKey('description');
                                                setActiveCell({ rowIndex: idx, key: 'description' });
                                            }, onDoubleClick: startEditOnDoubleClick(idx, 'description') },
                                            react_1.default.createElement("div", { className: "flex items-center h-10" }, isEditingDescription ? (react_1.default.createElement(react_2.VSCodeTextArea, { "data-edit-key": "description", className: "w-full", rows: 2, value: field.description || '', onInput: (e) => onUpdate(['fields', idx, 'description'], e.target.value), onBlur: handleBlur(idx) })) : (field.description || '-')))));
                                })()));
                            }))))))));
    }
    if (selectedType === 'memoryMap') {
        const map = selectedObject;
        const blocks = map.address_blocks || map.addressBlocks || [];
        const toHex = (n) => `0x${Math.max(0, n).toString(16).toUpperCase()}`;
        const getBlockColor = (idx) => {
            const colorKeys = ['blue', 'orange', 'emerald', 'pink', 'purple', 'cyan', 'amber', 'rose'];
            return colorKeys[idx % colorKeys.length];
        };
        return (react_1.default.createElement("div", { className: "flex flex-col w-full h-full min-h-0" },
            react_1.default.createElement("div", { className: "vscode-surface border-b vscode-border p-8 flex flex-col gap-6 shrink-0 relative overflow-hidden" },
                react_1.default.createElement("div", { className: "flex justify-between items-start relative z-10" },
                    react_1.default.createElement("div", null,
                        react_1.default.createElement("h2", { className: "text-2xl font-bold font-mono tracking-tight" }, map.name || 'Memory Map'),
                        react_1.default.createElement("p", { className: "vscode-muted text-sm mt-1 max-w-2xl" }, map.description || 'Address space layout'))),
                react_1.default.createElement("div", { className: "w-full relative z-10 mt-2 select-none" },
                    react_1.default.createElement(AddressMapVisualizer_1.default, { blocks: blocks, hoveredBlockIndex: hoveredBlockIndex, setHoveredBlockIndex: setHoveredBlockIndex }))),
            react_1.default.createElement("div", { className: "flex-1 flex overflow-hidden min-h-0" },
                react_1.default.createElement("div", { className: "flex-1 vscode-surface min-h-0 flex flex-col" },
                    react_1.default.createElement("div", { ref: blocksFocusRef, tabIndex: 0, "data-blocks-table": "true", className: "flex-1 overflow-auto min-h-0 outline-none focus:outline-none" },
                        react_1.default.createElement("table", { className: "w-full text-left border-collapse table-fixed" },
                            react_1.default.createElement("colgroup", null,
                                react_1.default.createElement("col", { className: "w-[25%] min-w-[200px]" }),
                                react_1.default.createElement("col", { className: "w-[20%] min-w-[120px]" }),
                                react_1.default.createElement("col", { className: "w-[15%] min-w-[100px]" }),
                                react_1.default.createElement("col", { className: "w-[15%] min-w-[100px]" }),
                                react_1.default.createElement("col", { className: "w-[25%]" })),
                            react_1.default.createElement("thead", { className: "vscode-surface-alt text-xs font-semibold vscode-muted uppercase tracking-wider sticky top-0 z-10 shadow-sm" },
                                react_1.default.createElement("tr", { className: "h-12" },
                                    react_1.default.createElement("th", { className: "px-6 py-3 border-b vscode-border align-middle" }, "Name"),
                                    react_1.default.createElement("th", { className: "px-4 py-3 border-b vscode-border align-middle" }, "Base Address"),
                                    react_1.default.createElement("th", { className: "px-4 py-3 border-b vscode-border align-middle" }, "Size"),
                                    react_1.default.createElement("th", { className: "px-4 py-3 border-b vscode-border align-middle" }, "Usage"),
                                    react_1.default.createElement("th", { className: "px-6 py-3 border-b vscode-border align-middle" }, "Description"))),
                            react_1.default.createElement("tbody", { className: "divide-y vscode-border text-sm" }, blocks.map((block, idx) => {
                                var _a, _b, _c, _d;
                                const color = getBlockColor(idx);
                                const base = (_b = (_a = block.base_address) !== null && _a !== void 0 ? _a : block.offset) !== null && _b !== void 0 ? _b : 0;
                                const size = (_d = (_c = block.size) !== null && _c !== void 0 ? _c : block.range) !== null && _d !== void 0 ? _d : 4096;
                                const colorMap = {
                                    blue: '#3b82f6',
                                    orange: '#f97316',
                                    emerald: '#10b981',
                                    pink: '#ec4899',
                                    purple: '#a855f7',
                                    cyan: '#06b6d4',
                                    amber: '#f59e0b',
                                    rose: '#f43f5e',
                                };
                                return (react_1.default.createElement("tr", { key: idx, "data-block-idx": idx, className: `group transition-colors border-l-4 border-transparent h-12 ${idx === selectedBlockIndex ? 'vscode-focus-border vscode-row-selected' :
                                        idx === hoveredBlockIndex ? 'vscode-focus-border vscode-row-hover' : ''}`, onMouseEnter: () => setHoveredBlockIndex(idx), onMouseLeave: () => setHoveredBlockIndex(null), onClick: () => {
                                        setSelectedBlockIndex(idx);
                                        setHoveredBlockIndex(idx);
                                        setBlockActiveCell((prev) => ({ rowIndex: idx, key: prev.key }));
                                    } },
                                    react_1.default.createElement("td", { "data-col-key": "name", className: `px-6 py-2 font-medium align-middle ${blockActiveCell.rowIndex === idx && blockActiveCell.key === 'name' ? 'vscode-cell-active' : ''}`, onClick: (e) => {
                                            e.stopPropagation();
                                            setSelectedBlockIndex(idx);
                                            setHoveredBlockIndex(idx);
                                            setBlockActiveCell({ rowIndex: idx, key: 'name' });
                                        } },
                                        react_1.default.createElement("div", { className: "flex items-center gap-2" },
                                            react_1.default.createElement("div", { className: "w-2.5 h-2.5 rounded-sm", style: { backgroundColor: colorMap[color] || color } }),
                                            react_1.default.createElement(react_2.VSCodeTextField, { "data-edit-key": "name", className: "flex-1", value: block.name || '', onInput: (e) => onUpdate(['addressBlocks', idx, 'name'], e.target.value) }))),
                                    react_1.default.createElement("td", { "data-col-key": "base", className: `px-4 py-2 font-mono vscode-muted align-middle ${blockActiveCell.rowIndex === idx && blockActiveCell.key === 'base' ? 'vscode-cell-active' : ''}`, onClick: (e) => {
                                            e.stopPropagation();
                                            setSelectedBlockIndex(idx);
                                            setHoveredBlockIndex(idx);
                                            setBlockActiveCell({ rowIndex: idx, key: 'base' });
                                        } },
                                        react_1.default.createElement(react_2.VSCodeTextField, { "data-edit-key": "base", className: "w-full font-mono", value: toHex(base), onInput: (e) => {
                                                const val = Number.parseInt(e.target.value, 0);
                                                if (!Number.isNaN(val)) {
                                                    onUpdate(['addressBlocks', idx, 'offset'], val);
                                                }
                                            } })),
                                    react_1.default.createElement("td", { "data-col-key": "size", className: `px-4 py-2 font-mono vscode-muted align-middle ${blockActiveCell.rowIndex === idx && blockActiveCell.key === 'size' ? 'vscode-cell-active' : ''}`, onClick: (e) => {
                                            e.stopPropagation();
                                            setSelectedBlockIndex(idx);
                                            setHoveredBlockIndex(idx);
                                            setBlockActiveCell({ rowIndex: idx, key: 'size' });
                                        } }, size < 1024 ? `${size}B` : `${(size / 1024).toFixed(1)}KB`),
                                    react_1.default.createElement("td", { "data-col-key": "usage", className: `px-4 py-2 align-middle ${blockActiveCell.rowIndex === idx && blockActiveCell.key === 'usage' ? 'vscode-cell-active' : ''}`, onClick: (e) => {
                                            e.stopPropagation();
                                            setSelectedBlockIndex(idx);
                                            setHoveredBlockIndex(idx);
                                            setBlockActiveCell({ rowIndex: idx, key: 'usage' });
                                        } },
                                        react_1.default.createElement("span", { className: "px-2 py-0.5 rounded text-xs font-medium vscode-badge whitespace-nowrap" }, block.usage || 'register')),
                                    react_1.default.createElement("td", { "data-col-key": "description", className: `px-6 py-2 vscode-muted align-middle ${blockActiveCell.rowIndex === idx && blockActiveCell.key === 'description' ? 'vscode-cell-active' : ''}`, onClick: (e) => {
                                            e.stopPropagation();
                                            setSelectedBlockIndex(idx);
                                            setHoveredBlockIndex(idx);
                                            setBlockActiveCell({ rowIndex: idx, key: 'description' });
                                        } },
                                        react_1.default.createElement(react_2.VSCodeTextArea, { "data-edit-key": "description", className: "w-full", rows: 1, value: block.description || '', onInput: (e) => onUpdate(['addressBlocks', idx, 'description'], e.target.value) }))));
                            }))))))));
    }
    if (selectedType === 'block') {
        const block = selectedObject;
        const registers = block.registers || [];
        const baseAddress = (_b = (_a = block.base_address) !== null && _a !== void 0 ? _a : block.offset) !== null && _b !== void 0 ? _b : 0;
        const toHex = (n) => `0x${Math.max(0, n).toString(16).toUpperCase()}`;
        const getRegColor = (idx) => {
            const colorKeys = ['blue', 'orange', 'emerald', 'pink', 'purple', 'cyan', 'amber', 'rose'];
            return colorKeys[idx % colorKeys.length];
        };
        return (react_1.default.createElement("div", { className: "flex flex-col w-full h-full min-h-0" },
            react_1.default.createElement("div", { className: "vscode-surface border-b vscode-border p-8 flex flex-col gap-6 shrink-0 relative overflow-hidden" },
                react_1.default.createElement("div", { className: "absolute inset-0 fpga-grid-bg bg-[size:24px_24px] pointer-events-none" }),
                react_1.default.createElement("div", { className: "flex justify-between items-start relative z-10" },
                    react_1.default.createElement("div", null,
                        react_1.default.createElement("h2", { className: "text-2xl font-bold font-mono tracking-tight" }, block.name || 'Address Block'),
                        react_1.default.createElement("p", { className: "vscode-muted text-sm mt-1 max-w-2xl" },
                            block.description || `Base: ${toHex(baseAddress)}`,
                            " \u2022 ",
                            block.usage || 'register'))),
                react_1.default.createElement("div", { className: "w-full relative z-10 mt-2 select-none" },
                    react_1.default.createElement(RegisterMapVisualizer_1.default, { registers: registers, hoveredRegIndex: hoveredRegIndex, setHoveredRegIndex: setHoveredRegIndex, baseAddress: baseAddress }))),
            react_1.default.createElement("div", { className: "flex-1 flex overflow-hidden min-h-0" },
                react_1.default.createElement("div", { className: "flex-1 vscode-surface min-h-0 flex flex-col" },
                    react_1.default.createElement("div", { ref: regsFocusRef, tabIndex: 0, "data-regs-table": "true", className: "flex-1 overflow-auto min-h-0 outline-none focus:outline-none" },
                        react_1.default.createElement("table", { className: "w-full text-left border-collapse table-fixed" },
                            react_1.default.createElement("colgroup", null,
                                react_1.default.createElement("col", { className: "w-[30%] min-w-[200px]" }),
                                react_1.default.createElement("col", { className: "w-[20%] min-w-[120px]" }),
                                react_1.default.createElement("col", { className: "w-[15%] min-w-[100px]" }),
                                react_1.default.createElement("col", { className: "w-[35%]" })),
                            react_1.default.createElement("thead", { className: "vscode-surface-alt text-xs font-semibold vscode-muted uppercase tracking-wider sticky top-0 z-10 shadow-sm" },
                                react_1.default.createElement("tr", { className: "h-12" },
                                    react_1.default.createElement("th", { className: "px-6 py-3 border-b vscode-border align-middle" }, "Name"),
                                    react_1.default.createElement("th", { className: "px-4 py-3 border-b vscode-border align-middle" }, "Offset"),
                                    react_1.default.createElement("th", { className: "px-4 py-3 border-b vscode-border align-middle" }, "Access"),
                                    react_1.default.createElement("th", { className: "px-6 py-3 border-b vscode-border align-middle" }, "Description"))),
                            react_1.default.createElement("tbody", { className: "divide-y vscode-border text-sm" }, registers.map((reg, idx) => {
                                var _a, _b;
                                const color = getRegColor(idx);
                                const offset = (_b = (_a = reg.address_offset) !== null && _a !== void 0 ? _a : reg.offset) !== null && _b !== void 0 ? _b : (idx * 4);
                                const colorMap = {
                                    blue: '#3b82f6',
                                    orange: '#f97316',
                                    emerald: '#10b981',
                                    pink: '#ec4899',
                                    purple: '#a855f7',
                                    cyan: '#06b6d4',
                                    amber: '#f59e0b',
                                    rose: '#f43f5e',
                                };
                                return (react_1.default.createElement("tr", { key: idx, "data-reg-idx": idx, className: `group transition-colors border-l-4 border-transparent h-12 ${idx === selectedRegIndex ? 'vscode-focus-border vscode-row-selected' :
                                        idx === hoveredRegIndex ? 'vscode-focus-border vscode-row-hover' : ''}`, onMouseEnter: () => setHoveredRegIndex(idx), onMouseLeave: () => setHoveredRegIndex(null), onClick: () => {
                                        setSelectedRegIndex(idx);
                                        setHoveredRegIndex(idx);
                                        setRegActiveCell((prev) => ({ rowIndex: idx, key: prev.key }));
                                    } },
                                    react_1.default.createElement("td", { "data-col-key": "name", className: `px-6 py-2 font-medium align-middle ${regActiveCell.rowIndex === idx && regActiveCell.key === 'name' ? 'vscode-cell-active' : ''}`, onClick: (e) => {
                                            e.stopPropagation();
                                            setSelectedRegIndex(idx);
                                            setHoveredRegIndex(idx);
                                            setRegActiveCell({ rowIndex: idx, key: 'name' });
                                        } },
                                        react_1.default.createElement("div", { className: "flex items-center gap-2" },
                                            react_1.default.createElement("div", { className: "w-2.5 h-2.5 rounded-sm", style: { backgroundColor: colorMap[color] || color } }),
                                            react_1.default.createElement(react_2.VSCodeTextField, { "data-edit-key": "name", className: "flex-1", value: reg.name || '', onInput: (e) => onUpdate(['registers', idx, 'name'], e.target.value) }))),
                                    react_1.default.createElement("td", { "data-col-key": "offset", className: `px-4 py-2 font-mono vscode-muted align-middle ${regActiveCell.rowIndex === idx && regActiveCell.key === 'offset' ? 'vscode-cell-active' : ''}`, onClick: (e) => {
                                            e.stopPropagation();
                                            setSelectedRegIndex(idx);
                                            setHoveredRegIndex(idx);
                                            setRegActiveCell({ rowIndex: idx, key: 'offset' });
                                        } },
                                        react_1.default.createElement(react_2.VSCodeTextField, { "data-edit-key": "offset", className: "w-full font-mono", value: toHex(offset), onInput: (e) => {
                                                const val = Number.parseInt(e.target.value, 0);
                                                if (!Number.isNaN(val)) {
                                                    onUpdate(['registers', idx, 'offset'], val);
                                                }
                                            } })),
                                    react_1.default.createElement("td", { "data-col-key": "access", className: `px-4 py-2 align-middle ${regActiveCell.rowIndex === idx && regActiveCell.key === 'access' ? 'vscode-cell-active' : ''}`, onClick: (e) => {
                                            e.stopPropagation();
                                            setSelectedRegIndex(idx);
                                            setHoveredRegIndex(idx);
                                            setRegActiveCell({ rowIndex: idx, key: 'access' });
                                        } },
                                        react_1.default.createElement(react_2.VSCodeDropdown, { "data-edit-key": "access", className: "w-full", value: reg.access || 'read-write', onInput: (e) => onUpdate(['registers', idx, 'access'], e.target.value) }, ACCESS_OPTIONS.map((opt) => (react_1.default.createElement(react_2.VSCodeOption, { key: opt, value: opt }, opt))))),
                                    react_1.default.createElement("td", { "data-col-key": "description", className: `px-6 py-2 vscode-muted align-middle ${regActiveCell.rowIndex === idx && regActiveCell.key === 'description' ? 'vscode-cell-active' : ''}`, onClick: (e) => {
                                            e.stopPropagation();
                                            setSelectedRegIndex(idx);
                                            setHoveredRegIndex(idx);
                                            setRegActiveCell({ rowIndex: idx, key: 'description' });
                                        } },
                                        react_1.default.createElement(react_2.VSCodeTextArea, { "data-edit-key": "description", className: "w-full", rows: 1, value: reg.description || '', onInput: (e) => onUpdate(['registers', idx, 'description'], e.target.value) }))));
                            }))))))));
    }
    return react_1.default.createElement("div", { className: "p-6 vscode-muted" }, "Select an item to view details");
};
exports.default = DetailsPanel;
//# sourceMappingURL=DetailsPanel.js.map