"""DataUpdateCoordinator for the integration."""

from dataclasses import dataclass
from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .scanner import ProbeNud, ProbeSubprocess

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=12)


@dataclass(slots=True, frozen=True)
class ProbeResult:
    """Dataclass returned by the coordinator."""

    is_alive: bool


class IphoneDetectUpdateCoordinator(DataUpdateCoordinator[ProbeResult]):
    """The update coordinator."""

    def __init__(self, hass: HomeAssistant, probe: ProbeNud | ProbeSubprocess) -> None:
        """Initialize the coordinator."""
        self.probe = probe

        super().__init__(
            hass,
            _LOGGER,
            name=probe.ip_address,
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self) -> ProbeResult:
        """Trigger check."""
        await self.probe.async_update()
        return ProbeResult(is_alive=self.probe.is_alive)
