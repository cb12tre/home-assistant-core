"""Verify experimental DHCP packages load as custom integrations."""

import json
from pathlib import Path
import shutil

import pytest

from homeassistant import loader
from homeassistant.core import HomeAssistant

PACKAGES = Path(__file__).parent / "custom_components"


@pytest.mark.usefixtures("enable_custom_integrations")
@pytest.mark.parametrize("domain", ["adguard", "huawei_lte"])
async def test_custom_integration_loads(hass: HomeAssistant, domain: str) -> None:
    """Load the custom integration and its switch platform in isolation."""
    destination = Path(hass.config.path("custom_components")) / domain
    await hass.async_add_executor_job(
        lambda: shutil.copytree(PACKAGES / domain, destination, dirs_exist_ok=True)
    )
    hass.data.pop(loader.DATA_CUSTOM_COMPONENTS, None)

    integration = await loader.async_get_integration(hass, domain)
    assert not integration.is_built_in
    assert integration.version == "2026.11.2-dhcp-test"
    component = await integration.async_get_component()
    assert component.__name__ == f"custom_components.{domain}"
    platform = await integration.async_get_platform("switch")
    assert platform.__name__ == f"custom_components.{domain}.switch"
    translations = json.loads(
        await hass.async_add_executor_job(
            (destination / "translations" / "en.json").read_text, "utf-8"
        )
    )
    assert translations["entity"]["switch"]["dhcp"]["name"] == "DHCP server"
