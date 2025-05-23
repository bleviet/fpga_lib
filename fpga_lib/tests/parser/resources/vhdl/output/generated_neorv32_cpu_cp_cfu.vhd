library ieee;
use ieee.std_logic_1164.all;

entity neorv32_cpu_cp_cfu is
    port (
        clk_i : in std_ulogic;
        rstn_i : in std_ulogic;
        start_i : in std_ulogic;
        active_i : in std_ulogic;
        csr_we_i : in std_ulogic;
        csr_addr_i : in std_ulogic_vector(1 downto 0);
        csr_wdata_i : in std_ulogic_vector(31 downto 0);
        csr_rdata_o : out std_ulogic_vector(31 downto 0);
        rtype_i : in std_ulogic;
        funct3_i : in std_ulogic_vector(2 downto 0);
        funct7_i : in std_ulogic_vector(6 downto 0);
        rs1_i : in std_ulogic_vector(31 downto 0);
        rs2_i : in std_ulogic_vector(31 downto 0);
        rs3_i : in std_ulogic_vector(31 downto 0);
        result_o : out std_ulogic_vector(31 downto 0);
        valid_o : out std_ulogic
    );
end entity neorv32_cpu_cp_cfu;