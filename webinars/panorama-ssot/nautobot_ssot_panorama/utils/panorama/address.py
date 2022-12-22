"""AddressObject API."""
from panos.objects import AddressGroup, AddressObject

from .base import BaseAPI


class PanoramaAddress(BaseAPI):
    """Address Objects API SDK."""

    addresses = {}

    def _delete_instance(self, name):
        """Deletes an instance of an AddressObject or AddressGroup."""
        obj = self.addresses.pop(name)
        obj.delete()

    def get(self, name):
        """Returns a prefetched instance."""
        return self.addresses[name]["value"]

    #####################
    # AddressGroup
    #####################

    def create_address_group(
        self, name, grp_type, location=None, addrs=None, filter=None
    ):  # pylint: disable=redefined-builtin,too-many-arguments
        """Creates AddressGroup."""
        location = self._get_location(location)
        if grp_type == "static":
            group = AddressGroup(name, static_value=addrs)
        else:
            group = AddressGroup(name, dynamic_value=filter)
        location.add(group)
        group.create()
        self.addresses[group.name] = {
            "value": group,
            "type": "group",
            "location": "shared" if location == self.pano else location.name,
        }
        return group

    def retrieve_address_groups(self):
        """Returns all AddressGroups."""
        self.addresses.update(self._get_all_via_device_groups(AddressGroup, "group"))
        return self.addresses

    def update_address_group(self, name, grp_type, addrs=None, filter=None):  # pylint: disable=redefined-builtin
        """Updates a single AddressGroup."""
        group = self.get(name)
        if grp_type == "static":
            group.static_value = addrs
            group.dynamic_value = None
        else:
            group.dynamic_value = filter
            group.static_value = None
        group.apply()
        self.addresses[name]["value"] = group
        return group

    def delete_address_group(self, name):
        """Deletes a single AddressGroup."""
        self._delete_instance(name)

    #####################
    # AddressObject
    #####################

    def create_address_object(self, name, address, addr_type, location=None):
        """Creates AddressObject."""
        location = self._get_location(location)
        addr = AddressObject(name, value=address, type=addr_type)
        location.add(addr)
        addr.create()
        self.addresses[addr.name] = {
            "value": addr,
            "type": "object",
            "location": "shared" if location == self.pano else location.name,
        }
        return addr

    def retrieve_address_objects(self):
        """Returns all AddressObjects."""
        self.addresses.update(self._get_all_via_device_groups(AddressObject, "object"))
        return self.addresses

    def update_address_object(self, name, address=None, addr_type=None):
        """Updates AddressObject."""
        addr = self.get(name)
        if address:
            addr.value = address
        if addr_type:
            addr.type = addr_type
        addr.apply()
        self.addresses[name]["value"] = addr
        return addr

    def delete_address_object(self, name):
        """Deletes a single AddressObject."""
        self._delete_instance(name)
