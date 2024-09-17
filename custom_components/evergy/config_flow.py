"""Config flow for Evergy integration."""
from __future__ import annotations

import logging

from .pyEvergy import Evergy
import voluptuous as vol

from homeassistant import config_entries, core, exceptions
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, CONF_ADDRESS
from .const import DOMAIN


_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
  {
    vol.Required(CONF_USERNAME): str,
    vol.Required(CONF_PASSWORD): str,
  }
)


async def validate_input(hass: core.HomeAssistant, data):
    """Validate the user input allows us to connect.
    Data has the keys from DATA_SCHEMA with values provided by the user.
    """
    evergy_api = Evergy(data[CONF_USERNAME], data[CONF_PASSWORD])
    await hass.async_add_executor_job(evergy_api.get_usage)

    # Return info that you want to store in the config entry.
    return {CONF_USERNAME: data[CONF_USERNAME], CONF_PASSWORD: data[CONF_PASSWORD], CONF_ADDRESS: evergy_api.dashboard_data['addresses'][0]['street']}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for the Evergy integration."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)

                return self.async_create_entry(title=user_input[CONF_USERNAME], data=info)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )   


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""
