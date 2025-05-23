library ieee;
use ieee.std_logic_1164.all;

entity neorv32_dma is
    port (
        clk_i : in std_ulogic;
        rstn_i : in std_ulogic;
        bus_req_i : in bus_req_t;
        bus_rsp_o : out bus_rsp_t;
        dma_req_o : out bus_req_t;
        dma_rsp_i : in bus_rsp_t;
        irq_o : out std_ulogic
    );
end entity neorv32_dma;