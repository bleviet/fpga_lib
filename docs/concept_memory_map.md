# Memory Map: The Single Source of Truth

This document defines the standardized YAML format for describing the memory map of an IP core. The goal is to create a single, human-readable file that serves as the single source of truth for the hardware's register and bit-field layout.

This file is the foundation for automating several critical engineering tasks:
*   **Driver Generation:** Dynamically creating Python drivers with a complete API for register access.
*   **Documentation:** Automatically generating hardware register maps for datasheets.
*   **Validation:** Enabling tools to check for address overlaps and other common errors.
*   **Simulation:** Providing the register model for testbenches.

---

## 1. Why YAML?

YAML was chosen because it provides the best balance of **human readability** and the ability to naturally represent the **nested structure** of a hardware memory map. The primary goal is for this file to be a definitive specification that is easy for engineers to read, understand, and maintain.

*   **Superior Readability:** YAML's minimal syntax and use of indentation to denote structure make the file clean and easy to comprehend, resembling a document outline.
*   **Natural for Nested Data:** The core structure is a "list of registers," where each register contains a "list of bit fields." This pattern maps perfectly and intuitively to YAML's indented list format.
*   **Essential Comment Support:** Hardware design requires documentation. YAML's first-class support for comments (`#`) is crucial for embedding descriptions and notes directly within the map, which is a major advantage over formats like JSON.

| Feature                | YAML               | TOML      | JSON       |
| :--------------------- | :----------------- | :-------- | :--------- |
| **Human Readability**  | ✅ **Excellent**   | ✅ Good   | 🆗 Okay    |
| **Comment Support**    | ✅ Yes             | ✅ Yes    | ❌ **No**  |
| **Nested Lists/Objects** | ✅ **Very Natural**  | 🆗 Awkward  | ✅ Natural |

---

## 2. Schema Definition

The memory map is defined by a top-level `registers` key, which contains a list of register definitions.

### Register Definition

A register is an object in the `registers` list. It can be a simple register, a register with bit-fields, or a register array (e.g., for a block of RAM).

| Key           | Type     | Required | Description                                                                 |
| :------------ | :------- | :------- | :-------------------------------------------------------------------------- |
| `name`        | `string` | Yes      | The name of the register, used for attribute access in the driver (e.g., `driver.control`). |
| `offset`      | `hex`    | Yes      | The byte offset of the register from the peripheral's base address.         |
| `description` | `string` | No       | A brief description of the register's purpose.                              |
| `fields`      | `list`   | No       | A list of `BitField` objects that define the layout of the register. If omitted, the register is treated as a single 32-bit entity. |
| `count`       | `integer`| No       | If present, defines a register array. See the "Register Arrays" section.    |
| `stride`      | `integer`| No       | The byte distance between elements in a register array. Defaults to 4.      |

### Bit Field Definition

A bit field is an object in a register's `fields` list.

| Key           | Type     | Required | Description                                                                 |
| :------------ | :------- | :------- | :-------------------------------------------------------------------------- |
| `name`        | `string` | Yes      | The name of the bit field, used for attribute access (e.g., `driver.control.enable`). |
| `bit` / `bits`| `any`    | Yes      | The bit position(s). Use `bit: 0` for a single bit or `bits: [7:4]` for a multi-bit field. |
| `access`      | `string` | No       | Access type. One of: `rw` (Read/Write), `ro` (Read-Only), `wo` (Write-Only), `rw1c` (Read/Write, 1 to Clear), `w1sc` (Write 1, Self-Clearing). Defaults to `rw`. |
| `reset`       | `integer`| No       | The default value of the field after a system reset. Must fit within the field's width. |
| `description` | `string` | No       | A brief description of the bit field's purpose.                             |

---

## 3. Comprehensive Example

This example defines a memory map for a simple GPIO controller.

```yaml
# file: gpio_controller.yaml
# Memory map for a standard GPIO controller.

registers:
  - name: data
    offset: 0x00
    description: GPIO data register. Each bit corresponds to a physical pin.
    fields:
      - name: pins
        bits: [31:0]
        access: rw
        description: Read for pin level, write to set output value.

  - name: direction
    offset: 0x04
    description: GPIO direction control. 0 = input, 1 = output.
    fields:
      - name: dir
        bits: [31:0]
        access: rw
        reset: 0 # Default all pins to input
        description: Sets the direction for each corresponding GPIO pin.

  - name: config
    offset: 0x08
    description: Core configuration and status register.
    fields:
      - name: enable
        bit: 0
        access: rw
        reset: 1 # Core is enabled by default
        description: Master enable for the GPIO core.
      - name: pin_count
        bits: [12:8]
        access: ro
        description: "Read-only field indicating the number of GPIO pins implemented."
      - name: version
        bits: [31:24]
        access: ro
        description: "IP core version number."

  - name: interrupt_status
    offset: 0x0C
    description: Interrupt status register. Write 1 to clear a pending interrupt.
    fields:
      - name: edge_detect
        bits: [31:0]
        access: rw1c # Write-1-to-clear access type
        description: Each bit indicates a detected edge on the corresponding pin.

  # --- Definition for a Register Array ---
  - name: pin_config
    offset: 0x100
    description: Per-pin configuration registers.
    count: 32      # Creates an array of 32 registers
    stride: 4      # Each register is 4 bytes apart
    fields:
      - name: pullup_en
        bit: 0
        access: rw
        reset: 0
        description: Enable internal pull-up for this pin.
      - name: debounce_en
        bit: 1
        access: rw
        reset: 0
        description: Enable input debouncing for this pin.
      - name: drive_strength
        bits: [3:2]
        access: rw
        reset: 1 # Default to medium drive strength
        description: "Sets the output driver strength."
```

### Accessing in Python (Conceptual)

The YAML above would allow a generated driver to be used like this:

```python
# Create the driver by loading the YAML
driver = create_driver_from_yaml("gpio_controller.yaml", bus)

# --- Basic Register/Field Access ---
# Set all pins to output
driver.direction.dir = 0xFFFFFFFF

# Set the lower 8 pins high
driver.data.pins = 0xFF

# Read the IP core version
version = driver.config.version
print(f"IP Core Version: {version}")

# Clear an interrupt on pin 5
driver.interrupt_status.edge_detect = (1 << 5)

# --- Register Array Access ---
# Configure pin 10 with a pull-up and high drive strength
driver.pin_config[10].pullup_en = 1
driver.pin_config[10].drive_strength = 3

# Read the debounce setting for pin 15
debounce_enabled = driver.pin_config[15].debounce_en
```
