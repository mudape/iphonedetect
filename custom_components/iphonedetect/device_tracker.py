"""Device Tracker platform for iPhone Detect."""
from typing import Optional
from datetime import timedelta

from homeassistant.components.device_tracker import SOURCE_TYPE_ROUTER
from homeassistant.components.device_tracker.config_entry import ScannerEntity
from homeassistant.components.device_tracker.const import (
    CONF_CONSIDER_HOME,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_IP_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import DOMAIN, DEFAULT_SCAN_INTERVAL
from .scanner import IphoneDetectScanner

from homeassistant.helpers.typing import ConfigType

SCAN_INTERVAL = timedelta(seconds=DEFAULT_SCAN_INTERVAL)


async def async_setup_scanner(
    hass: HomeAssistant,
    config: ConfigType,
    async_see,
    discovery_info=None,
) -> bool:
    """For the legacy tracker, if configuration.yaml still being used."""
    return True


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Setup device tracker for iPhone Detect."""

    async_add_entities([IphoneDetectScannerEntity(entry)], update_before_add=True)


class IphoneDetectScannerEntity(ScannerEntity):
    """Representation of a tracked device."""

    def __init__(self, entry: ConfigEntry) -> None:
        """Init."""
        self._mac_address: str = entry.data[CONNECTION_NETWORK_MAC]
        self._ip_address: str = entry.data[CONF_IP_ADDRESS]
        self._name: str = entry.title
        self._unique_id: str = entry.entry_id

        self._is_connected: Optional[bool] = None

        self.last_seen: timedelta = dt_util.utcnow() - timedelta(days=365)
        self._consider_home_time: int = entry.options[CONF_CONSIDER_HOME]

    async def async_update(self):
        """Update data."""

        now = dt_util.utcnow()
        self.last_seen = await IphoneDetectScanner.probe_device(
            self.ip_address, self.last_seen
        )
        self._last_home = int((now - self.last_seen).total_seconds())
        self._is_connected = self._last_home <= self._consider_home_time

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name

    @property
    def mac_address(self) -> str:
        """Return MAC address for this entity."""
        return self._mac_address

    @property
    def unique_id(self) -> str:
        """Return a unique id to use for this entity."""
        return self._unique_id

    @property
    def ip_address(self) -> str:
        """Return IP address of entity."""
        return self._ip_address

    @property
    def icon(self):
        """Return the default icon for the entity."""
        if self.is_connected:
            return "mdi:access-point-network"
        return "mdi:access-point-network-off"

    @property
    def source_type(self) -> str:
        """Return the source type."""
        return SOURCE_TYPE_ROUTER

    @property
    def is_connected(self) -> bool:
        """Return if entity is considered connected to the network."""
        return self._is_connected

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {
            CONF_CONSIDER_HOME: self._consider_home_time,
        }

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this entity."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.unique_id)},
            name=self.name,
            connections={
                (CONNECTION_NETWORK_MAC, self.mac_address),
            },
        )
