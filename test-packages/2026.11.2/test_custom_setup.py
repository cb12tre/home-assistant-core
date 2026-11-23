"""Exercise experimental custom integrations with simulated devices."""

from dataclasses import replace
from datetime import timedelta
from pathlib import Path
import shutil
from unittest.mock import AsyncMock, MagicMock, patch

from adguardhome import AdGuardHomeError, DhcpConfig
from freezegun.api import FrozenDateTimeFactory
import pytest
from pytest_homeassistant.common import MockConfigEntry, async_fire_time_changed

from homeassistant import loader
from homeassistant.const import ATTR_ENTITY_ID, CONF_URL, STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from tests.components.huawei_lte import magic_client  # noqa: TID251

PACKAGES = Path(__file__).parent / "custom_components"
pytest_plugins = ["tests.components.adguard.conftest"]


async def install_custom(hass: HomeAssistant, domain: str) -> None:
    """Make one experimental integration available to the isolated instance."""
    destination = Path(hass.config.path("custom_components")) / domain
    await hass.async_add_executor_job(
        lambda: shutil.copytree(PACKAGES / domain, destination, dirs_exist_ok=True)
    )
    hass.data.pop(loader.DATA_CUSTOM_COMPONENTS, None)
    integration = await loader.async_get_integration(hass, domain)
    assert not integration.is_built_in
    await integration.async_get_component()


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_adguard_custom_setup_and_commands(
    hass: HomeAssistant,
    mock_adguard: AsyncMock,
    mock_config_entry: MockConfigEntry,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Set up the custom AdGuard entry and control simulated DHCP."""
    await install_custom(hass, "adguard")
    mock_adguard.status.return_value = replace(
        mock_adguard.status.return_value, dhcp_available=True
    )
    mock_adguard.dhcp = AsyncMock()
    enabled = {"value": False}
    mock_adguard.dhcp.config.side_effect = lambda: DhcpConfig(
        enabled=enabled["value"]
    )

    async def turn_on() -> None:
        enabled["value"] = True

    async def turn_off() -> None:
        enabled["value"] = False

    mock_adguard.dhcp.enable.side_effect = turn_on
    mock_adguard.dhcp.disable.side_effect = turn_off
    mock_config_entry.add_to_hass(hass)
    with patch("custom_components.adguard.AdGuardHome", return_value=mock_adguard):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    entity_id = "switch.adguard_home_dhcp_server"
    assert hass.states.is_state(entity_id, STATE_OFF), [
        (state.entity_id, state.state) for state in hass.states.async_all("switch")
    ]
    await hass.services.async_call(
        "switch", "turn_on", {ATTR_ENTITY_ID: entity_id}, blocking=True
    )
    await hass.async_block_till_done()
    assert hass.states.is_state(entity_id, STATE_ON)
    await hass.services.async_call(
        "switch", "turn_off", {ATTR_ENTITY_ID: entity_id}, blocking=True
    )
    freezer.tick(timedelta(seconds=30))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert hass.states.is_state(entity_id, STATE_OFF)

    mock_adguard.dhcp.enable.side_effect = AdGuardHomeError("simulated failure")
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            "switch", "turn_on", {ATTR_ENTITY_ID: entity_id}, blocking=True
        )
    assert hass.states.is_state(entity_id, STATE_OFF)


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_huawei_custom_setup_and_commands(hass: HomeAssistant) -> None:
    """Set up the custom Huawei entry and control simulated DHCP."""
    await install_custom(hass, "huawei_lte")
    client = magic_client()
    settings = {
        "DhcpStatus": "0",
        "DhcpIPAddress": "10.0.0.1",
        "DhcpLanNetmask": "255.255.0.0",
        "DhcpStartIPAddress": "10.0.1.10",
        "DhcpEndIPAddress": "10.0.2.20",
        "DhcpLeaseTime": "86400",
        "DnsStatus": "0",
        "PrimaryDns": "1.1.1.1",
        "SecondaryDns": "8.8.8.8",
    }
    original = settings.copy()
    client.dhcp.settings.side_effect = lambda: settings.copy()
    connection = MagicMock()

    def write_settings(endpoint: str, data: dict[str, str]) -> None:
        assert endpoint == "dhcp/settings"
        settings.update(data)

    connection.post_set.side_effect = write_settings
    entry = MockConfigEntry(domain="huawei_lte", data={CONF_URL: "http://router"})
    entry.add_to_hass(hass)
    with (
        patch("custom_components.huawei_lte.Connection", return_value=connection),
        patch("custom_components.huawei_lte.Client", return_value=client),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    entity_id = "switch.test_router_dhcp_server"
    assert hass.states.is_state(entity_id, STATE_OFF)
    await hass.services.async_call(
        "switch", "turn_on", {ATTR_ENTITY_ID: entity_id}, blocking=True
    )
    await hass.async_block_till_done()
    assert hass.states.is_state(entity_id, STATE_ON)
    await hass.services.async_call(
        "switch", "turn_off", {ATTR_ENTITY_ID: entity_id}, blocking=True
    )
    await hass.async_block_till_done()
    assert hass.states.is_state(entity_id, STATE_OFF)
    assert settings == original

    connection.post_set.side_effect = HomeAssistantError("simulated failure")
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            "switch", "turn_on", {ATTR_ENTITY_ID: entity_id}, blocking=True
        )
    assert hass.states.is_state(entity_id, STATE_OFF)
