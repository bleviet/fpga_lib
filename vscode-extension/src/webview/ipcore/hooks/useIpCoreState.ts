import { useState, useCallback } from 'react';
import * as yaml from 'yaml';

export interface IpCoreState {
    ipCore: any | null;
    rawYaml: string;
    parseError: string | null;
    fileName: string;
    imports: {
        memoryMaps?: any[];
        fileSets?: any[];
        busLibrary?: any;
    };
}

interface UpdateMessage {
    type: 'update';
    text: string;
    fileName: string;
    imports?: {
        memoryMaps?: any[];
        fileSets?: any[];
        busLibrary?: any;
    };
}

/**
 * Hook for managing IP Core state
 * 
 * Handles:
 * - YAML parsing
 * - State updates from extension
 * - Import resolution data
 * - Reference validation
 */
export function useIpCoreState() {
    const [state, setState] = useState<IpCoreState>({
        ipCore: null,
        rawYaml: '',
        parseError: null,
        fileName: '',
        imports: {},
    });

    /**
     * Update state from YAML text
     * Called when extension sends new document content
     */
    const updateFromYaml = useCallback((text: string, fileName: string, imports?: any) => {
        try {
            const parsed = yaml.parse(text);

            if (!parsed || typeof parsed !== 'object') {
                throw new Error('Invalid YAML: must be an object');
            }

            // Basic validation: check for IP core structure
            const data = parsed as any;
            if (!data.apiVersion || !data.vlnv) {
                // Try to allow it temporarily if it's being edited or empty
                // but for now stick to strict check or log warning
            }

            setState({
                ipCore: data,
                rawYaml: text,
                parseError: null,
                fileName,
                imports: imports || {},
            });
        } catch (error) {
            setState((prev) => ({
                ...prev,
                rawYaml: text,
                parseError: (error as Error).message,
                fileName,
            }));
        }
    }, []);

    /**
     * Update IP core data at a specific path
     * 
     * @param path Path to update (e.g., ['clocks', 0, 'name'])
     * @param value New value
     */
    const updateIpCore = useCallback((path: Array<string | number>, value: any) => {
        setState((prev) => {
            if (!prev.ipCore) return prev;

            try {
                // Parse the existing YAML into a Document to preserve comments/structure
                const doc = yaml.parseDocument(prev.rawYaml);

                // Update the value at the specified path
                doc.setIn(path, value);

                // Convert back to string (preserves format and comments)
                const newYaml = doc.toString();

                // Get new JS object for the state
                const newIpCore = doc.toJSON();

                return {
                    ...prev,
                    ipCore: newIpCore,
                    rawYaml: newYaml,
                };
            } catch (error) {
                console.error('Failed to update YAML:', error);
                return prev;
            }
        });
    }, []);

    /**
     * Get validation errors for cross-references
     */
    const getValidationErrors = useCallback((): string[] => {
        if (!state.ipCore) return [];

        const errors: string[] = [];
        const { ipCore } = state;

        // Validate bus interface references
        if (ipCore.busInterfaces && Array.isArray(ipCore.busInterfaces)) {
            for (const bus of ipCore.busInterfaces) {
                // Check associated clock
                if (bus.associatedClock) {
                    const clockExists = Array.isArray(ipCore.clocks) && ipCore.clocks.some((c: any) => c.name === bus.associatedClock);
                    if (!clockExists) {
                        errors.push(`Bus interface '${bus.name}' references unknown clock '${bus.associatedClock}'`);
                    }
                }

                // Check associated reset
                if (bus.associatedReset) {
                    const resetExists = Array.isArray(ipCore.resets) && ipCore.resets.some((r: any) => r.name === bus.associatedReset);
                    if (!resetExists) {
                        errors.push(`Bus interface '${bus.name}' references unknown reset '${bus.associatedReset}'`);
                    }
                }

                // Check memory map reference
                if (bus.memoryMapRef) {
                    const memMapExists = (Array.isArray(ipCore.memoryMaps) && ipCore.memoryMaps.some((m: any) => m.name === bus.memoryMapRef))
                        || (Array.isArray(state.imports.memoryMaps) && state.imports.memoryMaps.some((m: any) => m.name === bus.memoryMapRef));
                    if (!memMapExists) {
                        errors.push(`Bus interface '${bus.name}' references unknown memory map '${bus.memoryMapRef}'`);
                    }
                }
            }
        }

        return errors;
    }, [state.ipCore, state.imports]);

    return {
        ...state,
        updateFromYaml,
        updateIpCore,
        getValidationErrors,
    };
}
