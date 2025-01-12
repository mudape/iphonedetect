"""Config flow for iPhone Device Tracker integration."""

import logging
from ipaddress import AddressValueError, IPv4Address, IPv4Network, ip_interface
from typing import Any

import voluptuous as vol
from homeassistant.components import network
from homeassistant.components.device_tracker.const import (
    CONF_CONSIDER_HOME,
)
from homeassistant.components.network.const import MDNS_TARGET_IP
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    FlowResult,
    OptionsFlow,
)
from homeassistant.const import (
    CONF_IP_ADDRESS,
    CONF_NAME,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.util import slugify

from .const import (
    DEFAULT_CONSIDER_HOME,
    DOMAIN,
    MAX_CONSIDER_HOME,
    MIN_CONSIDER_HOME,
)

_LOGGER = logging.getLogger(__name__)


async def validate_ip_address(
    subnets: list[IPv4Network], devices: list, ip: str
) -> dict:
    """Try to validate user input"""
    errors = {}

    if ip in devices:
        errors["base"] = "ip_already_configured"

    if not errors:
        try:
            ip_address = IPv4Address(ip)
        except AddressValueError:
            errors["base"] = "ip_invalid"
            return errors

    if not errors:
        if not any(ip_address in subnet for subnet in subnets):
            errors["base"] = "ip_range"

    return errors


async def async_get_networks(hass: HomeAssistant) -> list[IPv4Network]:
    """Search adapters for the networks."""
    networks = []
    local_ip = await network.async_get_source_ip(hass, MDNS_TARGET_IP)

    for adapter in await network.async_get_adapters(hass):
        for ipv4 in adapter["ipv4"]:
            if ipv4["address"] == local_ip or ipv4["address"] is not None:
                network_prefix = ipv4["network_prefix"]
                networks.append(
                    ip_interface(f"{ipv4['address']}/{network_prefix}").network
                )

    return networks


class IphoneDetectOptionsFlowHandler(OptionsFlow):
    """iPhone Detect config flow options handler."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        return await self.async_step_user(user_input)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle options flow."""
        errors = {}

        if (user_input is not None and user_input[CONF_CONSIDER_HOME] != self.config_entry.options[CONF_CONSIDER_HOME]):
            new_options = self.config_entry.options | {
                CONF_CONSIDER_HOME: user_input[CONF_CONSIDER_HOME]
            }
            return self.async_create_entry(title="", data=new_options)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_CONSIDER_HOME,
                        default=self.config_entry.options[CONF_CONSIDER_HOME],
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_CONSIDER_HOME, max=MAX_CONSIDER_HOME),
                    ),
                }
            ),
            errors=errors,
        )


class IphoneDetectFlowHandler(ConfigFlow, domain=DOMAIN):  # type: ignore
    """Handle a config flow."""

    VERSION = 2

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initialized by the user."""
        errors = {}

        if user_input is not None:
            ip = user_input[CONF_IP_ADDRESS]
            devices = [
                dev.options[CONF_IP_ADDRESS]
                for dev in self.hass.config_entries.async_entries(DOMAIN)
            ]
            subnet = await async_get_networks(self.hass)

            errors = await validate_ip_address(subnet, devices, ip)

            if not errors:
                unique_id = slugify(user_input[CONF_NAME]).lower()
                await self.async_set_unique_id(f"{DOMAIN}_{unique_id}")
                self._abort_if_unique_id_configured()

                self._async_abort_entries_match({CONF_NAME: user_input[CONF_NAME]})
                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data={},
                    options={
                        CONF_IP_ADDRESS: ip,
                        CONF_CONSIDER_HOME: user_input[CONF_CONSIDER_HOME],
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_NAME, description={"suggested_value": "My iPhone"}
                    ): str,
                    vol.Required(
                        CONF_IP_ADDRESS, description={"suggested_value": "192.168.1.xx"}
                    ): str,
                    vol.Required(
                        CONF_CONSIDER_HOME, default=DEFAULT_CONSIDER_HOME
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_CONSIDER_HOME, max=MAX_CONSIDER_HOME),
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_import(self, import_config) -> FlowResult:
        """Import from config."""
        _LOGGER.debug("Importing config '%s'", import_config)

        unique_id = slugify(import_config[CONF_NAME]).lower()
        await self.async_set_unique_id(f"{DOMAIN}_{unique_id}")
        self._abort_if_unique_id_configured()

        self._async_abort_entries_match({CONF_NAME: import_config[CONF_NAME]})

        return self.async_create_entry(
            title=import_config[CONF_NAME],
            data={},
            options={
                CONF_IP_ADDRESS: import_config[CONF_IP_ADDRESS],
                CONF_CONSIDER_HOME: import_config[CONF_CONSIDER_HOME],
            },
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle options flow."""
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        assert entry

        errors = {}
        if user_input is not None:
            new_ip = user_input.get(CONF_IP_ADDRESS)
            current_ip = entry.options[CONF_IP_ADDRESS]

            if new_ip and new_ip != current_ip:
                devices = [
                    other_entry.options[CONF_IP_ADDRESS]
                    for other_entry in self.hass.config_entries.async_entries(DOMAIN)
                    if other_entry.entry_id != entry.entry_id
                ]
                subnets = await async_get_networks(self.hass)

                errors = await validate_ip_address(subnets, devices, new_ip)

                if not errors:
                    new_options = entry.options | {
                        CONF_IP_ADDRESS: new_ip,
                    }
                    return self.async_update_reload_and_abort(
                        entry, options=new_options, reason="reconfigure_successful"
                    )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_IP_ADDRESS, default=entry.options[CONF_IP_ADDRESS]
                    ): str,
                }
            ),
            description_placeholders={"device_name": entry.title},
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> IphoneDetectOptionsFlowHandler:
        return IphoneDetectOptionsFlowHandler()
