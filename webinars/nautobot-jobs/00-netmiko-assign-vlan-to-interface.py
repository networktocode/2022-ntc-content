"""Add VLAN to Device."""
import os

import argparse
from netmiko import ConnectHandler
import pynautobot
from rich import print as rich_print


COMMAND_MAP = {
    "cisco_ios": "interface %s\nswitchport trunk allowed vlan add %s",
    "cisco_nxos": "interface %s\nswitchport trunk allowed vlan add %s",
    "arista_eos": "interface %s\nswitchport trunk allowed vlan add %s",
    "juniper_junos": "set interfaces %s unit 0 family ethernet-switching vlan members %s",
}


def parse_args():
    """Parse commandline arguments & defaulted ENV variables."""
    parser = argparse.ArgumentParser(description="Parse connection credentials.")
    parser.add_argument(
        "-n",
        "--nautobot-url",
        dest="nautobot_url",
        required=True,
        help="Base Nautobot URL for PyNautobot.",
        default=os.getenv("NAUTOBOT_URL"),
    )
    parser.add_argument(
        "-t",
        "--nautobot-token",
        dest="nautobot_token",
        required=True,
        help="Nautobot Token for PyNautobot.",
        default=os.getenv("NAUTOBOT_TOKEN"),
    )
    parser.add_argument(
        "-u",
        "--netmiko-user",
        dest="netmiko_user",
        required=True,
        help="Username for connecting to remote devices.",
        default=os.getenv("NETMIKO_USER"),
    )
    parser.add_argument(
        "-p",
        "--netmiko-pass",
        dest="netmiko_pass",
        required=True,
        help="Password for connecting to remote devices.",
        default=os.getenv("NETMIKO_PASS"),
    )
    return parser.parse_args()


def list_devices(nautobot, limit="nyc"):
    """Display list of devices for a site."""
    for device in nautobot.dcim.devices.filter(site=limit):
        print(device.name)


def list_sites(nautobot):
    """Display a list of site slugs."""
    for site in nautobot.dcim.sites.all():
        print(site.slug)


def list_interfaces(nautobot, limit=None):
    """Display list of interfaces for a Device."""
    for iface in nautobot.dcim.interfaces.filter(device=limit):
        print(iface.name)


def main(args):
    nautobot = pynautobot.api(
        url=args.nautobot_url, token=args.nautobot_token, api_version="1.4"
    )
    list_sites(nautobot)
    site = input("Type a site slug: ")
    list_devices(nautobot, limit=site)
    device = input("Type a device name: ")
    list_interfaces(nautobot, limit=device)
    iface = input("Type an interface name: ")
    vlan = input("Type vlan: ")
    device = nautobot.dcim.devices.get(name=device)
    try:
        with ConnectHandler(
            device_type="juniper_junos",
            host=device.primary_ip.address.split("/")[0],
            username=args.netmiko_user,
            password=args.netmiko_pass,
            conn_timeout=2,
        ) as conn:
            conn.send_config(COMMAND_MAP[device.platform.slug] % iface, vlan)
            rich_print(
                f"[green]VLAN {vlan} successfully added to {iface} on {device.name}!"
            )
    except:
        rich_print(
            f"[bold red]VLAN {vlan} failed to add to {iface} on {device.name}...."
        )


if __name__ == "__main__":
    args = parse_args()
    main(args)
