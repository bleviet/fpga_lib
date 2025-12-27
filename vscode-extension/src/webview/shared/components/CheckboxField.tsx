import React from 'react';

export interface CheckboxFieldProps {
    label: string;
    checked: boolean;
    onChange: (checked: boolean) => void;
    disabled?: boolean;
}

/**
 * Checkbox field for boolean values
 * Theme-aware with label
 */
export const CheckboxField: React.FC<CheckboxFieldProps> = ({
    label,
    checked,
    onChange,
    disabled = false,
}) => {
    return (
        <div className="flex items-center gap-2">
            <input
                type="checkbox"
                checked={checked}
                onChange={(e) => onChange(e.target.checked)}
                disabled={disabled}
                className="cursor-pointer"
                style={{
                    opacity: disabled ? 0.5 : 1,
                    cursor: disabled ? 'not-allowed' : 'pointer',
                }}
            />
            <label
                className="text-sm cursor-pointer"
                onClick={() => !disabled && onChange(!checked)}
                style={{
                    opacity: disabled ? 0.5 : 1,
                    cursor: disabled ? 'not-allowed' : 'pointer',
                }}
            >
                {label}
            </label>
        </div>
    );
};
