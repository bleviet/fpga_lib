import React from 'react';
import { VSCodeTextField } from '@vscode/webview-ui-toolkit/react';

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
    /** Additional data attribute for edit key (vim navigation) */
    'data-edit-key'?: string;
    /** Additional className for the text field */
    className?: string;
}

/**
 * Text input form field with validation
 * Uses VSCode Web UI Toolkit for native VS Code look and feel
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
    'data-edit-key': dataEditKey,
    className,
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
            {label && (
                <label className="text-sm font-semibold flex items-center gap-1">
                    {label}
                    {required && <span style={{ color: 'var(--vscode-errorForeground)' }}>*</span>}
                </label>
            )}
            <VSCodeTextField
                data-edit-key={dataEditKey}
                className={className}
                value={value}
                placeholder={placeholder}
                disabled={disabled}
                onInput={(e: any) => {
                    const newValue = e.target.value ?? '';
                    onChange(newValue);
                    if (localError && validator) {
                        const validationError = validator(newValue);
                        setLocalError(validationError);
                    }
                }}
                onBlur={handleBlur}
                style={{
                    '--input-border-color': displayError ? 'var(--vscode-inputValidation-errorBorder)' : undefined
                } as React.CSSProperties}
            />
            {displayError && (
                <span className="text-xs" style={{ color: 'var(--vscode-errorForeground)' }}>
                    {displayError}
                </span>
            )}
        </div>
    );
};

