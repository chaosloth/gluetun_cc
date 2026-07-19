from homeassistant import config_entries
import voluptuous as vol

from .const import DOMAIN, CONF_INSTANCE_NAME, CONF_BASE_URL, CONF_API_KEY


class GluetunConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            instance_name = user_input.get(CONF_INSTANCE_NAME, "gluetun")

            # Set unique ID to allow multiple instances
            await self.async_set_unique_id(instance_name)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"Gluetun - {instance_name}",
                data=user_input
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_INSTANCE_NAME, default="gluetun"): str,
                vol.Required(CONF_BASE_URL, default="http://localhost:8111"): str,
                vol.Optional(CONF_API_KEY, default=""): str,
            }),
            errors=errors
        )
