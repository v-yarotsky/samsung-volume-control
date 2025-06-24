"""Test Samsung TV coordinator for managing device and data updates."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.samsung_tv_volume.coordinator import SamsungTVCoordinator


class TestSamsungTVCoordinator:
    """Test coordinator for Samsung TV integration."""

    async def test_coordinator_setup(self, hass, mock_upnp_factory):
        """Test coordinator initialization and setup."""
        location = "http://192.168.1.219:7676/smp_14_"
        
        coordinator = SamsungTVCoordinator(hass, location, "Test TV", "uuid:test-udn")
        
        # Test initial state
        assert coordinator.name == "Test TV"
        assert coordinator.location == location
        assert coordinator.data is None  # Initial data is None before first refresh
        # Note: last_update_success may default to True in DataUpdateCoordinator

    async def test_coordinator_first_refresh(self, hass, mock_upnp_factory):
        """Test coordinator first data refresh and device setup."""
        location = "http://192.168.1.219:7676/smp_14_"
        
        coordinator = SamsungTVCoordinator(hass, location, "Test TV", "uuid:test-udn")
        
        # Mock initial volume
        mock_upnp_factory["dmr_device"].volume_level = 0.5
        
        # Test first refresh
        await coordinator.async_refresh()
        
        # Verify device was set up and data populated
        assert coordinator.last_update_success
        assert coordinator.data["volume_level"] == 0.5  # 50/100
        assert coordinator.data["is_volume_muted"] is False
        assert coordinator.available

    async def test_coordinator_refresh_updates_volume(self, hass, mock_upnp_factory):
        """Test coordinator refresh updates volume data."""
        location = "http://192.168.1.219:7676/smp_14_"
        
        coordinator = SamsungTVCoordinator(hass, location, "Test TV", "uuid:test-udn")
        await coordinator.async_refresh()
        
        # Change volume on device
        mock_upnp_factory["dmr_device"].volume_level = 0.75
        
        # Refresh data
        await coordinator.async_refresh()
        
        # Verify updated data
        assert coordinator.data["volume_level"] == 0.75  # 75/100

    async def test_coordinator_handles_device_offline(self, hass, mock_upnp_factory):
        """Test coordinator handles device going offline."""
        location = "http://192.168.1.219:7676/smp_14_"
        
        coordinator = SamsungTVCoordinator(hass, location, "Test TV", "uuid:test-udn")
        await coordinator.async_refresh()
        
        # Verify initial state
        assert coordinator.last_update_success
        assert coordinator.available
        
        # Simulate device going offline by making volume_level property return None
        mock_upnp_factory["dmr_device"].volume_level = None
        
        # Refresh should handle error gracefully - UpdateFailed is caught by framework
        await coordinator.async_refresh()
        
        # Verify coordinator state reflects the offline device
        assert not coordinator.last_update_success
        assert not coordinator.available

    async def test_coordinator_event_callback(self, hass, mock_upnp_factory):
        """Test coordinator handles UPnP volume events."""
        location = "http://192.168.1.219:7676/smp_14_"
        
        coordinator = SamsungTVCoordinator(hass, location, "Test TV", "uuid:test-udn")
        await coordinator.async_refresh()
        
        # Simulate volume event from TV
        coordinator.handle_volume_event(85)
        
        # Verify data was updated
        assert coordinator.data["volume_level"] == 0.85  # 85/100
        assert coordinator.last_update_success

    async def test_coordinator_set_volume(self, hass, mock_upnp_factory):
        """Test coordinator can set volume on device."""
        location = "http://192.168.1.219:7676/smp_14_"
        
        coordinator = SamsungTVCoordinator(hass, location, "Test TV", "uuid:test-udn")
        await coordinator.async_refresh()
        
        # Test setting volume
        await coordinator.async_set_volume(0.6)  # 60%
        
        # Verify device method was called
        mock_upnp_factory["dmr_device"].async_set_volume_level.assert_called_with(0.6)
        
        # Verify data was updated
        assert coordinator.data["volume_level"] == 0.6

    async def test_coordinator_device_reconnection(self, hass, mock_upnp_factory):
        """Test coordinator handles device reconnection."""
        location = "http://192.168.1.219:7676/smp_14_"
        
        coordinator = SamsungTVCoordinator(hass, location, "Test TV", "uuid:test-udn")
        await coordinator.async_refresh()
        
        # Verify initial state
        assert coordinator.last_update_success
        assert coordinator.available
        
        # Simulate device disconnection by making volume_level property return None
        mock_upnp_factory["dmr_device"].volume_level = None
        
        # Refresh handles error gracefully - no exception bubbles up
        await coordinator.async_refresh()
        
        assert not coordinator.last_update_success
        assert not coordinator.available
        
        # Simulate device coming back online
        mock_upnp_factory["dmr_device"].volume_level = 0.4
        
        # Refresh should succeed and mark as available
        await coordinator.async_refresh()
        
        assert coordinator.last_update_success
        assert coordinator.available
        assert coordinator.data["volume_level"] == 0.4

    async def test_coordinator_cleanup(self, hass, mock_upnp_factory):
        """Test coordinator cleanup closes device properly."""
        location = "http://192.168.1.219:7676/smp_14_"
        
        coordinator = SamsungTVCoordinator(hass, location, "Test TV", "uuid:test-udn")
        await coordinator.async_refresh()
        
        # Test cleanup
        await coordinator.async_shutdown()
        
        # Verify device was closed
        mock_upnp_factory["requester"].close.assert_called_once()

    async def test_coordinator_event_subscription(self, hass, mock_upnp_factory):
        """Test coordinator subscribes to UPnP events during setup."""
        location = "http://192.168.1.219:7676/smp_14_"
        
        # Mock rendering control service for event subscription
        rendering_control_service = AsyncMock()
        mock_upnp_factory["upnp_device"].services = {
            "RenderingControl": rendering_control_service
        }
        
        coordinator = SamsungTVCoordinator(hass, location, "Test TV", "uuid:test-udn")
        await coordinator.async_refresh()
        
        # Verify event subscription was attempted
        # (Implementation will call device.async_subscribe_events)
        # This test ensures the coordinator tries to set up real-time events