from homeassistant import config_entries, core
from homeassistant.const import CONF_IP_ADDRESS, CONF_USERNAME, CONF_PASSWORD
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.device_registry import DeviceInfo

from .const import (
    DOMAIN,
    CONF_SIZE,
    CONF_NAME,
)


class Gen24LppEvent(Entity):
    """Representation of a Gen24 Entity."""

    def __init__(self, ip: str, user: str, password: str, size: int, name: str) -> None:
        """Init Gen24"""
        self._ip = ip
        self._user = user
        self._password = password
        self.native_max_value = size
        self._attr_unique_id = f"{name}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{name}")},
            manufacturer="Fronius",
        )
        self.min_value = 0
        self.max_value = size
        self.native_min_value = 0
        self.native_max_value = size
        self.mode = "slider"
        self.native_step = 1
        self.native_value = 0
        self.unit_of_measurement = "W"

    async def async_added_to_hass(self) -> None:
        """Later..."""
        print("done.")

    async def convert_to_native_value(self, value: float) -> None:
        """Convert to native value."""
        self.native_value = value


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
) -> None:
    """Setup sensors from a config entry created in the integrations UI."""
    async_add_entities(
        [
            Gen24LppEvent(
                config_entry.data[CONF_IP_ADDRESS],
                config_entry.data[CONF_USERNAME],
                config_entry.data[CONF_PASSWORD],
                config_entry.data[CONF_SIZE],
                config_entry.data[CONF_NAME],
            )
        ]
    )
