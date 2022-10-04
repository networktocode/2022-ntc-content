"""Add VLAN to Device."""
import os

from netmiko import ConnectHandler
import pynautobot
from rich import print as rich_print


COMMAND_MAP = {
    "cisco_ios": "interface %s\nswitchport trunk allowed vlan add %s",
    "cisco_nxos": "interface %s\nswitchport trunk allowed vlan add %s",
    "arista_eos": "interface %s\nswitchport trunk allowed vlan add %s",
    "juniper_junos": "set interfaces %s unit 0 family ethernet-switching vlan members %s",
}


def main():
    nautobot = pynautobot.api(
        url=os.getenv("NAUTOBOT_URL"),
        token=os.getenv("NAUTOBOT_TOKEN"),
        api_version="1.4",
    )
    for site in nautobot.dcim.sites.all():
        print(site.slug)
    site = input("Type a site slug: ")
    for device in nautobot.dcim.devices.filter(site=site):
        print(device.name)
    device = input("Type a device name: ")
    for iface in nautobot.dcim.interfaces.filter(device=device):
        print(iface.name)
    iface = input("Type an interface name: ")
    vlan = input("Type vlan: ")
    device = nautobot.dcim.devices.get(name=device)
    try:
        with ConnectHandler(
            device_type=device.platform.slug,
            host=device.primary_ip.address.split("/")[0],
            username=os.getenv("NETMIKO_USER"),
            password=os.getenv("NETMIKO_PASS"),
            conn_timeout=2,
        ) as conn:
            conn.send_config(COMMAND_MAP[device.platform.slug] % (iface, vlan))
            rich_print(
                f"[green]VLAN {vlan} successfully added to {iface} on {device.name}!"
            )
    except:
        rich_print(
            f"[bold red]VLAN {vlan} failed to add to {iface} on {device.name}...."
        )


if __name__ == "__main__":
    main()
