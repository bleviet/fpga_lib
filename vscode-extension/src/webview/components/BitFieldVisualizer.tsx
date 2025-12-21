
import React from 'react';

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

const BitFieldVisualizer: React.FC<BitFieldVisualizerProps> = ({ fields, hoveredFieldIndex = null, setHoveredFieldIndex = () => {}, registerSize = 32, layout = 'default' }) => {
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

        if (layout === 'pro') {
            // Grouped, modern layout with floating labels and grid
            const groups = groupFields(fields);
            return (
                <div className="relative w-full max-w-4xl mx-auto">
                    {/* Bit grid background */}
                    <div className="absolute inset-0 pointer-events-none bg-[linear-gradient(to_right,#e5e7eb_1px,transparent_1px),linear-gradient(to_bottom,#e5e7eb_1px,transparent_1px)] bg-[size:32px_48px] rounded-lg" />
                    <div className="relative flex flex-row items-end gap-0.5 px-2 py-2 min-h-[64px]">
                        {/* Render each field as a colored segment with label */}
                        {groups.map((group) => {
                            const width = group.end - group.start + 1;
                            const isHovered = hoveredFieldIndex === group.idx;
                            // Render bits from LSB (0, right) to MSB (width-1, left)
                            return (
                                <div
                                    key={group.idx}
                                    className="relative flex flex-col items-center justify-end select-none"
                                    style={{ width: `${width * 32}px` }}
                                    onMouseEnter={() => setHoveredFieldIndex(group.idx)}
                                    onMouseLeave={() => setHoveredFieldIndex(null)}
                                >
                                    <div
                                        className={`h-10 w-full rounded-t-md ${isHovered ? 'ring-2 ring-indigo-400 z-10' : ''}`}
                                        style={{ background: colorMap[group.color], opacity: 0.92 }}
                                    ></div>
                                    <div className="absolute -top-7 left-1/2 -translate-x-1/2 px-2 py-0.5 rounded bg-white/90 border border-gray-200 shadow text-xs font-bold text-gray-900 whitespace-nowrap pointer-events-none">
                                        {group.name}
                                        <span className="ml-2 text-gray-500 font-mono text-[11px]">[{Math.max(group.start, group.end)}:{Math.min(group.start, group.end)}]</span>
                                    </div>
                                    {/* Per-bit numbers below, LSB (right) to MSB (left) */}
                                    <div className="flex flex-row w-full">
                                        {Array.from({ length: width }).map((_, i) => {
                                            const bit = group.end - i;
                                            return (
                                                <div key={bit} className="w-8 text-center text-[11px] text-gray-700 font-mono mt-1">{bit}</div>
                                            );
                                        })}
                                    </div>
                                </div>
                            );
                        })}
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
                                className={`w-7 h-10 flex flex-col items-center justify-end cursor-pointer group ${fieldIdx !== null ? 'bg-blue-500' : 'bg-gray-200'} ${isHovered ? 'ring-2 ring-indigo-400 z-10' : ''}`}
                                onMouseEnter={() => fieldIdx !== null && setHoveredFieldIndex(fieldIdx)}
                                onMouseLeave={() => setHoveredFieldIndex(null)}
                            >
                                <span className="text-[10px] text-gray-700 font-mono mb-1">{bit}</span>
                            </div>
                        );
                    })}
                </div>
                <div className="flex flex-row-reverse gap-0.5 mt-1">
                    {bits.map((fieldIdx, bit) => (
                        <div key={bit} className="w-7 text-center text-[10px] text-gray-400 font-mono">{fieldIdx !== null ? fields[fieldIdx].name : ''}</div>
                    ))}
                </div>
            </div>
        );
    };

export default BitFieldVisualizer;
