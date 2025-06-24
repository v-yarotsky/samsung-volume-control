"""UPnP device management for Samsung TV Volume Control."""

import logging
from typing import TypedDict

from async_upnp_client.aiohttp import AiohttpRequester
from async_upnp_client.client import UpnpDevice
from async_upnp_client.client_factory import UpnpFactory
from async_upnp_client.profiles.dlna import DmrDevice

_LOGGER = logging.getLogger(__name__)


class DeviceInfo(TypedDict, total=False):
    """Type definition for UPnP device info."""

    friendly_name: str
    manufacturer: str
    model_name: str
    model_number: str | None
    serial_number: str | None
    udn: str
    device_type: str | None
    presentation_url: str | None


class SamsungTVUPnPDevice:
    """Manages UPnP connection and volume control for Samsung TV."""

    def __init__(self, location: str) -> None:
        """Initialize the UPnP device manager."""
        self.location = location
        self._dmr_device: DmrDevice | None = None
        self._requester: AiohttpRequester | None = None
        self._upnp_device: UpnpDevice | None = None

    async def async_setup(self) -> None:
        """Set up the UPnP device connection."""
        _LOGGER.debug("Setting up UPnP device at %s", self.location)

        try:
            self._requester = AiohttpRequester(timeout=10)
            factory = UpnpFactory(self._requester)
            self._upnp_device = await factory.async_create_device(self.location)
            self._dmr_device = DmrDevice(self._upnp_device)

            _LOGGER.debug("Successfully created DmrDevice for %s", self.location)

        except Exception as err:
            _LOGGER.error("Failed to create UPnP device at %s: %s", self.location, err)
            raise

    async def async_get_volume(self) -> int:
        """Get current volume level."""
        if not self._dmr_device:
            raise RuntimeError("Device not set up")

        try:
            volume = await self._dmr_device.async_get_volume()
            _LOGGER.debug("Current volume: %s", volume)
            return volume
        except Exception as err:
            _LOGGER.error("Failed to get volume: %s", err)
            raise

    async def async_set_volume(self, volume: int) -> None:
        """Set volume level."""
        if not self._dmr_device:
            raise RuntimeError("Device not set up")

        if not 0 <= volume <= 100:
            raise ValueError(f"Volume must be between 0 and 100, got {volume}")

        try:
            await self._dmr_device.async_set_volume(volume)
            _LOGGER.debug("Set volume to %s", volume)
        except Exception as err:
            _LOGGER.error("Failed to set volume to %s: %s", volume, err)
            raise

    async def async_subscribe_events(self, callback) -> bool:
        """Subscribe to UPnP events from Samsung TV."""
        if not self._dmr_device:
            raise RuntimeError("Device not set up")

        try:
            # TODO: Implement actual event subscription using async-upnp-client
            # For now, just store the callback for testing
            self._event_callback = callback
            _LOGGER.debug("Subscribed to UPnP events")
            return True
        except Exception as err:
            _LOGGER.error("Failed to subscribe to events: %s", err)
            return False

    async def async_unsubscribe_events(self) -> None:
        """Unsubscribe from UPnP events."""
        try:
            # TODO: Implement actual event unsubscription
            self._event_callback = None
            _LOGGER.debug("Unsubscribed from UPnP events")
        except Exception as err:
            _LOGGER.error("Failed to unsubscribe from events: %s", err)

    def get_device_info(self) -> DeviceInfo | None:
        """Return device info from UPnP device."""
        if not self._upnp_device:
            return None

        # Extract real device info from UPnP device
        device_info = DeviceInfo(
            friendly_name=self._upnp_device.friendly_name,
            manufacturer=self._upnp_device.manufacturer,
            model_name=self._upnp_device.model_name,
            model_number=self._upnp_device.model_number,
            serial_number=self._upnp_device.serial_number,
            udn=self._upnp_device.udn,
            device_type=self._upnp_device.device_type,
            presentation_url=self._upnp_device.presentation_url,
        )

        return device_info

    async def async_close(self) -> None:
        """Close the UPnP device connection."""
        # Unsubscribe from events before closing
        if hasattr(self, "_event_callback") and self._event_callback:
            await self.async_unsubscribe_events()

        if self._requester:
            await self._requester.close()
            self._requester = None
        self._dmr_device = None
        self._upnp_device = None
        _LOGGER.debug("Closed UPnP device connection")

    @property
    def is_connected(self) -> bool:
        """Return if device is connected."""
        return self._dmr_device is not None
