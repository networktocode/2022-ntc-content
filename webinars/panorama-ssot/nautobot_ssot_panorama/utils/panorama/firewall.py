"""Zone API."""
from panos.network import Zone
from panos.device import Vsys, SystemSettings
from panos.errors import PanDeviceXapiError
from panos.firewall import Firewall

from .base import BaseAPI


class PanoramaFirewall(BaseAPI):
    """Firewall Zone Vsys Objects API SDK."""

    zones = {}
    firewalls = {}
    vsys = {}

    #####################
    # Firewall
    #####################

    def get_firewall(self, serial):
        """Returns a prefetched instance."""
        return self.firewalls[serial]["value"]

    def get_hostname(self, firewall: "Firewall") -> str:  # pylint: disable=no-self-use
        """Returns a firewall's hostname if reachable else serial.

        Args:
            firewall (Firewall): panos.firewall.Firewall instance

        Returns:
            str: Hostname or serial
        """
        try:
            return SystemSettings.refreshall(firewall)[0].hostname
        except PanDeviceXapiError:
            return firewall.serial

    def retrieve_firewalls(self):
        """Returns all Firewalls."""
        for d_g in self.device_groups.values():
            for firewall in d_g.children:
                if not isinstance(firewall, Firewall):
                    continue
                self.firewalls[firewall.serial] = firewall
        return self.firewalls

    def create_firewall(self, serial, group):
        """Create Firewall."""
        firewall = Firewall(serial=serial)
        self.device_groups[group].add(firewall)
        self.pano.add(firewall)
        firewall.create()
        self.firewalls[firewall.serial] = firewall
        return firewall

    def update_firewall(self):
        """Update Firewall."""
        raise NotImplementedError("Not implemented.")

    def delete_firewall(self, serial):
        """Deletes an instance of a Firewall."""
        obj = self.firewalls.pop(serial)
        obj.delete()
        self.zones.pop(serial)
        self.vsys.pop(serial)

    #####################
    # Vsys
    #####################

    def get_vsys(self, firewall, vsys):
        """Returns a prefetched instance."""
        return self.vsys[firewall][vsys]

    def retrieve_vsys(self):
        """Returns all Vsys."""
        for d_g in self.device_groups.values():
            for firewall in d_g.children:
                if not isinstance(firewall, Vsys):
                    continue
                self.vsys[firewall.serial] = {}
                for vsys in Vsys.refreshall(firewall):
                    self.vsys[firewall.serial][vsys.name] = vsys
        return self.vsys

    def create_vsys(self, serial, name):
        """Returns all Vsys."""
        firewall = self.get_firewall(serial)
        vsys = Vsys(name)
        firewall.add(vsys)
        vsys.create()
        self.vsys[serial][name] = vsys
        return vsys

    def update_vsys(self):
        """Returns all Vsys."""
        raise NotImplementedError("Not implemented.")

    def delete_vsys(self, serial, vsys):
        """Returns all Vsys."""
        vsys = self.vsys[serial][vsys]
        vsys.delete()

    #####################
    # Zone
    #####################

    def get_zone(self, firewall, name):
        """Returns a prefetched instance."""
        return self.zones[firewall][name]["value"]

    def retrieve_zones(self):
        """Returns all Zones."""
        for d_g in self.device_groups.values():
            for firewall in d_g.children:
                if not isinstance(firewall, Firewall):
                    continue
                try:
                    for zone in Zone.refreshall(firewall):
                        if not zone.interface:
                            continue
                        if not self.zones.get(firewall.serial):
                            self.zones[firewall.serial] = {zone.name: zone}
                        else:
                            self.zones[firewall.serial][zone.name] = zone
                except PanDeviceXapiError:
                    pass
        return self.zones

    def create_zone(
        self,
        name,
        firewall,
        ifaces,
    ):
        """Create Zone."""
        zone = Zone(name=name, mode="layer3", interface=ifaces)
        self.firewalls[firewall]["value"].add(zone)
        zone.create()

        if self.zones.get(firewall):
            self.zones[firewall] = {}
        self.zones[firewall][zone.name] = zone
        return zone

    def update_zone(
        self,
        name,
        firewall,
        ifaces,
    ):
        """Update Zone."""
        zone = self.get_zone(firewall, name)
        zone.interface = ifaces
        zone.apply()
        self.zones[firewall][zone.name] = zone

    def delete_zone(self, name, firewall):
        """Deletes an instance of a Zone."""
        obj = self.zones[firewall].pop(name)
        obj.delete()
