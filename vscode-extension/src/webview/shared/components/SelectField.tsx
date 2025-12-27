import React from 'react';

export interface SelectFieldProps {
    label: string;
    value: string;
    options: Array<{ value: string; label: string }>;
    onChange: (value: string) => void;
    error?: string;
    required?: boolean;
    disabled?: boolean;
}

/**
 * Dropdown select field
 * Theme-aware with validation support
 */
export const SelectField: React.FC<SelectFieldProps> = ({
    label,
    value,
    options,
    onChange,
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
            <select
                value={value}
                onChange={(e) => onChange(e.target.value)}
                disabled={disabled}
                className="px-3 py-2 rounded text-sm"
                style={{
                    background: 'var(--vscode-dropdown-background)',
                    color: 'var(--vscode-dropdown-foreground)',
                    border: error
                        ? '1px solid var(--vscode-inputValidation-errorBorder)'
                        : '1px solid var(--vscode-dropdown-border)',
                    opacity: disabled ? 0.5 : 1,
                    cursor: disabled ? 'not-allowed' : 'pointer',
                }}
            >
                {options.map((option) => (
                    <option key={option.value} value={option.value}>
                        {option.label}
                    </option>
                ))}
            </select>
            {error && (
                <span className="text-xs" style={{ color: 'var(--vscode-errorForeground)' }}>
                    {error}
                </span>
            )}
        </div>
    );
};
