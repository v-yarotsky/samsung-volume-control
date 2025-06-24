"""Data update coordinator for Samsung TV Volume Control."""

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.components import ssdp
from aiohttp import ClientPayloadError, ClientResponseError
from async_upnp_client.exceptions import UpnpXmlContentError

from .upnp_device import SamsungTVUPnPDevice, DeviceInfo

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=30)


class SamsungTVCoordinator(DataUpdateCoordinator):
    """Coordinator to manage Samsung TV UPnP device and data updates."""

    def __init__(
        self,
        hass: HomeAssistant,
        location: str,
        name: str,
        udn: str,
    ) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=name,
            update_interval=SCAN_INTERVAL,
        )
        self.location = location
        self.udn = udn
        self._device: SamsungTVUPnPDevice | None = None
        self._available = False

    @property
    def available(self) -> bool:
        """Return if device is available."""
        return self._available

    def get_device_info(self) -> DeviceInfo | None:
        """Return device info from UPnP device."""
        if self._device:
            return self._device.get_device_info()
        return None

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the device."""
        if not self._device:
            await self._setup_device()

        try:
            # Get current volume from device
            volume = await self._device.async_get_volume()

            self._available = True
            return {
                "volume_level": volume / 100.0,  # Convert to 0.0-1.0 range
                "is_volume_muted": False,  # TODO: Add mute support later
            }

        except Exception as err:
            self._available = False
            _LOGGER.error("Error updating Samsung TV data: %s", err)
            raise UpdateFailed(f"Error updating Samsung TV: {err}") from err

    async def _setup_device(self) -> None:
        """Set up the UPnP device."""
        _LOGGER.debug("Setting up Samsung TV device at %s", self.location)

        try:
            self._device = SamsungTVUPnPDevice(self.location)
            await self._device.async_setup()

            # Subscribe to volume events for real-time updates
            await self._device.async_subscribe_events(self.handle_volume_event)

            _LOGGER.debug("Successfully set up Samsung TV device")

        except Exception as err:
            _LOGGER.error("Failed to set up Samsung TV device: %s", err)
            self._device = None

            # Try to rediscover device if location is stale (specific exception types)
            if isinstance(err, (UpnpXmlContentError, ClientPayloadError, ClientResponseError)):
                _LOGGER.info(
                    "Attempting to rediscover Samsung TV with UDN %s (error: %s)",
                    self.udn,
                    type(err).__name__,
                )
                new_location = await self._rediscover_device()
                if new_location:
                    self.location = new_location
                    # Retry setup with new location
                    try:
                        self._device = SamsungTVUPnPDevice(self.location)
                        await self._device.async_setup()
                        await self._device.async_subscribe_events(
                            self.handle_volume_event
                        )
                        _LOGGER.info(
                            "Successfully reconnected to Samsung TV at %s",
                            self.location,
                        )
                        return
                    except Exception as retry_err:
                        _LOGGER.error(
                            "Failed to reconnect even with new location: %s", retry_err
                        )

            raise

    async def _rediscover_device(self) -> str | None:
        """Rediscover device location using Home Assistant SSDP cache."""
        try:
            discovery_infos = await ssdp.async_get_discovery_info_by_udn(
                self.hass, self.udn
            )
            if discovery_infos:
                # Use the first discovery info (they should all have the same location)
                new_location = discovery_infos[0].ssdp_location
                _LOGGER.info(
                    "Rediscovered Samsung TV at new location: %s", new_location
                )
                return new_location
            else:
                _LOGGER.warning(
                    "Samsung TV with UDN %s not found in SSDP cache", self.udn
                )
                return None
        except Exception as err:
            _LOGGER.error("Failed to rediscover Samsung TV: %s", err)
            return None

    @callback
    def handle_volume_event(self, volume: int) -> None:
        """Handle volume change events from Samsung TV."""
        _LOGGER.debug("Received volume event: %s", volume)

        # Update data without triggering device refresh
        new_data = self.data.copy() if self.data else {}
        new_data["volume_level"] = volume / 100.0

        # Trigger coordinator update
        self.async_set_updated_data(new_data)

    async def async_set_volume(self, volume_level: float) -> None:
        """Set volume on Samsung TV."""
        if not self._device:
            raise UpdateFailed("Device not available")

        try:
            volume = int(volume_level * 100)  # Convert to 0-100 range
            await self._device.async_set_volume(volume)

            # Update local data immediately
            new_data = self.data.copy() if self.data else {}
            new_data["volume_level"] = volume_level
            self.async_set_updated_data(new_data)

        except Exception as err:
            _LOGGER.error("Failed to set volume: %s", err)
            raise UpdateFailed(f"Failed to set volume: {err}") from err

    async def async_shutdown(self) -> None:
        """Shutdown coordinator and cleanup device."""
        if self._device:
            try:
                await self._device.async_close()
            except Exception as err:
                _LOGGER.error("Error closing Samsung TV device: %s", err)
            finally:
                self._device = None

        self._available = False
