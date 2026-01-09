import React, { useMemo } from "react";
import { FIELD_COLORS, FIELD_COLOR_KEYS } from "../shared/colors";

interface RegisterMapVisualizerProps {
  registers: any[];
  hoveredRegIndex?: number | null;
  setHoveredRegIndex?: (idx: number | null) => void;
  baseAddress?: number;
}

function getRegColor(idx: number) {
  return FIELD_COLOR_KEYS[idx % FIELD_COLOR_KEYS.length];
}

function toHex(n: number): string {
  return `0x${Math.max(0, n).toString(16).toUpperCase()}`;
}

const RegisterMapVisualizer: React.FC<RegisterMapVisualizerProps> = ({
  registers,
  hoveredRegIndex = null,
  setHoveredRegIndex = () => {},
  baseAddress = 0,
}) => {
  // Group registers
  const groups = useMemo(() => {
    return registers.map((reg, idx) => {
      const offset = reg.address_offset ?? reg.offset ?? idx * 4;
      const size = reg.size ?? 4; // Default 4 bytes (32-bit)
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

  return (
    <div className="w-full">
      <div className="relative w-full flex items-start overflow-x-auto pb-2">
        {/* Register grid background */}
        <div className="relative flex flex-row items-end gap-0 pl-4 pr-2 pt-12 pb-2 min-h-[64px] w-full">
          {groups.map((group, groupIdx) => {
            const isHovered = hoveredRegIndex === group.idx;
            return (
              <div
                key={group.idx}
                className={`relative flex-1 flex flex-col items-center justify-end select-none min-w-[120px] ${isHovered ? "z-10" : ""}`}
                onMouseEnter={() => setHoveredRegIndex(group.idx)}
                onMouseLeave={() => setHoveredRegIndex(null)}
              >
                <div
                  className="h-20 w-full rounded-t-md overflow-hidden flex items-center justify-center px-2"
                  style={{
                    background: FIELD_COLORS[group.color],
                    opacity: 1,
                    transform: isHovered ? "translateY(-2px)" : undefined,
                    filter: isHovered
                      ? "saturate(1.15) brightness(1.05)"
                      : undefined,
                    boxShadow: isHovered
                      ? "0 0 0 2px var(--vscode-focusBorder), 0 10px 20px color-mix(in srgb, var(--vscode-foreground) 22%, transparent)"
                      : undefined,
                  }}
                >
                  <div className="flex flex-col items-center gap-0.5">
                    <span className="text-lg select-none">📋</span>
                    <span className="text-[10px] font-mono text-white/80 font-semibold select-none text-center leading-tight">
                      REG
                    </span>
                  </div>
                </div>
                <div
                  className={`absolute -top-10 px-2 py-0.5 rounded border shadow text-xs whitespace-nowrap pointer-events-none ${
                    groupIdx === 0 ? "left-0" : "left-1/2 -translate-x-1/2"
                  }`}
                  style={{
                    background: "var(--vscode-editorWidget-background)",
                    color: "var(--vscode-foreground)",
                    borderColor: "var(--vscode-panel-border)",
                  }}
                >
                  <div className="font-bold">
                    {group.name}
                    <span className="ml-2 vscode-muted font-mono text-[11px]">
                      [+{toHex(group.offset)}]
                    </span>
                  </div>
                  <div className="text-[11px] vscode-muted font-mono">
                    {toHex(group.absoluteAddress)}
                  </div>
                </div>
                <div className="flex w-full justify-center">
                  <div className="text-center text-[11px] vscode-muted font-mono mt-1">
                    +{toHex(group.offset)}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default RegisterMapVisualizer;
