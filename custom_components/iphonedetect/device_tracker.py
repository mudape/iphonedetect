"""Device Tracker platform for iPhone Detect."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.device_tracker import BaseScannerEntity, SourceType
from homeassistant.const import (
    STATE_HOME,
    STATE_NOT_HOME,
)
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import IphoneDetectUpdateCoordinator

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Setup device tracker for iPhone Detect."""

    coordinator: IphoneDetectUpdateCoordinator = hass.data[DOMAIN]["coordinators"][entry.entry_id]

    async_add_entities([IphoneDetectDeviceTracker(entry, coordinator)])


class IphoneDetectDeviceTracker(CoordinatorEntity[IphoneDetectUpdateCoordinator], BaseScannerEntity, RestoreEntity):
    """Representation of a tracked device."""

    _attr_source_type: SourceType = SourceType.ROUTER
    _attr_has_entity_name = True

    def __init__(self, entry: ConfigEntry, coordinator: IphoneDetectUpdateCoordinator) -> None:
        """Initialize the tracked device."""
        super().__init__(coordinator)

        self._attr_name = entry.title
        self._attr_unique_id = entry.entry_id
        self._restored_state: bool | None = None

    async def async_added_to_hass(self):
        """Handle entity which will be added to Home Assistant."""
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        if state and state.state in (STATE_HOME, STATE_NOT_HOME):
            self._restored_state = state.state == STATE_HOME
            _LOGGER.debug(
                "Added '%s' to hass with restored state: %s",
                self._attr_name,
                state.state,
            )
        else:
            self._restored_state = None
            _LOGGER.debug(
                "Added '%s' to hass with no usable restored state",
                self._attr_name,
            )

    @property
    def is_connected(self) -> bool | None:
        """Return the connection state of the device."""
        current_state = self.coordinator.data.is_connected
        return current_state if current_state is not None else self._restored_state

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Return if entity is enabled by default."""
        return True
