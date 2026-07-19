from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_call_later
import aiohttp
import logging

from .const import (
    DOMAIN,
    CONF_INSTANCE_NAME,
    CONF_BASE_URL,
    CONF_API_KEY,
    CONF_TUNNEL_NAME,
    CONF_IP_CHECK_DELAY,
    DEFAULT_IP_CHECK_DELAY,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    instance_name = entry.data.get(CONF_INSTANCE_NAME, "gluetun")
    base_url = entry.data.get(CONF_BASE_URL, "http://localhost:8111")
    api_key = entry.data.get(CONF_API_KEY, "")
    tunnel_name = entry.data.get(CONF_TUNNEL_NAME, "")
    display_name = tunnel_name if tunnel_name else instance_name
    ip_check_delay = entry.data.get(CONF_IP_CHECK_DELAY, DEFAULT_IP_CHECK_DELAY)

    coordinator = hass.data[DOMAIN][entry.entry_id].get("status_coordinator")
    public_ip_coordinator = hass.data[DOMAIN][entry.entry_id].get("public_ip_coordinator")

    if coordinator is None:
        _LOGGER.warning("Status coordinator not available for switch, skipping")
        return

    async_add_entities([
        GluetunSwitch(
            coordinator, display_name, base_url, api_key,
            public_ip_coordinator, ip_check_delay,
        ),
    ])


class GluetunSwitch(SwitchEntity):
    def __init__(self, coordinator, display_name, base_url, api_key,
                 public_ip_coordinator=None, ip_check_delay=DEFAULT_IP_CHECK_DELAY):
        self.coordinator = coordinator
        self.instance_name = display_name
        self.base_url = base_url
        self.api_key = api_key
        self.public_ip_coordinator = public_ip_coordinator
        self.ip_check_delay = ip_check_delay
        self._attr_name = f"Gluetun {display_name} VPN"
        self._attr_unique_id = f"gluetun_{display_name}_switch"
        self._attr_icon = "mdi:vpn"

    @property
    def is_on(self):
        data = self.coordinator.data
        if isinstance(data, dict):
            return data.get("status") == "running"
        return False

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        if isinstance(data, dict):
            return {"status": data.get("status", "unknown")}
        return {"status": "unknown"}

    async def async_turn_on(self, **kwargs):
        await self._set_vpn_status("running")

    async def async_turn_off(self, **kwargs):
        await self._set_vpn_status("stopped")

    async def _set_vpn_status(self, status):
        url = f"{self.base_url.rstrip('/')}/v1/vpn/status"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        payload = {"status": status}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.put(url, json=payload, headers=headers) as response:
                    if response.status != 200:
                        _LOGGER.error(
                            "Failed to set VPN status to %s: HTTP %s",
                            status,
                            response.status,
                        )
                        return
            await self.coordinator.async_request_refresh()
            self._schedule_ip_refresh()
        except aiohttp.ClientError as err:
            _LOGGER.error("Error setting VPN status to %s: %s", status, err)

    def _schedule_ip_refresh(self):
        if self.public_ip_coordinator is None:
            return
        if self.ip_check_delay == 0:
            self.hass.async_create_task(
                self.public_ip_coordinator.async_request_refresh()
            )
        else:
            _LOGGER.info(
                "Scheduling IP refresh in %ds after VPN state change",
                self.ip_check_delay,
            )
            async_call_later(
                self.hass,
                self.ip_check_delay,
                lambda _now: self.hass.async_create_task(
                    self.public_ip_coordinator.async_request_refresh()
                ),
            )

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
