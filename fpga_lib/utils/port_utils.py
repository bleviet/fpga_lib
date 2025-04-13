# fpga_lib/utils/port_utils.py
from typing import List, Dict, Any
from enum import Enum

class PortDirection(str, Enum):
    """
    Enum for port directions.
    """

    IN = "in"
    OUT = "out"


def invert_port_direction(ports: List[Dict[str, Any]]):
    """
    Inverts the direction of all ports in a list of port dictionaries.

    Args:
        ports: A list of port dictionaries.
    """
    for port in ports:
        if port["direction"] == PortDirection.IN:
            port["direction"] = PortDirection.OUT
        elif port["direction"] == PortDirection.OUT:
            port["direction"] = PortDirection.IN