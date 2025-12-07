-- SPI Master interface with configurable clock polarity
-- Tests bus interface detection (SPI signals)

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity spi_master is
    generic (
        DATA_WIDTH : integer   := 8;
        CLK_DIV    : integer   := 4;   -- System clock divider
        CPOL       : std_logic := '0'; -- Clock polarity
        CPHA       : std_logic := '0'  -- Clock phase
    );
    port (
        -- System interface
        clk   : in std_logic;
        rst_n : in std_logic;

        -- Control/Data interface
        tx_data : in std_logic_vector(DATA_WIDTH - 1 downto 0);
        rx_data : out std_logic_vector(DATA_WIDTH - 1 downto 0);
        start   : in std_logic;
        busy    : out std_logic;
        done    : out std_logic;

        -- SPI interface
        spi_sclk : out std_logic;
        spi_mosi : out std_logic;
        spi_miso : in std_logic;
        spi_cs_n : out std_logic
    );
end entity spi_master;

architecture rtl of spi_master is

    type state_t is (IDLE, TRANSMIT, COMPLETE);
    signal state : state_t;

    signal clk_counter  : integer range 0 to CLK_DIV - 1;
    signal bit_counter  : integer range 0 to DATA_WIDTH - 1;
    signal tx_shift_reg : std_logic_vector(DATA_WIDTH - 1 downto 0);
    signal rx_shift_reg : std_logic_vector(DATA_WIDTH - 1 downto 0);
    signal spi_clk_en   : std_logic;
    signal spi_clk_reg  : std_logic;

begin

    spi_sclk <= spi_clk_reg when state = TRANSMIT else
        CPOL;

    -- Main FSM
    process (clk, rst_n)
    begin
        if rst_n = '0' then
            state        <= IDLE;
            spi_cs_n     <= '1';
            busy         <= '0';
            done         <= '0';
            clk_counter  <= 0;
            bit_counter  <= 0;
            spi_clk_reg  <= CPOL;
            tx_shift_reg <= (others => '0');
            rx_shift_reg <= (others => '0');
            spi_mosi     <= '0';
            rx_data      <= (others => '0');

        elsif rising_edge(clk) then
            done <= '0'; -- Pulse

            case state is
                when IDLE =>
                    spi_cs_n    <= '1';
                    busy        <= '0';
                    spi_clk_reg <= CPOL;

                    if start = '1' then
                        tx_shift_reg <= tx_data;
                        bit_counter  <= DATA_WIDTH - 1;
                        clk_counter  <= 0;
                        spi_cs_n     <= '0';
                        busy         <= '1';
                        state        <= TRANSMIT;
                    end if;

                when TRANSMIT =>
                    if clk_counter = CLK_DIV - 1 then
                        clk_counter <= 0;
                        spi_clk_reg <= not spi_clk_reg;

                        -- Data capture on appropriate edge
                        if (spi_clk_reg = CPOL and CPHA = '0') or
                            (spi_clk_reg /= CPOL and CPHA = '1') then
                            -- Shift out
                            spi_mosi     <= tx_shift_reg(DATA_WIDTH - 1);
                            tx_shift_reg <= tx_shift_reg(DATA_WIDTH - 2 downto 0) & '0';
                        else
                            -- Shift in
                            rx_shift_reg <= rx_shift_reg(DATA_WIDTH - 2 downto 0) & spi_miso;

                            if bit_counter = 0 then
                                state <= COMPLETE;
                            else
                                bit_counter <= bit_counter - 1;
                            end if;
                        end if;
                    else
                        clk_counter <= clk_counter + 1;
                    end if;

                when COMPLETE =>
                    spi_cs_n    <= '1';
                    spi_clk_reg <= CPOL;
                    rx_data     <= rx_shift_reg;
                    done        <= '1';
                    state       <= IDLE;

            end case;
        end if;
    end process;

end architecture rtl;
