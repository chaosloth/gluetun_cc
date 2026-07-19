from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .const import (
    DOMAIN,
    CONF_INSTANCE_NAME,
    CONF_API_KEY,
    CONF_IP_CHECK_DELAY,
    DEFAULT_IP_CHECK_DELAY,
    PLATFORMS,
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    hass.data.setdefault(DOMAIN, {})
    instance_name = entry.data.get(CONF_INSTANCE_NAME, "gluetun")
    api_key = entry.data.get(CONF_API_KEY, "")
    ip_check_delay = entry.data.get(CONF_IP_CHECK_DELAY, DEFAULT_IP_CHECK_DELAY)
    hass.data[DOMAIN][entry.entry_id] = {
        "instance_name": instance_name,
        "api_key": api_key,
        "ip_check_delay": ip_check_delay,
    }
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    hass.data[DOMAIN].pop(entry.entry_id, None)
    unload_ok = all(
        await hass.config_entries.async_forward_entry_unload(entry, platform)
        for platform in PLATFORMS
    )
    return unload_ok
