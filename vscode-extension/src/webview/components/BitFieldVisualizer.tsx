import React, { useMemo, useState } from 'react';

interface BitFieldVisualizerProps {
    fields: any[];
    hoveredFieldIndex?: number | null;
    setHoveredFieldIndex?: (idx: number | null) => void;
    registerSize?: number;
    layout?: 'default' | 'pro';
}

const colorMap: Record<string, string> = {
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

function getFieldColor(idx: number) {
    return colorKeys[idx % colorKeys.length];
}

function toBits(field: any) {
    if (field.bit_range) {
        const [hi, lo] = field.bit_range;
        return hi === lo ? `${hi}` : `${hi}:${lo}`;
    }
    if (field.bit !== undefined) return `${field.bit}`;
    return '';
}

function getFieldRange(field: any): { lo: number; hi: number } | null {
    if (field?.bit_range && Array.isArray(field.bit_range) && field.bit_range.length === 2) {
        const hi = Number(field.bit_range[0]);
        const lo = Number(field.bit_range[1]);
        if (!Number.isFinite(hi) || !Number.isFinite(lo)) return null;
        return { lo: Math.min(lo, hi), hi: Math.max(lo, hi) };
    }
    if (field?.bit !== undefined) {
        const b = Number(field.bit);
        if (!Number.isFinite(b)) return null;
        return { lo: b, hi: b };
    }
    return null;
}

function bitAt(value: number, bitIndex: number): 0 | 1 {
    if (!Number.isFinite(value) || bitIndex < 0) return 0;
    // Avoid 32-bit-only bitwise ops; support up to ~53 bits safely.
    const div = Math.floor(value / Math.pow(2, bitIndex));
    return (div % 2) === 1 ? 1 : 0;
}

// Group fields by contiguous bit ranges for pro layout
function groupFields(fields: any[]) {
    const groups: { idx: number; start: number; end: number; name: string; color: string }[] = [];
    fields.forEach((field, idx) => {
        let start = field.bit;
        let end = field.bit;
        if (field.bit_range) {
            [end, start] = field.bit_range; // [hi, lo]
        }
        if (start > end) [start, end] = [end, start];
        groups.push({ idx, start, end, name: field.name, color: getFieldColor(idx) });
    });
    // Sort by start bit descending (MSB on left)
    groups.sort((a, b) => b.start - a.start);
    return groups;
}

const BitFieldVisualizer: React.FC<BitFieldVisualizerProps> = ({ fields, hoveredFieldIndex = null, setHoveredFieldIndex = () => { }, registerSize = 32, layout = 'default' }) => {
    const [valueView, setValueView] = useState<'hex' | 'dec'>('hex');

    // Build a per-bit array with field index or null
    const bits: (number | null)[] = Array(registerSize).fill(null);
    fields.forEach((field, idx) => {
        if (field.bit_range) {
            const [hi, lo] = field.bit_range;
            for (let i = lo; i <= hi; ++i) bits[i] = idx;
        } else if (field.bit !== undefined) {
            bits[field.bit] = idx;
        }
    });

    const bitValues = useMemo(() => {
        const values: (0 | 1)[] = Array(registerSize).fill(0);
        fields.forEach((field) => {
            const r = getFieldRange(field);
            if (!r) return;
            const raw = field?.reset_value;
            const fieldValue = raw === null || raw === undefined ? 0 : Number(raw);
            for (let bit = r.lo; bit <= r.hi; bit++) {
                const localBit = bit - r.lo;
                values[bit] = bitAt(fieldValue, localBit);
            }
        });
        return values;
    }, [fields, registerSize]);

    const registerValue = useMemo(() => {
        let v = 0;
        for (let bit = 0; bit < registerSize; bit++) {
            if (bitValues[bit] === 1) v += Math.pow(2, bit);
        }
        return v;
    }, [bitValues, registerSize]);

    const registerValueText = useMemo(() => {
        if (valueView === 'dec') return registerValue.toString(10);
        return `0x${registerValue.toString(16).toUpperCase()}`;
    }, [registerValue, valueView]);

    if (layout === 'pro') {
        // Grouped, modern layout with floating labels and grid
        const groups = groupFields(fields);
        return (
            <div className="w-full max-w-4xl">
                <div className="relative w-full flex items-start">
                    {/* Bit grid background */}
                    <div className="absolute inset-0 pointer-events-none bg-[linear-gradient(to_right,#e5e7eb_1px,transparent_1px),linear-gradient(to_bottom,#e5e7eb_1px,transparent_1px)] bg-[size:32px_48px] rounded-lg" />
                    <div className="relative flex flex-row items-end gap-0.5 px-2 py-2 min-h-[64px]">
                        {/* Render each field as a colored segment with label */}
                        {groups.map((group) => {
                            const width = group.end - group.start + 1;
                            const isHovered = hoveredFieldIndex === group.idx;
                            const field = fields[group.idx];
                            const fieldReset = field?.reset_value === null || field?.reset_value === undefined ? 0 : Number(field.reset_value);

                            return (
                                <div
                                    key={group.idx}
                                    className="relative flex flex-col items-center justify-end select-none"
                                    style={{ width: `calc(${width} * 2.5rem)` }}
                                    onMouseEnter={() => setHoveredFieldIndex(group.idx)}
                                    onMouseLeave={() => setHoveredFieldIndex(null)}
                                >
                                    <div
                                        className={`h-20 w-full rounded-t-md overflow-hidden flex divide-x divide-white/30 ${isHovered ? 'ring-2 ring-indigo-400 z-10' : ''}`}
                                        style={{ opacity: 0.92 }}
                                    >
                                        {Array.from({ length: width }).map((_, i) => {
                                            const bit = group.end - i;
                                            const localBit = bit - group.start;
                                            const v = bitAt(fieldReset, localBit);
                                            return (
                                                <div
                                                    key={i}
                                                    className="w-10 h-20 flex items-center justify-center"
                                                    style={{ background: colorMap[group.color] }}
                                                >
                                                    <span className="text-sm font-mono text-white/90 select-none">{v}</span>
                                                </div>
                                            );
                                        })}
                                    </div>
                                    <div className="absolute -top-7 left-1/2 -translate-x-1/2 px-2 py-0.5 rounded bg-white/90 border border-gray-200 shadow text-xs font-bold text-gray-900 whitespace-nowrap pointer-events-none">
                                        {group.name}
                                        <span className="ml-2 text-gray-500 font-mono text-[11px]">[{Math.max(group.start, group.end)}:{Math.min(group.start, group.end)}]</span>
                                    </div>
                                    {/* Per-bit numbers below, LSB (right) to MSB (left) */}
                                    <div className="flex flex-row w-full">
                                        {Array.from({ length: width }).map((_, i) => {
                                            const bit = group.end - i;
                                            return (
                                                <div key={bit} className="w-10 text-center text-[11px] text-gray-700 font-mono mt-1">{bit}</div>
                                            );
                                        })}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>

                <div className="mt-2 flex items-center justify-end gap-2">
                    <div className="text-xs text-gray-500 font-mono">Value:</div>
                    <div className="text-sm font-mono text-gray-900">{registerValueText}</div>
                    <button
                        type="button"
                        className="px-2 py-1 text-xs border border-gray-200 rounded bg-white hover:bg-gray-50"
                        onClick={() => setValueView((v) => (v === 'hex' ? 'dec' : 'hex'))}
                        title="Toggle hex/dec"
                    >
                        {valueView.toUpperCase()}
                    </button>
                </div>
            </div>
        );
    }

    // Default: simple per-bit grid
    return (
        <div className="w-full flex flex-col items-center">
            <div className="flex flex-row-reverse gap-0.5 select-none">
                {bits.map((fieldIdx, bit) => {
                    const isHovered = fieldIdx !== null && fieldIdx === hoveredFieldIndex;
                    return (
                        <div
                            key={bit}
                            className={`w-10 h-20 flex flex-col items-center justify-end cursor-pointer group ${fieldIdx !== null ? 'bg-blue-500' : 'bg-gray-200'} ${isHovered ? 'ring-2 ring-indigo-400 z-10' : ''}`}
                            onMouseEnter={() => fieldIdx !== null && setHoveredFieldIndex(fieldIdx)}
                            onMouseLeave={() => setHoveredFieldIndex(null)}
                        >
                            <span className="text-[10px] text-gray-700 font-mono">{bit}</span>
                            <span className="text-[11px] text-gray-900 font-mono mb-1">{bitValues[bit]}</span>
                        </div>
                    );
                })}
            </div>
            <div className="flex flex-row-reverse gap-0.5 mt-1">
                {bits.map((fieldIdx, bit) => (
                    <div key={bit} className="w-7 text-center text-[10px] text-gray-400 font-mono">{fieldIdx !== null ? fields[fieldIdx].name : ''}</div>
                ))}
            </div>

            <div className="mt-2 flex items-center justify-end gap-2 w-full">
                <div className="text-xs text-gray-500 font-mono">Value:</div>
                <div className="text-sm font-mono text-gray-900">{registerValueText}</div>
                <button
                    type="button"
                    className="px-2 py-1 text-xs border border-gray-200 rounded bg-white hover:bg-gray-50"
                    onClick={() => setValueView((v) => (v === 'hex' ? 'dec' : 'hex'))}
                    title="Toggle hex/dec"
                >
                    {valueView.toUpperCase()}
                </button>
            </div>
        </div>
    );
};

export default BitFieldVisualizer;
