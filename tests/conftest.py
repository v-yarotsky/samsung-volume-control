"""Test configuration and fixtures."""

import pytest
from homeassistant.components import ssdp
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.samsung_tv_volume.const import DOMAIN


@pytest.fixture
def mock_ssdp_info():
    """Mock SSDP discovery info for Samsung TV."""
    return ssdp.SsdpServiceInfo(
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