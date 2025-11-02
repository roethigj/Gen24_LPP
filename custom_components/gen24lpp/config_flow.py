"""Config flow for Fronius Gen24 LPP integration."""

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_IP_ADDRESS, CONF_PASSWORD, CONF_USERNAME

from .const import CONF_NAME, CONF_SIZE, DOMAIN
from .lpp_a import FroniusGEN24

_LOGGER = logging.getLogger(__name__)

SCHEMA_DEVICE = vol.Schema(
    {
        vol.Required(CONF_IP_ADDRESS, default="0.0.0.0"): str,
        vol.Required(CONF_USERNAME, default="Technician"): str,
        vol.Required(CONF_PASSWORD, default=""): str,
        vol.Required(CONF_SIZE, default=10000): int,
        vol.Optional(CONF_NAME, default="gen24_lpp"): str,
    }
)


async def validate_connection(ip: str, user: str, password: str) -> None:
    """Validate Inverter Connection."""
    fronius = FroniusGEN24(ip, user, password, debug=False)

    if not await fronius.login():
        _LOGGER.error(f"Cannot login")
        raise ConnectionError


class ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> ConfigFlowResult:
        """Handle the initial step."""

        errors = {}

        # data: Optional[Dict[str, Any]]

        if user_input is not None:
            try:
                await validate_connection(
                    user_input[CONF_IP_ADDRESS],
                    user_input[CONF_USERNAME],
                    user_input[CONF_PASSWORD],
                )
            except ConnectionError:
                return "", "login failed!"

            if not errors:
                name = user_input[CONF_NAME]
                await self.async_set_unique_id(name)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"Gen24_LPP -name {name}", data=user_input
                )

        return self.async_show_form(
            step_id="user",
            data_schema=SCHEMA_DEVICE,
            errors=errors,
        )
