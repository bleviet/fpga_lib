library ieee;
use ieee.std_logic_1164.all;

entity neorv32_gpio is
    generic (
        GPIO_NUM : natural range 0 to 32
    );
    port (
        clk_i : in std_ulogic;
        rstn_i : in std_ulogic;
        bus_req_i : in bus_req_t;
        bus_rsp_o : out bus_rsp_t;
        gpio_o : out std_ulogic_vector(31 downto 0);
        gpio_i : in std_ulogic_vector(31 downto 0);
        cpu_irq_o : out std_ulogic
    );
end entity neorv32_gpio;