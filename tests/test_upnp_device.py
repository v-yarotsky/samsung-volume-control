"""Test UPnP device setup and volume control."""
import pytest
from custom_components.samsung_tv_volume.upnp_device import SamsungTVUPnPDevice


class TestUpnpDevice:
    """Test UPnP device creation and volume operations."""

    async def test_create_dmr_device_from_location(self, mock_upnp_factory):
        """Test creating DmrDevice from LOCATION URL."""
        location = "http://192.168.1.219:7676/smp_14_"
        
        device = SamsungTVUPnPDevice(location)
        await device.async_setup()
        
        # Verify the setup process
        assert device.is_connected
        mock_upnp_factory["factory"].async_create_device.assert_called_once_with(location)
        mock_upnp_factory["DmrDevice"].assert_called_once_with(mock_upnp_factory["upnp_device"], None)

    async def test_get_volume_via_dmr_device(self, mock_upnp_factory):
        """Test getting volume through DmrDevice."""
        location = "http://192.168.1.219:7676/smp_14_"
        
        device = SamsungTVUPnPDevice(location)
        await device.async_setup()
        volume = await device.async_get_volume()
        
        assert volume == 50

    async def test_set_volume_via_dmr_device(self, mock_upnp_factory):
        """Test setting volume through DmrDevice."""
        location = "http://192.168.1.219:7676/smp_14_"
        
        device = SamsungTVUPnPDevice(location)
        await device.async_setup()
        await device.async_set_volume(75)
        
        mock_upnp_factory["dmr_device"].async_set_volume_level.assert_called_once_with(0.75)

    async def test_volume_validation(self, mock_upnp_factory):
        """Test volume value validation."""
        location = "http://192.168.1.219:7676/smp_14_"
        
        device = SamsungTVUPnPDevice(location)
        await device.async_setup()
        
        # Test invalid volume values
        with pytest.raises(ValueError, match="Volume must be between 0 and 100"):
            await device.async_set_volume(-1)
        
        with pytest.raises(ValueError, match="Volume must be between 0 and 100"):
            await device.async_set_volume(101)

    async def test_device_not_setup_error(self):
        """Test operations fail when device not set up."""
        location = "http://192.168.1.219:7676/smp_14_"
        device = SamsungTVUPnPDevice(location)
        
        # Test operations without setup
        with pytest.raises(RuntimeError, match="Device not set up"):
            await device.async_get_volume()
        
        with pytest.raises(RuntimeError, match="Device not set up"):
            await device.async_set_volume(50)

    async def test_dmr_device_connection_error(self, mock_upnp_factory):
        """Test DmrDevice creation handles connection errors."""
        location = "http://192.168.1.219:7676/smp_14_"
        
        # Configure factory to raise ConnectionError
        mock_upnp_factory["factory"].async_create_device.side_effect = ConnectionError("Device unreachable")
        
        device = SamsungTVUPnPDevice(location)
        
        # Test that connection error is properly raised
        with pytest.raises(ConnectionError, match="Device unreachable"):
            await device.async_setup()

    async def test_device_cleanup(self, mock_upnp_factory):
        """Test device cleanup and close."""
        location = "http://192.168.1.219:7676/smp_14_"
        
        device = SamsungTVUPnPDevice(location)
        await device.async_setup()
        
        assert device.is_connected
        
        # Test cleanup
        await device.async_close()
        
        mock_upnp_factory["requester"].close.assert_called_once()
        assert not device.is_connected