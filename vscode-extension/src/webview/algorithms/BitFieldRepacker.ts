/**
 * Bit field repacking algorithms for maintaining proper bit field layouts
 */

/**
 * Parse a bits range string like "[31:0]" or "[5]"
 * @returns [msb, lsb] tuple or null if invalid
 */
export function parseBitsRange(bits: string): [number, number] | null {
    if (!bits) return null;
    const m = bits.match(/^\\[(\\d+):(\\d+)\\]$/);
    if (m) return [parseInt(m[1], 10), parseInt(m[2], 10)];
    const s = bits.match(/^\\[(\\d+)\\]$/);
    if (s) return [parseInt(s[1], 10), parseInt(s[1], 10)];
    return null;
}

/**
 * Format a bits range as a string
 */
export function formatBits(msb: number, lsb: number): string {
    return msb === lsb ? `[${msb}]` : `[${msb}:${lsb}]`;
}

/**
 * Helper to convert field to bits string
 */
function toBitsString(f: any): string {
    const o = Number(f?.bit_offset ?? 0);
    const w = Number(f?.bit_width ?? 1);
    if (!Number.isFinite(o) || !Number.isFinite(w)) {
        return '[?:?]';
    }
    const msb = o + w - 1;
    return `[${msb}:${o}]`;
}

/**
 * Repack only the updated field and subsequent fields, preserving order
 * @param fields Array of bit fields
 * @param regWidth Register width in bits
 * @param startIdx Starting index for repacking
 * @returns New array with repacked fields
 */
export function repackFieldsFrom(fields: any[], regWidth: number, startIdx: number): any[] {
    // Calculate starting MSB for the updated field
    let nextMsb = regWidth - 1;
    if (startIdx > 0) {
        // Previous field's LSB
        const prev = fields[startIdx - 1];
        let prevBits = prev.bits;
        let prevRange = parseBitsRange(typeof prevBits === 'string' ? prevBits : toBitsString(prev));
        if (prevRange) {
            nextMsb = prevRange[1] - 1;
        }
    }
    const newFields = [...fields];
    for (let i = startIdx; i < fields.length; ++i) {
        let width = 1;
        let bitsStr = newFields[i].bits;
        let parsed = parseBitsRange(
            typeof bitsStr === 'string' ? bitsStr : toBitsString(newFields[i])
        );
        if (parsed) width = Math.abs(parsed[0] - parsed[1]) + 1;
        const msb = nextMsb;
        let lsb = msb - width + 1;
        // Clamp LSB to zero
        if (lsb < 0) {
            lsb = 0;
        }
        nextMsb = lsb - 1;
        newFields[i] = {
            ...newFields[i],
            bits: formatBits(msb, lsb),
            bit_offset: lsb,
            bit_width: width,
            bit_range: [msb, lsb],
        };
    }
    return newFields;
}

/**
 * Repack bit fields downward (toward LSB/bit 0) starting from the given index.
 * Maintains field widths but shifts them to lower bit positions.
 * Used for spatial insertion when inserting a field after another.
 */
export function repackFieldsDownward(
    fields: any[],
    fromIndex: number,
    regWidth: number
): any[] {
    const newFields = [...fields];

    // Start from the field just before fromIndex to determine the starting position
    let nextMsb =
        fromIndex > 0
            ? (() => {
                const prev = newFields[fromIndex - 1];
                const prevBits = prev.bits || toBitsString(prev);
                const prevRange = parseBitsRange(prevBits);
                return prevRange ? prevRange[1] - 1 : regWidth - 1; // LSB - 1
            })()
            : regWidth - 1;

    for (let i = fromIndex; i < newFields.length; i++) {
        const field = newFields[i];
        const bitsStr = field.bits || toBitsString(field);
        const parsed = parseBitsRange(bitsStr);
        const width = parsed ? Math.abs(parsed[0] - parsed[1]) + 1 : 1;

        const msb = nextMsb;
        const lsb = Math.max(0, msb - width + 1);
        nextMsb = lsb - 1;

        newFields[i] = {
            ...field,
            bits: formatBits(msb, lsb),
            bit_offset: lsb,
            bit_width: width,
            bit_range: [msb, lsb],
        };
    }

    return newFields;
}

/**
 * Repack bit fields upward (toward MSB) starting from the given index going backwards.
 * Maintains field widths but shifts them to higher bit positions.
 * Used for spatial insertion when inserting a field before another.
 */
export function repackFieldsUpward(fields: any[], fromIndex: number, regWidth: number): any[] {
    const newFields = [...fields];

    // Start from the field just after fromIndex to determine the starting position
    let nextLsb =
        fromIndex < newFields.length - 1
            ? (() => {
                const next = newFields[fromIndex + 1];
                const nextBits = next.bits || toBitsString(next);
                const nextRange = parseBitsRange(nextBits);
                return nextRange ? nextRange[0] + 1 : 0; // MSB + 1
            })()
            : 0;

    for (let i = fromIndex; i >= 0; i--) {
        const field = newFields[i];
        const bitsStr = field.bits || toBitsString(field);
        const parsed = parseBitsRange(bitsStr);
        const width = parsed ? Math.abs(parsed[0] - parsed[1]) + 1 : 1;

        const lsb = nextLsb;
        const msb = Math.min(regWidth - 1, lsb + width - 1);
        nextLsb = msb + 1;

        newFields[i] = {
            ...field,
            bits: formatBits(msb, lsb),
            bit_offset: lsb,
            bit_width: width,
            bit_range: [msb, lsb],
        };
    }

    return newFields;
}
