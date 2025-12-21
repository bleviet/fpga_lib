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
const Outline = ({ memoryMap, selectedId, onSelect }) => {
    const [expanded, setExpanded] = (0, react_1.useState)(new Set(['root']));
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
    const renderRegister = (reg, blockId) => {
        const id = `${blockId}-reg-${reg.name}`;
        const isSelected = selectedId === id;
        return (react_1.default.createElement("div", { key: id, className: `tree-item ${isSelected ? 'selected' : ''}`, onClick: () => { var _a; return onSelect({ id, type: 'register', object: reg, breadcrumbs: [memoryMap.name, (_a = blockId.split('-block-')[1]) !== null && _a !== void 0 ? _a : '', reg.name] }); }, style: { paddingLeft: '40px' } },
            react_1.default.createElement("span", { className: "codicon codicon-symbol-variable", style: { marginRight: '6px' } }),
            reg.name,
            " ",
            react_1.default.createElement("span", { className: "opacity-50" },
                "@ +0x",
                reg.address_offset.toString(16).toUpperCase())));
    };
    const renderArray = (arr, blockId) => {
        const id = `${blockId}-arr-${arr.name}`;
        const isSelected = selectedId === id;
        const isExpanded = expanded.has(id);
        return (react_1.default.createElement("div", { key: id },
            react_1.default.createElement("div", { className: `tree-item ${isSelected ? 'selected' : ''}`, onClick: () => { var _a; return onSelect({ id, type: 'array', object: arr, breadcrumbs: [memoryMap.name, (_a = blockId.split('-block-')[1]) !== null && _a !== void 0 ? _a : '', arr.name] }); }, style: { paddingLeft: '40px' } },
                react_1.default.createElement("span", { className: `codicon codicon-chevron-${isExpanded ? 'down' : 'right'}`, onClick: (e) => toggleExpand(id, e), style: { marginRight: '6px', cursor: 'pointer' } }),
                react_1.default.createElement("span", { className: "codicon codicon-symbol-array", style: { marginRight: '6px' } }),
                arr.name,
                " ",
                react_1.default.createElement("span", { className: "opacity-50" },
                    "[",
                    arr.count,
                    "]")),
            isExpanded && Array.isArray(arr.children_registers) && (react_1.default.createElement("div", null, arr.children_registers.map((reg) => renderRegister(reg, `${id}-child`))))));
    };
    const renderBlock = (block, mapId) => {
        var _a, _b;
        const id = `${mapId}-block-${block.name}`;
        const isExpanded = expanded.has(id);
        const isSelected = selectedId === id;
        return (react_1.default.createElement("div", { key: id },
            react_1.default.createElement("div", { className: `tree-item ${isSelected ? 'selected' : ''}`, onClick: () => onSelect({ id, type: 'block', object: block, breadcrumbs: [memoryMap.name, block.name] }), style: { paddingLeft: '20px' } },
                react_1.default.createElement("span", { className: `codicon codicon-chevron-${isExpanded ? 'down' : 'right'}`, onClick: (e) => toggleExpand(id, e), style: { marginRight: '6px', cursor: 'pointer' } }),
                react_1.default.createElement("span", { className: "codicon codicon-package", style: { marginRight: '6px' } }),
                block.name,
                " ",
                react_1.default.createElement("span", { className: "opacity-50" },
                    "@ 0x",
                    block.base_address.toString(16).toUpperCase())),
            isExpanded && (react_1.default.createElement("div", null, (_a = block.registers) === null || _a === void 0 ? void 0 :
                _a.map(reg => renderRegister(reg, id)), (_b = block.register_arrays) === null || _b === void 0 ? void 0 :
                _b.map((arr) => renderArray(arr, id))))));
    };
    const rootId = 'root';
    const isRootExpanded = expanded.has(rootId);
    const isRootSelected = selectedId === rootId;
    const filteredBlocks = (0, react_1.useMemo)(() => {
        var _a, _b;
        const q = query.trim().toLowerCase();
        if (!q)
            return (_a = memoryMap.address_blocks) !== null && _a !== void 0 ? _a : [];
        return ((_b = memoryMap.address_blocks) !== null && _b !== void 0 ? _b : []).filter((block) => {
            var _a, _b;
            if (block.name.toLowerCase().includes(q))
                return true;
            const regs = (_a = block.registers) !== null && _a !== void 0 ? _a : [];
            if (regs.some((r) => r.name.toLowerCase().includes(q)))
                return true;
            const arrays = ((_b = block.register_arrays) !== null && _b !== void 0 ? _b : []);
            if (arrays.some((a) => { var _a; return ((_a = a.name) !== null && _a !== void 0 ? _a : '').toLowerCase().includes(q); }))
                return true;
            return false;
        });
    }, [memoryMap, query]);
    return (react_1.default.createElement("div", { className: "outline-shell" },
        react_1.default.createElement("div", { className: "outline-header" }, "Memory Map Outline"),
        react_1.default.createElement("div", { className: "outline-search" },
            react_1.default.createElement("input", { value: query, onChange: (e) => setQuery(e.target.value), placeholder: "Search registers..." })),
        react_1.default.createElement("div", { className: "outline-container" },
            react_1.default.createElement("div", { className: `tree-item ${isRootSelected ? 'selected' : ''}`, onClick: () => onSelect({ id: rootId, type: 'memoryMap', object: memoryMap, breadcrumbs: [memoryMap.name] }) },
                react_1.default.createElement("span", { className: `codicon codicon-chevron-${isRootExpanded ? 'down' : 'right'}`, onClick: (e) => toggleExpand(rootId, e), style: { marginRight: '6px', cursor: 'pointer' } }),
                react_1.default.createElement("span", { className: "codicon codicon-map", style: { marginRight: '6px' } }),
                memoryMap.name || 'Memory Map'),
            isRootExpanded && filteredBlocks.map((block) => renderBlock(block, rootId))),
        react_1.default.createElement("div", { className: "outline-actions" },
            react_1.default.createElement("button", { className: "outline-action", title: "Add Register", disabled: true },
                react_1.default.createElement("span", { className: "codicon codicon-add" }),
                "Reg"),
            react_1.default.createElement("button", { className: "outline-action", title: "Add Array", disabled: true },
                react_1.default.createElement("span", { className: "codicon codicon-add" }),
                "Arr"),
            react_1.default.createElement("button", { className: "outline-action", title: "Delete", disabled: true },
                react_1.default.createElement("span", { className: "codicon codicon-trash" })))));
};
exports.default = Outline;
//# sourceMappingURL=Outline.js.map