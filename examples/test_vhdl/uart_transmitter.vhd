-- UART Transmitter with configurable baud rate
-- Tests arithmetic expressions in generics and port widths

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity uart_transmitter is
    generic (
        CLK_FREQ      : integer := 50000000; -- 50 MHz
        BAUD_RATE     : integer := 115200;
        DATA_BITS     : integer := 8;
        STOP_BITS     : integer := 1;
        PARITY_ENABLE : boolean := false
    );
    port (
        -- System signals
        clk : in std_logic;
        rst : in std_logic;

        -- Data interface
        tx_data  : in std_logic_vector(DATA_BITS - 1 downto 0);
        tx_valid : in std_logic;
        tx_ready : out std_logic;

        -- UART output
        uart_tx : out std_logic
    );
end entity uart_transmitter;

architecture rtl of uart_transmitter is

    constant CLKS_PER_BIT : integer := CLK_FREQ / BAUD_RATE;

    type state_t is (IDLE, START_BIT, DATA_BITS_ST, PARITY_BIT, STOP_BITS_ST);
    signal state : state_t;

    signal bit_counter : integer range 0 to DATA_BITS - 1;
    signal clk_counter : integer range 0 to CLKS_PER_BIT - 1;
    signal tx_data_reg : std_logic_vector(DATA_BITS - 1 downto 0);

begin

    -- FSM for UART transmission
    process (clk, rst)
    begin
        if rst = '1' then
            state       <= IDLE;
            uart_tx     <= '1';
            tx_ready    <= '1';
            bit_counter <= 0;
            clk_counter <= 0;
        elsif rising_edge(clk) then
            case state is
                when IDLE =>
                    uart_tx  <= '1';
                    tx_ready <= '1';
                    if tx_valid = '1' then
                        tx_data_reg <= tx_data;
                        tx_ready    <= '0';
                        state       <= START_BIT;
                    end if;

                when START_BIT =>
                    uart_tx <= '0';
                    if clk_counter = CLKS_PER_BIT - 1 then
                        clk_counter <= 0;
                        state       <= DATA_BITS_ST;
                    else
                        clk_counter <= clk_counter + 1;
                    end if;

                when DATA_BITS_ST =>
                    uart_tx <= tx_data_reg(bit_counter);
                    if clk_counter = CLKS_PER_BIT - 1 then
                        clk_counter <= 0;
                        if bit_counter = DATA_BITS - 1 then
                            bit_counter <= 0;
                            if PARITY_ENABLE then
                                state <= PARITY_BIT;
                            else
                                state <= STOP_BITS_ST;
                            end if;
                        else
                            bit_counter <= bit_counter + 1;
                        end if;
                    else
                        clk_counter <= clk_counter + 1;
                    end if;

                when PARITY_BIT =>
                    -- Even parity
                    uart_tx <= xor tx_data_reg;
                    if clk_counter = CLKS_PER_BIT - 1 then
                        clk_counter <= 0;
                        state       <= STOP_BITS_ST;
                    else
                        clk_counter <= clk_counter + 1;
                    end if;

                when STOP_BITS_ST =>
                    uart_tx <= '1';
                    if clk_counter = CLKS_PER_BIT - 1 then
                        clk_counter <= 0;
                        state       <= IDLE;
                    else
                        clk_counter <= clk_counter + 1;
                    end if;

            end case;
        end if;
    end process;

end architecture rtl;
