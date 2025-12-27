import { useState, useRef, useCallback } from 'react';

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
     * IMPORTANT: Wrapped in useCallback to prevent infinite loops in useEffect dependencies
     */
    const handleSelect = useCallback((selection: Selection) => {
        selectionRef.current = selection;
        setSelectedId(selection.id);
        setSelectedType(selection.type);
        setSelectedObject(selection.object);
        setBreadcrumbs(selection.breadcrumbs);
        setSelectionMeta(selection.meta);
    }, []);

    /**
     * Clear selection
     */
    const clearSelection = useCallback(() => {
        selectionRef.current = null;
        setSelectedId('');
        setSelectedType(null);
        setSelectedObject(null);
        setBreadcrumbs([]);
        setSelectionMeta(undefined);
    }, []);

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
