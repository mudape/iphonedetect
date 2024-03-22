import logging
from datetime import timedelta
from typing import Any

from homeassistant.components.device_tracker import (
    CONF_CONSIDER_HOME,
    DEFAULT_CONSIDER_HOME as DEVICE_TRACKER_DEFAULT_HOME
)
from homeassistant.components.device_tracker.legacy import (
    YAML_DEVICES,
    remove_device_from_config,
)
from homeassistant.config import load_yaml_config_file
from homeassistant.config_entries import SOURCE_IMPORT
from homeassistant.const import (
    CONF_HOSTS,
    CONF_IP_ADDRESS,
    CONF_NAME,
    CONF_SOURCE,
)
from homeassistant.core import DOMAIN as HOMEASSISTANT_DOMAIN
from homeassistant.core import Event, HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.issue_registry import IssueSeverity, async_create_issue
from homeassistant.helpers.typing import ConfigType


from .const import (
    DEFAULT_CONSIDER_HOME,
    DOMAIN,
    MAX_CONSIDER_HOME,
    MIN_CONSIDER_HOME,
    NAME,
)

_LOGGER = logging.getLogger(__name__)


async def _run_import(_: Event, hass: HomeAssistant, config: ConfigType) -> None:
    """Delete devices from known_device.yaml and import them via config flow."""
    _LOGGER.debug("Home Assistant successfully started, importing config entries now")

    devices: dict[str, dict[str, Any]] = {}
    try:
        devices = await hass.async_add_executor_job(
            load_yaml_config_file, hass.config.path(YAML_DEVICES)
        )
    except (FileNotFoundError, HomeAssistantError):
        _LOGGER.debug(
            "No valid known_devices.yaml found, "
            "skip removal of devices from known_devices.yaml"
        )
        return None

    for dev_name, dev_host in config[CONF_HOSTS].items():
        if dev_name in devices:
            await hass.async_add_executor_job(remove_device_from_config, hass, dev_name)
            _LOGGER.debug("Removed device %s from known_devices.yaml", dev_name)

            if not hass.states.async_available(f"device_tracker.{dev_name}"):
                _LOGGER.debug("Removed device %s ", dev_name)
                hass.states.async_remove(f"device_tracker.{dev_name}")

        # Check if custom consider_home has been set
        con_home = config.get(CONF_CONSIDER_HOME, DEFAULT_CONSIDER_HOME)
        if con_home == DEVICE_TRACKER_DEFAULT_HOME:
            # HA sends its default if not entered in configuration
            con_home = DEFAULT_CONSIDER_HOME
        if isinstance(con_home, timedelta):
            con_home = con_home.seconds
        if con_home < MIN_CONSIDER_HOME:
            con_home = MIN_CONSIDER_HOME
        elif con_home > MAX_CONSIDER_HOME:
            con_home = MAX_CONSIDER_HOME

        # run import after everything has been cleaned up
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN,
                context={CONF_SOURCE: SOURCE_IMPORT},
                data={
                    CONF_NAME: dev_name,
                    CONF_IP_ADDRESS: dev_host,
                    CONF_CONSIDER_HOME: con_home,
                },
            )
        )

        async_create_issue(
            hass,
            HOMEASSISTANT_DOMAIN,
            f"deprecated_yaml_{DOMAIN}",
            # breaks_in_ha_version="2024.6.0",
            is_fixable=False,
            issue_domain=DOMAIN,
            severity=IssueSeverity.WARNING,
            translation_key="deprecated_yaml",
            translation_placeholders={
                "domain": DOMAIN,
                "integration_title": NAME,
            },
        )
