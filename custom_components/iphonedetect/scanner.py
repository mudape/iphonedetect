"""iPhone Detect Scanner."""

import asyncio
import logging
import socket
from contextlib import closing, suppress

from homeassistant.core import HomeAssistant

from pyroute2 import IPRoute

from .const import (
    CONF_PROBE_ARP, 
    CONF_PROBE_IP_NEIGH, 
    CONF_PROBE_IPROUTE,
)

_LOGGER = logging.getLogger(__name__)

UDP_PORT = 5353
UDP_MSG = b"Steve Jobs"

NUD_FALLBACK = 32
NUD_STATES = {
    0: {"state": "None", "consider_home": False},
    1: {"state": "Incomplete", "consider_home": False},
    2: {"state": "Reachable", "consider_home": True},
    4: {"state": "Stale", "consider_home": True},
    8: {"state": "Delay", "consider_home": True},
    16: {"state": "Probe", "consider_home": False},
    32: {"state": "Failed", "consider_home": False},
    64: {"state": "Noarp", "consider_home": False},
    128: {"state": "Permanent", "consider_home": True},
}


async def _select_probe() -> str|None:
    """Checks and returns which probe that can be used."""
    try:
        with closing(IPRoute()):
            ...
        _LOGGER.debug("Using IPRoute as probe")
        return CONF_PROBE_IPROUTE
    except Exception:
        _LOGGER.debug("Could not use IPRoute. Trying with IP Neigh")
        try:
            prober = await asyncio.create_subprocess_exec(
                *["which","ip"],
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                close_fds=False,
            )
            await prober.wait()
            if prober.returncode == 0:
                _LOGGER.debug("Using IP Neigh as probe")
                return CONF_PROBE_IP_NEIGH
            else:
                _LOGGER.debug("Could not use IP Neigh. Trying with ARP")
                prober = await asyncio.create_subprocess_exec(
                    *["which", "arp"],
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    close_fds=False,
                )
                await prober.wait()
                if prober.returncode == 0:
                    _LOGGER.debug("Using ARP as probe")
                    return CONF_PROBE_ARP
                else:
                    _LOGGER.fatal("Can't find a tool to use for probing devices.")
                    raise Exception
        except Exception:
            return None


async def async_message_device(hass: HomeAssistant, ip: str) -> None:
    """Send UDP message to IP asynchronously."""
    _LOGGER.debug(f"Sending 'ping' to {ip!r}")

    def send_msg():
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.sendto(UDP_MSG, (ip, UDP_PORT))

    await hass.async_add_executor_job(
        send_msg
    )


class ProbeData:
    is_alive: bool = False

    def __init__(self, hass: HomeAssistant, ip: str) -> None:
        self.hass = hass
        self.ip_address = ip


class ProbeSubprocess(ProbeData):
    """Helper class for getting ARP State."""

    def __init__(self, hass: HomeAssistant, ip: str, cmd: str|None) -> None:
        """Init."""
        super().__init__(hass, ip)
        if cmd == CONF_PROBE_IP_NEIGH:
            self.cmd = ["ip", "-4", "neigh", "show", "nud", "reachable", "nud", "delay"]
        elif cmd == CONF_PROBE_ARP:
            self.cmd = ["arp", "-na"]

    async def _get_state(self) -> bool:
        """Queries the network neighbours and lists found IP's"""
        prober = await asyncio.create_subprocess_exec(
            *self.cmd,
            self.ip_address,
            stdin=None,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            close_fds=False,
        )
        try:
            async with asyncio.timeout(2):
                out_data, out_error = await prober.communicate()
            
            if out_data: 
                _LOGGER.debug(f"Got {out_data!r}")
                return self.ip_address in str(out_data) and str(out_data).count(":") == 5
            if out_error:
                _LOGGER.debug(
                    "Error of command: `%s`, return code: %s:\n%s",
                    " ".join(self.cmd),
                    prober.returncode,
                    out_error,
                )
        except TimeoutError:
            _LOGGER.debug(f"Timeout waiting for {self.cmd}")
            if prober:
                with suppress(TypeError):
                    await prober.kill()  # type: ignore[func-returns-value]
                del prober
            return False
        except AttributeError:
            return False
        
        return False

    async def async_update(self) -> None:
        """Retrieve the latest status from the host."""
        await async_message_device(self.hass, self.ip_address)
        self.is_alive = await self._get_state()
        _LOGGER.debug(f"{self.ip_address!r} is considered home : {self.is_alive}")



class ProbeNud(ProbeData):
    """Helper class for getting NUD State."""

    def __init__(self, hass: HomeAssistant, ip: str, cmd: str|None = None) -> None:
        """Init."""
        super().__init__(hass, ip)

    async def _get_state(self) -> bool:
        """Retrieve the NUD state of an IP address."""
        _LOGGER.debug(f"Getting 'nud_state' for {self.ip_address!r}")
        try:
            with closing(IPRoute()) as ipr:
                nud_state = ipr.get_neighbours(dst=self.ip_address)[0].get(
                    "state", NUD_FALLBACK
                )
        except IndexError:
            _LOGGER.warning(f"No NUD state found for IP: {self.ip_address!r}")
            nud_state = NUD_FALLBACK

        _LOGGER.debug(
            f"Got 'nud_state' {NUD_STATES[nud_state]!r} for {self.ip_address!r}"
        )
        return NUD_STATES[nud_state]["consider_home"]

    async def async_update(self) -> None:
        """Retrieve the latest status from the host."""
        await async_message_device(self.hass, self.ip_address)
        self.is_alive = await self._get_state()
        _LOGGER.debug(f"{self.ip_address!r} is considered home : {self.is_alive}")



