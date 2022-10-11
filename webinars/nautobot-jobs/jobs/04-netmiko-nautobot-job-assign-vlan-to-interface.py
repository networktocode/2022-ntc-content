"""Add VLAN to Device."""
from django.conf import settings
from nautobot.dcim.models import Device, Site, Interface
from nautobot.extras.jobs import Job, ObjectVar, StringVar
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException


# Easy mapping of platform to device command
COMMAND_MAP = {
    "cisco_nxos": "interface %s\nswitchport access vlan %s",
    "arista_eos": "interface %s\nswitchport access vlan %s",
}


class VerifyHostnameNoInput(Job):
    """Job without inputs."""

    # Specify a job input of a Dynamic Choice Field with all Sites
    site = ObjectVar(model=Site)

    # Specify a job input of a Dynamic Choice Field with all Device, limited based on Site selection
    device = ObjectVar(model=Device, query_params={"site_id": "$site"})

    # Specify a job input of a Dynamic Choice Field with all Interface, limited based on Device selection
    iface = ObjectVar(model=Interface, query_params={"device_id": "$device"})

    # Specify a job input VLAN to be implemented
    vlan = StringVar()

    class Meta:
        """Meta object boilerplate for intended."""

        name = "Add VLAN to an Interface"
        description = "Configures the specificed VLAN on an Interface."

    def run(self, data, commit):
        """Run method for implementing VLAN on an Interface."""
        # Parse job submission data
        iface = data.get("iface")
        vlan = data.get("vlan")
        device = data.get("device")

        # Validate the Device has a primary IP set
        if not device.primary_ip:
            self.log_failure(device, "Missing Primary IP")
            # Skip to next iteration of the list
            continue

        # Validate the Device Platform is set and is supported by the script
        if not device.platform or not device.platform.slug in COMMAND_MAP:
            self.log_failure(device, "Not supported on routers. Check Platform slug supported device_types.")
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

                # Sends the string formatted configuration to the connected Device
                conn.send_config_set(COMMAND_MAP[device.platform.slug] % (iface, vlan))

                # If an excpetion is not raise the configuration was implemented successfully
                self.log_success(
                    iface, f"Successfully added to {iface.name} on {device.name}!"
                )

        # Catch exception and log the failure
        except:
            self.log_success(
                iface, f"VLAN {vlan} failed to add to {iface.name} on {device.name}...."
            )
