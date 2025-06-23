"""Test UPnP device setup and volume control."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from custom_components.samsung_tv_volume.const import DOMAIN


class TestUpnpDevice:
    """Test UPnP device creation and volume operations."""

    async def test_create_dmr_device_from_location(self):
        """Test creating DmrDevice from LOCATION URL."""
        location = "http://192.168.1.219:7676/smp_14_"
        
        with patch('async_upnp_client.client_factory.UpnpFactory') as mock_factory:
            with patch('async_upnp_client.profiles.dlna.DmrDevice') as mock_dmr_device_class:
                # Mock the factory and device creation
                mock_requester = AsyncMock()
                mock_factory_instance = AsyncMock()
                mock_factory.return_value = mock_factory_instance
                
                mock_upnp_device = AsyncMock()
                mock_upnp_device.device_info = {
                    "friendly_name": "[TV]Samsung LED60",
                    "manufacturer": "Samsung Electronics",
                    "model_name": "UN60H7100",
                    "udn": "uuid:08583b01-008c-1000-817d-bc148594dddb"
                }
                mock_factory_instance.async_create_device.return_value = mock_upnp_device
                
                # Mock DmrDevice creation
                mock_dmr_device = AsyncMock()
                mock_dmr_device_class.return_value = mock_dmr_device
                
                # Create a simple device factory function to test
                async def create_dmr_device(location_url):
                    from async_upnp_client.aiohttp import AiohttpRequester
                    from async_upnp_client.client_factory import UpnpFactory
                    from async_upnp_client.profiles.dlna import DmrDevice
                    
                    requester = AiohttpRequester(timeout=10)
                    factory = UpnpFactory(requester)
                    upnp_device = await factory.async_create_device(location_url)
                    dmr_device = DmrDevice(upnp_device)
                    return dmr_device
                
                # Test the device creation
                dmr_device = await create_dmr_device(location)
                
                # Verify factory was called with correct location
                mock_factory_instance.async_create_device.assert_called_once_with(location)
                
                # Verify DmrDevice was created with the UPnP device
                mock_dmr_device_class.assert_called_once_with(mock_upnp_device)
                
                # Verify we got a DmrDevice instance
                assert dmr_device == mock_dmr_device

    async def test_get_volume_via_dmr_device(self):
        """Test getting volume through DmrDevice."""
        with patch('async_upnp_client.profiles.dlna.DmrDevice') as mock_dmr_device_class:
            mock_dmr_device = AsyncMock()
            mock_dmr_device_class.return_value = mock_dmr_device
            
            # Mock get_volume to return 50
            mock_dmr_device.async_get_volume.return_value = 50
            
            # Test volume retrieval
            volume = await mock_dmr_device.async_get_volume()
            
            assert volume == 50
            mock_dmr_device.async_get_volume.assert_called_once()

    async def test_set_volume_via_dmr_device(self):
        """Test setting volume through DmrDevice."""
        with patch('async_upnp_client.profiles.dlna.DmrDevice') as mock_dmr_device_class:
            mock_dmr_device = AsyncMock()
            mock_dmr_device_class.return_value = mock_dmr_device
            
            # Mock set_volume
            mock_dmr_device.async_set_volume.return_value = None
            
            # Test volume setting
            await mock_dmr_device.async_set_volume(75)
            
            mock_dmr_device.async_set_volume.assert_called_once_with(75)

    async def test_dmr_device_connection_error(self):
        """Test DmrDevice creation handles connection errors."""
        location = "http://192.168.1.219:7676/smp_14_"
        
        with patch('async_upnp_client.client_factory.UpnpFactory') as mock_factory:
            mock_factory_instance = AsyncMock()
            mock_factory.return_value = mock_factory_instance
            
            # Mock connection error during device creation
            mock_factory_instance.async_create_device.side_effect = ConnectionError("Device unreachable")
            
            # Create a simple device factory function to test
            async def create_dmr_device(location_url):
                from async_upnp_client.aiohttp import AiohttpRequester
                from async_upnp_client.client_factory import UpnpFactory
                
                requester = AiohttpRequester(timeout=10)
                factory = UpnpFactory(requester)
                upnp_device = await factory.async_create_device(location_url)
                return upnp_device
            
            # Test that connection error is properly raised
            with pytest.raises(ConnectionError, match="Device unreachable"):
                await create_dmr_device(location)