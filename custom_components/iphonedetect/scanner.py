"""iPhone Detect Scanner."""

from __future__ import annotations

import asyncio
import logging
import socket
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Protocol, Sequence

from homeassistant.util import dt as dt_util
from pyroute2 import IPRoute

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

CMD_IP_NEIGH = "ip -4 neigh show nud reachable"
CMD_ARP = "arp -ne"


@dataclass(slots=True, kw_only=True)
class DeviceData:
    ip_address: str
    consider_home: timedelta
    title: str
    _reachable: bool = False
    _last_seen: datetime | None = None


async def pinger(loop: asyncio.AbstractEventLoop, ip_addresses: list[str]) -> None:
    transport, _ = await loop.create_datagram_endpoint(lambda: asyncio.DatagramProtocol(), family=socket.AF_INET)
    for ip_address in ip_addresses:
        try:
            transport.sendto(b"ping", (ip_address, 5353))
        except Exception as e:
            _LOGGER.error(f"Failed to ping {ip_address}", e)

    transport.close()


async def get_arp_subprocess(cmd: Sequence) -> list[str]:
    """Return list of IPv4 devices reachable by the network."""
    response = []
    if isinstance(cmd, str):
        cmd = cmd.split()

    try:
        proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, close_fds=False)

        async with asyncio.timeout(2):
            result, _ = await proc.communicate()
        if result:
            response = result.decode().splitlines()
    except Exception as exc:
        _LOGGER.debug("Exception on ARP lookup: %s", exc)

    return response


class ScannerException(Exception):
    """Scanner exception."""


class Scanner(Protocol):
    """Scanner class for getting ARP cache records."""

    async def get_arp_records(self, hass: HomeAssistant) -> list[str]:
        """Return list of IPv4 devices reachable by the network."""
        return []


class ScannerIPRoute:
    """Get ARP cache records using pyroute2."""

    def _get_arp_records(self) -> list[str]:
        """Return list of IPv4 devices reachable by the network."""
        response = []
        try:
            with closing(IPRoute()) as ipr:
                result = ipr.get_neighbours(family=socket.AF_INET, match=lambda x: x["state"] == 2)
            response = [dev["attrs"][0][1] for dev in result]
        except Exception as exc:
            _LOGGER.debug("Exception on ARP lookup: %s", exc)

        return response

    async def get_arp_records(self, hass: HomeAssistant) -> list[str]:
        """Return list of IPv4 devices reachable by the network."""
        response = await hass.async_add_executor_job(self._get_arp_records)
        return response


class ScannerIPNeigh:
    """Get ARP cache records using subprocess."""

    async def get_arp_records(self, hass: HomeAssistant = None) -> list[str]:
        """Return list of IPv4 devices reachable by the network."""
        response = []
        result = await get_arp_subprocess(CMD_IP_NEIGH.split())
        if result:
            response = [row.split()[0] for row in result if row.count(":") == 5]

        return response


class ScannerArp:
    """Get ARP cache records using subprocess."""

    async def get_arp_records(self, hass: HomeAssistant = None) -> list[str]:
        """Return list of IPv4 devices reachable by the network."""
        response = []
        result = await get_arp_subprocess(CMD_ARP.split())
        if result:
            response = [row.split()[0] for row in result if row.count(":") == 5]

        return response


async def async_update_devices(hass: HomeAssistant, scanner: Scanner, devices: dict[str, DeviceData]) -> None:
    """Update reachability for all tracked devices."""
    ip_addresses = [device.ip_address for device in devices.values()]

    # Ping devices
    _LOGGER.debug("Pinging devices: %s", ip_addresses)
    await pinger(hass.loop, ip_addresses)

    # Get devices found in ARP
    _LOGGER.debug("Fetching ARP records with %s", scanner.__class__.__name__)
    arp_records = await scanner.get_arp_records(hass)
    _LOGGER.debug("ARP response has %d records", len(arp_records))

    # Only keep reachable tracked devices
    reachable_ip = set(ip_addresses).intersection(arp_records)
    _LOGGER.debug("Matched %d tracked devices: %s", len(reachable_ip), reachable_ip)

    # Update reachable devices
    for device in devices.values():
        device._reachable = device.ip_address in reachable_ip
        if device._reachable:
            device._last_seen = dt_util.utcnow()


async def async_get_scanner(hass: HomeAssistant) -> Scanner:
    """Return Scanner to use."""

    if await ScannerIPRoute().get_arp_records(hass):
        return ScannerIPRoute()

    if await ScannerIPNeigh().get_arp_records():
        return ScannerIPNeigh()

    if await ScannerArp().get_arp_records():
        return ScannerArp()

    raise ScannerException("No scanner tool available")
