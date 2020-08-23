"""The tests for the surepetcare binary sensor platform."""
from typing import Any, Dict, Optional

from homeassistant.components.surepetcare.const import DOMAIN
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.setup import async_setup_component

from tests.async_mock import patch

CONFIG = {
    DOMAIN: {
        CONF_USERNAME: "test-username",
        CONF_PASSWORD: "test-password",
        "feeders": [12345],
        "flaps": [13579],
        "pets": [24680],
    },
}

HOUSEHOLD_ID = "household-id"
HUB_ID = "hub-id"

MOCK_HUB = {
    "id": HUB_ID,
    "product_id": 1,
    "household_id": HOUSEHOLD_ID,
    "name": "Hub",
    "status": {
        "online": "UNDEF",
        "led_mode": "UNDEF",
        "pairing_mode": "UNDEF",
    },
}

MOCK_FEEDER = {
    "id": 12345,
    "product_id": 4,
    "household_id": HOUSEHOLD_ID,
    "name": "Feeder",
    "status": {
        "signal": {
            "device_rssi": "60",
            "hub_rssi": "65",
        },
    },
}

MOCK_CAT_FLAP = {
    "id": 13579,
    "product_id": 6,
    "household_id": HOUSEHOLD_ID,
    "name": "Cat Flap",
    "status": {
        "signal": {
            "device_rssi": "65",
            "hub_rssi": "65",,
        },
    },
}

MOCK_PET_FLAP = {
    "id": 13576,
    "product_id": 3,
    "household_id": HOUSEHOLD_ID,
    "name": "Pet Flap",
    "status": {
        "signal": {
            "device_rssi": "70",
            "hub_rssi": "65",
        },
    },
}

MOCK_PET = {
    "id": 24680,
    "household_id": HOUSEHOLD_ID,
    "name": "Pet",
    "position": {
        "since": "2020-08-23T23:10:50+0000",
        "where": 1,
    },
    "status": "UNDEF",
}

MOCK_API_DATA = {
    "devices": [MOCK_HUB, MOCK_CAT_FLAP, MOCK_PET_FLAP, MOCK_FEEDER],
    "pets": [MOCK_PET],
}


async def test_unique_ids(hass) -> None:
    """Test the generation of unique ids."""
    with _patch_api_get_data(MOCK_API_DATA), _patch_api_data_property(
        MOCK_API_DATA
    ), _patch_sensor_setup():
        assert await async_setup_component(hass, DOMAIN, CONFIG)

    assert hass.states.get("binary_sensor.hub_hub")

    assert hass.states.get("binary_sensor.cat_flap_cat_flap")
    assert hass.states.get("binary_sensor.cat_flap_cat_flap_connectivity")

    assert hass.states.get("binary_sensor.pet_flap_pet_flap")
    assert hass.states.get("binary_sensor.pet_flap_pet_flap_connectivity")

    assert hass.states.get("binary_sensor.feeder_feeder")
    assert hass.states.get("binary_sensor.feeder_feeder_connectivity")

    assert hass.states.get("binary_sensor.pet_pet")


def _patch_api_data_property(return_value: Optional[Dict[str, Any]] = None):
    return patch(
        "homeassistant.components.surepetcare.SurePetcare.data",
        return_value=return_value,
    )


def _patch_api_get_data(return_value: Optional[Dict[str, Any]] = None):
    return patch(
        "homeassistant.components.surepetcare.SurePetcare.get_data",
        return_value=return_value,
    )


def _patch_sensor_setup():
    return patch(
        "homeassistant.components.surepetcare.sensor.async_setup_platform",
        return_value=True,
    )
