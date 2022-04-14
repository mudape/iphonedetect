"""iPhone Detect Scanner."""
from dataclasses import dataclass
import socket
from pyroute2 import IPRoute

from datetime import datetime
from homeassistant.util import dt as dt_util

from .const import CONF_NUD_STATE


UDP_PORT = 5353
UDP_MSG = b"Steve Jobs"


def ping_device(ip: str) -> None:
    """Send UDP message to IP."""
    socket.socket(socket.AF_INET, socket.SOCK_DGRAM).sendto(UDP_MSG, (ip, UDP_PORT))


class IphoneDetectScanner:
    """Helper class for getting NUD State."""

    @staticmethod
    async def probe_device(ip: str, seen: datetime) -> datetime:
        """Ping device and return NUD state."""
        now = dt_util.utcnow()

        ping_device(ip)

        # Return the device state
        _nud = IPRoute().get_neighbours(dst=ip)[0].get("state", 32)

        if CONF_NUD_STATE[_nud]["home"]:
            seen = now

        return seen

    @staticmethod
    async def get_mac_address(ip: str) -> str:
        """Return MAC address."""
        ping_device(ip)

        try:
            probe = list(IPRoute().get_neighbours(dst=ip)[0]["attrs"])
            mac = list(v for k, v in probe if k == "NDA_LLADDR")[0]
        except IndexError:
            mac = None

        return mac
