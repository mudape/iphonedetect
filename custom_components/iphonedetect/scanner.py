"""iPhone Detect Scanner."""
from dataclasses import dataclass
import logging
import socket
from pyroute2 import IPRoute
import asyncio
from homeassistant.core import HomeAssistant
from datetime import datetime
from homeassistant.util import dt as dt_util
from .const import CONF_NUD_STATE

_LOGGER = logging.getLogger(__name__)

UDP_PORT = 5353
UDP_MSG = b"Steve Jobs"

async def async_ping_device(hass: HomeAssistant, ip: str) -> None:
    """Send UDP message to IP asynchronously."""
    def ping():
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.sendto(UDP_MSG, (ip, UDP_PORT))
    await hass.async_add_executor_job(ping)  # Run the blocking operation in the executor

class IphoneDetectScanner:
    """Helper class for getting NUD State."""

    @staticmethod
    async def probe_device(hass: HomeAssistant, ip: str, seen: datetime) -> datetime:
        """Ping device and return NUD state asynchronously."""
        now = dt_util.utcnow()

        await async_ping_device(hass, ip)  # Use the async version of ping

        # Use Home Assistant's async_add_executor_job to avoid blocking
        nud_state = await hass.async_add_executor_job(IphoneDetectScanner._get_nud_state, ip)

        if CONF_NUD_STATE[nud_state]["home"]:
            seen = now
        return seen

    @staticmethod
    def _get_nud_state(ip: str) -> int:
        """Retrieve the NUD state of an IP address."""
        try:
            with IPRoute() as ipr:
                nud = ipr.get_neighbours(dst=ip)[0].get("state", 32)
                return nud
        except IndexError:
            _LOGGER.warning(f"No NUD state found for IP: {ip}")
            return 32  # Return a default NUD state indicating not present

    @staticmethod
    async def get_mac_address(hass: HomeAssistant, ip: str) -> str:
        """Return MAC address asynchronously."""
        await async_ping_device(hass, ip)  # Ensure ping_device is called asynchronously

        mac_address = await hass.async_add_executor_job(IphoneDetectScanner._retrieve_mac_address, ip)
        return mac_address

    @staticmethod
    def _retrieve_mac_address(ip: str) -> str:
        """Retrieve the MAC address for a given IP."""
        try:
            with IPRoute() as ipr:
                probe = list(ipr.get_neighbours(dst=ip)[0]["attrs"])
                mac = next((v for k, v in probe if k == "NDA_LLADDR"), None)
                return mac
        except IndexError:
            _LOGGER.error(f"MAC address could not be retrieved for IP: {ip}")
            return None
