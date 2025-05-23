library ieee;
use ieee.std_logic_1164.all;

entity neorv32_cpu_cp_cond is
    port (
        clk_i : in std_ulogic;
        rstn_i : in std_ulogic;
        ctrl_i : in ctrl_bus_t;
        rs1_i : in std_ulogic_vector(XLEN-1 downto 0);
        rs2_i : in std_ulogic_vector(XLEN-1 downto 0);
        res_o : out std_ulogic_vector(XLEN-1 downto 0);
        valid_o : out std_ulogic
    );
end entity neorv32_cpu_cp_cond;