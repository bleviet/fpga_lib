import React from 'react';
import { Section } from '../../hooks/useNavigation';

interface NavigationSidebarProps {
    selectedSection: Section;
    onNavigate: (section: Section) => void;
    ipCore: any;
}

interface SectionItem {
    id: Section;
    label: string;
    icon: string;
    count?: (ipCore: any) => number;
}

const SECTIONS: SectionItem[] = [
    { id: 'metadata', label: 'Metadata', icon: 'info' },
    { id: 'clocks', label: 'Clocks', icon: 'clock', count: (ip) => ip?.clocks?.length || 0 },
    { id: 'resets', label: 'Resets', icon: 'debug-restart', count: (ip) => ip?.resets?.length || 0 },
    { id: 'ports', label: 'Ports', icon: 'plug', count: (ip) => ip?.ports?.length || 0 },
    { id: 'busInterfaces', label: 'Bus Interfaces', icon: 'circuit-board', count: (ip) => ip?.busInterfaces?.length || 0 },
    { id: 'memoryMaps', label: 'Memory Maps', icon: 'circuit-board', count: (ip) => ip?.memoryMaps?.length || (ip?.imports?.memoryMaps?.length || 0) },
    { id: 'parameters', label: 'Parameters', icon: 'symbol-parameter', count: (ip) => ip?.parameters?.length || 0 },
    { id: 'fileSets', label: 'File Sets', icon: 'files', count: (ip) => ip?.fileSets?.length || 0 },
];

/**
 * Navigation sidebar for IP Core sections
 */
export const NavigationSidebar: React.FC<NavigationSidebarProps> = ({
    selectedSection,
    onNavigate,
    ipCore,
}) => {
    return (
        <div
            className="w-64 flex flex-col"
            style={{
                background: 'var(--vscode-sideBar-background)',
                borderRight: '1px solid var(--vscode-panel-border)',
                color: 'var(--vscode-sideBar-foreground)'
            }}
        >
            <div className="p-4" style={{ borderBottom: '1px solid var(--vscode-panel-border)' }}>
                <h2 className="text-lg font-semibold">IP Core</h2>
                {ipCore?.vlnv && (
                    <p className="text-sm mt-1" style={{ opacity: 0.7 }}>
                        {ipCore.vlnv.vendor} / {ipCore.vlnv.name}
                    </p>
                )}
            </div>

            <nav className="flex-1 overflow-y-auto py-2">
                {SECTIONS.map((section) => {
                    const isActive = selectedSection === section.id;
                    const count = section.count ? section.count(ipCore) : undefined;

                    return (
                        <button
                            key={section.id}
                            onClick={() => onNavigate(section.id)}
                            className="w-full px-4 py-2 text-left flex items-center justify-between transition-colors"
                            style={{
                                background: isActive ? 'var(--vscode-list-activeSelectionBackground)' : 'transparent',
                                color: isActive ? 'var(--vscode-list-activeSelectionForeground)' : 'inherit',
                                borderLeft: isActive ? '4px solid var(--vscode-focusBorder)' : '4px solid transparent',
                            }}
                            onMouseEnter={(e) => {
                                if (!isActive) {
                                    e.currentTarget.style.background = 'var(--vscode-list-hoverBackground)';
                                }
                            }}
                            onMouseLeave={(e) => {
                                if (!isActive) {
                                    e.currentTarget.style.background = 'transparent';
                                }
                            }}
                        >
                            <div className="flex items-center gap-2">
                                <span className={`codicon codicon-${section.icon}`} />
                                <span className="text-sm">{section.label}</span>
                            </div>
                            {count !== undefined && (
                                <span
                                    className="text-xs px-2 py-1 rounded-full"
                                    style={{
                                        background: 'var(--vscode-badge-background)',
                                        color: 'var(--vscode-badge-foreground)'
                                    }}
                                >
                                    {count}
                                </span>
                            )}
                        </button>
                    );
                })}
            </nav>
        </div>
    );
};
