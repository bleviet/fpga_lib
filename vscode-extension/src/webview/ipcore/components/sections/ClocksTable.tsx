import React, { useState } from 'react';
import { FormField, SelectField } from '../../../shared/components';
import { validateVhdlIdentifier, validateUniqueName, validateFrequency } from '../../../shared/utils/validation';

interface Clock {
    name: string;
    physicalPort: string;
    frequency?: string;
    direction?: string;
}

interface ClocksTableProps {
    clocks: Clock[];
    onUpdate: (path: Array<string | number>, value: any) => void;
}

/**
 * Editable table for IP Core clocks
 * Supports add, edit, delete operations
 */
export const ClocksTable: React.FC<ClocksTableProps> = ({ clocks, onUpdate }) => {
    const [editingIndex, setEditingIndex] = useState<number | null>(null);
    const [isAdding, setIsAdding] = useState(false);
    const [draft, setDraft] = useState<Clock>({
        name: '',
        physicalPort: '',
        frequency: '',
        direction: 'input',
    });

    const handleAdd = () => {
        setIsAdding(true);
        setDraft({
            name: '',
            physicalPort: '',
            frequency: '',
            direction: 'input',
        });
    };

    const handleEdit = (index: number) => {
        setEditingIndex(index);
        setDraft({ ...clocks[index] });
    };

    const handleSave = () => {
        if (isAdding) {
            // Add new clock
            onUpdate(['clocks'], [...clocks, draft]);
        } else if (editingIndex !== null) {
            // Update existing clock
            const updated = [...clocks];
            updated[editingIndex] = draft;
            onUpdate(['clocks'], updated);
        }
        handleCancel();
    };

    const handleCancel = () => {
        setIsAdding(false);
        setEditingIndex(null);
        setDraft({
            name: '',
            physicalPort: '',
            frequency: '',
            direction: 'input',
        });
    };

    const handleDelete = (index: number) => {
        const clockName = clocks[index].name;
        const confirmed = confirm(`Delete clock "${clockName}"?`);
        if (confirmed) {
            const updated = clocks.filter((_, i) => i !== index);
            onUpdate(['clocks'], updated);
        }
    };

    const existingNames = clocks.map(c => c.name).filter((_, i) => i !== editingIndex);
    const nameError = validateVhdlIdentifier(draft.name) || validateUniqueName(draft.name, existingNames);
    const physicalPortError = validateVhdlIdentifier(draft.physicalPort);
    const frequencyError = validateFrequency(draft.frequency || '');
    const canSave = !nameError && !physicalPortError && !frequencyError;

    return (
        <div className="p-6 space-y-4">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-semibold">Clocks</h2>
                    <p className="text-sm mt-1" style={{ opacity: 0.7 }}>
                        {clocks.length} clock{clocks.length !== 1 ? 's' : ''}
                    </p>
                </div>
                <button
                    onClick={handleAdd}
                    disabled={isAdding || editingIndex !== null}
                    className="px-4 py-2 rounded text-sm font-medium transition-colors flex items-center gap-2"
                    style={{
                        background: (isAdding || editingIndex !== null)
                            ? 'var(--vscode-button-secondaryBackground)'
                            : 'var(--vscode-button-background)',
                        color: 'var(--vscode-button-foreground)',
                        opacity: (isAdding || editingIndex !== null) ? 0.5 : 1,
                        cursor: (isAdding || editingIndex !== null) ? 'not-allowed' : 'pointer',
                    }}
                    onMouseEnter={(e) => {
                        if (!isAdding && editingIndex === null) {
                            e.currentTarget.style.background = 'var(--vscode-button-hoverBackground)';
                        }
                    }}
                    onMouseLeave={(e) => {
                        if (!isAdding && editingIndex === null) {
                            e.currentTarget.style.background = 'var(--vscode-button-background)';
                        }
                    }}
                >
                    <span className="codicon codicon-add"></span>
                    Add Clock
                </button>
            </div>

            {/* Table */}
            <div
                className="rounded overflow-hidden"
                style={{ border: '1px solid var(--vscode-panel-border)' }}
            >
                <table className="w-full">
                    <thead>
                        <tr style={{ background: 'var(--vscode-editor-background)', borderBottom: '1px solid var(--vscode-panel-border)' }}>
                            <th className="px-4 py-3 text-left text-sm font-semibold">Name</th>
                            <th className="px-4 py-3 text-left text-sm font-semibold">Physical Port</th>
                            <th className="px-4 py-3 text-left text-sm font-semibold">Frequency</th>
                            <th className="px-4 py-3 text-left text-sm font-semibold">Direction</th>
                            <th className="px-4 py-3 text-right text-sm font-semibold">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {clocks.map((clock, index) => {
                            const isEditing = editingIndex === index;

                            if (isEditing) {
                                return (
                                    <tr key={index} style={{ background: 'var(--vscode-list-activeSelectionBackground)', borderBottom: '1px solid var(--vscode-panel-border)' }}>
                                        <td className="px-4 py-3">
                                            <FormField
                                                label=""
                                                value={draft.name}
                                                onChange={(value: string) => setDraft({ ...draft, name: value })}
                                                error={nameError || undefined}
                                                placeholder="clk_name"
                                                required
                                            />
                                        </td>
                                        <td className="px-4 py-3">
                                            <FormField
                                                label=""
                                                value={draft.physicalPort}
                                                onChange={(value: string) => setDraft({ ...draft, physicalPort: value })}
                                                error={physicalPortError || undefined}
                                                placeholder="CLK_PORT"
                                                required
                                            />
                                        </td>
                                        <td className="px-4 py-3">
                                            <FormField
                                                label=""
                                                value={draft.frequency || ''}
                                                onChange={(value: string) => setDraft({ ...draft, frequency: value })}
                                                error={frequencyError || undefined}
                                                placeholder="100 MHz"
                                            />
                                        </td>
                                        <td className="px-4 py-3">
                                            <SelectField
                                                label=""
                                                value={draft.direction || 'input'}
                                                options={[
                                                    { value: 'input', label: 'input' },
                                                    { value: 'output', label: 'output' },
                                                ]}
                                                onChange={(value: string) => setDraft({ ...draft, direction: value })}
                                            />
                                        </td>
                                        <td className="px-4 py-3 text-right">
                                            <div className="flex items-center justify-end gap-2">
                                                <button
                                                    onClick={handleSave}
                                                    disabled={!canSave}
                                                    className="px-3 py-1 rounded text-xs font-medium"
                                                    style={{
                                                        background: canSave ? 'var(--vscode-button-background)' : 'var(--vscode-button-secondaryBackground)',
                                                        color: 'var(--vscode-button-foreground)',
                                                        opacity: canSave ? 1 : 0.5,
                                                        cursor: canSave ? 'pointer' : 'not-allowed',
                                                    }}
                                                >
                                                    Save
                                                </button>
                                                <button
                                                    onClick={handleCancel}
                                                    className="px-3 py-1 rounded text-xs font-medium"
                                                    style={{
                                                        background: 'var(--vscode-button-secondaryBackground)',
                                                        color: 'var(--vscode-button-foreground)',
                                                    }}
                                                >
                                                    Cancel
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                );
                            }

                            return (
                                <tr
                                    key={index}
                                    style={{
                                        background: 'var(--vscode-editor-background)',
                                        borderBottom: '1px solid var(--vscode-panel-border)'
                                    }}
                                    onMouseEnter={(e) => {
                                        e.currentTarget.style.background = 'var(--vscode-list-hoverBackground)';
                                    }}
                                    onMouseLeave={(e) => {
                                        e.currentTarget.style.background = 'var(--vscode-editor-background)';
                                    }}
                                >
                                    <td className="px-4 py-3 text-sm font-mono">{clock.name}</td>
                                    <td className="px-4 py-3 text-sm font-mono">{clock.physicalPort}</td>
                                    <td className="px-4 py-3 text-sm">{clock.frequency || '—'}</td>
                                    <td className="px-4 py-3 text-sm">{clock.direction || 'input'}</td>
                                    <td className="px-4 py-3 text-right">
                                        <div className="flex items-center justify-end gap-2">
                                            <button
                                                onClick={() => handleEdit(index)}
                                                disabled={isAdding || editingIndex !== null}
                                                className="p-1 rounded hover:bg-opacity-10"
                                                style={{
                                                    opacity: (isAdding || editingIndex !== null) ? 0.3 : 1,
                                                    cursor: (isAdding || editingIndex !== null) ? 'not-allowed' : 'pointer',
                                                }}
                                                title="Edit"
                                            >
                                                <span className="codicon codicon-edit"></span>
                                            </button>
                                            <button
                                                onClick={() => handleDelete(index)}
                                                disabled={isAdding || editingIndex !== null}
                                                className="p-1 rounded hover:bg-opacity-10"
                                                style={{
                                                    color: 'var(--vscode-errorForeground)',
                                                    opacity: (isAdding || editingIndex !== null) ? 0.3 : 1,
                                                    cursor: (isAdding || editingIndex !== null) ? 'not-allowed' : 'pointer',
                                                }}
                                                title="Delete"
                                            >
                                                <span className="codicon codicon-trash"></span>
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            );
                        })}

                        {/* Add new row */}
                        {isAdding && (
                            <tr style={{ background: 'var(--vscode-list-activeSelectionBackground)', borderBottom: '1px solid var(--vscode-panel-border)' }}>
                                <td className="px-4 py-3">
                                    <FormField
                                        label=""
                                        value={draft.name}
                                        onChange={(value: string) => setDraft({ ...draft, name: value })}
                                        error={nameError || undefined}
                                        placeholder="clk_name"
                                        required
                                    />
                                </td>
                                <td className="px-4 py-3">
                                    <FormField
                                        label=""
                                        value={draft.physicalPort}
                                        onChange={(value: string) => setDraft({ ...draft, physicalPort: value })}
                                        error={physicalPortError || undefined}
                                        placeholder="CLK_PORT"
                                        required
                                    />
                                </td>
                                <td className="px-4 py-3">
                                    <FormField
                                        label=""
                                        value={draft.frequency || ''}
                                        onChange={(value: string) => setDraft({ ...draft, frequency: value })}
                                        error={frequencyError || undefined}
                                        placeholder="100 MHz"
                                    />
                                </td>
                                <td className="px-4 py-3">
                                    <SelectField
                                        label=""
                                        value={draft.direction || 'input'}
                                        options={[
                                            { value: 'input', label: 'input' },
                                            { value: 'output', label: 'output' },
                                        ]}
                                        onChange={(value: string) => setDraft({ ...draft, direction: value })}
                                    />
                                </td>
                                <td className="px-4 py-3 text-right">
                                    <div className="flex items-center justify-end gap-2">
                                        <button
                                            onClick={handleSave}
                                            disabled={!canSave}
                                            className="px-3 py-1 rounded text-xs font-medium"
                                            style={{
                                                background: canSave ? 'var(--vscode-button-background)' : 'var(--vscode-button-secondaryBackground)',
                                                color: 'var(--vscode-button-foreground)',
                                                opacity: canSave ? 1 : 0.5,
                                                cursor: canSave ? 'pointer' : 'not-allowed',
                                            }}
                                        >
                                            Add
                                        </button>
                                        <button
                                            onClick={handleCancel}
                                            className="px-3 py-1 rounded text-xs font-medium"
                                            style={{
                                                background: 'var(--vscode-button-secondaryBackground)',
                                                color: 'var(--vscode-button-foreground)',
                                            }}
                                        >
                                            Cancel
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        )}

                        {clocks.length === 0 && !isAdding && (
                            <tr>
                                <td colSpan={5} className="px-4 py-8 text-center text-sm" style={{ opacity: 0.6 }}>
                                    No clocks defined. Click "Add Clock" to create one.
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};
