import React from 'react';

export interface NumberFieldProps {
    label: string;
    value: number;
    onChange: (value: number) => void;
    min?: number;
    max?: number;
    step?: number;
    error?: string;
    required?: boolean;
    disabled?: boolean;
}

/**
 * Numeric input field
 * Theme-aware with min/max validation
 */
export const NumberField: React.FC<NumberFieldProps> = ({
    label,
    value,
    onChange,
    min,
    max,
    step = 1,
    error,
    required = false,
    disabled = false,
}) => {
    const handleChange = (newValue: string) => {
        const num = parseInt(newValue, 10);
        if (!isNaN(num)) {
            onChange(num);
        } else if (newValue === '') {
            onChange(0);
        }
    };

    return (
        <div className="flex flex-col gap-1">
            <label className="text-sm font-semibold flex items-center gap-1">
                {label}
                {required && <span style={{ color: 'var(--vscode-errorForeground)' }}>*</span>}
            </label>
            <input
                type="number"
                value={value}
                onChange={(e) => handleChange(e.target.value)}
                min={min}
                max={max}
                step={step}
                disabled={disabled}
                className="px-3 py-2 rounded text-sm"
                style={{
                    background: 'var(--vscode-input-background)',
                    color: 'var(--vscode-input-foreground)',
                    border: error
                        ? '1px solid var(--vscode-inputValidation-errorBorder)'
                        : '1px solid var(--vscode-input-border)',
                    opacity: disabled ? 0.5 : 1,
                    cursor: disabled ? 'not-allowed' : 'text',
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
