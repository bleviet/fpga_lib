import React, { useRef } from 'react';
import { FormField, SelectField } from '../../../shared/components';
import { validateVhdlIdentifier, validateUniqueName, validateFrequency } from '../../../shared/utils/validation';
import { useVimTableNavigation } from '../../hooks/useVimTableNavigation';

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

const createEmptyClock = (): Clock => ({
    name: '',
    physicalPort: '',
    frequency: '',
    direction: 'input',
});

const COLUMN_KEYS = ['name', 'physicalPort', 'frequency', 'direction'];

/**
 * Editable table for IP Core clocks
 * Supports vim-style keyboard navigation:
 * - j/k or Arrow Up/Down: Navigate rows
 * - h/l or Arrow Left/Right: Navigate columns
 * - Enter or 'e': Edit selected cell
 * - 'd' or Delete: Delete selected row
 * - 'o': Add new row
 * - Escape: Cancel editing
 */
export const ClocksTable: React.FC<ClocksTableProps> = ({ clocks, onUpdate }) => {
    const {
        selectedIndex,
        activeColumn,
        editingIndex,
        isAdding,
        draft,
        setDraft,
        handleEdit,
        handleAdd,
        handleSave,
        handleCancel,
        handleDelete,
        containerRef,
        getRowProps,
        getCellProps,
    } = useVimTableNavigation<Clock>({
        items: clocks,
        onUpdate,
        dataKey: 'clocks',
        createEmptyItem: createEmptyClock,
        columnKeys: COLUMN_KEYS,
    });

    const existingNames = clocks.map(c => c.name).filter((_, i) => i !== editingIndex);
    const nameError = validateVhdlIdentifier(draft.name) || validateUniqueName(draft.name, existingNames);
    const physicalPortError = validateVhdlIdentifier(draft.physicalPort);
    const frequencyError = validateFrequency(draft.frequency || '');
    const canSave = !nameError && !physicalPortError && !frequencyError;

    const renderEditRow = (isNew: boolean) => (
        <tr style={{ background: 'var(--vscode-list-activeSelectionBackground)', borderBottom: '1px solid var(--vscode-panel-border)' }} data-row-idx={editingIndex ?? clocks.length}>
            <td className="px-4 py-3">
                <FormField label="" value={draft.name} onChange={(v: string) => setDraft({ ...draft, name: v })} error={nameError || undefined} placeholder="clk_name" required data-edit-key="name" />
            </td>
            <td className="px-4 py-3">
                <FormField label="" value={draft.physicalPort} onChange={(v: string) => setDraft({ ...draft, physicalPort: v })} error={physicalPortError || undefined} placeholder="CLK_PORT" required data-edit-key="physicalPort" />
            </td>
            <td className="px-4 py-3">
                <FormField label="" value={draft.frequency || ''} onChange={(v: string) => setDraft({ ...draft, frequency: v })} error={frequencyError || undefined} placeholder="100 MHz" data-edit-key="frequency" />
            </td>
            <td className="px-4 py-3">
                <SelectField label="" value={draft.direction || 'input'} options={[{ value: 'input', label: 'input' }, { value: 'output', label: 'output' }]} onChange={(v: string) => setDraft({ ...draft, direction: v })} data-edit-key="direction" />
            </td>
            <td className="px-4 py-3 text-right">
                <div className="flex items-center justify-end gap-2">
                    <button onClick={handleSave} disabled={!canSave} className="px-3 py-1 rounded text-xs font-medium" style={{ background: canSave ? 'var(--vscode-button-background)' : 'var(--vscode-button-secondaryBackground)', color: 'var(--vscode-button-foreground)', opacity: canSave ? 1 : 0.5 }}>
                        {isNew ? 'Add' : 'Save'}
                    </button>
                    <button onClick={handleCancel} className="px-3 py-1 rounded text-xs font-medium" style={{ background: 'var(--vscode-button-secondaryBackground)', color: 'var(--vscode-button-foreground)' }}>
                        Cancel
                    </button>
                </div>
            </td>
        </tr>
    );

    return (
        <div ref={containerRef} className="p-6 space-y-4" tabIndex={0}>
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-semibold">Clocks</h2>
                    <p className="text-sm mt-1" style={{ opacity: 0.7 }}>
                        {clocks.length} clock{clocks.length !== 1 ? 's' : ''} •
                        <span className="ml-2 text-xs font-mono" style={{ opacity: 0.5 }}>h/j/k/l: navigate • e: edit • d: delete • o: add</span>
                    </p>
                </div>
                <button
                    onClick={handleAdd}
                    disabled={isAdding || editingIndex !== null}
                    className="px-4 py-2 rounded text-sm font-medium flex items-center gap-2"
                    style={{
                        background: (isAdding || editingIndex !== null) ? 'var(--vscode-button-secondaryBackground)' : 'var(--vscode-button-background)',
                        color: 'var(--vscode-button-foreground)',
                        opacity: (isAdding || editingIndex !== null) ? 0.5 : 1,
                    }}
                >
                    <span className="codicon codicon-add"></span>
                    Add Clock
                </button>
            </div>

            <div className="rounded overflow-hidden" style={{ border: '1px solid var(--vscode-panel-border)' }}>
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
                            if (editingIndex === index) {
                                return <React.Fragment key={index}>{renderEditRow(false)}</React.Fragment>;
                            }

                            const rowProps = getRowProps(index);
                            return (
                                <tr key={index} {...rowProps} onDoubleClick={() => handleEdit(index)}>
                                    <td className="px-4 py-3 text-sm font-mono" {...getCellProps(index, 'name')}>{clock.name}</td>
                                    <td className="px-4 py-3 text-sm font-mono" {...getCellProps(index, 'physicalPort')}>{clock.physicalPort}</td>
                                    <td className="px-4 py-3 text-sm" {...getCellProps(index, 'frequency')}>{clock.frequency || '—'}</td>
                                    <td className="px-4 py-3 text-sm" {...getCellProps(index, 'direction')}>{clock.direction || 'input'}</td>
                                    <td className="px-4 py-3 text-right">
                                        <div className="flex items-center justify-end gap-2">
                                            <button onClick={(e) => { e.stopPropagation(); handleEdit(index); }} disabled={isAdding || editingIndex !== null} className="p-1 rounded" style={{ opacity: (isAdding || editingIndex !== null) ? 0.3 : 1 }} title="Edit (e)">
                                                <span className="codicon codicon-edit"></span>
                                            </button>
                                            <button onClick={(e) => { e.stopPropagation(); handleDelete(index); }} disabled={isAdding || editingIndex !== null} className="p-1 rounded" style={{ color: 'var(--vscode-errorForeground)', opacity: (isAdding || editingIndex !== null) ? 0.3 : 1 }} title="Delete (d)">
                                                <span className="codicon codicon-trash"></span>
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            );
                        })}

                        {isAdding && renderEditRow(true)}

                        {clocks.length === 0 && !isAdding && (
                            <tr>
                                <td colSpan={5} className="px-4 py-8 text-center text-sm" style={{ opacity: 0.6 }}>
                                    No clocks defined. Press 'o' or click "Add Clock" to create one.
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};
