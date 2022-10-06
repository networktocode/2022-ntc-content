"""Add VLAN to Device."""
import os

from netmiko import ConnectHandler
import pynautobot
from rich import print as rich_print

# Easy mapping of platform to device command
COMMAND_MAP = {
    "cisco_ios": "interface %s\nswitchport trunk allowed vlan add %s",
    "cisco_nxos": "interface %s\nswitchport trunk allowed vlan add %s",
    "arista_eos": "interface %s\nswitchport trunk allowed vlan add %s",
    "juniper_junos": "set interfaces %s unit 0 family ethernet-switching vlan members %s",
}


def main():
    # Create PyNautobot API SDK Object
    nautobot = pynautobot.api(
        url=os.getenv("NAUTOBOT_URL"),
        token=os.getenv("NAUTOBOT_TOKEN"),
        api_version="1.4",
    )

    # Get list of sites and debug
    for site in nautobot.dcim.sites.all():
        print(site.slug)

    # Prompt for site selection
    site = input("Type a site slug: ")

    # Get list of devices limited based on site selection and debug
    for device in nautobot.dcim.devices.filter(site=site):
        print(device.name)

    # Prompt for device selection
    device = input("Type a device name: ")

    # Get list of devices limited based on device selection and debug
    for iface in nautobot.dcim.interfaces.filter(device=device):
        print(iface.name)

    # Prompt for device selection
    iface = input("Type an interface name: ")

    # Prompt for vlan selection
    vlan = input("Type vlan: ")

    # Get device instance from Nautobot
    device = nautobot.dcim.devices.get(name=device)

    # Make sure to be able to gracefully catch an exception and log a failure
    try:
        # Build connection to Device
        with ConnectHandler(
            device_type=device.platform.slug,
            host=device.primary_ip.address.split("/")[0],
            username=os.getenv("NETMIKO_USER"),
            password=os.getenv("NETMIKO_PASS"),
            conn_timeout=2,
        ) as conn:

            # Sends the string formatted configuration to the connected Device
            conn.send_config_set(COMMAND_MAP[device.platform.slug] % (iface, vlan))

            # If an excpetion is not raise the configuration was implemented successfully
            rich_print(
                f"[green]VLAN {vlan} successfully added to {iface} on {device.name}!"
            )

    # Catch exception and log the failure
    except:
        rich_print(
            f"[bold red]VLAN {vlan} failed to add to {iface} on {device.name}...."
        )
