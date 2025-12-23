import jsyaml from 'js-yaml';

/**
 * Service for YAML serialization and parsing operations
 */
export class YamlService {
    /**
     * Dump a JavaScript object to YAML string
     * NOTE: This will not preserve comments or formatting from the original YAML
     */
    static dump(data: any): string {
        return jsyaml.dump(data, { noRefs: true, sortKeys: false, lineWidth: -1 });
    }

    /**
     * Parse a YAML string to JavaScript object
     */
    static parse(text: string): any {
        return jsyaml.load(text);
    }

    /**
     * Safely parse YAML text, returning null on error
     */
    static safeParse(text: string): any | null {
        try {
            return jsyaml.load(text);
        } catch (err) {
            console.warn('YAML parse error:', err);
            return null;
        }
    }
}
