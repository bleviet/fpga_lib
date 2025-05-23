library ieee;
use ieee.std_logic_1164.all;

entity neorv32_cpu_regfile is
    generic (
        RST_EN : boolean;
        RVE_EN : boolean;
        RS3_EN : boolean
    );
    port (
        clk_i : in std_ulogic;
        rstn_i : in std_ulogic;
        ctrl_i : in ctrl_bus_t;
        rd_i : in std_ulogic_vector(XLEN-1 downto 0);
        rs1_o : out std_ulogic_vector(XLEN-1 downto 0);
        rs2_o : out std_ulogic_vector(XLEN-1 downto 0);
        rs3_o : out std_ulogic_vector(XLEN-1 downto 0)
    );
end entity neorv32_cpu_regfile;