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
const client_1 = require("react-dom/client");
const js_yaml_1 = __importDefault(require("js-yaml"));
const Outline_1 = __importDefault(require("./components/Outline"));
const DetailsPanel_1 = __importDefault(require("./components/DetailsPanel"));
const vscode_1 = require("./vscode");
require("./index.css");
const App = () => {
    const [memoryMap, setMemoryMap] = (0, react_1.useState)(null);
    const [error, setError] = (0, react_1.useState)(null);
    const [rawText, setRawText] = (0, react_1.useState)('');
    const [fileName, setFileName] = (0, react_1.useState)('');
    const [selectedId, setSelectedId] = (0, react_1.useState)(null);
    const [selectedType, setSelectedType] = (0, react_1.useState)(null);
    const [selectedObject, setSelectedObject] = (0, react_1.useState)(null);
    const [breadcrumbs, setBreadcrumbs] = (0, react_1.useState)([]);
    const [activeTab, setActiveTab] = (0, react_1.useState)('properties');
    const didInitSelectionRef = (0, react_1.useRef)(false);
    (0, react_1.useEffect)(() => {
        const handleMessage = (event) => {
            var _a, _b;
            const message = event.data;
            if (message.type === 'update') {
                try {
                    const nextRawText = String((_a = message.text) !== null && _a !== void 0 ? _a : '');
                    setRawText(nextRawText);
                    setFileName(String((_b = message.fileName) !== null && _b !== void 0 ? _b : ''));
                    const data = js_yaml_1.default.load(message.text);
                    // Normalize the data structure
                    let map;
                    if (Array.isArray(data)) {
                        map = data[0];
                    }
                    else if (data.memory_maps) {
                        map = data.memory_maps[0];
                    }
                    else {
                        map = data;
                    }
                    // Normalize camelCase to snake_case for consistency with types
                    const normalized = normalizeMemoryMap(map);
                    setMemoryMap(normalized);
                    setError(null);
                    // Auto-select root on first load
                    if (!didInitSelectionRef.current) {
                        setSelectedId('root');
                        setSelectedType('memoryMap');
                        setSelectedObject(normalized);
                        setBreadcrumbs([normalized.name || 'Memory Map']);
                        didInitSelectionRef.current = true;
                    }
                }
                catch (e) {
                    setError(e.message);
                }
            }
        };
        window.addEventListener('message', handleMessage);
        return () => window.removeEventListener('message', handleMessage);
    }, []);
    const normalizeMemoryMap = (data) => {
        var _a;
        // Convert camelCase to snake_case
        return {
            name: data.name,
            description: data.description,
            address_blocks: (_a = data.addressBlocks) === null || _a === void 0 ? void 0 : _a.map((block) => {
                var _a, _b;
                return ({
                    name: block.name,
                    base_address: block.offset || block.base_address || 0,
                    range: block.range || '4K',
                    usage: block.usage || 'register',
                    access: block.access,
                    description: block.description,
                    registers: (_a = block.registers) === null || _a === void 0 ? void 0 : _a.map((reg) => normalizeRegister(reg)),
                    register_arrays: (_b = block.register_arrays) === null || _b === void 0 ? void 0 : _b.map((arr) => ({
                        name: arr.name,
                        base_address: arr.base_address || 0,
                        count: arr.count || 1,
                        stride: arr.stride || 4,
                        template: normalizeRegister(arr.template || {}),
                        description: arr.description
                    }))
                });
            })
        };
    };
    const normalizeRegister = (reg) => {
        var _a;
        return {
            name: reg.name,
            address_offset: reg.offset || reg.address_offset || 0,
            size: reg.size || 32,
            access: reg.access,
            reset_value: reg.reset_value,
            description: reg.description,
            fields: (_a = reg.fields) === null || _a === void 0 ? void 0 : _a.map((field) => normalizeField(field))
        };
    };
    const normalizeField = (field) => {
        // Parse bits field if it's a string like "[31:0]" or "[0:0]"
        let bit_offset = field.bit_offset || 0;
        let bit_width = field.bit_width || 1;
        if (field.bits && typeof field.bits === 'string') {
            const match = field.bits.match(/\[(\d+)(?::(\d+))?\]/);
            if (match) {
                const high = parseInt(match[1]);
                const low = match[2] ? parseInt(match[2]) : high;
                bit_offset = low;
                bit_width = high - low + 1;
            }
        }
        return {
            name: field.name,
            bit_offset,
            bit_width,
            access: field.access,
            reset_value: field.reset_value,
            description: field.description,
            enumerated_values: field.enumerated_values
        };
    };
    const handleSelect = (selection) => {
        setSelectedId(selection.id);
        setSelectedType(selection.type);
        setSelectedObject(selection.object);
        setBreadcrumbs(selection.breadcrumbs);
    };
    const handleUpdate = (path, value) => {
        console.log('Update requested:', path, value);
    };
    const headerTitle = (0, react_1.useMemo)(() => {
        if (fileName)
            return fileName;
        return 'Memory Map Editor';
    }, [fileName]);
    const sendCommand = (command) => {
        vscode_1.vscode === null || vscode_1.vscode === void 0 ? void 0 : vscode_1.vscode.postMessage({ type: 'command', command });
    };
    if (error) {
        return react_1.default.createElement("div", { className: "error-container" },
            "Error parsing YAML: ",
            error);
    }
    if (!memoryMap) {
        return react_1.default.createElement("div", { className: "loading" }, "Loading...");
    }
    return (react_1.default.createElement("div", { className: "app-shell" },
        react_1.default.createElement("div", { className: "app-header" },
            react_1.default.createElement("div", { className: "header-left" },
                react_1.default.createElement("span", { className: "codicon codicon-chip" }),
                react_1.default.createElement("span", { className: "header-title" }, headerTitle)),
            react_1.default.createElement("div", { className: "header-actions" },
                react_1.default.createElement("button", { className: "toolbar-button", onClick: () => sendCommand('validate'), title: "Validate YAML" },
                    react_1.default.createElement("span", { className: "codicon codicon-check" }),
                    "Validate"),
                react_1.default.createElement("button", { className: "toolbar-button", onClick: () => sendCommand('save'), title: "Save file" },
                    react_1.default.createElement("span", { className: "codicon codicon-save" }),
                    "Save"))),
        react_1.default.createElement("div", { className: "app-body" },
            react_1.default.createElement("div", { className: "sidebar" },
                react_1.default.createElement(Outline_1.default, { memoryMap: memoryMap, selectedId: selectedId, onSelect: handleSelect })),
            react_1.default.createElement("div", { className: "main-content" },
                react_1.default.createElement("div", { className: "main-chrome" },
                    react_1.default.createElement("div", { className: "breadcrumbs", title: breadcrumbs.join(' / ') }, breadcrumbs.length ? breadcrumbs.join(' / ') : '—'),
                    react_1.default.createElement("div", { className: "tabbar", role: "tablist", "aria-label": "Editor tabs" },
                        react_1.default.createElement("button", { className: `tab ${activeTab === 'properties' ? 'active' : ''}`, onClick: () => setActiveTab('properties'), role: "tab", "aria-selected": activeTab === 'properties' }, "Properties & Bits"),
                        react_1.default.createElement("button", { className: `tab ${activeTab === 'yaml' ? 'active' : ''}`, onClick: () => setActiveTab('yaml'), role: "tab", "aria-selected": activeTab === 'yaml' }, "Preview (YAML)"))),
                activeTab === 'yaml' ? (react_1.default.createElement("div", { className: "yaml-preview", role: "tabpanel" },
                    react_1.default.createElement("pre", null, rawText))) : (react_1.default.createElement("div", { className: "details-scroll", role: "tabpanel" },
                    react_1.default.createElement(DetailsPanel_1.default, { selectedType: selectedType, selectedObject: selectedObject, onUpdate: handleUpdate })))))));
};
const rootElement = document.getElementById('root');
if (rootElement) {
    const root = (0, client_1.createRoot)(rootElement);
    root.render(react_1.default.createElement(App, null));
}
//# sourceMappingURL=index.js.map