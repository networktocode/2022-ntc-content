"""Nautobot job to verify hostname matches pattern."""
import re

from django.conf import settings
from nautobot.dcim.models import Device
from nautobot.extras.jobs import Job
from netmiko import ConnectHandler

HOSTNAME_PATTERN = re.compile(r"[a-z0-1]+\-[a-z]+\-\d+\.infra\.ntc\.com")
COMMAND_MAP = {
    "cisco_ios": "show run | include hostname",
    "cisco_nxos": "show run | include hostname",
    "arista_eos": "show run | include hostname",
    "juniper_junos": "show configuration system host-name",
}


class VerifyHostnameNoInput(Job):
    """Job without inputs."""

    class Meta:
        """Meta object boilerplate for intended."""

        name = "Verify Hostname Pattern For NYC"
        description = "Checks all devices at NYC for configured hostname pattern."

    def run(self, data, commit):
        """Run method for executing the checks on the devices."""
        for device in Device.objects.filter(site__slug="nyc"):
            if not device.primary_ip:
                self.log_failure(device, "Missing Primary IP")
            if not device.platform or not device.platform.slug in COMMAND_MAP:
                self.log_failure(device, "Check Platform slug supported device_types.")
            try:
                with ConnectHandler(
                    device_type=device.platform.slug,
                    host=str(device.primary_ip.address.ip),
                    username=settings.NAPALM_USERNAME,
                    password=settings.NAPALM_USERNAME,
                    conn_timeout=2,
                ) as conn:
                    hostname = conn.send_command(COMMAND_MAP[device.platform.slug])
                    hostname = re.sub(r"(host\-name|hostname|\s|\;|\n)", "", hostname)
                    if HOSTNAME_PATTERN.match(hostname):
                        self.log_success(device, "Configured hostname is correct.")
                        continue
                    self.log_failure(device, "Does Not Match Hostname Pattern.")
            except NetmikoAuthenticationException:
                self.log_failure(device, "Authentication error.")
            except NetmikoTimeoutException:
                self.log_failure(device, "Timeout error.")
            except:
                self.log_failure(device, "Unknown error.")
