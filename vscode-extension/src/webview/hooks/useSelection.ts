import { useState, useRef } from 'react';

/**
 * YAML path type
 */
export type YamlPath = Array<string | number>;

/**
 * Selection type
 */
export interface Selection {
    id: string;
    type: 'memoryMap' | 'block' | 'register' | 'array';
    object: any;
    breadcrumbs: string[];
    path: YamlPath;
    meta?: {
        absoluteAddress?: number;
        relativeOffset?: number;
        focusDetails?: boolean;
    };
}

/**
 * Hook for managing selection state
 */
export function useSelection() {
    const [selectedId, setSelectedId] = useState<string>('');
    const [selectedType, setSelectedType] = useState<Selection['type'] | null>(null);
    const [selectedObject, setSelectedObject] = useState<any>(null);
    const [breadcrumbs, setBreadcrumbs] = useState<string[]>([]);
    const [selectionMeta, setSelectionMeta] = useState<Selection['meta'] | undefined>(undefined);

    // Use ref for callbacks that need current selection
    const selectionRef = useRef<Selection | null>(null);

    /**
     * Handle selection change
     */
    const handleSelect = (selection: Selection) => {
        selectionRef.current = selection;
        setSelectedId(selection.id);
        setSelectedType(selection.type);
        setSelectedObject(selection.object);
        setBreadcrumbs(selection.breadcrumbs);
        setSelectionMeta(selection.meta);
    };

    /**
     * Clear selection
     */
    const clearSelection = () => {
        selectionRef.current = null;
        setSelectedId('');
        setSelectedType(null);
        setSelectedObject(null);
        setBreadcrumbs([]);
        setSelectionMeta(undefined);
    };

    return {
        selectedId,
        selectedType,
        selectedObject,
        breadcrumbs,
        selectionMeta,
        selectionRef,
        handleSelect,
        clearSelection,
    };
}
