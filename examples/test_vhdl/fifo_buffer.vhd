-- Synchronous FIFO buffer with full/empty flags
-- Tests power-of-2 expressions and complex width calculations

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity fifo_buffer is
    generic (
        DATA_WIDTH : integer := 32;
        DEPTH_LOG2 : integer := 4 -- Depth = 2**4 = 16
    );
    port (
        -- System signals
        clk   : in std_logic;
        rst_n : in std_logic;

        -- Write interface
        wr_data : in std_logic_vector(DATA_WIDTH - 1 downto 0);
        wr_en   : in std_logic;
        wr_full : out std_logic;

        -- Read interface
        rd_data  : out std_logic_vector(DATA_WIDTH - 1 downto 0);
        rd_en    : in std_logic;
        rd_empty : out std_logic;

        -- Status
        data_count : out std_logic_vector(DEPTH_LOG2 downto 0)
    );
end entity fifo_buffer;

architecture rtl of fifo_buffer is

    constant DEPTH : integer := 2 ** DEPTH_LOG2;

    -- Memory array
    type mem_t is array (0 to DEPTH - 1) of std_logic_vector(DATA_WIDTH - 1 downto 0);
    signal memory : mem_t;

    -- Pointers
    signal wr_ptr : unsigned(DEPTH_LOG2 - 1 downto 0);
    signal rd_ptr : unsigned(DEPTH_LOG2 - 1 downto 0);
    signal count  : unsigned(DEPTH_LOG2 downto 0);

    -- Internal flags
    signal full_i  : std_logic;
    signal empty_i : std_logic;

begin

    -- Full and empty logic
    full_i <= '1' when count = DEPTH else
        '0';
    empty_i <= '1' when count = 0 else
        '0';

    wr_full    <= full_i;
    rd_empty   <= empty_i;
    data_count <= std_logic_vector(count);

    -- Write process
    process (clk, rst_n)
    begin
        if rst_n = '0' then
            wr_ptr <= (others => '0');
        elsif rising_edge(clk) then
            if wr_en = '1' and full_i = '0' then
                memory(to_integer(wr_ptr)) <= wr_data;
                wr_ptr                     <= wr_ptr + 1;
            end if;
        end if;
    end process;

    -- Read process
    process (clk, rst_n)
    begin
        if rst_n = '0' then
            rd_ptr  <= (others => '0');
            rd_data <= (others => '0');
        elsif rising_edge(clk) then
            if rd_en = '1' and empty_i = '0' then
                rd_data <= memory(to_integer(rd_ptr));
                rd_ptr  <= rd_ptr + 1;
            end if;
        end if;
    end process;

    -- Count process
    process (clk, rst_n)
    begin
        if rst_n = '0' then
            count <= (others => '0');
        elsif rising_edge(clk) then
            if wr_en = '1' and full_i = '0' and rd_en = '0' then
                count <= count + 1;
            elsif rd_en = '1' and empty_i = '0' and wr_en = '0' then
                count <= count - 1;
            end if;
        end if;
    end process;

end architecture rtl;
