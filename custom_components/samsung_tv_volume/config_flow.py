"""Config flow for Samsung TV Volume Control integration."""

from urllib.parse import urlparse

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.helpers.service_info.ssdp import SsdpServiceInfo

from async_upnp_client.aiohttp import AiohttpRequester
from async_upnp_client.client_factory import UpnpFactory

from .const import DOMAIN, LOGGER


class SamsungTVVolumeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Samsung TV Volume Control."""

    VERSION = 1

    async def async_step_ssdp(
        self, discovery_info: SsdpServiceInfo
    ) -> config_entries.ConfigFlowResult:
        """Handle SSDP discovery."""
        LOGGER.debug("SSDP discovery: %s", discovery_info)

        # Check if it's a Samsung device
        manufacturer = discovery_info.upnp.get("manufacturer", "")
        server_header = discovery_info.ssdp_headers.get("SERVER", "")

        if "Samsung" not in manufacturer and "Samsung" not in server_header:
            LOGGER.debug("Not a Samsung device: %s", manufacturer)
            return self.async_abort(reason="not_samsung_tv")

        # Extract UDN for uniqueness check
        udn = discovery_info.upnp.get("UDN") or discovery_info.ssdp_usn.split("::")[0]

        # Check if already configured
        await self.async_set_unique_id(udn)
        self._abort_if_unique_id_configured()

        # Extract device info
        location = discovery_info.ssdp_location
        parsed_url = urlparse(location)
        host = parsed_url.hostname
        friendly_name = discovery_info.upnp.get("friendlyName", f"Samsung TV ({host})")

        try:
            # Verify device is accessible via async-upnp-client
            requester = AiohttpRequester(timeout=10)
            factory = UpnpFactory(requester)
            device = await factory.async_create_device(location)

            LOGGER.debug("Successfully connected to Samsung TV: %s", friendly_name)

        except ConnectionError:
            LOGGER.error("Cannot connect to Samsung TV at %s", location)
            return self.async_abort(reason="cannot_connect")
        except Exception as err:
            LOGGER.error("Invalid UPnP device at %s: %s", location, err)
            return self.async_abort(reason="invalid_device")

        # Create config entry
        return self.async_create_entry(
            title=friendly_name,
            data={
                CONF_HOST: host,
                CONF_NAME: friendly_name,
                "location": location,
                "udn": udn,
            },
        )
