"""Nautobot job to verify hostname matches pattern."""
import re

from django.conf import settings
from nautobot.dcim.models import Device, Site
from nautobot.extras.jobs import Job, ObjectVar
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException


# Expected hostname regex pattern
HOSTNAME_PATTERN = re.compile(r"[a-z0-1]+\-[a-z]+\-\d+\.infra\.ntc\.com")
# Easy mapping of platform to device command
COMMAND_MAP = {
    "cisco_ios": "show run | include hostname",
    "cisco_nxos": "show run | include hostname",
    "arista_eos": "show run | include hostname",
    "juniper_junos": "show configuration system host-name",
}


class VerifyHostnameNoInput(Job):
    """Job without inputs."""

    # Specify a job input of a Dynamic Choice Field with all Sites
    site = ObjectVar(model=Site)

    class Meta:
        """Meta object boilerplate for intended."""

        name = "Verify Hostname Pattern For Any Site"
        description = "Checks all devices at any Site for configured hostname pattern."

    def run(self, data, commit):
        """Run method for executing the checks on the devices."""
        # Get Site instance based on job submission
        site = data.get("site")

        # Iterate through each Device object, limited to just the site of from job submission
        for device in Device.objects.filter(site=site):

            # Validate the Device has a primary IP set
            if not device.primary_ip:
                self.log_failure(device, "Missing Primary IP")
                # Skip to next iteration of the list
                continue

            # Validate the Device Platform is set and is supported by the script
            if not device.platform or not device.platform.slug in COMMAND_MAP:
                self.log_failure(device, "Check Platform slug supported device_types.")
                # Skip to next iteration of the list
                continue

            # Make sure to be able to gracefully catch an exception and log a failure
            try:
                # Build connection to Device
                with ConnectHandler(
                    device_type=device.platform.slug,
                    host=str(device.primary_ip.address.ip),
                    username=settings.NAPALM_USERNAME,
                    password=settings.NAPALM_PASSWORD,
                    conn_timeout=2,
                ) as conn:

                    # Send a Platform specific command to get configured hostname
                    hostname = conn.send_command(COMMAND_MAP[device.platform.slug])

                    # Remove any unneeded extra data from the return
                    hostname = re.sub(r"(host\-name|hostname|\s|\;|\n)", "", hostname)

                    # Check if the hostname matches the expected pattern
                    if HOSTNAME_PATTERN.match(hostname):
                        self.log_success(device, "Configured hostname is correct.")
                        # Skip to next iteration of the list
                        continue

                    # Mark the Device as failed in the job results
                    self.log_failure(device, "Does Not Match Hostname Pattern.")

            # Catch Authentication issue and log the failure
            except NetmikoAuthenticationException:
                self.log_failure(device, "Authentication error.")

            # Catch timeout issue and log the failure
            except NetmikoTimeoutException:
                self.log_failure(device, "Timeout error.")

            # Catch unaccounted issue and log the failure
            except:
                self.log_failure(device, "Unknown error.")
