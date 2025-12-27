import React, { useState } from 'react';
import { FormField, SelectField, NumberField } from '../../../shared/components';
import { validateVhdlIdentifier, validateUniqueName } from '../../../shared/utils/validation';

interface Port {
    name: string;
    direction: string;
    width?: number;
}

interface PortsTableProps {
    ports: Port[];
    onUpdate: (path: Array<string | number>, value: any) => void;
}

/**
 * Editable table for IP Core ports
 */
export const PortsTable: React.FC<PortsTableProps> = ({ ports, onUpdate }) => {
    const [editingIndex, setEditingIndex] = useState<number | null>(null);
    const [isAdding, setIsAdding] = useState(false);
    const [draft, setDraft] = useState<Port>({
        name: '',
        direction: 'input',
        width: 1,
    });

    const handleSave = () => {
        if (isAdding) {
            onUpdate(['ports'], [...ports, draft]);
        } else if (editingIndex !== null) {
            const updated = [...ports];
            updated[editingIndex] = draft;
            onUpdate(['ports'], updated);
        }
        setIsAdding(false);
        setEditingIndex(null);
    };

    const handleDelete = (index: number) => {
        if (confirm(`Delete port "${ports[index].name}"?`)) {
            onUpdate(['ports'], ports.filter((_, i) => i !== index));
        }
    };

    const existingNames = ports.map(p => p.name).filter((_, i) => i !== editingIndex);
    const nameError = validateVhdlIdentifier(draft.name) || validateUniqueName(draft.name, existingNames);

    // Normalize direction from YAML shorthand to full names
    const normalizeDirection = (dir: string): string => {
        const dirMap: { [key: string]: string } = {
            'in': 'input',
            'out': 'output',
            'inout': 'inout',
            'input': 'input',
            'output': 'output',
        };
        return dirMap[dir] || 'input';
    };

    return (
        <div className="p-6 space-y-4">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-semibold">Ports</h2>
                    <p className="text-sm mt-1" style={{ opacity: 0.7 }}>{ports.length} port{ports.length !== 1 ? 's' : ''}</p>
                </div>
                <button onClick={() => { setIsAdding(true); setDraft({ name: '', direction: 'input', width: 1 }); }} disabled={isAdding || editingIndex !== null} className="px-4 py-2 rounded text-sm flex items-center gap-2" style={{ background: (isAdding || editingIndex !== null) ? 'var(--vscode-button-secondaryBackground)' : 'var(--vscode-button-background)', color: 'var(--vscode-button-foreground)', opacity: (isAdding || editingIndex !== null) ? 0.5 : 1 }}>
                    <span className="codicon codicon-add"></span>Add Port
                </button>
            </div>

            <div className="rounded overflow-hidden" style={{ border: '1px solid var(--vscode-panel-border)' }}>
                <table className="w-full">
                    <thead>
                        <tr style={{ background: 'var(--vscode-editor-background)', borderBottom: '1px solid var(--vscode-panel-border)' }}>
                            <th className="px-4 py-3 text-left text-sm font-semibold">Name</th>
                            <th className="px-4 py-3 text-left text-sm font-semibold">Direction</th>
                            <th className="px-4 py-3 text-left text-sm font-semibold">Width</th>
                            <th className="px-4 py-3 text-right text-sm font-semibold">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {ports.map((port, idx) => (
                            editingIndex === idx ? (
                                <tr key={idx} style={{ background: 'var(--vscode-list-activeSelectionBackground)', borderBottom: '1px solid var(--vscode-panel-border)' }}>
                                    <td className="px-4 py-3"><FormField label="" value={draft.name} onChange={(v: string) => setDraft({ ...draft, name: v })} error={nameError || undefined} placeholder="port_name" required /></td>
                                    <td className="px-4 py-3"><SelectField label="" value={draft.direction} options={[{ value: 'input', label: 'input' }, { value: 'output', label: 'output' }, { value: 'inout', label: 'inout' }]} onChange={(v: string) => setDraft({ ...draft, direction: v })} /></td>
                                    <td className="px-4 py-3"><NumberField label="" value={draft.width || 1} onChange={(v: number) => setDraft({ ...draft, width: v })} min={1} /></td>
                                    <td className="px-4 py-3 text-right">
                                        <button onClick={handleSave} disabled={!!nameError} className="px-3 py-1 rounded text-xs mr-2" style={{ background: !nameError ? 'var(--vscode-button-background)' : 'var(--vscode-button-secondaryBackground)', color: 'var(--vscode-button-foreground)' }}>Save</button>
                                        <button onClick={() => { setEditingIndex(null); }} className="px-3 py-1 rounded text-xs" style={{ background: 'var(--vscode-button-secondaryBackground)', color: 'var(--vscode-button-foreground)' }}>Cancel</button>
                                    </td>
                                </tr>
                            ) : (
                                <tr key={idx} style={{ background: 'var(--vscode-editor-background)', borderBottom: '1px solid var(--vscode-panel-border)' }} onMouseEnter={(e) => e.currentTarget.style.background = 'var(--vscode-list-hoverBackground)'} onMouseLeave={(e) => e.currentTarget.style.background = 'var(--vscode-editor-background)'}>
                                    <td className="px-4 py-3 text-sm font-mono">{port.name}</td>
                                    <td className="px-4 py-3 text-sm">{port.direction}</td>
                                    <td className="px-4 py-3 text-sm">{port.width || 1}</td>
                                    <td className="px-4 py-3 text-right">
                                        <button onClick={() => { setEditingIndex(idx); setDraft({ ...port, direction: normalizeDirection(port.direction) }); }} disabled={isAdding || editingIndex !== null} className="p-1 mr-2" title="Edit"><span className="codicon codicon-edit"></span></button>
                                        <button onClick={() => handleDelete(idx)} disabled={isAdding || editingIndex !== null} className="p-1" style={{ color: 'var(--vscode-errorForeground)' }} title="Delete"><span className="codicon codicon-trash"></span></button>
                                    </td>
                                </tr>
                            )
                        ))}
                        {isAdding && (
                            <tr style={{ background: 'var(--vscode-list-activeSelectionBackground)', borderBottom: '1px solid var(--vscode-panel-border)' }}>
                                <td className="px-4 py-3"><FormField label="" value={draft.name} onChange={(v: string) => setDraft({ ...draft, name: v })} error={nameError || undefined} placeholder="port_name" required /></td>
                                <td className="px-4 py-3"><SelectField label="" value={draft.direction} options={[{ value: 'input', label: 'input' }, { value: 'output', label: 'output' }, { value: 'inout', label: 'inout' }]} onChange={(v: string) => setDraft({ ...draft, direction: v })} /></td>
                                <td className="px-4 py-3"><NumberField label="" value={draft.width || 1} onChange={(v: number) => setDraft({ ...draft, width: v })} min={1} /></td>
                                <td className="px-4 py-3 text-right">
                                    <button onClick={handleSave} disabled={!!nameError} className="px-3 py-1 rounded text-xs mr-2" style={{ background: !nameError ? 'var(--vscode-button-background)' : 'var(--vscode-button-secondaryBackground)', color: 'var(--vscode-button-foreground)' }}>Add</button>
                                    <button onClick={() => setIsAdding(false)} className="px-3 py-1 rounded text-xs" style={{ background: 'var(--vscode-button-secondaryBackground)', color: 'var(--vscode-button-foreground)' }}>Cancel</button>
                                </td>
                            </tr>
                        )}
                        {ports.length === 0 && !isAdding && (
                            <tr><td colSpan={4} className="px-4 py-8 text-center text-sm" style={{ opacity: 0.6 }}>No ports defined.</td></tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};
