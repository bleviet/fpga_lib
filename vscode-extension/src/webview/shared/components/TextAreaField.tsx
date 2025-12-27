import React from 'react';

export interface TextAreaFieldProps {
    label: string;
    value: string;
    onChange: (value: string) => void;
    rows?: number;
    placeholder?: string;
    error?: string;
    required?: boolean;
    disabled?: boolean;
}

/**
 * Multi-line text area field
 * Theme-aware with validation support
 */
export const TextAreaField: React.FC<TextAreaFieldProps> = ({
    label,
    value,
    onChange,
    rows = 4,
    placeholder,
    error,
    required = false,
    disabled = false,
}) => {
    return (
        <div className="flex flex-col gap-1">
            <label className="text-sm font-semibold flex items-center gap-1">
                {label}
                {required && <span style={{ color: 'var(--vscode-errorForeground)' }}>*</span>}
            </label>
            <textarea
                value={value}
                onChange={(e) => onChange(e.target.value)}
                rows={rows}
                placeholder={placeholder}
                disabled={disabled}
                className="px-3 py-2 rounded text-sm resize-vertical"
                style={{
                    background: 'var(--vscode-input-background)',
                    color: 'var(--vscode-input-foreground)',
                    border: error
                        ? '1px solid var(--vscode-inputValidation-errorBorder)'
                        : '1px solid var(--vscode-input-border)',
                    opacity: disabled ? 0.5 : 1,
                    cursor: disabled ? 'not-allowed' : 'text',
                    fontFamily: 'var(--vscode-font-family)',
                }}
            />
            {error && (
                <span className="text-xs" style={{ color: 'var(--vscode-errorForeground)' }}>
                    {error}
                </span>
            )}
        </div>
    );
};
