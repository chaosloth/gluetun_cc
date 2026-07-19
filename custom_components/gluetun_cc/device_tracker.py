from homeassistant.components.device_tracker import TrackerEntity, SourceType
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
import logging

from .const import DOMAIN, CONF_INSTANCE_NAME, CONF_TUNNEL_NAME

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    instance_name = entry.data.get(CONF_INSTANCE_NAME, "gluetun")
    tunnel_name = entry.data.get(CONF_TUNNEL_NAME, "")
    display_name = tunnel_name if tunnel_name else instance_name

    coordinator = hass.data[DOMAIN][entry.entry_id].get("public_ip_coordinator")

    if coordinator is None:
        _LOGGER.warning("Public IP coordinator not available for device tracker, skipping")
        return

    async_add_entities([
        GluetunTrackerEntity(coordinator, display_name),
    ])


class GluetunTrackerEntity(TrackerEntity):
    def __init__(self, coordinator, display_name="gluetun"):
        self.coordinator = coordinator
        self.instance_name = display_name
        self._attr_name = f"Gluetun {display_name} VPN Location"
        self._attr_unique_id = f"gluetun_{display_name}_tracker"
        self._attr_icon = "mdi:vpn"

    @property
    def source_type(self):
        return SourceType.GPS

    @property
    def latitude(self):
        data = self.coordinator.data
        if isinstance(data, dict):
            location = data.get("location")
            if location and isinstance(location, str) and "," in location:
                try:
                    lat, _ = location.split(",", 1)
                    return float(lat)
                except (ValueError, AttributeError):
                    return None
        return None

    @property
    def longitude(self):
        data = self.coordinator.data
        if isinstance(data, dict):
            location = data.get("location")
            if location and isinstance(location, str) and "," in location:
                try:
                    _, lon = location.split(",", 1)
                    return float(lon)
                except (ValueError, AttributeError):
                    return None
        return None

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        if isinstance(data, dict):
            return {
                "public_ip": data.get("public_ip"),
                "city": data.get("city"),
                "country": data.get("country"),
                "region": data.get("region"),
                "organization": data.get("organization"),
            }
        return {}

    @property
    def should_poll(self):
        return False

    @property
    def available(self):
        return self.coordinator.last_update_success

    async def async_added_to_hass(self):
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )
