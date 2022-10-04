"""Gathers devices from nautobot, filtered by site and validates hostname pattern."""
import os
import re

from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException
import pynautobot
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


def verify_hostnames(devices):
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
                username=os.getenv("NETMIKO_USER"),
                password=os.getenv("NETMIKO_PASS"),
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


def main():
    nautobot = pynautobot.api(
        url=os.getenv("NAUTOBOT_URL"),
        token=os.getenv("NAUTOBOT_TOKEN"),
        api_version="1.4",
    )
    devices = nautobot.dcim.devices.filter(site="nyc")
    results = verify_hostnames(devices)
    rich_print(results)


if __name__ == "__main__":
    main()
