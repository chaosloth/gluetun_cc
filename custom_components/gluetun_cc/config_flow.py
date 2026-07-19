from homeassistant import config_entries
import voluptuous as vol

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


class GluetunConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            instance_name = user_input.get(CONF_INSTANCE_NAME, "gluetun")

            await self.async_set_unique_id(instance_name)
            self._abort_if_unique_id_configured()

            tunnel_name = user_input.get(CONF_TUNNEL_NAME, "")
            title = tunnel_name if tunnel_name else instance_name

            return self.async_create_entry(
                title=f"Gluetun - {title}",
                data=user_input
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_INSTANCE_NAME, default="gluetun"): str,
                vol.Required(CONF_BASE_URL, default="http://localhost:8111"): str,
                vol.Optional(CONF_API_KEY, default=""): str,
                vol.Optional(CONF_TUNNEL_NAME, default=""): str,
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
                    int, vol.Range(min=1, max=3600)
                ),
                vol.Optional(CONF_IP_UPDATE_INTERVAL, default=DEFAULT_IP_UPDATE_INTERVAL): vol.All(
                    int, vol.Range(min=10, max=86400)
                ),
                vol.Optional(CONF_IP_CHECK_DELAY, default=DEFAULT_IP_CHECK_DELAY): vol.All(
                    int, vol.Range(min=0, max=300)
                ),
            }),
            errors=errors
        )

    async def async_step_reconfigure(self, user_input=None):
        reconfigure_entry = self._get_reconfigure_entry()

        if user_input is not None:
            await self.async_set_unique_id(reconfigure_entry.unique_id)
            self._abort_if_unique_id_mismatch()

            return self.async_update_reload_and_abort(
                reconfigure_entry,
                data_updates={
                    CONF_BASE_URL: user_input[CONF_BASE_URL],
                    CONF_API_KEY: user_input.get(CONF_API_KEY, ""),
                    CONF_TUNNEL_NAME: user_input.get(CONF_TUNNEL_NAME, ""),
                    CONF_SCAN_INTERVAL: user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                    CONF_IP_UPDATE_INTERVAL: user_input.get(CONF_IP_UPDATE_INTERVAL, DEFAULT_IP_UPDATE_INTERVAL),
                    CONF_IP_CHECK_DELAY: user_input.get(CONF_IP_CHECK_DELAY, DEFAULT_IP_CHECK_DELAY),
                },
            )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema({
                vol.Required(
                    CONF_BASE_URL,
                    default=reconfigure_entry.data.get(CONF_BASE_URL, "http://localhost:8111"),
                ): str,
                vol.Optional(
                    CONF_API_KEY,
                    default=reconfigure_entry.data.get(CONF_API_KEY, ""),
                ): str,
                vol.Optional(
                    CONF_TUNNEL_NAME,
                    default=reconfigure_entry.data.get(CONF_TUNNEL_NAME, ""),
                ): str,
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=reconfigure_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                ): vol.All(int, vol.Range(min=1, max=3600)),
                vol.Optional(
                    CONF_IP_UPDATE_INTERVAL,
                    default=reconfigure_entry.data.get(CONF_IP_UPDATE_INTERVAL, DEFAULT_IP_UPDATE_INTERVAL),
                ): vol.All(int, vol.Range(min=10, max=86400)),
                vol.Optional(
                    CONF_IP_CHECK_DELAY,
                    default=reconfigure_entry.data.get(CONF_IP_CHECK_DELAY, DEFAULT_IP_CHECK_DELAY),
                ): vol.All(int, vol.Range(min=0, max=300)),
            }),
        )
