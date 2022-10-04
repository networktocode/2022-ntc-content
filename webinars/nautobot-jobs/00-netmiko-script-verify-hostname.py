"""Gathers devices from nautobot, filtered by site and validates hostname pattern."""
import os
import re

import argparse
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException
import pynautobot
from pynautobot.core.query import RequestError
from rich import print as rich_print
from rich.table import Table


SUCCESS_STATUS = "[green]Success"
FAILED_STATUS = "[bold red]Failed"
HOSTNAME_PATTERN = re.compile(r"[a-z0-1]+\-[a-z]+\-\d+\.infra\.ntc\.com")
COMMAND_MAP = {
    "cisco_ios": "show run | include hostname",
    "cisco_nxos": "show run | include hostname",
    "arista_eos": "show run | include hostname",
    "juniper_junos": "show configuration system host-name",
}


def parse_args():
    """Parse commandline arguments & defaulted ENV variables."""
    parser = argparse.ArgumentParser(description="Parse connection credentials.")
    parser.add_argument(
        "-n",
        "--nautobot-url",
        dest="nautobot_url",
        required=True,
        help="Base Nautobot URL for PyNautobot, can be specified via environment variable NAUTOBOT_URL.",
        default=os.getenv("NAUTOBOT_URL"),
    )
    parser.add_argument(
        "-t",
        "--nautobot-token",
        dest="nautobot_token",
        required=True,
        help="Nautobot Token for PyNautobot, can be specified via environment variable NAUTOBOT_TOKEN.",
        default=os.getenv("NAUTOBOT_TOKEN"),
    )
    parser.add_argument(
        "-s",
        "--nautobot-site",
        dest="nautobot_site",
        required=True,
        help="Nautobot Site slug to limit scope of devices, defaults to `nyc`.",
        default="nyc",
    )
    parser.add_argument(
        "-u",
        "--netmiko-user",
        dest="netmiko_user",
        required=True,
        help="Username for connecting to remote devices, can be specified via environment variable NETMIKO_USER.",
        default=os.getenv("NETMIKO_USER"),
    )
    parser.add_argument(
        "-p",
        "--netmiko-pass",
        dest="netmiko_pass",
        required=True,
        help="Password for connecting to remote devices, can be specified via environment variable NETMIKO_PASS.",
        default=os.getenv("NETMIKO_PASS"),
    )
    return parser.parse_args()


def get_devices(nautobot, limit="nyc"):
    """Query Nautobot Devices API and limit to a single Site slug."""
    return nautobot.dcim.devices.filter(site=limit)


def verify_hostnames(devices, args):
    """Connect to devices, verify hostname pattern & matching Nautobot."""
    results_table = Table(title="Hostname Validation")
    results_table.add_column("Hostname", no_wrap=True)
    results_table.add_column("Status")
    results_table.add_column("Reason", no_wrap=True, justify="right")
    for device in devices:
        if not device.primary_ip:
            results_table.add_row(device.name, FAILED_STATUS, "Missing Primary IP")
            continue
        if not device.platform or not device.platform.slug in COMMAND_MAP:
            results_table.add_row(
                device.name,
                FAILED_STATUS,
                "Check Platform slug supported device_types.",
            )
            continue
        try:
            with ConnectHandler(
                device_type=device.platform.slug,
                host=device.primary_ip.address.split("/")[0],
                username=args.netmiko_user,
                password=args.netmiko_pass,
                conn_timeout=2,
            ) as conn:
                hostname = conn.send_command(COMMAND_MAP[device.platform.slug])
                hostname = re.sub(r"(host\-name|hostname|\s|\;|\n)", "", hostname)
                if HOSTNAME_PATTERN.match(hostname):
                    results_table.add_row(device.name, SUCCESS_STATUS, "")
                    continue
                results_table.add_row(
                    device.name, FAILED_STATUS, "Does Not Match Hostname Pattern."
                )
        except NetmikoAuthenticationException:
            results_table.add_row(device.name, FAILED_STATUS, "Authentication error.")
        except NetmikoTimeoutException:
            results_table.add_row(device.name, FAILED_STATUS, "Timeout error.")
    return results_table


def main(args):
    try:
        nautobot = pynautobot.api(
            url=args.nautobot_url, token=args.nautobot_token, api_version="1.4"
        )
        devices = get_devices(nautobot, limit=args.nautobot_site)
        results = verify_hostnames(devices, args)
        rich_print(results)
    except RequestError:
        rich_print(
            f"[bold red]Failure occured retrieving devices from Nautobot, please validate specified site `{args.nautobot_site}`."
        )


if __name__ == "__main__":
    args = parse_args()
    main(args)
