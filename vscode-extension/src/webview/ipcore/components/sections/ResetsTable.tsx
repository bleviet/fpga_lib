import React, { useState } from 'react';
import { FormField, SelectField } from '../../../shared/components';
import { validateVhdlIdentifier, validateUniqueName } from '../../../shared/utils/validation';

interface Reset {
    name: string;
    physicalPort: string;
    polarity: string;
    direction?: string;
}

interface ResetsTableProps {
    resets: Reset[];
    onUpdate: (path: Array<string | number>, value: any) => void;
}

/**
 * Editable table for IP Core resets
 */
export const ResetsTable: React.FC<ResetsTableProps> = ({ resets, onUpdate }) => {
    const [editingIndex, setEditingIndex] = useState<number | null>(null);
    const [isAdding, setIsAdding] = useState(false);
    const [draft, setDraft] = useState<Reset>({
        name: '',
        physicalPort: '',
        polarity: 'active_low',
        direction: 'input',
    });

    const handleAdd = () => {
        setIsAdding(true);
        setDraft({
            name: '',
            physicalPort: '',
            polarity: 'active_low',
            direction: 'input',
        });
    };

    const handleEdit = (index: number) => {
        setEditingIndex(index);
        const reset = resets[index];
        // Normalize polarity to handle both activeLow/activeHigh and active_low/active_high
        const normalizedPolarity = reset.polarity.includes('_')
            ? reset.polarity
            : reset.polarity.replace(/([A-Z])/g, '_$1').toLowerCase();
        setDraft({ ...reset, polarity: normalizedPolarity });
    };

    const handleSave = () => {
        if (isAdding) {
            onUpdate(['resets'], [...resets, draft]);
        } else if (editingIndex !== null) {
            const updated = [...resets];
            updated[editingIndex] = draft;
            onUpdate(['resets'], updated);
        }
        handleCancel();
    };

    const handleCancel = () => {
        setIsAdding(false);
        setEditingIndex(null);
        setDraft({
            name: '',
            physicalPort: '',
            polarity: 'active_low',
            direction: 'input',
        });
    };

    const handleDelete = (index: number) => {
        const confirmed = confirm(`Delete reset "${resets[index].name}"?`);
        if (confirmed) {
            onUpdate(['resets'], resets.filter((_, i) => i !== index));
        }
    };

    const existingNames = resets.map(r => r.name).filter((_, i) => i !== editingIndex);
    const nameError = validateVhdlIdentifier(draft.name) || validateUniqueName(draft.name, existingNames);
    const physicalPortError = validateVhdlIdentifier(draft.physicalPort);
    const canSave = !nameError && !physicalPortError;

    const renderRow = (reset: Reset, index: number, isEditing: boolean) => {
        if (isEditing) {
            return (
                <tr key={index} style={{ background: 'var(--vscode-list-activeSelectionBackground)', borderBottom: '1px solid var(--vscode-panel-border)' }}>
                    <td className="px-4 py-3">
                        <FormField label="" value={draft.name} onChange={(v: string) => setDraft({ ...draft, name: v })} error={nameError || undefined} placeholder="rst_name" required />
                    </td>
                    <td className="px-4 py-3">
                        <FormField label="" value={draft.physicalPort} onChange={(v: string) => setDraft({ ...draft, physicalPort: v })} error={physicalPortError || undefined} placeholder="RST_PORT" required />
                    </td>
                    <td className="px-4 py-3">
                        <SelectField label="" value={draft.polarity} options={[{ value: 'active_low', label: 'active_low' }, { value: 'active_high', label: 'active_high' }]} onChange={(v: string) => setDraft({ ...draft, polarity: v })} />
                    </td>
                    <td className="px-4 py-3">
                        <SelectField label="" value={draft.direction || 'input'} options={[{ value: 'input', label: 'input' }, { value: 'output', label: 'output' }]} onChange={(v: string) => setDraft({ ...draft, direction: v })} />
                    </td>
                    <td className="px-4 py-3 text-right">
                        <button onClick={handleSave} disabled={!canSave} className="px-3 py-1 rounded text-xs mr-2" style={{ background: canSave ? 'var(--vscode-button-background)' : 'var(--vscode-button-secondaryBackground)', color: 'var(--vscode-button-foreground)', opacity: canSave ? 1 : 0.5 }}>Save</button>
                        <button onClick={handleCancel} className="px-3 py-1 rounded text-xs" style={{ background: 'var(--vscode-button-secondaryBackground)', color: 'var(--vscode-button-foreground)' }}>Cancel</button>
                    </td>
                </tr>
            );
        }

        return (
            <tr key={index} style={{ background: 'var(--vscode-editor-background)', borderBottom: '1px solid var(--vscode-panel-border)' }} onMouseEnter={(e) => e.currentTarget.style.background = 'var(--vscode-list-hoverBackground)'} onMouseLeave={(e) => e.currentTarget.style.background = 'var(--vscode-editor-background)'}>
                <td className="px-4 py-3 text-sm font-mono">{reset.name}</td>
                <td className="px-4 py-3 text-sm font-mono">{reset.physicalPort}</td>
                <td className="px-4 py-3 text-sm">{reset.polarity}</td>
                <td className="px-4 py-3 text-sm">{reset.direction || 'input'}</td>
                <td className="px-4 py-3 text-right">
                    <button onClick={() => handleEdit(index)} disabled={isAdding || editingIndex !== null} className="p-1 mr-2" title="Edit"><span className="codicon codicon-edit"></span></button>
                    <button onClick={() => handleDelete(index)} disabled={isAdding || editingIndex !== null} className="p-1" style={{ color: 'var(--vscode-errorForeground)' }} title="Delete"><span className="codicon codicon-trash"></span></button>
                </td>
            </tr>
        );
    };

    return (
        <div className="p-6 space-y-4">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-semibold">Resets</h2>
                    <p className="text-sm mt-1" style={{ opacity: 0.7 }}>{resets.length} reset{resets.length !== 1 ? 's' : ''}</p>
                </div>
                <button onClick={handleAdd} disabled={isAdding || editingIndex !== null} className="px-4 py-2 rounded text-sm flex items-center gap-2" style={{ background: (isAdding || editingIndex !== null) ? 'var(--vscode-button-secondaryBackground)' : 'var(--vscode-button-background)', color: 'var(--vscode-button-foreground)', opacity: (isAdding || editingIndex !== null) ? 0.5 : 1 }}>
                    <span className="codicon codicon-add"></span>Add Reset
                </button>
            </div>

            <div className="rounded overflow-hidden" style={{ border: '1px solid var(--vscode-panel-border)' }}>
                <table className="w-full">
                    <thead>
                        <tr style={{ background: 'var(--vscode-editor-background)', borderBottom: '1px solid var(--vscode-panel-border)' }}>
                            <th className="px-4 py-3 text-left text-sm font-semibold">Name</th>
                            <th className="px-4 py-3 text-left text-sm font-semibold">Physical Port</th>
                            <th className="px-4 py-3 text-left text-sm font-semibold">Polarity</th>
                            <th className="px-4 py-3 text-left text-sm font-semibold">Direction</th>
                            <th className="px-4 py-3 text-right text-sm font-semibold">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {resets.map((reset, index) => renderRow(reset, index, editingIndex === index))}
                        {isAdding && renderRow(draft, -1, true)}
                        {resets.length === 0 && !isAdding && (
                            <tr><td colSpan={5} className="px-4 py-8 text-center text-sm" style={{ opacity: 0.6 }}>No resets defined.</td></tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};
