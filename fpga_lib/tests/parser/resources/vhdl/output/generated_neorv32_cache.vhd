library ieee;
use ieee.std_logic_1164.all;

entity neorv32_cache is
    generic (
        NUM_BLOCKS : natural range 2 to 1024;
        BLOCK_SIZE : natural range 4 to 32768;
        UC_BEGIN : std_ulogic_vector(3 downto 0);
        READ_ONLY : boolean
    );
    port (
        clk_i : in std_ulogic;
        rstn_i : in std_ulogic;
        clean_o : out std_ulogic;
        host_req_i : in bus_req_t;
        host_rsp_o : out bus_rsp_t;
        bus_req_o : out bus_req_t;
        bus_rsp_i : in bus_rsp_t
    );
end entity neorv32_cache;