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
