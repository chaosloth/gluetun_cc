from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
import logging

from .const import DOMAIN, CONF_INSTANCE_NAME, CONF_TUNNEL_NAME

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    instance_name = entry.data.get(CONF_INSTANCE_NAME, "gluetun")
    tunnel_name = entry.data.get(CONF_TUNNEL_NAME, "")
    display_name = tunnel_name if tunnel_name else instance_name

    public_ip_coordinator = hass.data[DOMAIN][entry.entry_id].get("public_ip_coordinator")

    if public_ip_coordinator is None:
        _LOGGER.warning("Public IP coordinator not available for refresh button, skipping")
        return

    async_add_entities([
        GluetunRefreshButton(public_ip_coordinator, display_name),
    ])


class GluetunRefreshButton(ButtonEntity):
    def __init__(self, coordinator, display_name="gluetun"):
        self.coordinator = coordinator
        self.instance_name = display_name
        self._attr_name = f"Gluetun {display_name} Refresh IP"
        self._attr_unique_id = f"gluetun_{display_name}_refresh_ip"
        self._attr_icon = "mdi:refresh"
        self._attr_state = self._get_public_ip()

    def _get_public_ip(self):
        data = self.coordinator.data
        if isinstance(data, dict):
            ip = data.get("public_ip")
            if ip:
                return ip
        return None

    async def async_press(self) -> None:
        _LOGGER.info("Manual IP refresh triggered for %s", self.instance_name)
        await self.coordinator.async_request_refresh()

    async def async_added_to_hass(self):
        self._update_state()

        def _on_coordinator_update():
            self._update_state()
            self.async_write_ha_state()

        self.async_on_remove(
            self.coordinator.async_add_listener(_on_coordinator_update)
        )

    def _update_state(self):
        self._attr_state = self._get_public_ip()

    @property
    def available(self):
        return self.coordinator.last_update_success
