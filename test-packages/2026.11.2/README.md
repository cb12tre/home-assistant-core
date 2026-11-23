# Experimental DHCP integrations for Home Assistant 2026.11.2

These custom integrations are experimental copies of the built-in AdGuard Home
and Huawei LTE integrations. They override the corresponding built-in domains.
They are for isolated testing only and have not been verified on physical
devices. They are not suitable for an unattended production installation.

Each integration adds a DHCP switch. The Huawei switch reads the current
settings before a write and checks the DHCP and DNS settings afterwards.
This check detects unexpected changes but does not undo them.

The copies are based on Home Assistant Core 2026.11.2. The developer changes
for contribution to Core are in the separate `adguard-dhcp-status` and
`huawei-dhcp-switch` branches.

The Italian translations mirror the existing Home Assistant installation and
add a name for the DHCP switch. English remains the fallback for missing keys.

## Physical-device test plan

Perform physical tests only with local access to the network, a recovery route
that does not rely on DHCP, and permission to restart Home Assistant. Take and
verify a Home Assistant backup first. Save the existing router and AdGuard
network settings, including gateway, DNS, pools and lease time. Confirm that the
two address pools and reservations cannot give out duplicate addresses.

Keep DHCP failover automations disabled throughout the test. Install one
experimental integration at a time and restart Home Assistant. First compare
the new switch state with the corresponding device web interface, without
operating the switch. Check the existing integration entities and logs. A
successful read is not proof that DHCP requests are being served.

Do not enable the Huawei DHCP server while AdGuard DHCP is active on the same
network. Do not test a write on either device until a separate controlled test
window and a network recovery plan are agreed. Turning off a DHCP server can
prevent clients from renewing their leases. Stop if an entity is unavailable,
the reported state differs from the device, or other network settings change.

To roll back, stop Home Assistant, remove or move only the experimental custom
integration directory that was installed, restore any previous directory from
backup, and restart Home Assistant. Confirm that the built-in integration and
its existing entities load again. This rollback does not restore router or
AdGuard settings: check those separately in their web interfaces.
