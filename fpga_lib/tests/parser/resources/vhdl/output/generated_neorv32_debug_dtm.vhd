library ieee;
use ieee.std_logic_1164.all;

entity neorv32_debug_dtm is
    generic (
        IDCODE_VERSION : std_ulogic_vector(3 downto 0);
        IDCODE_PARTID : std_ulogic_vector(15 downto 0);
        IDCODE_MANID : std_ulogic_vector(10 downto 0)
    );
    port (
        clk_i : in std_ulogic;
        rstn_i : in std_ulogic;
        jtag_tck_i : in std_ulogic;
        jtag_tdi_i : in std_ulogic;
        jtag_tdo_o : out std_ulogic;
        jtag_tms_i : in std_ulogic;
        dmi_req_o : out dmi_req_t;
        dmi_rsp_i : in dmi_rsp_t
    );
end entity neorv32_debug_dtm;