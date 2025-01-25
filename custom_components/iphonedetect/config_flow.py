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
)
from homeassistant.const import (
    CONF_IP_ADDRESS,
    CONF_NAME,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.schema_config_entry_flow import (
    SchemaFlowFormStep,
    SchemaOptionsFlowHandler,
)
from homeassistant.util import slugify

from .const import (
    DEFAULT_CONSIDER_HOME,
    DOMAIN,
)


_LOGGER = logging.getLogger(__name__)


OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CONSIDER_HOME, default=DEFAULT_CONSIDER_HOME): int
    }
)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME, description={"suggested_value": "My iPhone"}): str,
        vol.Required(CONF_IP_ADDRESS, description={"suggested_value": "192.168.1.xx"}): str,
        **OPTIONS_SCHEMA.schema,
        vol.Optional("subnet_check", default=True): bool,
    }
)

OPTIONS_FLOW = {
    "init": SchemaFlowFormStep(OPTIONS_SCHEMA),
}


async def async_get_networks(hass: HomeAssistant) -> list[IPv4Network]:
    """Search adapters for the networks."""
    networks = []
    local_ip = await network.async_get_source_ip(hass, MDNS_TARGET_IP)

    for adapter in await network.async_get_adapters(hass):
        for ipv4 in adapter["ipv4"]:
            if ipv4["address"] == local_ip or ipv4["address"] is not None:
                network_prefix = ipv4["network_prefix"]
                networks.append(ip_interface(f"{ipv4['address']}/{network_prefix}").network)

    return networks


async def _validate_input(hass: HomeAssistant, user_input: dict[str, Any]) -> dict[str, str] | None:
    """Try to validate user input"""
    entries = [entry for entry in hass.config_entries.async_entries(DOMAIN)]
    ip = user_input[CONF_IP_ADDRESS]

    # Check if name already used for a clearer error
    if user_input.get(CONF_NAME, False):
        entries_id = [entry.unique_id for entry in entries]
        entry_id = f"{DOMAIN}_{slugify(user_input[CONF_NAME]).lower()}"
        if entry_id in entries_id:
            return {"base": "name_not_unique"}

    # Check if valid IP address
    try:
        IPv4Address(ip)
    except AddressValueError:
        return {"base": "ip_invalid"}

    # Check if IP address already used for a clearer error
    entries_ip = [entry.options[CONF_IP_ADDRESS] for entry in entries]
    if ip in entries_ip:
        return {"base": "ip_already_configured"}

    # Check if device IP will be seen by ARP
    if user_input["subnet_check"]:
        subnets = await async_get_networks(hass)
        if not any(IPv4Address(ip) in subnet for subnet in subnets):
            return {"base": "ip_range"}


class IphoneDetectFlowHandler(ConfigFlow, domain=DOMAIN):  # type: ignore
    """Handle a config flow."""

    VERSION = 2

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> SchemaOptionsFlowHandler:
        return SchemaOptionsFlowHandler(config_entry, OPTIONS_FLOW)

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle a flow initialized by the user."""
        errors = {}

        if user_input is not None:
            errors = await _validate_input(self.hass, user_input)

            if not errors:
                unique_id = slugify(user_input[CONF_NAME]).lower()
                await self.async_set_unique_id(f"{DOMAIN}_{unique_id}")
                self._abort_if_unique_id_configured()

                self._async_abort_entries_match({CONF_NAME: user_input[CONF_NAME]})

                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data={},
                    options={
                        CONF_IP_ADDRESS: user_input[CONF_IP_ADDRESS],
                        CONF_CONSIDER_HOME: user_input[CONF_CONSIDER_HOME],
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(DATA_SCHEMA, user_input),
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

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle options flow."""
        errors = {}
        entry = self._get_reconfigure_entry()

        if user_input is not None:
            errors = await _validate_input(self.hass, user_input)
            if not errors:
                await self.async_set_unique_id(entry.unique_id)
                self._abort_if_unique_id_mismatch()
                new_options = entry.options | {CONF_IP_ADDRESS: user_input[CONF_IP_ADDRESS]}

                return self.async_update_reload_and_abort(
                    entry,
                    options=new_options,
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema({vol.Required(CONF_IP_ADDRESS, default=entry.options[CONF_IP_ADDRESS]): str, vol.Optional("subnet_check", default=True): bool}),
            description_placeholders={"device_name": entry.title},
            errors=errors,
        )
