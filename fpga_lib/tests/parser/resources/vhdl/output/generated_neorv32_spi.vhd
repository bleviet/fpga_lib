library ieee;
use ieee.std_logic_1164.all;

entity neorv32_spi is
    generic (
        IO_SPI_FIFO : natural range 1 to 2**15
    );
    port (
        clk_i : in std_ulogic;
        rstn_i : in std_ulogic;
        bus_req_i : in bus_req_t;
        bus_rsp_o : out bus_rsp_t;
        clkgen_en_o : out std_ulogic;
        clkgen_i : in std_ulogic_vector(7 downto 0);
        spi_clk_o : out std_ulogic;
        spi_dat_o : out std_ulogic;
        spi_dat_i : in std_ulogic;
        spi_csn_o : out std_ulogic_vector(7 downto 0);
        irq_o : out std_ulogic
    );
end entity neorv32_spi;