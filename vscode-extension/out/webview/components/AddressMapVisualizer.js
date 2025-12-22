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
const colorMap = {
    blue: '#3b82f6',
    orange: '#f97316',
    emerald: '#10b981',
    pink: '#ec4899',
    purple: '#a855f7',
    cyan: '#06b6d4',
    amber: '#f59e0b',
    rose: '#f43f5e',
    gray: '#6b7280',
};
const colorKeys = Object.keys(colorMap);
function getBlockColor(idx) {
    return colorKeys[idx % colorKeys.length];
}
function toHex(n) {
    return `0x${Math.max(0, n).toString(16).toUpperCase()}`;
}
const AddressMapVisualizer = ({ blocks, hoveredBlockIndex = null, setHoveredBlockIndex = () => { }, totalAddressSpace = 65536, // Default 64KB
 }) => {
    // Calculate max address to determine total range
    const maxAddress = (0, react_1.useMemo)(() => {
        if (!blocks || blocks.length === 0)
            return totalAddressSpace;
        const max = blocks.reduce((acc, block) => {
            var _a, _b, _c, _d;
            const base = (_b = (_a = block.base_address) !== null && _a !== void 0 ? _a : block.offset) !== null && _b !== void 0 ? _b : 0;
            const size = (_d = (_c = block.size) !== null && _c !== void 0 ? _c : block.range) !== null && _d !== void 0 ? _d : 4096; // Default 4KB
            return Math.max(acc, base + size);
        }, 0);
        return Math.max(max, totalAddressSpace);
    }, [blocks, totalAddressSpace]);
    // Group blocks by address ranges
    const groups = (0, react_1.useMemo)(() => {
        return blocks.map((block, idx) => {
            var _a, _b, _c, _d;
            const base = (_b = (_a = block.base_address) !== null && _a !== void 0 ? _a : block.offset) !== null && _b !== void 0 ? _b : 0;
            const size = (_d = (_c = block.size) !== null && _c !== void 0 ? _c : block.range) !== null && _d !== void 0 ? _d : 4096;
            return {
                idx,
                name: block.name || `Block ${idx}`,
                start: base,
                end: base + size - 1,
                size,
                color: getBlockColor(idx),
                usage: block.usage || 'register',
            };
        });
    }, [blocks]);
    // Calculate visual widths (proportional to combined block sizes, not total address space)
    const visualGroups = (0, react_1.useMemo)(() => {
        const totalBlockSize = groups.reduce((sum, g) => sum + g.size, 0);
        if (totalBlockSize === 0)
            return groups.map(g => (Object.assign(Object.assign({}, g), { widthPercent: 100 / groups.length })));
        return groups.map((group) => {
            const widthPercent = (group.size / totalBlockSize) * 100;
            return Object.assign(Object.assign({}, group), { widthPercent });
        });
    }, [groups]);
    return (react_1.default.createElement("div", { className: "w-full" },
        react_1.default.createElement("div", { className: "relative w-full flex items-start" },
            react_1.default.createElement("div", { className: "absolute inset-0 pointer-events-none fpga-bit-grid-bg bg-[size:32px_48px] rounded-lg" }),
            react_1.default.createElement("div", { className: "relative flex flex-row items-end gap-0 pt-12 pb-2 min-h-[64px] w-full" }, visualGroups.map((group) => {
                const isHovered = hoveredBlockIndex === group.idx;
                return (react_1.default.createElement("div", { key: group.idx, className: `relative flex flex-col items-center justify-end select-none ${isHovered ? 'z-10' : ''}`, style: { width: `${group.widthPercent}%`, minWidth: '120px' }, onMouseEnter: () => setHoveredBlockIndex(group.idx), onMouseLeave: () => setHoveredBlockIndex(null) },
                    react_1.default.createElement("div", { className: "h-20 w-full rounded-t-md overflow-hidden flex items-center justify-center px-2", style: {
                            background: colorMap[group.color],
                            opacity: 1,
                            transform: isHovered ? 'translateY(-2px)' : undefined,
                            filter: isHovered ? 'saturate(1.15) brightness(1.05)' : undefined,
                            boxShadow: isHovered
                                ? '0 0 0 2px var(--vscode-focusBorder), 0 10px 20px color-mix(in srgb, var(--vscode-foreground) 22%, transparent)'
                                : undefined,
                        } },
                        react_1.default.createElement("div", { className: "flex flex-col items-center gap-0.5" },
                            react_1.default.createElement("span", { className: "text-lg select-none" }, group.usage === 'memory' ? '📦' : '📋'),
                            react_1.default.createElement("span", { className: "text-[10px] font-mono text-white/80 font-semibold select-none text-center leading-tight" }, group.usage === 'memory' ? 'MEM' : 'REG'))),
                    react_1.default.createElement("div", { className: "absolute -top-10 left-1/2 -translate-x-1/2 px-2 py-0.5 rounded border shadow text-xs whitespace-nowrap pointer-events-none", style: {
                            background: 'var(--vscode-editorWidget-background)',
                            color: 'var(--vscode-foreground)',
                            borderColor: 'var(--vscode-panel-border)',
                        } },
                        react_1.default.createElement("div", { className: "font-bold" },
                            group.name,
                            react_1.default.createElement("span", { className: "ml-2 vscode-muted font-mono text-[11px]" },
                                "[",
                                toHex(group.start),
                                ":",
                                toHex(group.end),
                                "]")),
                        react_1.default.createElement("div", { className: "text-[11px] vscode-muted font-mono" }, group.size < 1024 ? `${group.size}B` : group.size < 1048576 ? `${(group.size / 1024).toFixed(1)}KB` : `${(group.size / 1048576).toFixed(1)}MB`)),
                    react_1.default.createElement("div", { className: "flex w-full justify-center" },
                        react_1.default.createElement("div", { className: "text-center text-[11px] vscode-muted font-mono mt-1" }, toHex(group.start)))));
            }))),
        react_1.default.createElement("div", { className: "mt-3 flex items-center justify-end gap-3" },
            react_1.default.createElement("div", { className: "text-sm vscode-muted font-mono" },
                "Total Address Space: ",
                toHex(maxAddress)))));
};
exports.default = AddressMapVisualizer;
//# sourceMappingURL=AddressMapVisualizer.js.map