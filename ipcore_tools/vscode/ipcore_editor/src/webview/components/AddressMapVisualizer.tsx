import React, { useMemo, useState } from 'react';
import { FIELD_COLORS, FIELD_COLOR_KEYS } from '../shared/colors';

interface AddressMapVisualizerProps {
  blocks: any[];
  hoveredBlockIndex?: number | null;
  setHoveredBlockIndex?: (idx: number | null) => void;
  totalAddressSpace?: number;
}

function getBlockColor(idx: number) {
  return FIELD_COLOR_KEYS[idx % FIELD_COLOR_KEYS.length];
}

function toHex(n: number): string {
  return `0x${Math.max(0, n).toString(16).toUpperCase()}`;
}

const AddressMapVisualizer: React.FC<AddressMapVisualizerProps> = ({
  blocks,
  hoveredBlockIndex = null,
  setHoveredBlockIndex = () => { },
  totalAddressSpace = 65536, // Default 64KB
}) => {
  // Calculate max address to determine total range
  const maxAddress = useMemo(() => {
    if (!blocks || blocks.length === 0) {
      return totalAddressSpace;
    }
    const max = blocks.reduce((acc, block) => {
      const base = block.base_address ?? block.offset ?? 0;
      const size = block.size ?? block.range ?? 4096; // Default 4KB
      return Math.max(acc, base + size);
    }, 0);
    return Math.max(max, totalAddressSpace);
  }, [blocks, totalAddressSpace]);

  // Group blocks by address ranges
  const groups = useMemo(() => {
    return blocks.map((block, idx) => {
      const base = block.base_address ?? block.offset ?? 0;
      const size = block.size ?? block.range ?? 4096;
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
  const visualGroups = useMemo(() => {
    const totalBlockSize = groups.reduce((sum, g) => sum + g.size, 0);
    if (totalBlockSize === 0) {
      return groups.map((g) => ({ ...g, widthPercent: 100 / groups.length }));
    }
    return groups.map((group) => {
      const widthPercent = (group.size / totalBlockSize) * 100;
      return { ...group, widthPercent };
    });
  }, [groups]);

  return (
    <div className="w-full">
      <div className="relative w-full flex items-start">
        {/* Address grid background */}
        <div className="absolute inset-0 pointer-events-none fpga-bit-grid-bg bg-[size:32px_48px] rounded-lg" />
        <div className="relative flex flex-row items-end gap-0 pt-12 pb-2 min-h-[64px] w-full">
          {visualGroups.map((group) => {
            const isHovered = hoveredBlockIndex === group.idx;
            return (
              <div
                key={group.idx}
                className={`relative flex flex-col items-center justify-end select-none ${isHovered ? 'z-10' : ''}`}
                style={{ width: `${group.widthPercent}%`, minWidth: '120px' }}
                onMouseEnter={() => setHoveredBlockIndex(group.idx)}
                onMouseLeave={() => setHoveredBlockIndex(null)}
              >
                <div
                  className="h-20 w-full rounded-t-md overflow-hidden flex items-center justify-center px-2"
                  style={{
                    background: FIELD_COLORS[group.color],
                    opacity: 1,
                    transform: isHovered ? 'translateY(-2px)' : undefined,
                    filter: isHovered ? 'saturate(1.15) brightness(1.05)' : undefined,
                    boxShadow: isHovered
                      ? '0 0 0 2px var(--vscode-focusBorder), 0 10px 20px color-mix(in srgb, var(--vscode-foreground) 22%, transparent)'
                      : undefined,
                  }}
                >
                  <div className="flex flex-col items-center gap-0.5">
                    <span className="text-lg select-none">
                      {group.usage === 'memory' ? '📦' : '📋'}
                    </span>
                    <span className="text-[10px] font-mono text-white/80 font-semibold select-none text-center leading-tight">
                      {group.usage === 'memory' ? 'MEM' : 'REG'}
                    </span>
                  </div>
                </div>
                <div
                  className="absolute -top-10 left-1/2 -translate-x-1/2 px-2 py-0.5 rounded border shadow text-xs whitespace-nowrap pointer-events-none"
                  style={{
                    background: 'var(--vscode-editorWidget-background)',
                    color: 'var(--vscode-foreground)',
                    borderColor: 'var(--vscode-panel-border)',
                  }}
                >
                  <div className="font-bold">
                    {group.name}
                    <span className="ml-2 vscode-muted font-mono text-[11px]">
                      [{toHex(group.start)}:{toHex(group.end)}]
                    </span>
                  </div>
                  <div className="text-[11px] vscode-muted font-mono">
                    {group.size < 1024
                      ? `${group.size}B`
                      : group.size < 1048576
                        ? `${(group.size / 1024).toFixed(1)}KB`
                        : `${(group.size / 1048576).toFixed(1)}MB`}
                  </div>
                </div>
                <div className="flex w-full justify-center">
                  <div className="text-center text-[11px] vscode-muted font-mono mt-1">
                    {toHex(group.start)}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
      <div className="mt-3 flex items-center justify-end gap-3">
        <div className="text-sm vscode-muted font-mono">
          Total Address Space: {toHex(maxAddress)}
        </div>
      </div>
    </div>
  );
};

export default AddressMapVisualizer;
