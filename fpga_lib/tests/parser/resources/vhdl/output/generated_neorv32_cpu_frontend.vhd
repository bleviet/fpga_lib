library ieee;
use ieee.std_logic_1164.all;

entity neorv32_cpu_frontend is
    generic (
        RVC_EN : boolean
    );
    port (
        clk_i : in std_ulogic;
        rstn_i : in std_ulogic;
        ctrl_i : in ctrl_bus_t;
        ibus_req_o : out bus_req_t;
        ibus_rsp_i : in bus_rsp_t;
        frontend_o : out if_bus_t
    );
end entity neorv32_cpu_frontend;