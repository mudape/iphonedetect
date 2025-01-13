"""Device Tracker platform for iPhone Detect."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.device_tracker import SourceType
from homeassistant.components.device_tracker.config_entry import BaseTrackerEntity
from homeassistant.const import (
    EVENT_HOMEASSISTANT_STARTED,
    STATE_HOME,
    STATE_NOT_HOME,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import IphoneDetectUpdateCoordinator
from .helpers import _run_import

if TYPE_CHECKING:
    from homeassistant.components.device_tracker import AsyncSeeCallback
    from homeassistant.config_entries import ConfigEntry, DiscoveryInfoType
    from homeassistant.core import Event, HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
    from homeassistant.helpers.typing import ConfigType


async def async_setup_scanner(
    hass: HomeAssistant,
    config: ConfigType,
    async_see: AsyncSeeCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> bool:
    """Import configuration to the new integration."""

    async def schedule_import(_: Event) -> None:
        """Schedule delayed import after HA is fully started."""
        await _run_import(hass, config)

    # The legacy device tracker entities will be restored after the legacy device tracker platforms
    # have been set up, so we can only remove the entities from the state machine then
    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, schedule_import)

    return True


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Setup device tracker for iPhone Detect."""

    coordinator: IphoneDetectUpdateCoordinator = hass.data[DOMAIN]["coordinators"][entry.entry_id]

    async_add_entities([IphoneDetectDeviceTracker(entry, coordinator)])


class IphoneDetectDeviceTracker(CoordinatorEntity[IphoneDetectUpdateCoordinator], BaseTrackerEntity):
    """Representation of a tracked device."""

    _attr_source_type: SourceType = SourceType.ROUTER
    _attr_has_entity_name = True

    def __init__(self, entry: ConfigEntry, coordinator: IphoneDetectUpdateCoordinator) -> None:
        """Initialize the tracked device."""
        super().__init__(coordinator)

        self._attr_name = entry.title
        self._attr_unique_id = entry.entry_id

    @property
    def state(self) -> str:
        """Return the state of the device."""
        return STATE_HOME if self.coordinator.data.is_connected else STATE_NOT_HOME

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Return if entity is enabled by default."""
        return True
