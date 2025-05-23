library ieee;
use ieee.std_logic_1164.all;

entity neorv32_cpu_counters is
    generic (
        ZICNTR_EN : boolean;
        ZIHPM_EN : boolean;
        HPM_NUM : natural range 0 to 13;
        HPM_WIDTH : natural range 0 to 64
    );
    port (
        clk_i : in std_ulogic;
        rstn_i : in std_ulogic;
        ctrl_i : in ctrl_bus_t;
        rdata_o : out std_ulogic_vector(XLEN-1 downto 0)
    );
end entity neorv32_cpu_counters;