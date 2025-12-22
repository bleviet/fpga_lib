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
const isArrayNode = (node) => {
    return !!node && typeof node === 'object' && node.__kind === 'array' && typeof node.count === 'number' && typeof node.stride === 'number';
};
const toHex = (n) => `0x${Math.max(0, n).toString(16).toUpperCase()}`;
const Outline = ({ memoryMap, selectedId, onSelect }) => {
    var _a, _b, _c;
    // By default, expand all blocks and registers
    const allIds = (0, react_1.useMemo)(() => {
        var _a;
        const ids = new Set(['root']);
        ((_a = memoryMap.address_blocks) !== null && _a !== void 0 ? _a : []).forEach((block, blockIdx) => {
            var _a, _b;
            const blockId = `block-${blockIdx}`;
            ids.add(blockId);
            const regs = ((_a = block.registers) !== null && _a !== void 0 ? _a : []);
            regs.forEach((reg, regIdx) => {
                if (reg && reg.__kind === 'array') {
                    ids.add(`block-${blockIdx}-arrreg-${regIdx}`);
                }
            });
            ((_b = block.register_arrays) !== null && _b !== void 0 ? _b : []).forEach((arr, arrIdx) => {
                ids.add(`block-${blockIdx}-arr-${arrIdx}`);
            });
        });
        return ids;
    }, [memoryMap]);
    const [expanded, setExpanded] = (0, react_1.useState)(allIds);
    const [query, setQuery] = (0, react_1.useState)('');
    const toggleExpand = (id, e) => {
        e.stopPropagation();
        const newExpanded = new Set(expanded);
        if (newExpanded.has(id)) {
            newExpanded.delete(id);
        }
        else {
            newExpanded.add(id);
        }
        setExpanded(newExpanded);
    };
    const renderLeafRegister = (reg, blockIndex, regIndex) => {
        var _a, _b, _c;
        const id = `block-${blockIndex}-reg-${regIndex}`;
        const isSelected = selectedId === id;
        const block = (_a = memoryMap.address_blocks) === null || _a === void 0 ? void 0 : _a[blockIndex];
        const absolute = ((_b = block === null || block === void 0 ? void 0 : block.base_address) !== null && _b !== void 0 ? _b : 0) + ((_c = reg.address_offset) !== null && _c !== void 0 ? _c : 0);
        return (react_1.default.createElement("div", { key: id, className: `tree-item ${isSelected ? 'selected' : ''} gap-2 text-sm`, onClick: () => {
                var _a, _b, _c, _d;
                return onSelect({
                    id,
                    type: 'register',
                    object: reg,
                    breadcrumbs: [memoryMap.name || 'Memory Map', (_c = (_b = (_a = memoryMap.address_blocks) === null || _a === void 0 ? void 0 : _a[blockIndex]) === null || _b === void 0 ? void 0 : _b.name) !== null && _c !== void 0 ? _c : '', reg.name],
                    path: ['addressBlocks', blockIndex, 'registers', regIndex],
                    meta: { absoluteAddress: absolute, relativeOffset: (_d = reg.address_offset) !== null && _d !== void 0 ? _d : 0 },
                });
            }, style: { paddingLeft: '40px' } },
            react_1.default.createElement("span", { className: `codicon codicon-symbol-variable text-[16px] ${isSelected ? '' : 'opacity-70'}` }),
            react_1.default.createElement("span", { className: "flex-1" }, reg.name),
            react_1.default.createElement("span", { className: "text-[10px] vscode-muted font-mono" }, toHex(reg.address_offset))));
    };
    const renderArrayRegister = (arr, block, blockIndex, regIndex) => {
        var _a, _b;
        const id = `block-${blockIndex}-arrreg-${regIndex}`;
        const isSelected = selectedId === id;
        const isExpanded = expanded.has(id);
        const start = ((_a = block.base_address) !== null && _a !== void 0 ? _a : 0) + ((_b = arr.address_offset) !== null && _b !== void 0 ? _b : 0);
        const end = start + Math.max(1, arr.count) * Math.max(1, arr.stride) - 1;
        return (react_1.default.createElement("div", { key: id },
            react_1.default.createElement("div", { className: `tree-item ${isSelected ? 'selected' : ''}`, onClick: () => onSelect({
                    id,
                    type: 'array',
                    object: arr,
                    breadcrumbs: [memoryMap.name || 'Memory Map', block.name, arr.name],
                    path: ['addressBlocks', blockIndex, 'registers', regIndex],
                }), style: { paddingLeft: '40px' } },
                react_1.default.createElement("span", { className: `codicon codicon-chevron-${isExpanded ? 'down' : 'right'}`, onClick: (e) => toggleExpand(id, e), style: { marginRight: '6px', cursor: 'pointer' } }),
                react_1.default.createElement("span", { className: "codicon codicon-symbol-array", style: { marginRight: '6px' } }),
                arr.name,
                " ",
                react_1.default.createElement("span", { className: "opacity-50" },
                    "@ ",
                    toHex(start),
                    "-",
                    toHex(end),
                    " [",
                    arr.count,
                    "]")),
            isExpanded && (react_1.default.createElement("div", null, Array.from({ length: arr.count }).map((_, elementIndex) => {
                var _a;
                const elementId = `${id}-el-${elementIndex}`;
                const elementBase = start + elementIndex * arr.stride;
                const isElementSelected = selectedId === elementId;
                return (react_1.default.createElement("div", { key: elementId },
                    react_1.default.createElement("div", { className: `tree-item ${isElementSelected ? 'selected' : ''}`, onClick: () => onSelect({
                            id: elementId,
                            type: 'array',
                            object: Object.assign(Object.assign({}, arr), { __element_index: elementIndex, __element_base: elementBase }),
                            breadcrumbs: [memoryMap.name || 'Memory Map', block.name, `${arr.name}[${elementIndex}]`],
                            path: ['addressBlocks', blockIndex, 'registers', regIndex],
                        }), style: { paddingLeft: '60px' } },
                        react_1.default.createElement("span", { className: "codicon codicon-symbol-namespace", style: { marginRight: '6px' } }),
                        arr.name,
                        "[",
                        elementIndex,
                        "] ",
                        react_1.default.createElement("span", { className: "opacity-50" },
                            "@ ",
                            toHex(elementBase))), (_a = arr.registers) === null || _a === void 0 ? void 0 :
                    _a.map((reg, childIndex) => {
                        var _a;
                        const childId = `${elementId}-reg-${childIndex}`;
                        const isChildSelected = selectedId === childId;
                        const absolute = elementBase + ((_a = reg.address_offset) !== null && _a !== void 0 ? _a : 0);
                        return (react_1.default.createElement("div", { key: childId, className: `tree-item ${isChildSelected ? 'selected' : ''}`, onClick: () => {
                                var _a;
                                return onSelect({
                                    id: childId,
                                    type: 'register',
                                    object: reg,
                                    breadcrumbs: [memoryMap.name || 'Memory Map', block.name, `${arr.name}[${elementIndex}]`, reg.name],
                                    path: ['addressBlocks', blockIndex, 'registers', regIndex, 'registers', childIndex],
                                    meta: { absoluteAddress: absolute, relativeOffset: (_a = reg.address_offset) !== null && _a !== void 0 ? _a : 0 },
                                });
                            }, style: { paddingLeft: '80px' } },
                            react_1.default.createElement("span", { className: "codicon codicon-symbol-variable", style: { marginRight: '6px' } }),
                            reg.name,
                            " ",
                            react_1.default.createElement("span", { className: "opacity-50" },
                                "@ ",
                                toHex(absolute))));
                    })));
            })))));
    };
    const renderArray = (arr, blockIndex, arrayIndex) => {
        const id = `block-${blockIndex}-arr-${arrayIndex}`;
        const isSelected = selectedId === id;
        const isExpanded = expanded.has(id);
        return (react_1.default.createElement("div", { key: id },
            react_1.default.createElement("div", { className: `tree-item ${isSelected ? 'selected' : ''}`, onClick: () => {
                    var _a, _b, _c;
                    return onSelect({
                        id,
                        type: 'array',
                        object: arr,
                        breadcrumbs: [memoryMap.name || 'Memory Map', (_c = (_b = (_a = memoryMap.address_blocks) === null || _a === void 0 ? void 0 : _a[blockIndex]) === null || _b === void 0 ? void 0 : _b.name) !== null && _c !== void 0 ? _c : '', arr.name],
                        path: ['addressBlocks', blockIndex, 'register_arrays', arrayIndex],
                    });
                }, style: { paddingLeft: '40px' } },
                react_1.default.createElement("span", { className: `codicon codicon-chevron-${isExpanded ? 'down' : 'right'}`, onClick: (e) => toggleExpand(id, e), style: { marginRight: '6px', cursor: 'pointer' } }),
                react_1.default.createElement("span", { className: "codicon codicon-symbol-array", style: { marginRight: '6px' } }),
                arr.name,
                " ",
                react_1.default.createElement("span", { className: "opacity-50" },
                    "[",
                    arr.count,
                    "]")),
            isExpanded && Array.isArray(arr.children_registers) && (react_1.default.createElement("div", null, arr.children_registers.map((reg, idx) => renderLeafRegister(reg, blockIndex, idx))))));
    };
    const renderBlock = (block, blockIndex) => {
        var _a, _b;
        const id = `block-${blockIndex}`;
        const isExpanded = expanded.has(id);
        const isSelected = selectedId === id;
        const regsAny = ((_a = block.registers) !== null && _a !== void 0 ? _a : []);
        return (react_1.default.createElement("div", { key: id },
            react_1.default.createElement("div", { className: `tree-item ${isSelected ? 'selected' : ''}`, onClick: () => onSelect({
                    id,
                    type: 'block',
                    object: block,
                    breadcrumbs: [memoryMap.name || 'Memory Map', block.name],
                    path: ['addressBlocks', blockIndex],
                }), style: { paddingLeft: '20px' } },
                react_1.default.createElement("span", { className: `codicon codicon-chevron-${isExpanded ? 'down' : 'right'}`, onClick: (e) => toggleExpand(id, e), style: { marginRight: '6px', cursor: 'pointer' } }),
                react_1.default.createElement("span", { className: "codicon codicon-package", style: { marginRight: '6px' } }),
                block.name,
                " ",
                react_1.default.createElement("span", { className: "opacity-50" },
                    "@ 0x",
                    block.base_address.toString(16).toUpperCase())),
            isExpanded && (react_1.default.createElement("div", null,
                regsAny.map((node, idx) => {
                    if (isArrayNode(node))
                        return renderArrayRegister(node, block, blockIndex, idx);
                    return renderLeafRegister(node, blockIndex, idx);
                }), (_b = block.register_arrays) === null || _b === void 0 ? void 0 :
                _b.map((arr, idx) => renderArray(arr, blockIndex, idx))))));
    };
    const rootId = 'root';
    const isRootExpanded = expanded.has(rootId);
    const isRootSelected = selectedId === rootId;
    const filteredBlocks = (0, react_1.useMemo)(() => {
        var _a;
        const q = query.trim().toLowerCase();
        const blocks = ((_a = memoryMap.address_blocks) !== null && _a !== void 0 ? _a : []).map((block, index) => ({ block, index }));
        if (!q)
            return blocks;
        return blocks.filter(({ block }) => {
            var _a, _b, _c;
            if (((_a = block.name) !== null && _a !== void 0 ? _a : '').toLowerCase().includes(q))
                return true;
            const regs = ((_b = block.registers) !== null && _b !== void 0 ? _b : []);
            if (regs.some((r) => {
                var _a, _b;
                if (!r)
                    return false;
                if (String((_a = r.name) !== null && _a !== void 0 ? _a : '').toLowerCase().includes(q))
                    return true;
                if (isArrayNode(r)) {
                    return ((_b = r.registers) !== null && _b !== void 0 ? _b : []).some((rr) => { var _a; return String((_a = rr.name) !== null && _a !== void 0 ? _a : '').toLowerCase().includes(q); });
                }
                return false;
            })) {
                return true;
            }
            const arrays = ((_c = block.register_arrays) !== null && _c !== void 0 ? _c : []);
            if (arrays.some((a) => { var _a; return ((_a = a.name) !== null && _a !== void 0 ? _a : '').toLowerCase().includes(q); }))
                return true;
            return false;
        });
    }, [memoryMap, query]);
    return (react_1.default.createElement(react_1.default.Fragment, null,
        react_1.default.createElement("div", { className: "p-3 border-b vscode-border vscode-surface flex items-center gap-2" },
            react_1.default.createElement("div", { className: "relative flex-1" },
                react_1.default.createElement("span", { className: "codicon codicon-search absolute left-2.5 top-2 vscode-muted text-[18px]" }),
                react_1.default.createElement("input", { className: "outline-filter-input w-full pl-9 pr-3 py-1.5 text-sm rounded-md outline-none", placeholder: "Filter registers...", type: "text", value: query, onChange: (e) => setQuery(e.target.value) })),
            react_1.default.createElement("button", { className: "outline-filter-button ml-2 p-2 rounded flex items-center justify-center", title: expanded.size === allIds.size ? 'Collapse All' : 'Expand All', onClick: () => {
                    if (expanded.size === allIds.size) {
                        setExpanded(new Set(['root']));
                    }
                    else {
                        setExpanded(new Set(allIds));
                    }
                } }, expanded.size === allIds.size ? (
            // Collapse All SVG icon
            react_1.default.createElement("svg", { width: "20", height: "20", viewBox: "0 0 20 20", xmlns: "http://www.w3.org/2000/svg" },
                react_1.default.createElement("rect", { x: "3", y: "3", width: "14", height: "14", rx: "3", fill: "none", stroke: "currentColor", strokeWidth: "1.5" }),
                react_1.default.createElement("rect", { x: "6", y: "9", width: "8", height: "2", rx: "1", fill: "currentColor" }))) : (
            // Expand All SVG icon
            react_1.default.createElement("svg", { width: "20", height: "20", viewBox: "0 0 20 20", xmlns: "http://www.w3.org/2000/svg" },
                react_1.default.createElement("rect", { x: "3", y: "3", width: "14", height: "14", rx: "3", fill: "none", stroke: "currentColor", strokeWidth: "1.5" }),
                react_1.default.createElement("rect", { x: "6", y: "9", width: "8", height: "2", rx: "1", fill: "currentColor" }),
                react_1.default.createElement("rect", { x: "9", y: "6", width: "2", height: "8", rx: "1", fill: "currentColor" }))))),
        react_1.default.createElement("div", { className: "flex-1 overflow-y-auto py-2" },
            react_1.default.createElement("div", { className: "px-3 mb-2 text-xs font-bold vscode-muted uppercase tracking-wider" }, "Memory Map"),
            react_1.default.createElement("div", { className: `tree-item ${isRootSelected ? 'selected' : ''} gap-2 text-sm`, onClick: () => onSelect({
                    id: rootId,
                    type: 'memoryMap',
                    object: memoryMap,
                    breadcrumbs: [memoryMap.name || 'Memory Map'],
                    path: [],
                }) },
                react_1.default.createElement("span", { className: `codicon codicon-chevron-${isRootExpanded ? 'down' : 'right'} text-[16px] ${isRootSelected ? '' : 'opacity-70'}`, onClick: (e) => toggleExpand(rootId, e) }),
                react_1.default.createElement("span", { className: `codicon codicon-map text-[16px] ${isRootSelected ? '' : 'opacity-70'}` }),
                react_1.default.createElement("span", { className: "flex-1" }, memoryMap.name || 'Memory Map')),
            isRootExpanded && filteredBlocks.map(({ block, index }) => renderBlock(block, index))),
        react_1.default.createElement("div", { className: "outline-footer p-3 text-xs vscode-muted flex justify-between" },
            react_1.default.createElement("span", null,
                filteredBlocks.length,
                " Items"),
            react_1.default.createElement("span", null,
                "Base: ",
                toHex((_c = (_b = (_a = memoryMap.address_blocks) === null || _a === void 0 ? void 0 : _a[0]) === null || _b === void 0 ? void 0 : _b.base_address) !== null && _c !== void 0 ? _c : 0)))));
};
exports.default = Outline;
//# sourceMappingURL=Outline.js.map