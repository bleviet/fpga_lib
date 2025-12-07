-- Simple 8-bit counter with enable and reset
-- Demonstrates basic entity structure with minimal complexity

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity simple_counter is
    generic (
        WIDTH : integer := 8
    );
    port (
        clk    : in std_logic;
        rst_n  : in std_logic;
        enable : in std_logic;
        count  : out std_logic_vector(WIDTH - 1 downto 0)
    );
end entity simple_counter;

architecture rtl of simple_counter is
    signal count_reg : unsigned(WIDTH - 1 downto 0);
begin

    process (clk, rst_n)
    begin
        if rst_n = '0' then
            count_reg <= (others => '0');
        elsif rising_edge(clk) then
            if enable = '1' then
                count_reg <= count_reg + 1;
            end if;
        end if;
    end process;

    count <= std_logic_vector(count_reg);

end architecture rtl;
