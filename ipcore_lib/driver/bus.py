from typing import Any
from ipcore_lib.runtime.register import AbstractBusInterface

# AbstractBusInterface is now imported from core.register
# This module only provides concrete implementations


class CocotbBus(AbstractBusInterface):
    """Bus interface implementation for Cocotb simulations using AXI-Lite."""
    def __init__(self, dut: Any, bus_name: str, clock: Any, reset: Any = None):
        # delayed import to avoiding forcing cocotb dependency on standard users
        from cocotbext.axi import AxiLiteMaster, AxiLiteBus

        bus = AxiLiteBus.from_prefix(dut, bus_name)
        # Use provided reset or try common reset names
        if reset is None:
            # Try common reset signal names
            for rst_name in ['rst', 'rst_n', 'i_rst_n', 'reset', 'reset_n']:
                if hasattr(dut, rst_name):
                    reset = getattr(dut, rst_name)
                    break
            if reset is None:
                raise AttributeError(f"No reset signal found. Please provide reset explicitly.")
        self._axi = AxiLiteMaster(bus, clock, reset)

    def read_word(self, address: int) -> int:
        # Note: Cocotb/cocotbext-axi are async. This interface is synchronous
        # to provide a clean user API. This means this driver CANNOT be used
        # directly in a standard async cocotb test function without bridging.
        #
        # HOWEVER: To make the API "feeling" identical, we might need to expose
        # these as async methods if we want to await them.
        # But standard hardware drivers (PySerial, etc) are blocking.
        #
        # If we make this async, the hardware JTAG implementation also needs to be async
        # (or just simple functions that don't await).
        #
        # Problem: 'await driver.reg.field' is syntax error.
        # 'val = await driver.reg.read_field()' works.
        # 'driver.reg.field = 1' implies immediate write.
        #
        # For Cocotb, we MUST yield to the scheduler.
        # So we simply CANNOT use property setters 'reg.field = 1' in an async test
        # if the underlying bus ops are async, unless we hide the event loop.
        #
        # COMPROMISE: We will implement async methods on the interface.
        # The 'Register' class needs to handle this.
        #
        # BUT: The concept document showed synchronous usage:
        # driver.control.enable = 1
        #
        # For this to work in Cocotb, we need a blocking call? No, Cocotb is single threaded co-routines.
        # We can't block.
        #
        # Perhaps the driver concept needs to acknowledge async?
        # Or we use a helper to run it?
        #
        # Let's check typical usage. If we return a Coroutine, the user MUST await it.
        # 'await (driver.register.write(1))'
        # 'val = await driver.register.read()'
        #
        # Property access 'driver.reg.field = 1' can't return a coroutine.
        # So property setters are OUT for async busses.
        #
        # Let's adjust the implementation to simply return the coroutine object from the low level bus.
        # But this breaks the 'property setter' abstraction.
        #
        # REVISION: For the first version, let's Stick to explicit read/write methods if async is required,
        # OR assume we are running in a context where we can trigger the write?
        #
        # Actually, for the best UX, maybe we differentiate?
        #
        # Let's look at `cocotbext-axi`. It returns coroutines.
        #
        # If we want `reg.field = 1` to work, `__setattr__` must schedule the write.
        # In Cocotb, `cocotb.start_soon()` can schedule a task without awaiting.
        # But for READ, we MUST await result. `val = reg.field` cannot work if it needs to fetch from sim time.
        #
        # So for Cocotb support, the Concept of `val = reg.field` is fundamentally broken unless we cache values
        # (shadow register) or use a non-async backdoor (simulation only).
        #
        # Let's stick to generating async-compatible API or acknowledge limitation.
        #
        # FOR NOW: I will implement `read_word` / `write_word` to return Coroutines in CocotbBus.
        # And I will update `models.py` to handle this?
        # No, `models.py` uses `self.read() & mask`. If `read()` returns a coroutine, we can't `&` it.
        #
        # CRITICAL DESIGN DECISION:
        # The `property` based access (`reg.field`) is suitable for:
        # 1. Hardware drivers (blocking JTAG/UART).
        # 2. Register models with a shadow copy (write goes to shadow, commit sends to bus).
        #
        # It is NOT suitable for direct-to-bus async simulation without `await`.
        #
        # SOLUTION:
        # I will modify `models.py` to be `async` aware where possible, OR
        # I will implement the bus interface such that for Cocotb we expect users to use `await driver.reg.read()`.
        # The `reg.field` property access might need to be dropped or modified for async.
        #
        # Let's assume the user is okay with `await driver.reg.field.read()` or similar.
        # But the concept doc promised `driver.reg.field = 1`.
        #
        # Let's implement the bus methods as async.
        # And I will update `models.py` to NOT use properties for fields, but methods, OR
        # properties that return objects we can await? `val = await driver.reg.field`?

        pass

    async def read_word(self, address: int) -> int:
        val = await self._axi.read(address, 4)
        return int.from_bytes(val.data, byteorder='little')

    async def write_word(self, address: int, data: int) -> None:
        await self._axi.write(address, data.to_bytes(4, byteorder='little'))
