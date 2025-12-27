import React, { useState } from 'react';
import { FormField, SelectField, NumberField, CheckboxField, TextAreaField } from '../../../shared/components';
import { validateVhdlIdentifier, validateUniqueName } from '../../../shared/utils/validation';

interface Parameter {
    name: string;
    dataType: string;
    defaultValue: any;
    description?: string;
}

interface ParametersTableProps {
    parameters: Parameter[];
    onUpdate: (path: Array<string | number>, value: any) => void;
}

/**
 * Editable table for IP Core parameters
 * Supports different input types based on dataType
 */
export const ParametersTable: React.FC<ParametersTableProps> = ({ parameters, onUpdate }) => {
    const [editingIndex, setEditingIndex] = useState<number | null>(null);
    const [isAdding, setIsAdding] = useState(false);
    const [draft, setDraft] = useState<Parameter>({
        name: '',
        dataType: 'integer',
        defaultValue: 0,
        description: '',
    });

    const handleAdd = () => {
        setIsAdding(true);
        setDraft({
            name: '',
            dataType: 'integer',
            defaultValue: 0,
            description: '',
        });
    };

    const handleEdit = (index: number) => {
        setEditingIndex(index);
        setDraft({ ...parameters[index] });
    };

    const handleSave = () => {
        if (isAdding) {
            onUpdate(['parameters'], [...parameters, draft]);
        } else if (editingIndex !== null) {
            const updated = [...parameters];
            updated[editingIndex] = draft;
            onUpdate(['parameters'], updated);
        }
        handleCancel();
    };

    const handleCancel = () => {
        setIsAdding(false);
        setEditingIndex(null);
        setDraft({
            name: '',
            dataType: 'integer',
            defaultValue: 0,
            description: '',
        });
    };

    const handleDelete = (index: number) => {
        const confirmed = confirm(`Delete parameter "${parameters[index].name}"?`);
        if (confirmed) {
            onUpdate(['parameters'], parameters.filter((_, i) => i !== index));
        }
    };

    const handleDataTypeChange = (newType: string) => {
        let newDefault: any = '';
        if (newType === 'integer') newDefault = 0;
        else if (newType === 'boolean') newDefault = false;
        else if (newType === 'string') newDefault = '';

        setDraft({ ...draft, dataType: newType, defaultValue: newDefault });
    };

    const existingNames = parameters.map(p => p.name).filter((_, i) => i !== editingIndex);
    const nameError = validateVhdlIdentifier(draft.name) || validateUniqueName(draft.name, existingNames);
    const canSave = !nameError;

    const renderDefaultValueField = () => {
        switch (draft.dataType) {
            case 'integer':
                return (
                    <NumberField
                        label=""
                        value={typeof draft.defaultValue === 'number' ? draft.defaultValue : 0}
                        onChange={(v: number) => setDraft({ ...draft, defaultValue: v })}
                    />
                );
            case 'boolean':
                return (
                    <CheckboxField
                        label="True"
                        checked={!!draft.defaultValue}
                        onChange={(v: boolean) => setDraft({ ...draft, defaultValue: v })}
                    />
                );
            case 'string':
            default:
                return (
                    <FormField
                        label=""
                        value={String(draft.defaultValue || '')}
                        onChange={(v: string) => setDraft({ ...draft, defaultValue: v })}
                        placeholder="default value"
                    />
                );
        }
    };

    const formatDefaultValue = (param: Parameter): string => {
        if (param.dataType === 'boolean') {
            return param.defaultValue ? 'true' : 'false';
        }
        return String(param.defaultValue);
    };

    const renderEditRow = () => (
        <>
            <td className="px-4 py-3">
                <FormField
                    label=""
                    value={draft.name}
                    onChange={(v: string) => setDraft({ ...draft, name: v })}
                    error={nameError || undefined}
                    placeholder="PARAM_NAME"
                    required
                />
            </td>
            <td className="px-4 py-3">
                <SelectField
                    label=""
                    value={draft.dataType}
                    options={[
                        { value: 'integer', label: 'integer' },
                        { value: 'boolean', label: 'boolean' },
                        { value: 'string', label: 'string' },
                    ]}
                    onChange={handleDataTypeChange}
                />
            </td>
            <td className="px-4 py-3">
                {renderDefaultValueField()}
            </td>
            <td className="px-4 py-3">
                <FormField
                    label=""
                    value={draft.description || ''}
                    onChange={(v: string) => setDraft({ ...draft, description: v })}
                    placeholder="Optional description"
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
                        {isAdding ? 'Add' : 'Save'}
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
        </>
    );

    return (
        <div className="p-6 space-y-4">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-semibold">Parameters</h2>
                    <p className="text-sm mt-1" style={{ opacity: 0.7 }}>
                        {parameters.length} parameter{parameters.length !== 1 ? 's' : ''}
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
                >
                    <span className="codicon codicon-add"></span>
                    Add Parameter
                </button>
            </div>

            <div
                className="rounded overflow-hidden"
                style={{ border: '1px solid var(--vscode-panel-border)' }}
            >
                <table className="w-full">
                    <thead>
                        <tr style={{ background: 'var(--vscode-editor-background)', borderBottom: '1px solid var(--vscode-panel-border)' }}>
                            <th className="px-4 py-3 text-left text-sm font-semibold">Name</th>
                            <th className="px-4 py-3 text-left text-sm font-semibold">Data Type</th>
                            <th className="px-4 py-3 text-left text-sm font-semibold">Default Value</th>
                            <th className="px-4 py-3 text-left text-sm font-semibold">Description</th>
                            <th className="px-4 py-3 text-right text-sm font-semibold">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {parameters.map((param, index) => {
                            const isEditing = editingIndex === index;

                            if (isEditing) {
                                return (
                                    <tr key={index} style={{ background: 'var(--vscode-list-activeSelectionBackground)', borderBottom: '1px solid var(--vscode-panel-border)' }}>
                                        {renderEditRow()}
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
                                    <td className="px-4 py-3 text-sm font-mono">{param.name}</td>
                                    <td className="px-4 py-3 text-sm">{param.dataType}</td>
                                    <td className="px-4 py-3 text-sm font-mono">{formatDefaultValue(param)}</td>
                                    <td className="px-4 py-3 text-sm" style={{ opacity: param.description ? 1 : 0.5 }}>
                                        {param.description || '—'}
                                    </td>
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
                                {renderEditRow()}
                            </tr>
                        )}

                        {parameters.length === 0 && !isAdding && (
                            <tr>
                                <td colSpan={5} className="px-4 py-8 text-center text-sm" style={{ opacity: 0.6 }}>
                                    No parameters defined. Click "Add Parameter" to create one.
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};
