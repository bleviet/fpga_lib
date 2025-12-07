# VHDL Test Files for AI Parser

This directory contains diverse VHDL test files to validate the AI-powered parser's capabilities.

## Test Files

### 1. `simple_counter.vhd`
**Purpose:** Basic entity structure with minimal complexity

**Features:**
- Single generic with simple arithmetic (`WIDTH-1`)
- Basic port types (std_logic, std_logic_vector)
- Active-low reset
- Simple sequential logic

**Expected Parser Output:**
- 1 generic (WIDTH)
- 4 ports (clk, rst_n, enable, count)
- 0 bus interfaces

---

### 2. `uart_transmitter.vhd`
**Purpose:** Tests arithmetic expressions and boolean generics

**Features:**
- Multiple generics with different types (integer, boolean)
- Constant calculations in architecture
- Complex FSM
- Conditional logic based on generics

**Expected Parser Output:**
- 5 generics (CLK_FREQ, BAUD_RATE, DATA_BITS, STOP_BITS, PARITY_ENABLE)
- 6 ports (system + data interface + UART)
- 0 bus interfaces (custom protocol)

---

### 3. `fifo_buffer.vhd`
**Purpose:** Tests power-of-2 expressions and complex width calculations

**Features:**
- Power-of-2 depth calculation (`2**DEPTH_LOG2`)
- Width expressions with addition (`DEPTH_LOG2 downto 0`)
- Memory array architecture
- Full/empty flags

**Expected Parser Output:**
- 2 generics (DATA_WIDTH, DEPTH_LOG2)
- 8 ports (clk, rst_n, write interface, read interface, status)
- 0 bus interfaces

---

### 4. `spi_master.vhd`
**Purpose:** Tests SPI bus interface detection

**Features:**
- SPI protocol signals (sclk, mosi, miso, cs_n)
- Clock polarity/phase configuration
- Bidirectional data transfer
- FSM with clock division

**Expected Parser Output:**
- 4 generics (DATA_WIDTH, CLK_DIV, CPOL, CPHA)
- 10 ports (system + control + SPI interface)
- 1 bus interface (SPI master)

---

### 5. `axi_stream_filter.vhd`
**Purpose:** Tests AXI-Stream bus interface detection

**Features:**
- AXI-Stream slave interface (s_axis_*)
- AXI-Stream master interface (m_axis_*)
- Standard handshaking (tvalid, tready, tlast)
- Moving average filter algorithm

**Expected Parser Output:**
- 2 generics (DATA_WIDTH, WINDOW_SIZE)
- 10 ports (aclk, aresetn, slave interface, master interface)
- 2 bus interfaces (AXI-Stream slave, AXI-Stream master)

---

### 6. `pwm_generator.vhd`
**Purpose:** Tests multiple output channels and array handling

**Features:**
- Multiple PWM channels
- Individual duty cycle control
- Counter-based generation
- Generate statement for multiple outputs

**Expected Parser Output:**
- 2 generics (COUNTER_WIDTH, NUM_CHANNELS)
- 8 ports (clk, rst_n, period, 4 duty cycles, pwm_out)
- 0 bus interfaces

---

### 7. `wishbone_slave.vhd`
**Purpose:** Tests Wishbone bus interface detection

**Features:**
- Wishbone B4 protocol (wb_clk_i, wb_rst_i, wb_adr_i, etc.)
- Register bank with byte-select
- Error handling (wb_err_o)
- Interrupt generation

**Expected Parser Output:**
- 3 generics (ADDR_WIDTH, DATA_WIDTH, NUM_REGS)
- 11 ports (Wishbone interface + interrupt)
- 1 bus interface (Wishbone slave)

---

### 8. `axi_example_peripheral.vhd` (Already exists)
**Purpose:** Tests AXI4-Lite bus interface detection

**Features:**
- Full AXI4-Lite slave interface
- Complex arithmetic (`(C_DATA_WIDTH/8)-1`)
- Write/read channels with handshaking
- Address decoding

**Expected Parser Output:**
- 4 generics
- 24 ports
- 1 bus interface (AXI4_LITE slave)

---

## Testing Strategy

### Complexity Levels

1. **Simple** (`simple_counter.vhd`): Basic validation
2. **Medium** (`uart_transmitter.vhd`, `fifo_buffer.vhd`, `pwm_generator.vhd`): Arithmetic expressions
3. **Complex** (`spi_master.vhd`, `axi_stream_filter.vhd`, `wishbone_slave.vhd`, `axi_example_peripheral.vhd`): Bus interface detection

### Bus Interface Detection Tests

| File | Expected Bus Type | Detection Clues |
|------|------------------|-----------------|
| `spi_master.vhd` | SPI master | `spi_sclk`, `spi_mosi`, `spi_miso`, `spi_cs_n` |
| `axi_stream_filter.vhd` | AXI-Stream (slave & master) | `s_axis_tdata`, `s_axis_tvalid`, `s_axis_tready`, `m_axis_*` |
| `wishbone_slave.vhd` | Wishbone slave | `wb_clk_i`, `wb_adr_i`, `wb_dat_i`, `wb_we_i`, `wb_cyc_i`, `wb_stb_i`, `wb_ack_o` |
| `axi_example_peripheral.vhd` | AXI4-Lite slave | `s_axi_awaddr`, `s_axi_wdata`, `s_axi_rdata`, etc. |

### Expression Complexity Tests

| File | Expression Type | Example |
|------|----------------|---------|
| `simple_counter.vhd` | Simple subtraction | `WIDTH-1` |
| `fifo_buffer.vhd` | Power of 2 | `2**DEPTH_LOG2` |
| `uart_transmitter.vhd` | Division | `CLK_FREQ / BAUD_RATE` |
| `axi_example_peripheral.vhd` | Division with parens | `(C_DATA_WIDTH/8)-1` |
| `wishbone_slave.vhd` | Byte-select calculation | `(DATA_WIDTH/8)-1` |

---

## Running Tests

### Parse All Files
```bash
cd examples
for file in test_vhdl/*.vhd; do
    echo "Testing: $file"
    python ai_parser_demo.py "$file"
    echo "---"
done
```

### Test Specific Provider
```bash
# With Ollama (local)
python ai_parser_demo.py test_vhdl/axi_stream_filter.vhd

# With OpenAI
python ai_parser_demo.py test_vhdl/spi_master.vhd --provider openai

# With Gemini
python ai_parser_demo.py test_vhdl/wishbone_slave.vhd --provider gemini
```

### Verbose Mode
```bash
python ai_parser_demo.py test_vhdl/uart_transmitter.vhd --verbose
```

---

## Expected Results

All test files should successfully parse with the AI parser, producing:
- ✅ Correct entity name
- ✅ Accurate port counts and directions
- ✅ Proper generic extraction with defaults
- ✅ Correct width calculations (even complex ones)
- ✅ Bus interface detection (where applicable)
- ✅ Generated description based on comments

---

## Validation Checklist

For each test file, verify:
- [ ] Entity name matches filename
- [ ] All ports parsed with correct directions
- [ ] All generics extracted with defaults
- [ ] Width calculations correct (including arithmetic)
- [ ] Bus interfaces detected (if expected)
- [ ] Description generated appropriately
- [ ] No parsing errors or warnings
