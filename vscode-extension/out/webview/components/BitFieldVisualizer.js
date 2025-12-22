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
Object.defineProperty(exports, "__esModule", { value: true });
const react_1 = __importStar(require("react"));
const react_2 = require("@vscode/webview-ui-toolkit/react");
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
const colorKeys = Object.keys(colorMap);
function getFieldColor(idx) {
    return colorKeys[idx % colorKeys.length];
}
function toBits(field) {
    if (field.bit_range) {
        const [hi, lo] = field.bit_range;
        return hi === lo ? `${hi}` : `${hi}:${lo}`;
    }
    if (field.bit !== undefined)
        return `${field.bit}`;
    return '';
}
function getFieldRange(field) {
    if ((field === null || field === void 0 ? void 0 : field.bit_range) && Array.isArray(field.bit_range) && field.bit_range.length === 2) {
        const hi = Number(field.bit_range[0]);
        const lo = Number(field.bit_range[1]);
        if (!Number.isFinite(hi) || !Number.isFinite(lo))
            return null;
        return { lo: Math.min(lo, hi), hi: Math.max(lo, hi) };
    }
    if ((field === null || field === void 0 ? void 0 : field.bit) !== undefined) {
        const b = Number(field.bit);
        if (!Number.isFinite(b))
            return null;
        return { lo: b, hi: b };
    }
    return null;
}
function bitAt(value, bitIndex) {
    if (!Number.isFinite(value) || bitIndex < 0)
        return 0;
    // Avoid 32-bit-only bitwise ops; support up to ~53 bits safely.
    const div = Math.floor(value / Math.pow(2, bitIndex));
    return (div % 2) === 1 ? 1 : 0;
}
function setBit(value, bitIndex, desired) {
    const base = Number.isFinite(value) ? Math.max(0, Math.trunc(value)) : 0;
    if (bitIndex < 0)
        return base;
    const current = bitAt(base, bitIndex);
    if (current === desired)
        return base;
    const delta = Math.pow(2, bitIndex);
    return desired === 1 ? base + delta : Math.max(0, base - delta);
}
function parseRegisterValue(text) {
    const s = text.trim();
    if (!s)
        return null;
    // Accept decimal or 0x-prefixed hex.
    const v = Number.parseInt(s, 0);
    if (!Number.isFinite(v))
        return null;
    return v;
}
function maxForBits(bitCount) {
    if (bitCount <= 0)
        return 0;
    // JS Numbers are safe up to 53 bits of integer precision.
    if (bitCount >= 53)
        return Number.MAX_SAFE_INTEGER;
    return Math.pow(2, bitCount) - 1;
}
function extractBits(value, lo, width) {
    if (!Number.isFinite(value))
        return 0;
    if (width <= 0)
        return 0;
    const shifted = Math.floor(value / Math.pow(2, lo));
    const mask = width >= 53 ? Number.MAX_SAFE_INTEGER : Math.pow(2, width) - 1;
    return shifted % (mask + 1);
}
// Group fields by contiguous bit ranges for pro layout
function groupFields(fields) {
    const groups = [];
    fields.forEach((field, idx) => {
        let start = field.bit;
        let end = field.bit;
        if (field.bit_range) {
            [end, start] = field.bit_range; // [hi, lo]
        }
        if (start > end)
            [start, end] = [end, start];
        groups.push({ idx, start, end, name: field.name, color: getFieldColor(idx) });
    });
    // Sort by start bit descending (MSB on left)
    groups.sort((a, b) => b.start - a.start);
    return groups;
}
const BitFieldVisualizer = ({ fields, hoveredFieldIndex = null, setHoveredFieldIndex = () => { }, registerSize = 32, layout = 'default', onUpdateFieldReset, }) => {
    const [valueView, setValueView] = (0, react_1.useState)('hex');
    const [valueDraft, setValueDraft] = (0, react_1.useState)('');
    const [valueEditing, setValueEditing] = (0, react_1.useState)(false);
    const [valueError, setValueError] = (0, react_1.useState)(null);
    const [dragActive, setDragActive] = (0, react_1.useState)(false);
    const [dragSetTo, setDragSetTo] = (0, react_1.useState)(0);
    const [dragLast, setDragLast] = (0, react_1.useState)(null);
    (0, react_1.useEffect)(() => {
        if (!dragActive)
            return;
        const stop = () => {
            setDragActive(false);
            setDragLast(null);
        };
        window.addEventListener('pointerup', stop);
        window.addEventListener('pointercancel', stop);
        window.addEventListener('blur', stop);
        return () => {
            window.removeEventListener('pointerup', stop);
            window.removeEventListener('pointercancel', stop);
            window.removeEventListener('blur', stop);
        };
    }, [dragActive]);
    const applyBit = (fieldIndex, localBit, desired) => {
        var _a;
        if (!onUpdateFieldReset)
            return;
        const raw = (_a = fields === null || fields === void 0 ? void 0 : fields[fieldIndex]) === null || _a === void 0 ? void 0 : _a.reset_value;
        const current = raw === null || raw === undefined ? 0 : Number(raw);
        const next = setBit(current, localBit, desired);
        onUpdateFieldReset(fieldIndex, next);
    };
    // Build a per-bit array with field index or null
    const bits = Array(registerSize).fill(null);
    fields.forEach((field, idx) => {
        if (field.bit_range) {
            const [hi, lo] = field.bit_range;
            for (let i = lo; i <= hi; ++i)
                bits[i] = idx;
        }
        else if (field.bit !== undefined) {
            bits[field.bit] = idx;
        }
    });
    const bitValues = (0, react_1.useMemo)(() => {
        const values = Array(registerSize).fill(0);
        fields.forEach((field) => {
            const r = getFieldRange(field);
            if (!r)
                return;
            const raw = field === null || field === void 0 ? void 0 : field.reset_value;
            const fieldValue = raw === null || raw === undefined ? 0 : Number(raw);
            for (let bit = r.lo; bit <= r.hi; bit++) {
                const localBit = bit - r.lo;
                values[bit] = bitAt(fieldValue, localBit);
            }
        });
        return values;
    }, [fields, registerSize]);
    const registerValue = (0, react_1.useMemo)(() => {
        let v = 0;
        for (let bit = 0; bit < registerSize; bit++) {
            if (bitValues[bit] === 1)
                v += Math.pow(2, bit);
        }
        return v;
    }, [bitValues, registerSize]);
    const registerValueText = (0, react_1.useMemo)(() => {
        if (valueView === 'dec')
            return registerValue.toString(10);
        return `0x${registerValue.toString(16).toUpperCase()}`;
    }, [registerValue, valueView]);
    (0, react_1.useEffect)(() => {
        if (valueEditing)
            return;
        setValueDraft(registerValueText);
        setValueError(null);
    }, [registerValueText, valueEditing]);
    const validateRegisterValue = (v) => {
        if (v === null)
            return 'Value is required';
        if (!Number.isFinite(v))
            return 'Invalid number';
        if (v < 0)
            return 'Value must be >= 0';
        const max = maxForBits(registerSize);
        if (v > max)
            return `Value too large for ${registerSize} bit(s)`;
        return null;
    };
    const applyRegisterValue = (v) => {
        if (!onUpdateFieldReset)
            return;
        fields.forEach((field, fieldIndex) => {
            const r = getFieldRange(field);
            if (!r)
                return;
            const width = r.hi - r.lo + 1;
            const sub = extractBits(v, r.lo, width);
            onUpdateFieldReset(fieldIndex, sub);
        });
    };
    const commitRegisterValueDraft = () => {
        const parsed = parseRegisterValue(valueDraft);
        const err = validateRegisterValue(parsed);
        setValueError(err);
        if (err || parsed === null)
            return;
        applyRegisterValue(parsed);
    };
    const renderValueBar = () => (react_1.default.createElement("div", { className: "mt-3 flex items-start justify-end gap-3" },
        react_1.default.createElement("div", { className: "text-sm vscode-muted font-mono font-semibold mt-[7px]" }, "Value:"),
        react_1.default.createElement("div", { className: "min-w-[320px] text-base" },
            react_1.default.createElement(react_2.VSCodeTextField, { className: "w-full", value: valueDraft, onFocus: () => setValueEditing(true), onBlur: () => {
                    setValueEditing(false);
                    commitRegisterValueDraft();
                }, onInput: (e) => {
                    var _a;
                    const next = String((_a = e.target.value) !== null && _a !== void 0 ? _a : '');
                    setValueDraft(next);
                    const parsed = parseRegisterValue(next);
                    setValueError(validateRegisterValue(parsed));
                }, onKeyDown: (e) => {
                    var _a, _b;
                    if (e.key !== 'Enter')
                        return;
                    e.preventDefault();
                    e.stopPropagation();
                    commitRegisterValueDraft();
                    setValueEditing(false);
                    // Return focus to the visualizer root.
                    (_b = (_a = e.currentTarget) === null || _a === void 0 ? void 0 : _a.blur) === null || _b === void 0 ? void 0 : _b.call(_a);
                } }),
            valueError ? react_1.default.createElement("div", { className: "text-xs vscode-error mt-1" }, valueError) : null),
        react_1.default.createElement("button", { type: "button", className: "px-3 py-2 text-sm font-semibold border rounded self-start", style: {
                borderColor: 'var(--vscode-button-border, var(--vscode-panel-border))',
                background: 'var(--vscode-button-background)',
                color: 'var(--vscode-button-foreground)',
            }, onMouseEnter: (e) => {
                e.currentTarget.style.background = 'var(--vscode-button-hoverBackground)';
            }, onMouseLeave: (e) => {
                e.currentTarget.style.background = 'var(--vscode-button-background)';
            }, onClick: () => setValueView((v) => (v === 'hex' ? 'dec' : 'hex')), title: "Toggle hex/dec" }, valueView.toUpperCase())));
    if (layout === 'pro') {
        // Grouped, modern layout with floating labels and grid
        const groups = groupFields(fields);
        return (react_1.default.createElement("div", { className: "w-full max-w-4xl" },
            react_1.default.createElement("div", { className: "relative w-full flex items-start" },
                react_1.default.createElement("div", { className: "relative flex flex-row items-end gap-0.5 px-2 pt-12 pb-2 min-h-[64px]" }, groups.map((group) => {
                    const width = group.end - group.start + 1;
                    const isHovered = hoveredFieldIndex === group.idx;
                    const field = fields[group.idx];
                    const fieldReset = (field === null || field === void 0 ? void 0 : field.reset_value) === null || (field === null || field === void 0 ? void 0 : field.reset_value) === undefined ? 0 : Number(field.reset_value);
                    return (react_1.default.createElement("div", { key: group.idx, className: `relative flex flex-col items-center justify-end select-none ${isHovered ? 'z-10' : ''}`, style: { width: `calc(${width} * 2.5rem)` }, onMouseEnter: () => setHoveredFieldIndex(group.idx), onMouseLeave: () => setHoveredFieldIndex(null) },
                        react_1.default.createElement("div", { className: "h-20 w-full rounded-t-md overflow-hidden flex", style: {
                                opacity: 1,
                                transform: isHovered ? 'translateY(-2px)' : undefined,
                                filter: isHovered ? 'saturate(1.15) brightness(1.05)' : undefined,
                                boxShadow: isHovered
                                    ? '0 0 0 2px var(--vscode-focusBorder), 0 10px 20px color-mix(in srgb, var(--vscode-foreground) 22%, transparent)'
                                    : undefined,
                            } }, Array.from({ length: width }).map((_, i) => {
                            const bit = group.end - i;
                            const localBit = bit - group.start;
                            const v = bitAt(fieldReset, localBit);
                            const dragKey = `${group.idx}:${localBit}`;
                            return (react_1.default.createElement("div", { key: i, className: `w-10 h-20 flex items-center justify-center cursor-pointer touch-none ${v === 1 ? 'ring-1 ring-white/70 ring-inset' : ''}`, style: { background: colorMap[group.color] }, onPointerDown: (e) => {
                                    if (!onUpdateFieldReset)
                                        return;
                                    if (e.button !== 0)
                                        return;
                                    e.preventDefault();
                                    e.stopPropagation();
                                    const desired = v === 1 ? 0 : 1;
                                    setDragActive(true);
                                    setDragSetTo(desired);
                                    setDragLast(dragKey);
                                    applyBit(group.idx, localBit, desired);
                                }, onPointerEnter: (e) => {
                                    if (!dragActive)
                                        return;
                                    if (!onUpdateFieldReset)
                                        return;
                                    if (dragLast === dragKey)
                                        return;
                                    e.preventDefault();
                                    e.stopPropagation();
                                    setDragLast(dragKey);
                                    applyBit(group.idx, localBit, dragSetTo);
                                } },
                                react_1.default.createElement("span", { className: `text-sm font-mono text-white/90 select-none ${v === 1 ? 'font-bold' : 'font-normal'}` }, v)));
                        })),
                        react_1.default.createElement("div", { className: "absolute -top-10 left-1/2 -translate-x-1/2 px-2 py-0.5 rounded border shadow text-xs whitespace-nowrap pointer-events-none", style: {
                                background: 'var(--vscode-editorWidget-background)',
                                color: 'var(--vscode-foreground)',
                                borderColor: 'var(--vscode-panel-border)',
                            } },
                            react_1.default.createElement("div", { className: "font-bold" },
                                group.name,
                                react_1.default.createElement("span", { className: "ml-2 vscode-muted font-mono text-[11px]" },
                                    "[",
                                    Math.max(group.start, group.end),
                                    ":",
                                    Math.min(group.start, group.end),
                                    "]")),
                            react_1.default.createElement("div", { className: "text-[11px] vscode-muted font-mono" }, valueView === 'dec' ? Math.trunc(fieldReset).toString(10) : `0x${Math.trunc(fieldReset).toString(16).toUpperCase()}`)),
                        react_1.default.createElement("div", { className: "flex flex-row w-full" }, Array.from({ length: width }).map((_, i) => {
                            const bit = group.end - i;
                            return (react_1.default.createElement("div", { key: bit, className: "w-10 text-center text-[11px] vscode-muted font-mono mt-1" }, bit));
                        }))));
                }))),
            renderValueBar()));
    }
    // Default: simple per-bit grid
    return (react_1.default.createElement("div", { className: "w-full flex flex-col items-center" },
        react_1.default.createElement("div", { className: "flex flex-row-reverse gap-0.5 select-none" }, bits.map((fieldIdx, bit) => {
            const isHovered = fieldIdx !== null && fieldIdx === hoveredFieldIndex;
            const dragKey = fieldIdx !== null ? `${fieldIdx}:${bit}` : null;
            return (react_1.default.createElement("div", { key: bit, className: `w-10 h-20 flex flex-col items-center justify-end cursor-pointer group ${fieldIdx !== null ? 'bg-blue-500' : 'vscode-surface-alt'} ${isHovered ? 'z-10' : ''}`, style: { boxShadow: isHovered ? 'inset 0 0 0 2px var(--vscode-focusBorder)' : undefined }, onMouseEnter: () => fieldIdx !== null && setHoveredFieldIndex(fieldIdx), onMouseLeave: () => setHoveredFieldIndex(null), onPointerDown: (e) => {
                    var _a;
                    if (!onUpdateFieldReset)
                        return;
                    if (fieldIdx === null)
                        return;
                    if (e.button !== 0)
                        return;
                    const r = getFieldRange(fields[fieldIdx]);
                    if (!r)
                        return;
                    const localBit = bit - r.lo;
                    if (localBit < 0 || localBit > (r.hi - r.lo))
                        return;
                    const raw = (_a = fields[fieldIdx]) === null || _a === void 0 ? void 0 : _a.reset_value;
                    const current = raw === null || raw === undefined ? 0 : Number(raw);
                    const curBit = bitAt(current, localBit);
                    const desired = curBit === 1 ? 0 : 1;
                    e.preventDefault();
                    e.stopPropagation();
                    setDragActive(true);
                    setDragSetTo(desired);
                    setDragLast(`${fieldIdx}:${localBit}`);
                    applyBit(fieldIdx, localBit, desired);
                }, onPointerEnter: (e) => {
                    if (!dragActive)
                        return;
                    if (!onUpdateFieldReset)
                        return;
                    if (fieldIdx === null)
                        return;
                    const r = getFieldRange(fields[fieldIdx]);
                    if (!r)
                        return;
                    const localBit = bit - r.lo;
                    if (localBit < 0 || localBit > (r.hi - r.lo))
                        return;
                    const key = `${fieldIdx}:${localBit}`;
                    if (dragLast === key)
                        return;
                    e.preventDefault();
                    e.stopPropagation();
                    setDragLast(key);
                    applyBit(fieldIdx, localBit, dragSetTo);
                } },
                react_1.default.createElement("span", { className: "text-[10px] vscode-muted font-mono" }, bit),
                react_1.default.createElement("span", { className: "text-[11px] font-mono mb-1" }, bitValues[bit])));
        })),
        react_1.default.createElement("div", { className: "flex flex-row-reverse gap-0.5 mt-1" }, bits.map((fieldIdx, bit) => (react_1.default.createElement("div", { key: bit, className: "w-7 text-center text-[10px] vscode-muted font-mono" }, fieldIdx !== null ? fields[fieldIdx].name : '')))),
        react_1.default.createElement("div", { className: "w-full" }, renderValueBar())));
};
exports.default = BitFieldVisualizer;
//# sourceMappingURL=BitFieldVisualizer.js.map