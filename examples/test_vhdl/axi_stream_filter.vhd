-- AXI-Stream moving average filter
-- Tests AXI-Stream bus interface detection

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity axi_stream_filter is
    generic (
        DATA_WIDTH  : integer := 16;
        WINDOW_SIZE : integer := 4 -- Moving average window
    );
    port (
        aclk    : in std_logic;
        aresetn : in std_logic;

        -- AXI-Stream slave interface (input)
        s_axis_tdata  : in std_logic_vector(DATA_WIDTH - 1 downto 0);
        s_axis_tvalid : in std_logic;
        s_axis_tready : out std_logic;
        s_axis_tlast  : in std_logic;

        -- AXI-Stream master interface (output)
        m_axis_tdata  : out std_logic_vector(DATA_WIDTH - 1 downto 0);
        m_axis_tvalid : out std_logic;
        m_axis_tready : in std_logic;
        m_axis_tlast  : out std_logic
    );
end entity axi_stream_filter;

architecture rtl of axi_stream_filter is

    -- Shift register for window samples
    type sample_array_t is array (0 to WINDOW_SIZE - 1) of signed(DATA_WIDTH - 1 downto 0);
    signal samples : sample_array_t;

    signal sample_count : integer range 0 to WINDOW_SIZE;
    signal sum          : signed(DATA_WIDTH + 3 downto 0); -- Extra bits for accumulation
    signal average      : signed(DATA_WIDTH - 1 downto 0);

    signal input_ready  : std_logic;
    signal output_valid : std_logic;
    signal last_reg     : std_logic;

begin

    s_axis_tready <= input_ready;
    m_axis_tvalid <= output_valid;
    m_axis_tlast  <= last_reg;

    -- Input handshake
    input_ready <= '1' when sample_count < WINDOW_SIZE or m_axis_tready = '1' else
        '0';

    -- Moving average calculation
    process (aclk, aresetn)
        variable sum_temp : signed(DATA_WIDTH + 3 downto 0);
    begin
        if aresetn = '0' then
            samples      <= (others => (others => '0'));
            sample_count <= 0;
            sum          <= (others => '0');
            average      <= (others => '0');
            output_valid <= '0';
            last_reg     <= '0';

        elsif rising_edge(aclk) then

            -- Input path
            if s_axis_tvalid = '1' and input_ready = '1' then
                -- Shift samples
                for i in WINDOW_SIZE - 1 downto 1 loop
                    samples(i) <= samples(i - 1);
                end loop;
                samples(0) <= signed(s_axis_tdata);

                last_reg <= s_axis_tlast;

                -- Update count
                if sample_count < WINDOW_SIZE then
                    sample_count <= sample_count + 1;
                end if;

                -- Calculate sum
                sum_temp := (others => '0');
                for i in 0 to WINDOW_SIZE - 1 loop
                    if i < sample_count + 1 then
                        sum_temp := sum_temp + resize(samples(i), DATA_WIDTH + 4);
                    end if;
                end loop;
                sum <= sum_temp;

                -- Calculate average
                if sample_count + 1 >= WINDOW_SIZE then
                    average      <= resize(sum_temp / WINDOW_SIZE, DATA_WIDTH);
                    output_valid <= '1';
                end if;
            end if;

            -- Output path
            if m_axis_tready = '1' and output_valid = '1' then
                output_valid <= '0';
            end if;

        end if;
    end process;

    m_axis_tdata <= std_logic_vector(average);

end architecture rtl;
