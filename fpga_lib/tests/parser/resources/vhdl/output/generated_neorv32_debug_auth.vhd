library ieee;
use ieee.std_logic_1164.all;

entity neorv32_debug_auth is
    port (
        clk_i : in std_ulogic;
        rstn_i : in std_ulogic;
        we_i : in std_ulogic;
        re_i : in std_ulogic;
        wdata_i : in std_ulogic_vector(31 downto 0);
        rdata_o : out std_ulogic_vector(31 downto 0);
        enable_i : in std_ulogic;
        busy_o : out std_ulogic;
        valid_o : out std_ulogic
    );
end entity neorv32_debug_auth;