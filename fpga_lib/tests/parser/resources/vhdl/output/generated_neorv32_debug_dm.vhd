library ieee;
use ieee.std_logic_1164.all;

entity neorv32_debug_dm is
    generic (
        NUM_HARTS : natural range 1 to 4 := 1;
        AUTHENTICATOR : boolean := false
    );
    port (
        clk_i : in std_ulogic;
        rstn_i : in std_ulogic;
        dmi_req_i : in dmi_req_t;
        dmi_rsp_o : out dmi_rsp_t;
        bus_req_i : in bus_req_t;
        bus_rsp_o : out bus_rsp_t;
        ndmrstn_o : out std_ulogic;
        halt_req_o : out std_ulogic_vector(NUM_HARTS-1 downto 0)
    );
end entity neorv32_debug_dm;