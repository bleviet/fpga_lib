# Bit Field Reset Values Feature

This document describes the new bit field reset values feature implemented in the Memory Map Editor.

## Overview

The Memory Map Editor now supports defining and visualizing reset values for individual bit fields. This feature provides critical information for debugging and verification by allowing engineers to know the default state of a register immediately after power-on or system reset.

## Key Features

### 1. Data Model Support
- **BitField Class**: Extended with optional `reset_value` parameter
- **Register Class**: New `reset_value` property that calculates the complete register reset value from its bit fields
- **Validation**: Reset values are validated to ensure they fit within the field's bit width

### 2. Enhanced UI

#### Bit Fields Table
- **New Reset Column**: Added "Reset" column in the bit fields table
- **Inline Editing**: Users can edit reset values directly in the table
- **Validation**: Prevents entering values that exceed the field's maximum value

#### Calculated Reset Value Display
- **Register Properties**: Shows the calculated total reset value in hexadecimal format
- **Real-time Updates**: Automatically recalculates when bit field reset values change
- **Array Handling**: Shows "N/A (Array)" for register arrays since each instance is separate

#### Enhanced Bit Field Visualizer
- **Dual Display**: Each bit box shows both the bit number (top) and reset value (bottom)
- **Color Coding**: 
  - Green text for reset value '1'
  - Gray text for reset value '0'
- **Visual Feedback**: Immediately see the default state of the entire register

### 3. YAML Schema Extension

#### Loading Support
```yaml
registers:
  - name: config
    offset: 0x10
    fields:
      - name: enable
        bit: 0
        access: rw
        reset: 0          # Reset to 'disabled'
      - name: mode
        bits: [3:1]
        access: rw
        reset: 5          # 3-bit field resets to '101'
      - name: clk_sel
        bits: [5:4]
        access: ro
        reset: 1          # 2-bit field resets to '01'
```

#### Saving Support
- Reset values are automatically saved to YAML when specified
- Fields without reset values omit the `reset` key (backward compatible)

## Usage Examples

### Basic Usage
1. **Create a new register** with bit fields
2. **Set reset values** by editing the "Reset" column in the bit fields table
3. **View calculated reset value** in the register properties panel
4. **Visualize reset state** in the enhanced bit field visualizer

### Example Register
For a configuration register with:
- `enable` (bit 0) = reset value 0
- `mode` (bits 3:1) = reset value 5 (binary 101)  
- `clk_sel` (bits 5:4) = reset value 1 (binary 01)
- `interrupt_enable` (bit 6) = reset value 1

**Calculated Reset Value**: `0x52` (binary: 01010010)

**Visualizer Display**:
```
Bit:    7  6  5  4  3  2  1  0
Reset:  0  1  0  1  1  0  1  0
        ^  ^  ^^^^^  ^^^^^  ^
        |  |    |     |    +-- enable=0
        |  |    |     +------- mode=5
        |  |    +------------- clk_sel=1  
        |  +------------------ interrupt_enable=1
        +--------------------- unused=0
```

## Technical Implementation

### Data Model
```python
@dataclass
class BitField:
    name: str
    offset: int
    width: int
    access: Union[AccessType, str] = AccessType.RW
    description: str = ''
    reset_value: Optional[int] = None  # New field

class Register:
    @property
    def reset_value(self) -> int:
        """Calculate total reset value from bit fields."""
        total_reset = 0
        for field in self._fields.values():
            if field.reset_value is not None:
                total_reset |= (field.reset_value << field.offset)
        return total_reset
```

### UI Components
- **Register Detail Form**: Added reset value column and calculated display
- **Bit Field Visualizer**: Enhanced to show reset values in each bit box
- **YAML Core**: Extended loading/saving to handle reset values

## Backward Compatibility

- **Existing YAML files** without reset values continue to work
- **Default behavior**: Fields without reset values show "0" in the UI
- **Optional feature**: Reset values are completely optional and don't break existing workflows

## Testing

Use the provided `test_reset_values.yaml` file to test the feature:

```bash
cd examples/gui/memory_map_editor
python main.py
# File -> Open -> test_reset_values.yaml
```

This will load a sample register with various reset values to demonstrate the feature.
