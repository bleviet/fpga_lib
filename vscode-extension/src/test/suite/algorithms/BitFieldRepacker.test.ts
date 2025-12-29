import {
  parseBitsRange,
  formatBits,
  repackFieldsFrom,
  repackFieldsDownward,
  repackFieldsUpward,
} from '../../../webview/algorithms/BitFieldRepacker';

describe('BitFieldRepacker', () => {
  describe('parseBitsRange', () => {
    it('should parse range format [MSB:LSB]', () => {
      expect(parseBitsRange('[31:0]')).toEqual([31, 0]);
      expect(parseBitsRange('[15:8]')).toEqual([15, 8]);
      expect(parseBitsRange('[7:0]')).toEqual([7, 0]);
    });

    it('should parse single bit format [N]', () => {
      expect(parseBitsRange('[5]')).toEqual([5, 5]);
      expect(parseBitsRange('[0]')).toEqual([0, 0]);
      expect(parseBitsRange('[31]')).toEqual([31, 31]);
    });

    it('should return null for invalid formats', () => {
      expect(parseBitsRange('')).toBeNull();
      expect(parseBitsRange('invalid')).toBeNull();
      expect(parseBitsRange('[31-0]')).toBeNull();
      expect(parseBitsRange('31:0')).toBeNull();
    });

    it('should handle reverse order (LSB:MSB)', () => {
      expect(parseBitsRange('[0:7]')).toEqual([0, 7]);
    });
  });

  describe('formatBits', () => {
    it('should format as single bit when MSB equals LSB', () => {
      expect(formatBits(5, 5)).toBe('[5]');
      expect(formatBits(0, 0)).toBe('[0]');
      expect(formatBits(31, 31)).toBe('[31]');
    });

    it('should format as range when MSB differs from LSB', () => {
      expect(formatBits(31, 0)).toBe('[31:0]');
      expect(formatBits(15, 8)).toBe('[15:8]');
      expect(formatBits(7, 0)).toBe('[7:0]');
    });
  });

  describe('repackFieldsFrom', () => {
    it('should repack fields from start index maintaining widths', () => {
      const fields = [
        { name: 'field1', bits: '[31:24]', bit_offset: 24, bit_width: 8 },
        { name: 'field2', bits: '[15:8]', bit_offset: 8, bit_width: 8 },
        { name: 'field3', bits: '[7:0]', bit_offset: 0, bit_width: 8 },
      ];

      const result = repackFieldsFrom(fields, 32, 1);

      // Field 1 unchanged, field 2 starts at bit 23, field 3 at bit 15
      expect(result[0].bits).toBe('[31:24]');
      expect(result[1].bits).toBe('[23:16]');
      expect(result[2].bits).toBe('[15:8]');
    });

    it('should start from MSB when repacking from index 0', () => {
      const fields = [
        { name: 'field1', bits: '[10:5]', bit_offset: 5, bit_width: 6 },
        { name: 'field2', bits: '[3:0]', bit_offset: 0, bit_width: 4 },
      ];

      const result = repackFieldsFrom(fields, 32, 0);

      expect(result[0].bits).toBe('[31:26]');
      expect(result[1].bits).toBe('[25:22]');
    });

    it('should clamp LSB to 0 on overflow', () => {
      const fields = [
        { name: 'field1', bits: '[7:0]', bit_offset: 0, bit_width: 8 },
        { name: 'field2', bits: '[7:0]', bit_offset: 0, bit_width: 8 },
        { name: 'field3', bits: '[7:0]', bit_offset: 0, bit_width: 8 },
        { name: 'field4', bits: '[7:0]', bit_offset: 0, bit_width: 8 },
        { name: 'field5', bits: '[7:0]', bit_offset: 0, bit_width: 8 }, // This will overflow
      ];

      const result = repackFieldsFrom(fields, 32, 0);

      // Last field should have LSB clamped to 0
      expect(result[4].bit_offset).toBe(0);
      expect(result[4].bits).toBe('[7:0]');
    });

    it('should handle fields with bit_offset/bit_width instead of bits string', () => {
      const fields = [
        { name: 'field1', bit_offset: 24, bit_width: 8 },
        { name: 'field2', bit_offset: 16, bit_width: 8 },
      ];

      const result = repackFieldsFrom(fields, 32, 0);

      expect(result[0].bits).toBe('[31:24]');
      expect(result[1].bits).toBe('[23:16]');
    });
  });

  describe('repackFieldsDownward', () => {
    it('should move fields toward LSB starting from index', () => {
      const fields = [
        { name: 'field1', bits: '[31:24]', bit_offset: 24, bit_width: 8 },
        { name: 'field2', bits: '[23:16]', bit_offset: 16, bit_width: 8 },
        { name: 'field3', bits: '[15:8]', bit_offset: 8, bit_width: 8 },
        { name: 'field4', bits: '[7:0]', bit_offset: 0, bit_width: 8 },
      ];

      // Repack fields 2-4 downward
      const result = repackFieldsDownward(fields, 2, 32);

      // Field 1 and 2 unchanged, field 3 moves down to [15:8], field 4 to [7:0]
      expect(result[0].bits).toBe('[31:24]');
      expect(result[1].bits).toBe('[23:16]');
      expect(result[2].bits).toBe('[15:8]');
      expect(result[3].bits).toBe('[7:0]');
    });

    it('should start from MSB-1 when previous field exists', () => {
      const fields = [
        { name: 'field1', bits: '[31:28]', bit_offset: 28, bit_width: 4 },
        { name: 'field2', bits: '[20:16]', bit_offset: 16, bit_width: 5 },
      ];

      const result = repackFieldsDownward(fields, 1, 32);

      // Field 2 should start at bit 27 (MSB-1 of field 1)
      expect(result[1].bits).toBe('[27:23]');
    });

    it('should clamp to LSB = 0', () => {
      const fields = [
        { name: 'field1', bits: '[10:5]', bit_offset: 5, bit_width: 6 },
        { name: 'field2', bits: '[15:8]', bit_offset: 8, bit_width: 8 }, // Too wide
      ];

      const result = repackFieldsDownward(fields, 1, 16);

      // Should clamp field 2's LSB to 0
      expect(result[1].bit_offset).toBeGreaterThanOrEqual(0);
    });
  });

  describe('repackFieldsUpward', () => {
    it('should move fields toward MSB going backward from index', () => {
      const fields = [
        { name: 'field1', bits: '[31:24]', bit_offset: 24, bit_width: 8 },
        { name: 'field2', bits: '[23:16]', bit_offset: 16, bit_width: 8 },
        { name: 'field3', bits: '[15:8]', bit_offset: 8, bit_width: 8 },
      ];

      // Repack fields 0-1 upward
      const result = repackFieldsUpward(fields, 1, 32);

      // Fields move upward
      expect(result[1].bit_offset).toBeGreaterThanOrEqual(0);
      expect(result[0].bit_offset).toBeGreaterThanOrEqual(
        result[1].bit_offset + result[1].bit_width
      );
    });

    it('should start from LSB+1 of next field when it exists', () => {
      const fields = [
        { name: 'field1', bits: '[25:20]', bit_offset: 20, bit_width: 6 },
        { name: 'field2', bits: '[15:10]', bit_offset: 10, bit_width: 6 },
      ];

      const result = repackFieldsUpward(fields, 0, 32);

      // Field 1 should start at LSB = 16 (MSB+1 of field 2)
      expect(result[0].bit_offset).toBe(16);
    });

    it('should clamp to MSB = regWidth-1', () => {
      const fields = [
        { name: 'field1', bits: '[20:10]', bit_offset: 10, bit_width: 11 },
        { name: 'field2', bits: '[5:0]', bit_offset: 0, bit_width: 6 },
      ];

      const result = repackFieldsUpward(fields, 0, 16);

      // Field 1's MSB should be clamped to 15
      const msb = result[0].bit_offset + result[0].bit_width - 1;
      expect(msb).toBeLessThanOrEqual(15);
    });
  });

  describe('Edge cases', () => {
    it('should handle empty fields array', () => {
      expect(repackFieldsFrom([], 32, 0)).toEqual([]);
      expect(repackFieldsDownward([], 0, 32)).toEqual([]);
      expect(repackFieldsUpward([], 0, 32)).toEqual([]);
    });

    it('should handle single field', () => {
      const fields = [{ name: 'field1', bits: '[7:0]', bit_offset: 0, bit_width: 8 }];

      const result1 = repackFieldsFrom(fields, 32, 0);
      expect(result1[0].bits).toBe('[31:24]');

      const result2 = repackFieldsDownward(fields, 0, 32);
      expect(result2[0].bits).toBe('[31:24]');

      const result3 = repackFieldsUpward(fields, 0, 32);
      expect(result3.length).toBe(1);
    });

    it('should handle 1-bit fields', () => {
      const fields = [
        { name: 'bit1', bits: '[5]', bit_offset: 5, bit_width: 1 },
        { name: 'bit2', bits: '[3]', bit_offset: 3, bit_width: 1 },
      ];

      const result = repackFieldsFrom(fields, 8, 0);
      expect(result[0].bits).toBe('[7]');
      expect(result[1].bits).toBe('[6]');
    });
  });
});
