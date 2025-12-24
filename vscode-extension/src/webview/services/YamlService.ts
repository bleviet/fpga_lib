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
        const cleaned = YamlService.cleanForYaml(data);
        return jsyaml.dump(cleaned, { noRefs: true, sortKeys: false, lineWidth: -1 });
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

    /**
     * Clean object before YAML serialization
     * Removes computed properties that shouldn't be in the YAML output
     */
    static cleanForYaml(obj: any): any {
        if (!obj || typeof obj !== 'object') return obj;

        if (Array.isArray(obj)) {
            return obj.map(item => YamlService.cleanForYaml(item));
        }

        const cleaned: any = {};
        for (const key in obj) {
            if (!obj.hasOwnProperty(key)) continue;

            // Skip computed properties for bit fields
            if (key === 'bit_offset' || key === 'bit_width' || key === 'bit_range') {
                // Only skip if 'bits' property exists
                if (obj.bits) continue;
            }

            cleaned[key] = YamlService.cleanForYaml(obj[key]);
        }
        return cleaned;
    }
}
