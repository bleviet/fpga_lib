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
    const selectionRef = (0, react_1.useRef)(null);
    const rawTextRef = (0, react_1.useRef)('');
    (0, react_1.useEffect)(() => {
        const handleMessage = (event) => {
            var _a, _b, _c, _d;
            const message = event.data;
            if (message.type === 'update') {
                try {
                    const nextRawText = String((_a = message.text) !== null && _a !== void 0 ? _a : '');
                    setRawText(nextRawText);
                    rawTextRef.current = nextRawText;
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
                    const resolveFromSelection = (sel) => {
                        var _a, _b, _c;
                        if (!sel)
                            return null;
                        if (sel.type === 'memoryMap') {
                            return { type: 'memoryMap', object: normalized, breadcrumbs: [normalized.name || 'Memory Map'] };
                        }
                        // Selection paths are YAML-style: ['addressBlocks', blockIndex, ...]
                        const blockIndex = typeof sel.path[1] === 'number' ? sel.path[1] : null;
                        if (blockIndex === null)
                            return null;
                        const block = (_a = normalized.address_blocks) === null || _a === void 0 ? void 0 : _a[blockIndex];
                        if (!block)
                            return null;
                        if (sel.type === 'block') {
                            return { type: 'block', object: block, breadcrumbs: [normalized.name || 'Memory Map', block.name] };
                        }
                        const blockRegs = ((_b = block.registers) !== null && _b !== void 0 ? _b : []);
                        if (sel.type === 'array') {
                            const regIndex = typeof sel.path[3] === 'number' ? sel.path[3] : null;
                            if (regIndex === null)
                                return null;
                            const node = blockRegs[regIndex];
                            if (node && node.__kind === 'array') {
                                const arr = node;
                                return { type: 'array', object: arr, breadcrumbs: [normalized.name || 'Memory Map', block.name, arr.name] };
                            }
                            return null;
                        }
                        if (sel.type === 'register') {
                            // Direct register: ['addressBlocks', b, 'registers', r]
                            // Nested register inside array: ['addressBlocks', b, 'registers', r, 'registers', rr]
                            if (sel.path.length === 4) {
                                const regIndex = typeof sel.path[3] === 'number' ? sel.path[3] : null;
                                if (regIndex === null)
                                    return null;
                                const node = blockRegs[regIndex];
                                if (!node || node.__kind === 'array')
                                    return null;
                                const reg = node;
                                return { type: 'register', object: reg, breadcrumbs: [normalized.name || 'Memory Map', block.name, reg.name] };
                            }
                            if (sel.path.length === 6) {
                                const arrIndex = typeof sel.path[3] === 'number' ? sel.path[3] : null;
                                const nestedIndex = typeof sel.path[5] === 'number' ? sel.path[5] : null;
                                if (arrIndex === null || nestedIndex === null)
                                    return null;
                                const node = blockRegs[arrIndex];
                                if (!node || node.__kind !== 'array')
                                    return null;
                                const arr = node;
                                const reg = (_c = arr.registers) === null || _c === void 0 ? void 0 : _c[nestedIndex];
                                if (!reg)
                                    return null;
                                return { type: 'register', object: reg, breadcrumbs: [normalized.name || 'Memory Map', block.name, arr.name, reg.name] };
                            }
                            return null;
                        }
                        return null;
                    };
                    // Auto-select root on first load
                    if (!didInitSelectionRef.current) {
                        setSelectedId('root');
                        setSelectedType('memoryMap');
                        setSelectedObject(normalized);
                        setBreadcrumbs([normalized.name || 'Memory Map']);
                        selectionRef.current = {
                            id: 'root',
                            type: 'memoryMap',
                            object: normalized,
                            breadcrumbs: [normalized.name || 'Memory Map'],
                            path: [],
                        };
                        didInitSelectionRef.current = true;
                    }
                    else {
                        const resolved = resolveFromSelection(selectionRef.current);
                        if (resolved) {
                            setSelectedId((_d = (_c = selectionRef.current) === null || _c === void 0 ? void 0 : _c.id) !== null && _d !== void 0 ? _d : null);
                            setSelectedType(resolved.type);
                            setSelectedObject(resolved.object);
                            setBreadcrumbs(resolved.breadcrumbs);
                        }
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
    const parseNumber = (value, fallback = 0) => {
        if (typeof value === 'number' && Number.isFinite(value))
            return value;
        if (typeof value === 'string') {
            const s = value.trim();
            if (!s)
                return fallback;
            const n = Number.parseInt(s, 0);
            return Number.isFinite(n) ? n : fallback;
        }
        return fallback;
    };
    const getDefaultRegBytes = (block) => {
        var _a, _b;
        const bits = parseNumber((_b = (_a = block.defaultRegWidth) !== null && _a !== void 0 ? _a : block.default_reg_width) !== null && _b !== void 0 ? _b : 32, 32);
        const bytes = Math.max(1, Math.floor(bits / 8));
        return bytes;
    };
    const normalizeRegisterList = (regs, defaultRegBytes) => {
        var _a, _b, _c;
        const out = [];
        let currentOffset = 0;
        for (const entry of regs !== null && regs !== void 0 ? regs : []) {
            const explicitOffset = (_b = (_a = entry.offset) !== null && _a !== void 0 ? _a : entry.address_offset) !== null && _b !== void 0 ? _b : entry.addressOffset;
            if (explicitOffset !== undefined) {
                currentOffset = parseNumber(explicitOffset, currentOffset);
            }
            const isArray = entry && typeof entry === 'object' && entry.count !== undefined && entry.stride !== undefined && Array.isArray(entry.registers);
            if (isArray) {
                const arrayOffset = currentOffset;
                const count = Math.max(1, parseNumber(entry.count, 1));
                const stride = Math.max(1, parseNumber(entry.stride, defaultRegBytes));
                const nested = normalizeRegisterList(entry.registers, defaultRegBytes);
                out.push({
                    __kind: 'array',
                    name: entry.name,
                    address_offset: arrayOffset,
                    count,
                    stride,
                    description: entry.description,
                    registers: nested.filter((n) => n.__kind !== 'array'),
                });
                currentOffset = arrayOffset + count * stride;
                continue;
            }
            const regOffset = currentOffset;
            const normalizedReg = {
                name: entry.name,
                address_offset: regOffset,
                size: parseNumber(entry.size, 32),
                access: entry.access,
                reset_value: entry.reset_value,
                description: entry.description,
                fields: (_c = entry.fields) === null || _c === void 0 ? void 0 : _c.map((field) => normalizeField(field)),
            };
            out.push(normalizedReg);
            currentOffset = regOffset + defaultRegBytes;
        }
        return out;
    };
    const normalizeMemoryMap = (data) => {
        var _a, _b;
        const blocks = (_b = (_a = data.addressBlocks) !== null && _a !== void 0 ? _a : data.address_blocks) !== null && _b !== void 0 ? _b : [];
        return {
            name: data.name,
            description: data.description,
            address_blocks: (blocks !== null && blocks !== void 0 ? blocks : []).map((block) => {
                var _a, _b, _c, _d, _e;
                const defaultRegBytes = getDefaultRegBytes(block);
                const baseAddress = parseNumber((_c = (_b = (_a = block.offset) !== null && _a !== void 0 ? _a : block.base_address) !== null && _b !== void 0 ? _b : block.baseAddress) !== null && _c !== void 0 ? _c : 0, 0);
                const normalizedRegs = normalizeRegisterList((_d = block.registers) !== null && _d !== void 0 ? _d : [], defaultRegBytes);
                return {
                    name: block.name,
                    base_address: baseAddress,
                    range: block.range || '4K',
                    usage: block.usage || 'register',
                    access: block.access,
                    description: block.description,
                    // NOTE: this intentionally holds both registers and arrays; treated as "any" in consumers.
                    registers: normalizedRegs,
                    register_arrays: ((_e = block.register_arrays) !== null && _e !== void 0 ? _e : []).map((arr) => ({
                        name: arr.name,
                        base_address: parseNumber(arr.base_address, 0),
                        count: parseNumber(arr.count, 1),
                        stride: parseNumber(arr.stride, defaultRegBytes),
                        template: normalizeRegister(arr.template || {}),
                        description: arr.description
                    }))
                };
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
        var _a, _b;
        // Parse bits field if it's a string like "[31:0]" or "[0:0]"
        let bit_offset = field.bit_offset || 0;
        let bit_width = field.bit_width || 1;
        if (field.bits && typeof field.bits === 'string') {
            const match = field.bits.match(/\[(\d+)(?::(\d+))?\]/);
            if (match) {
                const high = parseInt(match[1], 10);
                const low = match[2] ? parseInt(match[2], 10) : high;
                bit_offset = Math.min(low, high);
                bit_width = Math.abs(high - low) + 1;
            }
        }
        // Ensure numeric values are valid
        bit_offset = Number.isFinite(Number(bit_offset)) ? Number(bit_offset) : 0;
        bit_width = Number.isFinite(Number(bit_width)) && Number(bit_width) > 0 ? Number(bit_width) : 1;
        return {
            name: field.name,
            bit_offset,
            bit_width,
            access: field.access,
            reset_value: (_b = (_a = field.reset_value) !== null && _a !== void 0 ? _a : field.resetValue) !== null && _b !== void 0 ? _b : field.reset,
            description: field.description,
            enumerated_values: field.enumerated_values
        };
    };
    const handleSelect = (selection) => {
        selectionRef.current = selection;
        setSelectedId(selection.id);
        setSelectedType(selection.type);
        setSelectedObject(selection.object);
        setBreadcrumbs(selection.breadcrumbs);
    };
    const setAtPath = (root, path, value) => {
        if (!path.length) {
            throw new Error('Cannot set empty path');
        }
        let cursor = root;
        for (let i = 0; i < path.length - 1; i++) {
            const key = path[i];
            if (cursor == null)
                throw new Error(`Path not found at ${String(key)}`);
            cursor = cursor[key];
        }
        const last = path[path.length - 1];
        if (cursor == null)
            throw new Error(`Path not found at ${String(last)}`);
        cursor[last] = value;
    };
    const getAtPath = (root, path) => {
        let cursor = root;
        for (const key of path) {
            if (cursor == null)
                return undefined;
            cursor = cursor[key];
        }
        return cursor;
    };
    const deleteAtPath = (root, path) => {
        if (!path.length)
            return;
        let cursor = root;
        for (let i = 0; i < path.length - 1; i++) {
            const key = path[i];
            if (cursor == null)
                return;
            cursor = cursor[key];
        }
        const last = path[path.length - 1];
        if (cursor == null)
            return;
        if (Array.isArray(cursor) && typeof last === 'number') {
            cursor.splice(last, 1);
            return;
        }
        delete cursor[last];
    };
    const getMapRootInfo = (data) => {
        if (Array.isArray(data)) {
            return { root: data, mapPrefix: [0], map: data[0] };
        }
        if (data && typeof data === 'object' && Array.isArray(data.memory_maps)) {
            return { root: data, mapPrefix: ['memory_maps', 0], map: data.memory_maps[0] };
        }
        return { root: data, mapPrefix: [], map: data };
    };
    const dumpYaml = (data) => {
        // NOTE: js-yaml will not preserve comments/formatting.
        return js_yaml_1.default.dump(data, { noRefs: true, sortKeys: false, lineWidth: -1 });
    };
    const handleUpdate = (path, value) => {
        var _a, _b, _c, _d, _e, _f, _g, _h, _j, _k, _l;
        const sel = selectionRef.current;
        if (!sel)
            return;
        const currentText = rawTextRef.current;
        let rootObj;
        try {
            rootObj = js_yaml_1.default.load(currentText);
        }
        catch (err) {
            console.warn('Cannot apply update: YAML parse failed', err);
            return;
        }
        const { root, mapPrefix } = getMapRootInfo(rootObj);
        const parseBitsLike = (text) => {
            const trimmed = String(text !== null && text !== void 0 ? text : '').trim().replace(/\[|\]/g, '');
            if (!trimmed)
                return null;
            const parts = trimmed.split(':').map((p) => Number(String(p).trim()));
            if (parts.some((p) => Number.isNaN(p)))
                return null;
            let msb;
            let lsb;
            if (parts.length === 1) {
                msb = parts[0];
                lsb = parts[0];
            }
            else {
                msb = parts[0];
                lsb = parts[1];
            }
            if (!Number.isFinite(msb) || !Number.isFinite(lsb))
                return null;
            if (msb < lsb)
                [msb, lsb] = [lsb, msb];
            return { bit_offset: lsb, bit_width: msb - lsb + 1 };
        };
        const formatBitsLike = (bit_offset, bit_width) => {
            const lsb = Number(bit_offset);
            const width = Math.max(1, Number(bit_width));
            const msb = lsb + width - 1;
            return `[${msb}:${lsb}]`;
        };
        // Field operations (add/delete/move)
        if (path[0] === '__op' && sel.type === 'register') {
            const op = String((_a = path[1]) !== null && _a !== void 0 ? _a : '');
            const payload = value !== null && value !== void 0 ? value : {};
            const registerYamlPath = [...mapPrefix, ...sel.path];
            const fieldsPath = [...registerYamlPath, 'fields'];
            const current = getAtPath(root, fieldsPath);
            if (!Array.isArray(current)) {
                setAtPath(root, fieldsPath, []);
            }
            const fieldsArr = ((_b = getAtPath(root, fieldsPath)) !== null && _b !== void 0 ? _b : []);
            if (!Array.isArray(fieldsArr))
                return;
            if (op === 'field-add') {
                const afterIndex = typeof payload.afterIndex === 'number' ? payload.afterIndex : -1;
                const insertIndex = Math.max(0, Math.min(fieldsArr.length, afterIndex + 1));
                // Pick a free 1-bit slot in [0..31] as a starting point.
                const currentFields = ((_d = (_c = sel.object) === null || _c === void 0 ? void 0 : _c.fields) !== null && _d !== void 0 ? _d : []);
                const used = new Set();
                for (const f of currentFields) {
                    const o = Number((_e = f === null || f === void 0 ? void 0 : f.bit_offset) !== null && _e !== void 0 ? _e : 0);
                    const w = Number((_f = f === null || f === void 0 ? void 0 : f.bit_width) !== null && _f !== void 0 ? _f : 1);
                    for (let b = o; b < o + w; b++)
                        used.add(b);
                }
                let lsb = 0;
                while (used.has(lsb) && lsb < 32)
                    lsb++;
                const bits = `[${lsb}:${lsb}]`;
                fieldsArr.splice(insertIndex, 0, {
                    name: (_g = payload.name) !== null && _g !== void 0 ? _g : 'NEW_FIELD',
                    bits,
                    access: (_h = payload.access) !== null && _h !== void 0 ? _h : 'read-write',
                    description: (_j = payload.description) !== null && _j !== void 0 ? _j : '',
                });
            }
            if (op === 'field-delete') {
                const index = typeof payload.index === 'number' ? payload.index : -1;
                if (index >= 0 && index < fieldsArr.length) {
                    fieldsArr.splice(index, 1);
                }
            }
            if (op === 'field-move') {
                const index = typeof payload.index === 'number' ? payload.index : -1;
                const delta = typeof payload.delta === 'number' ? payload.delta : 0;
                const next = index + delta;
                if (index >= 0 && next >= 0 && index < fieldsArr.length && next < fieldsArr.length) {
                    const tmp = fieldsArr[index];
                    fieldsArr[index] = fieldsArr[next];
                    fieldsArr[next] = tmp;
                    // Re-pack bit offsets sequentially based on width (Python reference behavior).
                    let offset = 0;
                    for (const f of fieldsArr) {
                        let width = Number(f === null || f === void 0 ? void 0 : f.bit_width);
                        if (!Number.isFinite(width)) {
                            const parsed = parseBitsLike(f === null || f === void 0 ? void 0 : f.bits);
                            width = (_k = parsed === null || parsed === void 0 ? void 0 : parsed.bit_width) !== null && _k !== void 0 ? _k : 1;
                        }
                        width = Math.max(1, Math.min(32, Math.trunc(width)));
                        f.bit_offset = offset;
                        f.bit_width = width;
                        // Keep legacy "bits" in sync if it exists.
                        if (typeof (f === null || f === void 0 ? void 0 : f.bits) === 'string') {
                            f.bits = formatBitsLike(offset, width);
                        }
                        offset += width;
                    }
                }
            }
            const newText = dumpYaml(root);
            rawTextRef.current = newText;
            setRawText(newText);
            vscode_1.vscode === null || vscode_1.vscode === void 0 ? void 0 : vscode_1.vscode.postMessage({ type: 'update', text: newText });
            return;
        }
        const field = path[0];
        if (!field || typeof field !== 'string')
            return;
        // Bit-field edits: ['fields', fieldIndex, key]
        if (field === 'fields' && typeof path[1] === 'number' && typeof path[2] === 'string') {
            const fieldIndex = path[1];
            const fieldKey = path[2];
            const registerYamlPath = [...mapPrefix, ...sel.path];
            const keyMap = {
                name: 'name',
                bits: 'bits',
                access: 'access',
                description: 'description',
                reset: 'reset',
                reset_value: 'reset',
            };
            const yamlKey = (_l = keyMap[fieldKey]) !== null && _l !== void 0 ? _l : fieldKey;
            const fullPath = [...registerYamlPath, 'fields', fieldIndex, yamlKey];
            try {
                if (yamlKey === 'reset' && (value === '' || value === null || value === undefined)) {
                    deleteAtPath(root, fullPath);
                }
                else {
                    setAtPath(root, fullPath, value);
                }
            }
            catch (err) {
                console.warn('Failed to apply field update at path', fullPath, err);
                return;
            }
            const newText = dumpYaml(root);
            rawTextRef.current = newText;
            setRawText(newText);
            vscode_1.vscode === null || vscode_1.vscode === void 0 ? void 0 : vscode_1.vscode.postMessage({ type: 'update', text: newText });
            return;
        }
        const mapFieldToYamlKey = () => {
            // Root fields
            if (sel.type === 'memoryMap') {
                if (field === 'name')
                    return 'name';
                if (field === 'description')
                    return 'description';
            }
            if (sel.type === 'block') {
                if (field === 'name')
                    return 'name';
                if (field === 'description')
                    return 'description';
                // base address editing not implemented
            }
            if (sel.type === 'register') {
                if (field === 'name')
                    return 'name';
                if (field === 'description')
                    return 'description';
                if (field === 'access')
                    return 'access';
                if (field === 'address_offset')
                    return 'offset';
            }
            return field;
        };
        const yamlKey = mapFieldToYamlKey();
        const fullPath = [...mapPrefix, ...sel.path, yamlKey];
        try {
            setAtPath(root, fullPath, value);
        }
        catch (err) {
            console.warn('Failed to apply update at path', fullPath, err);
            return;
        }
        const newText = dumpYaml(root);
        rawTextRef.current = newText;
        setRawText(newText);
        vscode_1.vscode === null || vscode_1.vscode === void 0 ? void 0 : vscode_1.vscode.postMessage({ type: 'update', text: newText });
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
    return (react_1.default.createElement(react_1.default.Fragment, null,
        react_1.default.createElement("header", { className: "h-14 vscode-surface border-b vscode-border flex items-center justify-between px-4 shrink-0 z-20" },
            react_1.default.createElement("div", { className: "flex items-center gap-4" },
                react_1.default.createElement("div", { className: "flex items-center gap-2 font-semibold tracking-tight" },
                    react_1.default.createElement("div", { className: "w-8 h-8 rounded-lg flex items-center justify-center vscode-badge" },
                        react_1.default.createElement("span", { className: "codicon codicon-chip text-[20px]" })),
                    react_1.default.createElement("span", null,
                        "RegEdit ",
                        react_1.default.createElement("span", { className: "vscode-muted font-normal" }, "Pro"))),
                react_1.default.createElement("div", { className: "h-6 w-px mx-2", style: { background: 'var(--vscode-panel-border)' } }),
                react_1.default.createElement("div", { className: "flex items-center gap-2 text-sm vscode-muted" },
                    react_1.default.createElement("span", { className: "cursor-pointer", style: { color: 'var(--vscode-foreground)' } }, headerTitle),
                    breadcrumbs.length > 1 && (react_1.default.createElement(react_1.default.Fragment, null,
                        react_1.default.createElement("span", { className: "codicon codicon-chevron-right text-[16px]" }),
                        react_1.default.createElement("span", { className: "font-medium px-2 py-0.5 rounded vscode-surface-alt", style: { border: '1px solid var(--vscode-panel-border)' } }, breadcrumbs[breadcrumbs.length - 1]))))),
            react_1.default.createElement("div", { className: "flex items-center gap-2" },
                react_1.default.createElement("button", { className: "p-2 rounded-md transition-colors vscode-icon-button", onClick: () => sendCommand('save'), title: "Save" },
                    react_1.default.createElement("span", { className: "codicon codicon-save" })),
                react_1.default.createElement("button", { className: "p-2 rounded-md transition-colors vscode-icon-button", onClick: () => sendCommand('validate'), title: "Validate" },
                    react_1.default.createElement("span", { className: "codicon codicon-check" })),
                react_1.default.createElement("div", { className: "h-6 w-px mx-1", style: { background: 'var(--vscode-panel-border)' } }),
                react_1.default.createElement("button", { className: "p-2 rounded-md transition-colors vscode-icon-button", title: "Export Header" },
                    react_1.default.createElement("span", { className: "codicon codicon-code" })),
                react_1.default.createElement("button", { className: "p-2 rounded-md transition-colors vscode-icon-button", title: "Documentation" },
                    react_1.default.createElement("span", { className: "codicon codicon-book" })))),
        react_1.default.createElement("main", { className: "flex-1 flex overflow-hidden" },
            react_1.default.createElement("aside", { className: "sidebar flex flex-col shrink-0" },
                react_1.default.createElement(Outline_1.default, { memoryMap: memoryMap, selectedId: selectedId, onSelect: handleSelect })),
            activeTab === 'yaml' ? (react_1.default.createElement("section", { className: "flex-1 vscode-surface overflow-auto" },
                react_1.default.createElement("div", { className: "p-6" },
                    react_1.default.createElement("pre", { className: "font-mono text-sm" }, rawText)))) : (react_1.default.createElement(DetailsPanel_1.default, { selectedType: selectedType, selectedObject: selectedObject, onUpdate: handleUpdate })))));
};
class ErrorBoundary extends react_1.default.Component {
    constructor(props) {
        super(props);
        this.state = { error: null, info: null };
    }
    static getDerivedStateFromError(error) {
        return { error, info: null };
    }
    componentDidCatch(error, info) {
        this.setState({ error, info });
    }
    render() {
        var _a;
        if (this.state.error) {
            return (react_1.default.createElement("div", { style: { background: '#fff0f0', color: '#b91c1c', padding: 32, fontFamily: 'monospace' } },
                react_1.default.createElement("h2", { style: { fontWeight: 'bold' } }, "UI Error"),
                react_1.default.createElement("div", null, ((_a = this.state.error) === null || _a === void 0 ? void 0 : _a.message) || String(this.state.error)),
                this.state.info && react_1.default.createElement("pre", { style: { marginTop: 16, fontSize: 12 } }, this.state.info.componentStack)));
        }
        return this.props.children;
    }
}
const rootElement = document.getElementById('root');
if (rootElement) {
    const root = (0, client_1.createRoot)(rootElement);
    root.render(react_1.default.createElement(ErrorBoundary, null,
        react_1.default.createElement(App, null)));
}
//# sourceMappingURL=index.js.map