library ieee;
use ieee.std_logic_1164.all;

entity neorv32_clint is
    generic (
        NUM_HARTS : natural range 1 to 4095
    );
    port (
        clk_i : in std_ulogic;
        rstn_i : in std_ulogic;
        bus_req_i : in bus_req_t;
        bus_rsp_o : out bus_rsp_t;
        time_o : out std_ulogic_vector(63 downto 0);
        mti_o : out std_ulogic_vector(NUM_HARTS-1 downto 0);
        msi_o : out std_ulogic_vector(NUM_HARTS-1 downto 0)
    );
end entity neorv32_clint;