library ieee;
use ieee.std_logic_1164.all;

entity neorv32_gptmr is
    port (
        clk_i : in std_ulogic;
        rstn_i : in std_ulogic;
        bus_req_i : in bus_req_t;
        bus_rsp_o : out bus_rsp_t;
        clkgen_en_o : out std_ulogic;
        clkgen_i : in std_ulogic_vector(7 downto 0);
        irq_o : out std_ulogic
    );
end entity neorv32_gptmr;