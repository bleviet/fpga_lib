library ieee;
use ieee.std_logic_1164.all;

entity neorv32_sys_reset is
    port (
        clk_i : in std_ulogic;
        rstn_ext_i : in std_ulogic;
        rstn_wdt_i : in std_ulogic;
        rstn_dbg_i : in std_ulogic;
        rstn_ext_o : out std_ulogic;
        rstn_sys_o : out std_ulogic;
        xrstn_wdt_o : out std_ulogic;
        xrstn_ocd_o : out std_ulogic
    );
end entity neorv32_sys_reset;