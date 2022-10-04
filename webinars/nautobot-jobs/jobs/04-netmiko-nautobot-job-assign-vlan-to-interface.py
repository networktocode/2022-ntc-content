"""Add VLAN to Device."""
from django.conf import settings
from nautobot.dcim.models import Device, Site, Interface
from nautobot.extras.jobs import Job, ObjectVar, StringVar
from netmiko import ConnectHandler


COMMAND_MAP = {
    "cisco_ios": "interface %s\nswitchport trunk allowed vlan add %s",
    "cisco_nxos": "interface %s\nswitchport trunk allowed vlan add %s",
    "arista_eos": "interface %s\nswitchport trunk allowed vlan add %s",
    "juniper_junos": "set interfaces %s unit 0 family ethernet-switching vlan members %s",
}


class VerifyHostnameNoInput(Job):
    """Job without inputs."""

    site = ObjectVar(model=Site)
    device = ObjectVar(model=Device, query_params={"site_id": "$site"})
    iface = ObjectVar(model=Interface, query_params={"device_id": "$device"})
    vlan = StringVar()

    class Meta:
        """Meta object boilerplate for intended."""

        name = "Add VLAN to an Interface"
        description = "Configures the specificed VLAN on an Interface."

    def run(self, data, commit):
        """Run method for implementing VLAN on an Interface."""
        iface = data.get("iface")
        vlan = data.get("vlan")
        device = data.get("device")
        try:
            with ConnectHandler(
                device_type=device.platform.slug,
                host=device.primary_ip.address.split("/")[0],
                username=settings.NAPALM_USERNAME,
                password=settings.NAPALM_USERNAME,
                conn_timeout=2,
            ) as conn:
                conn.send_config(COMMAND_MAP[device.platform.slug] % (iface, vlan))
                self.log_success(
                    iface, f"Successfully added to {iface.name} on {device.name}!"
                )
        except:
            self.log_success(
                iface, f"VLAN {vlan} failed to add to {iface.name} on {device.name}...."
            )
