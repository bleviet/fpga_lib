library ieee;
use ieee.std_logic_1164.all;

entity neorv32_cpu_decompressor is
    port (
        instr_i : in std_ulogic_vector(15 downto 0);
        instr_o : out std_ulogic_vector(31 downto 0)
    );
end entity neorv32_cpu_decompressor;