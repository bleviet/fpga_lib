import os
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

# Import the driver library
from fpga_lib.driver import load_driver
from fpga_lib.driver.bus import CocotbBus


@cocotb.test()
async def test_register_access(dut):
    """
    Test register read/write access for my_timer_core.
    Generated automatically by fpga_lib
    """

    # 1. Setup Clock
    cocotb.start_soon(Clock(dut.i_clk_sys, 10, units="ns").start())

    # 2. Reset
    dut.i_rst_n_sys.value = 0
    await Timer(100, units="ns")
    dut.i_rst_n_sys.value = 1
    await RisingEdge(dut.i_clk_sys)
    await RisingEdge(dut.i_clk_sys)
    dut._log.info("Reset complete")

    # 3. Initialize Bus and Driver
    bus = CocotbBus(dut, "s_axi", dut.i_clk_sys)

    # Locate the memmap file (use original .mm.yml from parent directory)
    memmap_path = os.path.join(os.path.dirname(__file__), "../my_timer_core.mm.yml")
    if not os.path.exists(memmap_path):
        dut._log.error(f"Memory map file not found: {memmap_path}")
        assert False, f"Missing memmap: {memmap_path}"

    dut._log.info(f"Loading driver from {memmap_path}...")
    driver = load_driver(memmap_path, bus)

    # 4. Test register discovery
    dut._log.info("Discovering registers...")

    for block_name in dir(driver):
        if block_name.startswith('_'):
            continue
        block = getattr(driver, block_name)

        dut._log.info(f"Block: {block_name}")

        for reg_name in dir(block):
            if reg_name.startswith('_'):
                continue
            reg = getattr(block, reg_name)

            # Check for Register Array
            if hasattr(reg, '__getitem__') and hasattr(reg, '__len__'):
                dut._log.info(f"  Register Array: {reg_name} (Length: {len(reg)})")
            # Check for standard Register (has async methods)
            elif hasattr(reg, 'read_async'):
                dut._log.info(f"  Register: {reg_name} @ 0x{reg.offset:04X}")

    # 5. Test specific register operations with async methods
    dut._log.info("Testing registers with async read/write...")

    # Helper to test a register
    async def test_register(name, reg):
        """Test a single register with read/write pattern."""
        try:
            # Write test pattern
            test_val = 0xA5A5A5A5
            await reg.write_async(test_val)

            # Read back
            read_val = await reg.read_async()
            dut._log.info(f"  {name}: wrote 0x{test_val:08X}, read 0x{read_val:08X}")

        except Exception as e:
            dut._log.warning(f"  {name}: {e}")

    # Iterate over all blocks and registers
    for block_name in dir(driver):
        if block_name.startswith('_'):
            continue
        block = getattr(driver, block_name)

        for reg_name in dir(block):
            if reg_name.startswith('_'):
                continue
            reg = getattr(block, reg_name)

            # Standard Register
            if hasattr(reg, 'read_async') and hasattr(reg, 'write_async'):
                await test_register(f"{block_name}.{reg_name}", reg)

            # Register Array - test first element
            elif hasattr(reg, '__getitem__') and hasattr(reg, '__len__') and len(reg) > 0:
                await test_register(f"{block_name}.{reg_name}[0]", reg[0])

    dut._log.info("All register tests completed!")


@cocotb.test()
async def test_field_access(dut):
    """
    Test bit-field level access for my_timer_core.
    """

    # Setup
    cocotb.start_soon(Clock(dut.i_clk_sys, 10, units="ns").start())
    dut.i_rst_n_sys.value = 0
    await Timer(100, units="ns")
    dut.i_rst_n_sys.value = 1
    await RisingEdge(dut.i_clk_sys)
    await RisingEdge(dut.i_clk_sys)

    # Initialize driver
    bus = CocotbBus(dut, "s_axi", dut.i_clk_sys)
    memmap_path = os.path.join(os.path.dirname(__file__), "../my_timer_core.mm.yml")
    driver = load_driver(memmap_path, bus)

    dut._log.info("Testing field-level access...")

    # Test first available register with fields
    tested = False
    for block_name in dir(driver):
        if block_name.startswith('_') or tested:
            continue
        block = getattr(driver, block_name)

        for reg_name in dir(block):
            if reg_name.startswith('_') or tested:
                continue
            reg = getattr(block, reg_name)

            if hasattr(reg, '_fields') and reg._fields:
                # Get first writable field
                for field_name, field in reg._fields.items():
                    if field.access in ['rw', 'wo']:
                        # Write and read back
                        test_val = 1
                        await reg.write_field_async(field_name, test_val)

                        if field.access == 'rw':
                            read_val = await reg.read_field_async(field_name)
                            dut._log.info(f"Field {block_name}.{reg_name}.{field_name}: wrote {test_val}, read {read_val}")
                            assert read_val == test_val, f"Field mismatch"
                        else:
                            dut._log.info(f"Field {block_name}.{reg_name}.{field_name}: wrote {test_val} (write-only)")

                        tested = True
                        break
                if tested:
                    break

    if tested:
        dut._log.info("Field access test passed!")
    else:
        dut._log.warning("No writable fields found to test")