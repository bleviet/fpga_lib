library ieee;
use ieee.std_logic_1164.all;

entity neorv32_boot_rom is
    port (
        clk_i : in std_ulogic;
        rstn_i : in std_ulogic;
        bus_req_i : in bus_req_t;
        bus_rsp_o : out bus_rsp_t
    );
end entity neorv32_boot_rom;