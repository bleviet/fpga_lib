# Definitional proc to organize widgets for parameters.
proc init_gui { IPINST } {
  ipgui::add_param $IPINST -name "Component_Name"
  ipgui::add_param $IPINST -name "NUM_LEDS"
  ipgui::add_param $IPINST -name "PWM_BITS"
  ipgui::add_param $IPINST -name "BLINK_COUNTER_WIDTH"

}

proc update_PARAM_VALUE.Component_Name { PARAM_VALUE.Component_Name } {
	# Procedure called to update Component_Name when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.Component_Name { PARAM_VALUE.Component_Name } {
	# Procedure called to validate Component_Name
	return true
}

proc update_PARAM_VALUE.NUM_LEDS { PARAM_VALUE.NUM_LEDS } {
	# Procedure called to update NUM_LEDS when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.NUM_LEDS { PARAM_VALUE.NUM_LEDS } {
	# Procedure called to validate NUM_LEDS
	return true
}
proc update_PARAM_VALUE.PWM_BITS { PARAM_VALUE.PWM_BITS } {
	# Procedure called to update PWM_BITS when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.PWM_BITS { PARAM_VALUE.PWM_BITS } {
	# Procedure called to validate PWM_BITS
	return true
}
proc update_PARAM_VALUE.BLINK_COUNTER_WIDTH { PARAM_VALUE.BLINK_COUNTER_WIDTH } {
	# Procedure called to update BLINK_COUNTER_WIDTH when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.BLINK_COUNTER_WIDTH { PARAM_VALUE.BLINK_COUNTER_WIDTH } {
	# Procedure called to validate BLINK_COUNTER_WIDTH
	return true
}

proc update_MODELPARAM_VALUE.Component_Name { MODELPARAM_VALUE.Component_Name PARAM_VALUE.Component_Name } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.Component_Name}] ${MODELPARAM_VALUE.Component_Name}
}

proc update_MODELPARAM_VALUE.NUM_LEDS { MODELPARAM_VALUE.NUM_LEDS PARAM_VALUE.NUM_LEDS } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.NUM_LEDS}] ${MODELPARAM_VALUE.NUM_LEDS}
}
proc update_MODELPARAM_VALUE.PWM_BITS { MODELPARAM_VALUE.PWM_BITS PARAM_VALUE.PWM_BITS } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.PWM_BITS}] ${MODELPARAM_VALUE.PWM_BITS}
}
proc update_MODELPARAM_VALUE.BLINK_COUNTER_WIDTH { MODELPARAM_VALUE.BLINK_COUNTER_WIDTH PARAM_VALUE.BLINK_COUNTER_WIDTH } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.BLINK_COUNTER_WIDTH}] ${MODELPARAM_VALUE.BLINK_COUNTER_WIDTH}
}
