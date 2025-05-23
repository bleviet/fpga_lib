library ieee;
use ieee.std_logic_1164.all;

entity neorv32_sdi is
    generic (
        RTX_FIFO : natural range 1 to 2**15
    );
    port (
        clk_i : in std_ulogic;
        rstn_i : in std_ulogic;
        bus_req_i : in bus_req_t;
        bus_rsp_o : out bus_rsp_t;
        sdi_csn_i : in std_ulogic;
        sdi_clk_i : in std_ulogic;
        sdi_dat_i : in std_ulogic;
        sdi_dat_o : out std_ulogic;
        irq_o : out std_ulogic
    );
end entity neorv32_sdi;