-- Wishbone B4 slave with register bank
-- Tests Wishbone bus interface detection

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity wishbone_slave is
    generic (
        ADDR_WIDTH : integer := 8;
        DATA_WIDTH : integer := 32;
        NUM_REGS   : integer := 16
    );
    port (
        -- Wishbone bus interface
        wb_clk_i : in std_logic;
        wb_rst_i : in std_logic;
        wb_adr_i : in std_logic_vector(ADDR_WIDTH - 1 downto 0);
        wb_dat_i : in std_logic_vector(DATA_WIDTH - 1 downto 0);
        wb_dat_o : out std_logic_vector(DATA_WIDTH - 1 downto 0);
        wb_we_i  : in std_logic;
        wb_sel_i : in std_logic_vector((DATA_WIDTH/8) - 1 downto 0);
        wb_stb_i : in std_logic;
        wb_cyc_i : in std_logic;
        wb_ack_o : out std_logic;
        wb_err_o : out std_logic;

        -- Interrupt output
        irq_o : out std_logic
    );
end entity wishbone_slave;

architecture rtl of wishbone_slave is

    -- Register bank
    type reg_array_t is array (0 to NUM_REGS - 1) of std_logic_vector(DATA_WIDTH - 1 downto 0);
    signal registers : reg_array_t;

    signal wb_ack : std_logic;
    signal wb_err : std_logic;

    -- Register addresses
    constant REG_CONTROL : integer := 0;
    constant REG_STATUS  : integer := 1;
    constant REG_IRQ_EN  : integer := 2;
    constant REG_IRQ_STS : integer := 3;

begin

    wb_ack_o <= wb_ack;
    wb_err_o <= wb_err;

    -- Wishbone bus access
    process (wb_clk_i, wb_rst_i)
        variable reg_addr : integer range 0 to NUM_REGS - 1;
    begin
        if wb_rst_i = '1' then
            wb_ack    <= '0';
            wb_err    <= '0';
            wb_dat_o  <= (others => '0');
            registers <= (others => (others => '0'));

        elsif rising_edge(wb_clk_i) then
            wb_ack <= '0';
            wb_err <= '0';

            if wb_cyc_i = '1' and wb_stb_i = '1' then
                reg_addr := to_integer(unsigned(wb_adr_i(ADDR_WIDTH - 1 downto 2)));

                -- Check valid address range
                if reg_addr < NUM_REGS then
                    wb_ack <= '1';

                    -- Write operation
                    if wb_we_i = '1' then
                        for i in 0 to (DATA_WIDTH/8) - 1 loop
                            if wb_sel_i(i) = '1' then
                                registers(reg_addr)(8 * i + 7 downto 8 * i) <= wb_dat_i(8 * i + 7 downto 8 * i);
                            end if;
                        end loop;
                    else
                        -- Read operation
                        wb_dat_o <= registers(reg_addr);
                    end if;
                else
                    -- Address error
                    wb_err <= '1';
                end if;
            end if;
        end if;
    end process;

    -- Interrupt generation
    process (wb_clk_i, wb_rst_i)
    begin
        if wb_rst_i = '1' then
            irq_o <= '0';
        elsif rising_edge(wb_clk_i) then
            -- Interrupt when IRQ_STS & IRQ_EN != 0
            if (registers(REG_IRQ_STS) and registers(REG_IRQ_EN)) /= (DATA_WIDTH - 1 downto 0 => '0') then
                irq_o <= '1';
            else
                irq_o <= '0';
            end if;
        end if;
    end process;

end architecture rtl;
