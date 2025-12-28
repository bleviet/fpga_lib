import React, { RefObject, useEffect, useRef } from 'react';
import { vscode } from '../../../vscode';
import { MetadataEditor } from '../sections/MetadataEditor';
import { ClocksTable } from '../sections/ClocksTable';
import { ResetsTable } from '../sections/ResetsTable';
import { PortsTable } from '../sections/PortsTable';
import { ParametersTable } from '../sections/ParametersTable';
import { FileSetsEditor } from '../sections/FileSetsEditor';
import { BusInterfacesEditor } from '../sections/BusInterfacesEditor';
import { Section } from '../../hooks/useNavigation';

interface EditorPanelProps {
    selectedSection: Section;
    ipCore: any;
    imports?: { busLibrary?: any };
    onUpdate: (path: Array<string | number>, value: any) => void;
    isFocused?: boolean;
    onFocus?: () => void;
    panelRef?: RefObject<HTMLDivElement>;
}

/**
 * Main editor panel that displays the selected section
 */
export const EditorPanel: React.FC<EditorPanelProps> = ({
    selectedSection,
    ipCore,
    imports = {},
    onUpdate,
    isFocused = false,
    onFocus,
    panelRef,
}) => {
    const contentRef = useRef<HTMLDivElement>(null);

    // Auto-focus the inner table container when panel receives focus
    useEffect(() => {
        if (isFocused && contentRef.current) {
            // Find and focus the first focusable element with tabIndex (table container)
            const focusableElement = contentRef.current.querySelector('[tabindex="0"]') as HTMLElement;
            if (focusableElement) {
                focusableElement.focus();
            }
        }
    }, [isFocused]);

    if (!ipCore) {
        return (
            <div className="flex-1 flex items-center justify-center text-gray-500">
                <p>No IP core loaded</p>
            </div>
        );
    }

    const renderSection = () => {
        switch (selectedSection) {
            case 'metadata':
                return <MetadataEditor ipCore={ipCore} onUpdate={onUpdate} />;
            case 'clocks':
                return <ClocksTable clocks={ipCore.clocks || []} busInterfaces={ipCore.busInterfaces || []} onUpdate={onUpdate} />;
            case 'resets':
                return <ResetsTable resets={ipCore.resets || []} busInterfaces={ipCore.busInterfaces || []} onUpdate={onUpdate} />;
            case 'ports':
                return <PortsTable ports={ipCore.ports || []} onUpdate={onUpdate} />;
            case 'busInterfaces':
                return <BusInterfacesEditor busInterfaces={ipCore.busInterfaces || []} busLibrary={imports.busLibrary} clocks={ipCore.clocks || []} resets={ipCore.resets || []} onUpdate={onUpdate} />;
            case 'memoryMaps':
                return <MemoryMapsSection memoryMaps={ipCore.memoryMaps || []} onUpdate={onUpdate} />;
            case 'parameters':
                return <ParametersTable parameters={ipCore.parameters || []} onUpdate={onUpdate} />;
            case 'fileSets':
                return <FileSetsEditor fileSets={ipCore.fileSets || []} onUpdate={onUpdate} />;
            default:
                return <div>Unknown section</div>;
        }
    };

    return (
        <div
            ref={panelRef}
            tabIndex={-1}
            onClick={onFocus}
            className="flex-1 overflow-y-auto outline-none"
            style={{
                outline: isFocused ? '1px solid var(--vscode-focusBorder)' : 'none',
                outlineOffset: '-1px',
                opacity: isFocused ? 1 : 0.7,
                transition: 'opacity 0.2s'
            }}
        >
            <div ref={contentRef}>
                {renderSection()}
            </div>
        </div>
    );
};

// Placeholder section components (will be replaced as we build editors in Phase 2)
const ClocksSection: React.FC<any> = ({ clocks }) => (
    <div className="p-6 space-y-4">
        <h2 className="text-2xl font-semibold">Clocks</h2>
        <p className="text-sm" style={{ opacity: 0.7 }}>Found {clocks.length} clock(s)</p>
        {clocks.map((clock: any, idx: number) => (
            <div key={idx} className="p-4 rounded shadow" style={{ background: 'var(--vscode-editor-background)', border: '1px solid var(--vscode-panel-border)' }}>
                <p className="font-semibold">{clock.name}</p>
                <p className="text-sm" style={{ opacity: 0.7 }}>Physical Port: {clock.physicalPort}</p>
                <p className="text-sm" style={{ opacity: 0.7 }}>Frequency: {clock.frequency || 'N/A'}</p>
            </div>
        ))}
    </div>
);

const ResetsSection: React.FC<any> = ({ resets }) => (
    <div className="p-6 space-y-4">
        <h2 className="text-2xl font-semibold">Resets</h2>
        <p className="text-sm" style={{ opacity: 0.7 }}>Found {resets.length} reset(s)</p>
        {resets.map((reset: any, idx: number) => (
            <div key={idx} className="p-4 rounded shadow" style={{ background: 'var(--vscode-editor-background)', border: '1px solid var(--vscode-panel-border)' }}>
                <p className="font-semibold">{reset.name}</p>
                <p className="text-sm" style={{ opacity: 0.7 }}>Physical Port: {reset.physicalPort}</p>
                <p className="text-sm" style={{ opacity: 0.7 }}>Polarity: {reset.polarity}</p>
            </div>
        ))}
    </div>
);

const PortsSection: React.FC<any> = ({ ports }) => (
    <div className="p-6 space-y-4">
        <h2 className="text-2xl font-semibold">Ports</h2>
        <p className="text-sm" style={{ opacity: 0.7 }}>Found {ports.length} port(s)</p>
    </div>
);

const BusInterfacesSection: React.FC<any> = ({ busInterfaces }) => (
    <div className="p-6 space-y-4">
        <h2 className="text-2xl font-semibold">Bus Interfaces</h2>
        <p className="text-sm" style={{ opacity: 0.7 }}>Found {busInterfaces.length} bus interface(s)</p>
        {busInterfaces.map((bus: any, idx: number) => (
            <div key={idx} className="p-4 rounded shadow" style={{ background: 'var(--vscode-editor-background)', border: '1px solid var(--vscode-panel-border)' }}>
                <p className="font-semibold">{bus.name}</p>
                <p className="text-sm" style={{ opacity: 0.7 }}>Type: {bus.type}</p>
                <p className="text-sm" style={{ opacity: 0.7 }}>Mode: {bus.mode}</p>
            </div>
        ))}
    </div>
);

const MemoryMapsSection: React.FC<any> = ({ memoryMaps }) => {
    // Check if it's an import object (as per schema using 'import' keyword)
    const importFile = memoryMaps?.import;

    return (
        <div className="p-6 space-y-4">
            <h2 className="text-2xl font-semibold">Memory Maps</h2>

            {importFile ? (
                <div className="p-4 rounded border-l-4" style={{
                    background: 'var(--vscode-editor-background)',
                    border: '1px solid var(--vscode-panel-border)',
                    borderLeftColor: 'var(--vscode-textLink-foreground)'
                }}>
                    <h3 className="font-semibold mb-2">External Memory Map</h3>
                    <p className="text-sm mb-4" style={{ opacity: 0.8 }}>
                        Linked file: <code className="px-1 py-0.5 rounded" style={{ background: 'var(--vscode-textBlockQuote-background)' }}>{importFile}</code>
                    </p>
                    <button
                        onClick={() => vscode.postMessage({ type: 'command', command: 'openFile', path: importFile })}
                        className="px-4 py-2 rounded text-sm flex items-center gap-2"
                        style={{ background: 'var(--vscode-button-background)', color: 'var(--vscode-button-foreground)' }}
                    >
                        <span className="codicon codicon-go-to-file"></span>
                        Open Memory Map Editor
                    </button>
                    <p className="text-xs mt-3 opacity-60">
                        Opens the dedicated Memory Map Editor in a new tab.
                    </p>
                </div>
            ) : (
                <div className="p-8 text-center text-sm" style={{ opacity: 0.6 }}>
                    No external memory map linked. Inline memory maps are not yet supported.
                    {/* TODO: Support creating new memory map file or inline editing */}
                </div>
            )}
        </div>
    );
};

const ParametersSection: React.FC<any> = ({ parameters }) => (
    <div className="p-6 space-y-4">
        <h2 className="text-2xl font-semibold">Parameters</h2>
        <p className="text-sm" style={{ opacity: 0.7 }}>Found {parameters.length} parameter(s)</p>
    </div>
);

const FileSetsSection: React.FC<any> = ({ fileSets }) => (
    <div className="p-6 space-y-4">
        <h2 className="text-2xl font-semibold">File Sets</h2>
        <p className="text-sm" style={{ opacity: 0.7 }}>Found {fileSets.length} file set(s)</p>
    </div>
);
