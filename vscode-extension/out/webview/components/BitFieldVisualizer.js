"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const react_1 = __importDefault(require("react"));
const BitFieldVisualizer = ({ fields, registerSize = 32, onFieldSelect }) => {
    // Create an array of 32 bits (or registerSize)
    const bits = Array(registerSize).fill(null);
    // Map fields to bits
    // Note: fields might overlap or be out of order, so we need to be careful.
    // We'll just render the fields as blocks on a timeline from 31 down to 0.
    // Sort fields by offset descending (MSB on left)
    const sortedFields = [...fields].sort((a, b) => (b.bit_offset + b.bit_width) - (a.bit_offset + a.bit_width));
    // Calculate gaps and segments
    const segments = [];
    let currentBit = registerSize;
    sortedFields.forEach(field => {
        const fieldEnd = field.bit_offset + field.bit_width;
        // Check for gap before this field
        if (currentBit > fieldEnd) {
            segments.push({ type: 'gap', width: currentBit - fieldEnd });
        }
        // Add field
        segments.push({ type: 'field', width: field.bit_width, data: field });
        currentBit = field.bit_offset;
    });
    // Check for gap at the end (LSB)
    if (currentBit > 0) {
        segments.push({ type: 'gap', width: currentBit });
    }
    return (react_1.default.createElement("div", { className: "visualizer-container" },
        react_1.default.createElement("div", { className: "bit-scale" },
            react_1.default.createElement("span", null, registerSize - 1),
            react_1.default.createElement("span", null, "0")),
        react_1.default.createElement("div", { className: "bit-bar" }, segments.map((seg, idx) => (react_1.default.createElement("div", { key: idx, className: `bit-segment ${seg.type}`, style: { flex: seg.width }, title: seg.type === 'field' && seg.data ? `${seg.data.name} [${seg.data.bit_offset + seg.data.bit_width - 1}:${seg.data.bit_offset}]` : 'Reserved', onClick: () => seg.type === 'field' && seg.data && onFieldSelect && onFieldSelect(seg.data) }, seg.type === 'field' && seg.data && (react_1.default.createElement("div", { className: "segment-content" },
            react_1.default.createElement("span", { className: "segment-name" }, seg.data.name),
            seg.width > 1 && react_1.default.createElement("span", { className: "segment-bits" },
                seg.width,
                "b")))))))));
};
exports.default = BitFieldVisualizer;
//# sourceMappingURL=BitFieldVisualizer.js.map