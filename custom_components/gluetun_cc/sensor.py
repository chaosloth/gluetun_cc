from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_call_later
from datetime import timedelta
import aiohttp
import logging
import json
from urllib.parse import urljoin

from .const import (
    DOMAIN,
    CONF_INSTANCE_NAME,
    CONF_BASE_URL,
    CONF_API_KEY,
    CONF_TUNNEL_NAME,
    CONF_SCAN_INTERVAL,
    CONF_IP_UPDATE_INTERVAL,
    CONF_IP_CHECK_DELAY,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_IP_UPDATE_INTERVAL,
    DEFAULT_IP_CHECK_DELAY,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    instance_name = entry.data.get(CONF_INSTANCE_NAME, "gluetun")
    base_url = entry.data.get(CONF_BASE_URL, "http://localhost:8111")
    api_key = entry.data.get(CONF_API_KEY, "")
    tunnel_name = entry.data.get(CONF_TUNNEL_NAME, "")
    display_name = tunnel_name if tunnel_name else instance_name
    scan_interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    ip_update_interval = entry.data.get(CONF_IP_UPDATE_INTERVAL, DEFAULT_IP_UPDATE_INTERVAL)
    ip_check_delay = entry.data.get(CONF_IP_CHECK_DELAY, DEFAULT_IP_CHECK_DELAY)

    status_url = urljoin(base_url, "/v1/vpn/status")
    public_ip_url = urljoin(base_url, "/v1/publicip/ip")

    status_coordinator = GluetunStatusCoordinator(
        hass, status_url, instance_name, api_key, scan_interval
    )
    public_ip_coordinator = GluetunPublicIPCoordinator(
        hass, public_ip_url, instance_name, api_key, ip_update_interval
    )

    hass.data[DOMAIN][entry.entry_id]["status_coordinator"] = status_coordinator
    hass.data[DOMAIN][entry.entry_id]["public_ip_coordinator"] = public_ip_coordinator

    await status_coordinator.async_refresh()
    await public_ip_coordinator.async_refresh()

    _setup_status_listener(hass, status_coordinator, public_ip_coordinator, ip_check_delay)

    async_add_entities([
        GluetunStatusSensor(status_coordinator, display_name),
        GluetunPublicIPSensor(public_ip_coordinator, "public_ip", display_name),
        GluetunPublicIPSensor(public_ip_coordinator, "region", display_name),
        GluetunPublicIPSensor(public_ip_coordinator, "country", display_name),
        GluetunPublicIPSensor(public_ip_coordinator, "city", display_name),
        GluetunPublicIPSensor(public_ip_coordinator, "location", display_name),
        GluetunPublicIPSensor(public_ip_coordinator, "organization", display_name),
        GluetunPublicIPSensor(public_ip_coordinator, "postal_code", display_name),
        GluetunPublicIPSensor(public_ip_coordinator, "timezone", display_name),
    ])


@callback
def _setup_status_listener(hass, status_coordinator, public_ip_coordinator, ip_check_delay):
    cancel_handle = None

    @callback
    def _on_status_update():
        nonlocal cancel_handle
        new_status = None
        data = status_coordinator.data
        if isinstance(data, dict):
            new_status = data.get("status")

        previous_status = status_coordinator.previous_status
        status_coordinator.previous_status = new_status

        if previous_status is not None and new_status != previous_status:
            _LOGGER.info(
                "VPN status changed from %s to %s, scheduling IP refresh in %ds",
                previous_status, new_status, ip_check_delay,
            )
            if cancel_handle is not None:
                cancel_handle()
            if ip_check_delay == 0:
                hass.async_create_task(public_ip_coordinator.async_request_refresh())
                cancel_handle = None
            else:
                cancel_handle = async_call_later(
                    hass,
                    ip_check_delay,
                    lambda _now: hass.async_create_task(
                        public_ip_coordinator.async_request_refresh()
                    ),
                )

    status_coordinator.async_add_listener(_on_status_update)


class GluetunStatusCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, url, instance_name="gluetun", api_key="",
                 scan_interval=DEFAULT_SCAN_INTERVAL):
        self.url = url
        self.instance_name = instance_name
        self.api_key = api_key
        self.previous_status = None
        super().__init__(
            hass,
            _LOGGER,
            name=f"gluetun_status_{instance_name}",
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_update_data(self):
        headers = {}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url, headers=headers) as response:
                if response.status != 200:
                    raise UpdateFailed(f"Error fetching status: {response.status}")
                text = await response.text()
                try:
                    data = json.loads(text)
                except json.JSONDecodeError:
                    raise UpdateFailed("Invalid JSON response")
                return data


class GluetunPublicIPCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, url, instance_name="gluetun", api_key="",
                 ip_update_interval=DEFAULT_IP_UPDATE_INTERVAL):
        self.url = url
        self.instance_name = instance_name
        self.api_key = api_key
        super().__init__(
            hass,
            _LOGGER,
            name=f"gluetun_public_ip_{instance_name}",
            update_interval=timedelta(seconds=ip_update_interval),
        )

    async def _async_update_data(self):
        headers = {}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url, headers=headers) as response:
                if response.status != 200:
                    raise UpdateFailed(f"Error fetching public IP: {response.status}")
                text = await response.text()
                try:
                    data = json.loads(text)
                except json.JSONDecodeError:
                    raise UpdateFailed("Invalid JSON response")
                return data


class GluetunStatusSensor(SensorEntity):
    def __init__(self, coordinator, display_name="gluetun"):
        self.coordinator = coordinator
        self.instance_name = display_name
        self._attr_name = f"Gluetun {display_name} Status"
        self._attr_unique_id = f"gluetun_{display_name}_status_sensor"

    @property
    def state(self):
        data = self.coordinator.data
        if isinstance(data, dict):
            return data.get("status", "unknown")
        return "unknown"

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


class GluetunPublicIPSensor(SensorEntity):
    def __init__(self, coordinator, key, display_name="gluetun"):
        self.coordinator = coordinator
        self.key = key
        self.instance_name = display_name
        self._attr_name = f"Gluetun {display_name} {key.replace('_', ' ').title()}"
        self._attr_unique_id = f"gluetun_{display_name}_{key}_sensor"

    @property
    def state(self):
        data = self.coordinator.data
        if isinstance(data, dict):
            return data.get(self.key, "unknown")
        return "unknown"

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
