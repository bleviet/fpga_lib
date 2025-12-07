-- PWM Generator with configurable frequency and duty cycle
-- Tests percentage calculations and real-time control

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity pwm_generator is
    generic (
        COUNTER_WIDTH : integer := 16;
        NUM_CHANNELS  : integer := 4
    );
    port (
        clk   : in std_logic;
        rst_n : in std_logic;

        -- Configuration interface
        period : in std_logic_vector(COUNTER_WIDTH - 1 downto 0);
        duty_0 : in std_logic_vector(COUNTER_WIDTH - 1 downto 0);
        duty_1 : in std_logic_vector(COUNTER_WIDTH - 1 downto 0);
        duty_2 : in std_logic_vector(COUNTER_WIDTH - 1 downto 0);
        duty_3 : in std_logic_vector(COUNTER_WIDTH - 1 downto 0);

        -- PWM outputs
        pwm_out : out std_logic_vector(NUM_CHANNELS - 1 downto 0)
    );
end entity pwm_generator;

architecture rtl of pwm_generator is

    signal counter : unsigned(COUNTER_WIDTH - 1 downto 0);

    type duty_array_t is array (0 to NUM_CHANNELS - 1) of unsigned(COUNTER_WIDTH - 1 downto 0);
    signal duty_cycles : duty_array_t;

begin

    -- Map duty cycle inputs to array
    duty_cycles(0) <= unsigned(duty_0);
    duty_cycles(1) <= unsigned(duty_1);
    duty_cycles(2) <= unsigned(duty_2);
    duty_cycles(3) <= unsigned(duty_3);

    -- Counter process
    process (clk, rst_n)
    begin
        if rst_n = '0' then
            counter <= (others => '0');
        elsif rising_edge(clk) then
            if counter >= unsigned(period) then
                counter <= (others => '0');
            else
                counter <= counter + 1;
            end if;
        end if;
    end process;

    -- PWM output generation
    gen_pwm : for i in 0 to NUM_CHANNELS - 1 generate
        process (clk, rst_n)
        begin
            if rst_n = '0' then
                pwm_out(i) <= '0';
            elsif rising_edge(clk) then
                if counter < duty_cycles(i) then
                    pwm_out(i) <= '1';
                else
                    pwm_out(i) <= '0';
                end if;
            end if;
        end process;
    end generate;

end architecture rtl;
