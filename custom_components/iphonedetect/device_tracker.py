"""Device Tracker platform for iPhone Detect."""

from datetime import datetime, timedelta

from homeassistant.components.device_tracker import (
    CONF_CONSIDER_HOME,
    ScannerEntity,
    SourceType,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_IP_ADDRESS, EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import Event, HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .coordinator import IphoneDetectUpdateCoordinator
from .helpers import _run_import


async def async_setup_scanner(
    hass: HomeAssistant,
    config: ConfigType,
    async_see,
    discovery_info=None,
) -> bool:
    """For the legacy tracker, if configuration.yaml still being used."""

    # Helper for hopefully cleaner import (from Ping integration)
    hass.bus.async_listen_once(
        EVENT_HOMEASSISTANT_STARTED, _run_import(Event, hass, config)
    )

    return True


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Setup device tracker for iPhone Detect."""
    coordinator = hass.data[DOMAIN].coordinators[entry.entry_id]
    async_add_entities(
        [IphoneDetectDeviceTracker(entry, coordinator)]
    )


class IphoneDetectDeviceTracker(
    CoordinatorEntity[IphoneDetectUpdateCoordinator], ScannerEntity
):
    """Representation of a tracked device."""
    
    _last_seen: datetime | None = None

    def __init__(
        self, config_entry: ConfigEntry, coordinator: IphoneDetectUpdateCoordinator
    ) -> None:
        """Init."""
        super().__init__(coordinator)

        self._attr_name = config_entry.title
        self._ip_address = config_entry.options[CONF_IP_ADDRESS]
        self._unique_id = config_entry.entry_id
        self._consider_home_interval = timedelta(
            seconds=config_entry.options[CONF_CONSIDER_HOME]
        )

    @property
    def unique_id(self) -> str:
        """Return a unique id to use for this entity."""
        return self._unique_id

    @property
    def ip_address(self) -> str:
        """Return IP address of entity."""
        return self._ip_address
        # return self.coordinator.data.ip_address

    @property
    def source_type(self) -> str:
        """Return the source type."""
        return SourceType.ROUTER

    @property
    def is_connected(self) -> bool:
        """Return if entity is considered connected to the network."""
        if self.coordinator.data.is_alive:
            self._last_seen = dt_util.utcnow()

        return (
            self._last_seen is not None
            and (dt_util.utcnow() - self._last_seen) < self._consider_home_interval
        )

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Return if entity is enabled by default."""
        return True
