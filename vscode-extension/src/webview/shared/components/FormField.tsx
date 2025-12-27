import React from 'react';

export interface FormFieldProps {
    label: string;
    value: string;
    onChange: (value: string) => void;
    error?: string;
    placeholder?: string;
    required?: boolean;
    disabled?: boolean;
    validator?: (value: string) => string | null;
    onBlur?: () => void;
}

/**
 * Text input form field with validation
 * Theme-aware, supports validation, errors, and required fields
 */
export const FormField: React.FC<FormFieldProps> = ({
    label,
    value,
    onChange,
    error,
    placeholder,
    required = false,
    disabled = false,
    validator,
    onBlur,
}) => {
    const [localError, setLocalError] = React.useState<string | null>(null);

    const handleBlur = () => {
        if (validator) {
            const validationError = validator(value);
            setLocalError(validationError);
        }
        onBlur?.();
    };

    const displayError = error || localError;

    return (
        <div className="flex flex-col gap-1">
            <label className="text-sm font-semibold flex items-center gap-1">
                {label}
                {required && <span style={{ color: 'var(--vscode-errorForeground)' }}>*</span>}
            </label>
            <input
                type="text"
                value={value}
                onChange={(e) => {
                    onChange(e.target.value);
                    if (localError && validator) {
                        const validationError = validator(e.target.value);
                        setLocalError(validationError);
                    }
                }}
                onBlur={handleBlur}
                placeholder={placeholder}
                disabled={disabled}
                className="px-3 py-2 rounded text-sm"
                style={{
                    background: disabled ? 'var(--vscode-input-background)' : 'var(--vscode-input-background)',
                    color: 'var(--vscode-input-foreground)',
                    border: displayError
                        ? '1px solid var(--vscode-inputValidation-errorBorder)'
                        : '1px solid var(--vscode-input-border)',
                    opacity: disabled ? 0.5 : 1,
                    cursor: disabled ? 'not-allowed' : 'text',
                }}
            />
            {displayError && (
                <span className="text-xs" style={{ color: 'var(--vscode-errorForeground)' }}>
                    {displayError}
                </span>
            )}
        </div>
    );
};
