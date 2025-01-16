"""DataUpdateCoordinator for the integration."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import UPDATE_INTERVAL

if TYPE_CHECKING:
    from .scanner import DeviceData

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class DeviceConnected:
    """Return class for coordinator result."""

    is_connected: bool | None = None


class IphoneDetectUpdateCoordinator(DataUpdateCoordinator[DeviceConnected]):
    """The update coordinator."""

    def __init__(self, hass: HomeAssistant, device: DeviceData) -> None:
        """Initialize the coordinator."""
        self.device = device

        super().__init__(
            hass,
            _LOGGER,
            name=self.device.title,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )

    def is_connected(self) -> bool:
        """Return if device is considered connected."""

        if self.device._reachable:
            _LOGGER.debug("Device '%s' (%s) is home", self.device.title, self.device.ip_address)
            return True

        if self.device._last_seen is not None:
            _last_seen: timedelta = dt_util.utcnow() - self.device._last_seen
            if _last_seen < self.device.consider_home:
                _LOGGER.debug(
                    "Device '%s' (%s) considered home, seen: %ss ago",
                    self.device.title,
                    self.device.ip_address,
                    round(_last_seen.total_seconds(), 2),
                )
                return True
            else:
                _LOGGER.debug(
                    "Device '%s' (%s) is not home",
                    self.device.title,
                    self.device.ip_address,
                )
                return False
        else:
            _LOGGER.debug(
                "Device '%s' (%s) not seen since last restart.",
                self.device.title,
                self.device.ip_address,
            )
            return False

    async def _async_update_data(self) -> DeviceConnected:
        """Trigger check."""
        return DeviceConnected(is_connected=self.is_connected())
