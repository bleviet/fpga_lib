import React, { useState } from 'react';
import { FormField, SelectField, TextAreaField } from '../../../shared/components';
import { validateRequired, validateVersion } from '../../../shared/utils/validation';

interface MetadataEditorProps {
    ipCore: any;
    onUpdate: (path: Array<string | number>, value: any) => void;
}

/**
 * Metadata editor for IP Core VLNV and description
 * Allows inline editing of vendor, library, name, version, API version, and description
 */
export const MetadataEditor: React.FC<MetadataEditorProps> = ({ ipCore, onUpdate }) => {
    const [isEditing, setIsEditing] = useState(false);
    const [draft, setDraft] = useState({
        apiVersion: ipCore?.apiVersion || 'v1',
        vendor: ipCore?.vlnv?.vendor || '',
        library: ipCore?.vlnv?.library || '',
        name: ipCore?.vlnv?.name || '',
        version: ipCore?.vlnv?.version || '',
        description: ipCore?.description || '',
    });

    const handleSave = () => {
        // Update API version
        onUpdate(['apiVersion'], draft.apiVersion);

        // Update VLNV
        onUpdate(['vlnv', 'vendor'], draft.vendor);
        onUpdate(['vlnv', 'library'], draft.library);
        onUpdate(['vlnv', 'name'], draft.name);
        onUpdate(['vlnv', 'version'], draft.version);

        // Update description
        onUpdate(['description'], draft.description);

        setIsEditing(false);
    };

    const handleCancel = () => {
        setDraft({
            apiVersion: ipCore?.apiVersion || 'v1',
            vendor: ipCore?.vlnv?.vendor || '',
            library: ipCore?.vlnv?.library || '',
            name: ipCore?.vlnv?.name || '',
            version: ipCore?.vlnv?.version || '',
            description: ipCore?.description || '',
        });
        setIsEditing(false);
    };

    const hasChanges =
        draft.apiVersion !== ipCore?.apiVersion ||
        draft.vendor !== ipCore?.vlnv?.vendor ||
        draft.library !== ipCore?.vlnv?.library ||
        draft.name !== ipCore?.vlnv?.name ||
        draft.version !== ipCore?.vlnv?.version ||
        draft.description !== ipCore?.description;

    if (!isEditing) {
        return (
            <div className="p-6 space-y-4">
                <div className="flex items-center justify-between mb-4">
                    <h2 className="text-2xl font-semibold">Metadata</h2>
                    <button
                        onClick={() => setIsEditing(true)}
                        className="px-4 py-2 rounded text-sm font-medium transition-colors"
                        style={{
                            background: 'var(--vscode-button-background)',
                            color: 'var(--vscode-button-foreground)',
                        }}
                        onMouseEnter={(e) => {
                            e.currentTarget.style.background = 'var(--vscode-button-hoverBackground)';
                        }}
                        onMouseLeave={(e) => {
                            e.currentTarget.style.background = 'var(--vscode-button-background)';
                        }}
                    >
                        Edit Metadata
                    </button>
                </div>

                <div
                    className="p-4 rounded space-y-3"
                    style={{
                        background: 'var(--vscode-editor-background)',
                        border: '1px solid var(--vscode-panel-border)'
                    }}
                >
                    <div>
                        <p className="text-xs font-semibold mb-1" style={{ opacity: 0.7 }}>API Version</p>
                        <p className="text-sm">{ipCore?.apiVersion}</p>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <p className="text-xs font-semibold mb-1" style={{ opacity: 0.7 }}>Vendor</p>
                            <p className="text-sm">{ipCore?.vlnv?.vendor}</p>
                        </div>
                        <div>
                            <p className="text-xs font-semibold mb-1" style={{ opacity: 0.7 }}>Library</p>
                            <p className="text-sm">{ipCore?.vlnv?.library}</p>
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <p className="text-xs font-semibold mb-1" style={{ opacity: 0.7 }}>Name</p>
                            <p className="text-sm">{ipCore?.vlnv?.name}</p>
                        </div>
                        <div>
                            <p className="text-xs font-semibold mb-1" style={{ opacity: 0.7 }}>Version</p>
                            <p className="text-sm">{ipCore?.vlnv?.version}</p>
                        </div>
                    </div>

                    {ipCore?.description && (
                        <div>
                            <p className="text-xs font-semibold mb-1" style={{ opacity: 0.7 }}>Description</p>
                            <p className="text-sm" style={{ whiteSpace: 'pre-wrap' }}>{ipCore.description}</p>
                        </div>
                    )}
                </div>
            </div>
        );
    }

    return (
        <div className="p-6 space-y-6">
            <h2 className="text-2xl font-semibold mb-4">Edit Metadata</h2>

            <div className="space-y-4">
                <SelectField
                    label="API Version"
                    value={draft.apiVersion}
                    options={[
                        { value: 'v1', label: 'v1' },
                    ]}
                    onChange={(value: string) => setDraft({ ...draft, apiVersion: value })}
                    required
                />

                <div className="grid grid-cols-2 gap-4">
                    <FormField
                        label="Vendor"
                        value={draft.vendor}
                        onChange={(value: string) => setDraft({ ...draft, vendor: value })}
                        placeholder="e.g., my-company.com"
                        required
                        validator={validateRequired}
                    />
                    <FormField
                        label="Library"
                        value={draft.library}
                        onChange={(value: string) => setDraft({ ...draft, library: value })}
                        placeholder="e.g., my_lib"
                        required
                        validator={validateRequired}
                    />
                </div>

                <div className="grid grid-cols-2 gap-4">
                    <FormField
                        label="Name"
                        value={draft.name}
                        onChange={(value: string) => setDraft({ ...draft, name: value })}
                        placeholder="e.g., my_core"
                        required
                        validator={validateRequired}
                    />
                    <FormField
                        label="Version"
                        value={draft.version}
                        onChange={(value: string) => setDraft({ ...draft, version: value })}
                        placeholder="e.g., 1.0.0"
                        required
                        validator={validateVersion}
                    />
                </div>

                <TextAreaField
                    label="Description"
                    value={draft.description}
                    onChange={(value: string) => setDraft({ ...draft, description: value })}
                    placeholder="Describe the IP core..."
                    rows={4}
                />
            </div>

            <div className="flex items-center gap-3 pt-4" style={{ borderTop: '1px solid var(--vscode-panel-border)' }}>
                <button
                    onClick={handleSave}
                    disabled={!hasChanges}
                    className="px-4 py-2 rounded text-sm font-medium transition-colors"
                    style={{
                        background: hasChanges ? 'var(--vscode-button-background)' : 'var(--vscode-button-secondaryBackground)',
                        color: 'var(--vscode-button-foreground)',
                        opacity: hasChanges ? 1 : 0.5,
                        cursor: hasChanges ? 'pointer' : 'not-allowed',
                    }}
                    onMouseEnter={(e) => {
                        if (hasChanges) {
                            e.currentTarget.style.background = 'var(--vscode-button-hoverBackground)';
                        }
                    }}
                    onMouseLeave={(e) => {
                        if (hasChanges) {
                            e.currentTarget.style.background = 'var(--vscode-button-background)';
                        } else {
                            e.currentTarget.style.background = 'var(--vscode-button-secondaryBackground)';
                        }
                    }}
                >
                    Save Changes
                </button>
                <button
                    onClick={handleCancel}
                    className="px-4 py-2 rounded text-sm font-medium transition-colors"
                    style={{
                        background: 'var(--vscode-button-secondaryBackground)',
                        color: 'var(--vscode-button-foreground)',
                    }}
                    onMouseEnter={(e) => {
                        e.currentTarget.style.background = 'var(--vscode-button-secondaryHoverBackground)';
                    }}
                    onMouseLeave={(e) => {
                        e.currentTarget.style.background = 'var(--vscode-button-secondaryBackground)';
                    }}
                >
                    Cancel
                </button>
                {hasChanges && (
                    <span className="text-xs" style={{ opacity: 0.7 }}>
                        Unsaved changes
                    </span>
                )}
            </div>
        </div>
    );
};
