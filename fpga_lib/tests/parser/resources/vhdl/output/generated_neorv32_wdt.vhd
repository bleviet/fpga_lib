library ieee;
use ieee.std_logic_1164.all;

entity neorv32_wdt is
    port (
        clk_i : in std_ulogic;
        rstn_ext_i : in std_ulogic;
        rstn_dbg_i : in std_ulogic;
        rstn_sys_i : in std_ulogic;
        bus_req_i : in bus_req_t;
        bus_rsp_o : out bus_rsp_t;
        clkgen_en_o : out std_ulogic;
        clkgen_i : in std_ulogic_vector(7 downto 0);
        rstn_o : out std_ulogic
    );
end entity neorv32_wdt;