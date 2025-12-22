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
function getRegColor(idx) {
    return colorKeys[idx % colorKeys.length];
}
function toHex(n) {
    return `0x${Math.max(0, n).toString(16).toUpperCase()}`;
}
const RegisterMapVisualizer = ({ registers, hoveredRegIndex = null, setHoveredRegIndex = () => { }, baseAddress = 0, }) => {
    // Group registers
    const groups = (0, react_1.useMemo)(() => {
        return registers.map((reg, idx) => {
            var _a, _b, _c;
            const offset = (_b = (_a = reg.address_offset) !== null && _a !== void 0 ? _a : reg.offset) !== null && _b !== void 0 ? _b : (idx * 4);
            const size = (_c = reg.size) !== null && _c !== void 0 ? _c : 4; // Default 4 bytes (32-bit)
            return {
                idx,
                name: reg.name || `Reg ${idx}`,
                offset,
                absoluteAddress: baseAddress + offset,
                size,
                color: getRegColor(idx),
            };
        });
    }, [registers, baseAddress]);
    // Calculate visual widths (proportional to combined sizes)
    const visualGroups = (0, react_1.useMemo)(() => {
        const totalSize = groups.reduce((sum, g) => sum + g.size, 0);
        if (totalSize === 0)
            return groups.map(g => (Object.assign(Object.assign({}, g), { widthPercent: 100 / groups.length })));
        return groups.map((group) => {
            const widthPercent = (group.size / totalSize) * 100;
            return Object.assign(Object.assign({}, group), { widthPercent });
        });
    }, [groups]);
    return (react_1.default.createElement("div", { className: "w-full" },
        react_1.default.createElement("div", { className: "relative w-full flex items-start" },
            react_1.default.createElement("div", { className: "relative flex flex-row items-end gap-0 pt-12 pb-2 min-h-[64px] w-full" }, visualGroups.map((group) => {
                const isHovered = hoveredRegIndex === group.idx;
                return (react_1.default.createElement("div", { key: group.idx, className: `relative flex flex-col items-center justify-end select-none ${isHovered ? 'z-10' : ''}`, style: { width: `${group.widthPercent}%`, minWidth: '120px' }, onMouseEnter: () => setHoveredRegIndex(group.idx), onMouseLeave: () => setHoveredRegIndex(null) },
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
                            react_1.default.createElement("span", { className: "text-lg select-none" }, "\uD83D\uDCCB"),
                            react_1.default.createElement("span", { className: "text-[10px] font-mono text-white/80 font-semibold select-none text-center leading-tight" }, "REG"))),
                    react_1.default.createElement("div", { className: "absolute -top-10 left-1/2 -translate-x-1/2 px-2 py-0.5 rounded border shadow text-xs whitespace-nowrap pointer-events-none", style: {
                            background: 'var(--vscode-editorWidget-background)',
                            color: 'var(--vscode-foreground)',
                            borderColor: 'var(--vscode-panel-border)',
                        } },
                        react_1.default.createElement("div", { className: "font-bold" },
                            group.name,
                            react_1.default.createElement("span", { className: "ml-2 vscode-muted font-mono text-[11px]" },
                                "[+",
                                toHex(group.offset),
                                "]")),
                        react_1.default.createElement("div", { className: "text-[11px] vscode-muted font-mono" }, toHex(group.absoluteAddress))),
                    react_1.default.createElement("div", { className: "flex w-full justify-center" },
                        react_1.default.createElement("div", { className: "text-center text-[11px] vscode-muted font-mono mt-1" },
                            "+",
                            toHex(group.offset)))));
            }))),
        react_1.default.createElement("div", { className: "mt-3 flex items-center justify-end gap-3" },
            react_1.default.createElement("div", { className: "text-sm vscode-muted font-mono" },
                "Base: ",
                toHex(baseAddress),
                " | Registers: ",
                registers.length))));
};
exports.default = RegisterMapVisualizer;
//# sourceMappingURL=RegisterMapVisualizer.js.map