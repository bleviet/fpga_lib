"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const react_1 = __importDefault(require("react"));
const react_2 = require("@vscode/webview-ui-toolkit/react");
const BitFieldVisualizer_1 = __importDefault(require("./BitFieldVisualizer"));
const DetailsPanel = ({ selectedType, selectedObject, onUpdate }) => {
    var _a, _b, _c, _d, _e;
    if (!selectedObject) {
        return react_1.default.createElement("div", { className: "empty-state" }, "Select an item to view details");
    }
    const handleChange = (field, value) => {
        // In a real app, we'd construct the full path. For now, we'll just log it or assume root level of object
        // This needs a more robust state management (Redux/Context) to know the full path of selectedObject
        console.log(`Update ${field} to ${value}`);
        // onUpdate([field], value);
    };
    if (selectedType === 'register') {
        const reg = selectedObject;
        return (react_1.default.createElement("div", { className: "details-form" },
            react_1.default.createElement("h2", null, "Register Properties"),
            react_1.default.createElement("div", { className: "form-group" },
                react_1.default.createElement("label", null, "Name"),
                react_1.default.createElement(react_2.VSCodeTextField, { value: reg.name, onInput: (e) => handleChange('name', e.target.value) })),
            react_1.default.createElement("div", { className: "form-group" },
                react_1.default.createElement("label", null, "Offset"),
                react_1.default.createElement(react_2.VSCodeTextField, { value: `0x${reg.address_offset.toString(16)}` })),
            react_1.default.createElement("div", { className: "form-group" },
                react_1.default.createElement("label", null, "Description"),
                react_1.default.createElement(react_2.VSCodeTextArea, { value: reg.description || '', resize: "vertical" })),
            react_1.default.createElement("h3", null, "Bit Fields"),
            react_1.default.createElement(BitFieldVisualizer_1.default, { fields: reg.fields || [] }),
            react_1.default.createElement("div", { className: "fields-table-container" },
                react_1.default.createElement("table", { className: "fields-table" },
                    react_1.default.createElement("thead", null,
                        react_1.default.createElement("tr", null,
                            react_1.default.createElement("th", null, "Name"),
                            react_1.default.createElement("th", null, "Bits"),
                            react_1.default.createElement("th", null, "Access"),
                            react_1.default.createElement("th", null, "Reset"),
                            react_1.default.createElement("th", null, "Description"))),
                    react_1.default.createElement("tbody", null, (_a = reg.fields) === null || _a === void 0 ? void 0 : _a.map((field, idx) => {
                        var _a;
                        return (react_1.default.createElement("tr", { key: idx },
                            react_1.default.createElement("td", null, field.name),
                            react_1.default.createElement("td", null, field.bit_width === 1 ? field.bit_offset : `${field.bit_offset + field.bit_width - 1}:${field.bit_offset}`),
                            react_1.default.createElement("td", null, field.access),
                            react_1.default.createElement("td", null, field.reset_value !== null ? `0x${(_a = field.reset_value) === null || _a === void 0 ? void 0 : _a.toString(16)}` : '-'),
                            react_1.default.createElement("td", null, field.description)));
                    }))))));
    }
    if (selectedType === 'memoryMap') {
        const map = selectedObject;
        return (react_1.default.createElement("div", { className: "details-form" },
            react_1.default.createElement("h2", null, "Memory Map Overview"),
            react_1.default.createElement("div", { className: "form-group" },
                react_1.default.createElement("label", null, "Name"),
                react_1.default.createElement(react_2.VSCodeTextField, { value: map.name, readOnly: true })),
            react_1.default.createElement("div", { className: "form-group" },
                react_1.default.createElement("label", null, "Description"),
                react_1.default.createElement(react_2.VSCodeTextArea, { value: map.description || '', rows: 3, readOnly: true })),
            react_1.default.createElement("div", { className: "stats" },
                react_1.default.createElement("div", { className: "stat-item" },
                    react_1.default.createElement("span", { className: "stat-label" }, "Address Blocks:"),
                    react_1.default.createElement("span", { className: "stat-value" }, ((_b = map.address_blocks) === null || _b === void 0 ? void 0 : _b.length) || 0)))));
    }
    if (selectedType === 'block') {
        const block = selectedObject;
        return (react_1.default.createElement("div", { className: "details-form" },
            react_1.default.createElement("h2", null, "Address Block Properties"),
            react_1.default.createElement("div", { className: "form-group" },
                react_1.default.createElement("label", null, "Name"),
                react_1.default.createElement(react_2.VSCodeTextField, { value: block.name, readOnly: true })),
            react_1.default.createElement("div", { className: "form-group" },
                react_1.default.createElement("label", null, "Base Address"),
                react_1.default.createElement(react_2.VSCodeTextField, { value: `0x${block.base_address.toString(16).toUpperCase()}`, readOnly: true })),
            react_1.default.createElement("div", { className: "form-group" },
                react_1.default.createElement("label", null, "Range"),
                react_1.default.createElement(react_2.VSCodeTextField, { value: (_c = block.range) === null || _c === void 0 ? void 0 : _c.toString(), readOnly: true })),
            react_1.default.createElement("div", { className: "form-group" },
                react_1.default.createElement("label", null, "Description"),
                react_1.default.createElement(react_2.VSCodeTextArea, { value: block.description || '', rows: 3, readOnly: true })),
            react_1.default.createElement("div", { className: "stats" },
                react_1.default.createElement("div", { className: "stat-item" },
                    react_1.default.createElement("span", { className: "stat-label" }, "Registers:"),
                    react_1.default.createElement("span", { className: "stat-value" }, ((_d = block.registers) === null || _d === void 0 ? void 0 : _d.length) || 0)),
                react_1.default.createElement("div", { className: "stat-item" },
                    react_1.default.createElement("span", { className: "stat-label" }, "Register Arrays:"),
                    react_1.default.createElement("span", { className: "stat-value" }, ((_e = block.register_arrays) === null || _e === void 0 ? void 0 : _e.length) || 0)))));
    }
    return (react_1.default.createElement("div", { className: "details-form" },
        react_1.default.createElement("h2", null,
            selectedType,
            " Properties"),
        react_1.default.createElement("div", { className: "form-group" },
            react_1.default.createElement("label", null, "Name"),
            react_1.default.createElement(react_2.VSCodeTextField, { value: selectedObject.name, readOnly: true })),
        selectedObject.description !== undefined && (react_1.default.createElement("div", { className: "form-group" },
            react_1.default.createElement("label", null, "Description"),
            react_1.default.createElement(react_2.VSCodeTextArea, { value: selectedObject.description || '', readOnly: true })))));
};
exports.default = DetailsPanel;
//# sourceMappingURL=DetailsPanel.js.map