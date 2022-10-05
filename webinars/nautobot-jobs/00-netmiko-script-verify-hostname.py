"""Gathers devices from nautobot, filtered by site and validates hostname pattern."""
import os
import re

from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException
import pynautobot
from rich import print as rich_print
from rich.table import Table

# Colorized statuses
SUCCESS_STATUS = "[green]Success"
FAILED_STATUS = "[bold red]Failed"
# Expected hostname regex pattern
HOSTNAME_PATTERN = re.compile(r"[a-z0-1]+\-[a-z]+\-\d+\.infra\.ntc\.com")
# Easy mapping of platform to device command
COMMAND_MAP = {
    "cisco_ios": "show run | include hostname",
    "cisco_nxos": "show run | include hostname",
    "arista_eos": "show run | include hostname",
    "juniper_junos": "show configuration system host-name",
}


def verify_hostnames(devices):
    """Connect to devices, verify hostname pattern & matching Nautobot."""
    # Start a results Table object
    results_table = Table(title="Hostname Validation")
    results_table.add_column("Hostname", no_wrap=True)
    results_table.add_column("Status")
    results_table.add_column("Reason", no_wrap=True, justify="right")

    # Iterate through each Device object, limited to just the site of NYC.
    for device in devices:

        # Validate the Device has a primary IP set
        if not device.primary_ip:
            results_table.add_row(device.name, FAILED_STATUS, "Missing Primary IP")
            # Skip to next iteration of the list
            continue

        # Validate the Device Platform is set and is supported by the script
        if not device.platform or not device.platform.slug in COMMAND_MAP:
            results_table.add_row(
                device.name,
                FAILED_STATUS,
                "Check Platform slug supported device_types.",
            )
            # Skip to next iteration of the list
            continue

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

                # Send a Platform specific command to get configured hostname
                hostname = conn.send_command(COMMAND_MAP[device.platform.slug])

                # Remove any unneeded extra data from the return
                hostname = re.sub(r"(host\-name|hostname|\s|\;|\n)", "", hostname)

                # Check if the hostname matches the expected pattern
                if HOSTNAME_PATTERN.match(hostname):
                    results_table.add_row(device.name, SUCCESS_STATUS, "")
                    # Skip to next iteration of the list
                    continue

                # Mark the Device as failed in the job results
                results_table.add_row(
                    device.name, FAILED_STATUS, "Does Not Match Hostname Pattern."
                )

        # Catch Authentication issue and log the failure
        except NetmikoAuthenticationException:
            results_table.add_row(device.name, FAILED_STATUS, "Authentication error.")

        # Catch timeout issue and log the failure
        except NetmikoTimeoutException:
            results_table.add_row(device.name, FAILED_STATUS, "Timeout error.")

        # Catch unaccounted issue and log the failure
        except:
            results_table.add_row(device.name, FAILED_STATUS, "Unknown error.")

    # Return the table that was built
    return results_table


def main():
    # Create PyNautobot API SDK Object
    nautobot = pynautobot.api(
        url=os.getenv("NAUTOBOT_URL"),
        token=os.getenv("NAUTOBOT_TOKEN"),
        api_version="1.4",
    )

    # Query nautobot via pynautobot SDK and limit to just NYC
    devices = nautobot.dcim.devices.filter(site="nyc")

    # Call function to connect to devices and perform check
    results = verify_hostnames(devices)

    # Send colorized results to terminal
    rich_print(results)


if __name__ == "__main__":
    main()
