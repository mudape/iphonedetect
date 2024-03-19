"""iPhone Detect Scanner."""
from contextlib import closing

import socket
import asyncio

from pyroute2 import IPRoute

from datetime import datetime
from homeassistant.util import dt as dt_util

from .const import CONF_NUD_STATE


UDP_PORT = 5353
UDP_MSG = b"Steve Jobs"

async def async_ping_device(ip: str) -> None:
    """Send UDP message to IP asynchronously."""
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, ping_device, ip)


def ping_device(ip: str) -> None:
    """Send UDP message to IP."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.sendto(UDP_MSG, (ip, UDP_PORT))


class IphoneDetectScanner:
    """Helper class for getting NUD State."""

    @staticmethod
    async def probe_device(ip: str, seen: datetime) -> datetime:
        """Ping device and return NUD state."""
        nud_fallback = 32

        await async_ping_device(ip)

        # Return the device state
        try:
            with closing(IPRoute()) as ipr:
                _nud = ipr.get_neighbours(dst=ip)[0].get("state", nud_fallback)
        except Exception:
            _nud = nud_fallback

        if CONF_NUD_STATE[_nud]["home"]:
            seen = dt_util.utcnow()

        return seen

    @staticmethod
    async def get_mac_address(ip: str) -> str:
        """Return MAC address."""
        await async_ping_device(ip)

        try:
            with closing(IPRoute()) as ipr:
                probe = list(ipr.get_neighbours(dst=ip)[0]["attrs"])
                mac = list(v for k, v in probe if k == "NDA_LLADDR")[0]
        except Exception:
            mac = None

        return mac
