"""DeviceGroup API."""
from panos.panorama import DeviceGroup, DeviceGroupHierarchy, PanoramaDeviceGroupHierarchy

from .base import BaseAPI


class PanoramaDeviceGroup(BaseAPI):
    """DeviceGroup Objects API SDK."""

    def get(self, name):
        """Returns a prefetched instance."""
        return self.device_groups[name]["value"]

    def get_parent(self, name):
        """Returns parent DeviceGroup name."""
        return PanoramaDeviceGroupHierarchy(self.pano).fetch().get(name)

    def create_device_group(self, name, parent=None):
        """Creates a DeviceGroup."""
        dev_group = DeviceGroup(name)
        self.pano.add(dev_group)
        dev_group.create()
        self.device_groups[name] = dev_group
        if parent:
            if not self.device_groups.get(parent):
                parent_dg = DeviceGroup(parent)
                self.pano.add(parent_dg)
                parent_dg.create()
                self.device_groups[parent] = parent_dg
            dgh = DeviceGroupHierarchy(dev_group)
            dgh.parent = parent
            dgh.update()
        return dev_group

    def retrieve_device_groups(self):
        """Returns all DeviceGroups."""
        self.device_groups = {i.name: i for i in self.pano.refresh_devices() if isinstance(i, DeviceGroup)}
        return self.device_groups

    def update_device_group(self, name, parent):
        """Updates a DeviceGroup."""
        dgh = DeviceGroupHierarchy(self.get(name))
        dgh.parent = parent
        dgh.update()
        return self.get(name)

    def delete_device_group(self, name):
        """Deletes a DeviceGroup."""
        dev_group = self.get(name)
        dev_group.delete()
