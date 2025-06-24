"""Test configuration and fixtures."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from homeassistant.helpers.service_info.ssdp import SsdpServiceInfo
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.samsung_tv_volume.const import DOMAIN


@pytest.fixture
def mock_ssdp_info():
    """Mock SSDP discovery info for Samsung TV."""
    return SsdpServiceInfo(
        ssdp_usn="uuid:08583b01-008c-1000-817d-bc148594dddb::urn:schemas-upnp-org:service:RenderingControl:1",
        ssdp_st="urn:schemas-upnp-org:service:RenderingControl:1",
        ssdp_location="http://192.168.1.219:7676/smp_14_",
        upnp={
            "deviceType": "urn:schemas-upnp-org:device:MediaRenderer:1",
            "friendlyName": "[TV]Samsung LED60",
            "manufacturer": "Samsung Electronics",
            "modelName": "UN60H7100",
            "UDN": "uuid:08583b01-008c-1000-817d-bc148594dddb"
        },
        ssdp_headers={
            "SERVER": "SHP, UPnP/1.0, Samsung UPnP SDK/1.0",
            "USN": "uuid:08583b01-008c-1000-817d-bc148594dddb::urn:schemas-upnp-org:service:RenderingControl:1"
        }
    )


@pytest.fixture
def mock_config_entry():
    """Mock config entry for Samsung TV."""
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id="uuid:08583b01-008c-1000-817d-bc148594dddb",
        data={
            "host": "192.168.1.219",
            "name": "[TV]Samsung LED60",
            "location": "http://192.168.1.219:7676/smp_14_",
            "udn": "uuid:08583b01-008c-1000-817d-bc148594dddb",
        },
    )


@pytest.fixture
def mock_upnp_device():
    """Create a mock UPnP device with pre-configured common methods."""
    device = MagicMock()
    device.device_info = {
        "friendly_name": "[TV]Samsung LED60",
        "manufacturer": "Samsung Electronics",
        "model_name": "UN60H7100",
        "udn": "uuid:08583b01-008c-1000-817d-bc148594dddb"
    }
    
    # Mock async methods with new API
    device.volume_level = 0.5  # 50% volume (0.0-1.0 range)
    device.async_set_volume_level = AsyncMock()
    
    return device


@pytest.fixture  
def mock_upnp_factory():
    """Mock the UPnP factory and related components."""
    with patch('custom_components.samsung_tv_volume.upnp_device.AiohttpRequester') as mock_requester_class, \
         patch('custom_components.samsung_tv_volume.upnp_device.UpnpFactory') as mock_factory_class, \
         patch('custom_components.samsung_tv_volume.upnp_device.DmrDevice') as mock_dmr_class:
        
        # Configure requester mock  
        requester_instance = AsyncMock()
        mock_requester_class.return_value = requester_instance
        
        # Configure factory mock
        factory_instance = AsyncMock()
        mock_factory_class.return_value = factory_instance
        
        # Configure UPnP device creation
        upnp_device = MagicMock()
        upnp_device.friendly_name = "[TV]Samsung LED60"
        upnp_device.manufacturer = "Samsung Electronics"
        upnp_device.model_name = "UN60H7100"
        upnp_device.model_number = "2014"
        upnp_device.serial_number = "12345"
        upnp_device.udn = "uuid:08583b01-008c-1000-817d-bc148594dddb"
        upnp_device.device_type = "urn:schemas-upnp-org:device:MediaRenderer:1"
        upnp_device.presentation_url = "http://192.168.1.219/"
        factory_instance.async_create_device.return_value = upnp_device
        
        # Configure DmrDevice mock
        dmr_device = AsyncMock()
        dmr_device.volume_level = 0.5  # 50% volume (0.0-1.0 range)
        dmr_device.async_set_volume_level = AsyncMock()
        mock_dmr_class.return_value = dmr_device
        
        yield {
            "factory": factory_instance,
            "requester": requester_instance, 
            "upnp_device": upnp_device,
            "dmr_device": dmr_device,
            "AiohttpRequester": mock_requester_class,
            "UpnpFactory": mock_factory_class,
            "DmrDevice": mock_dmr_class
        }