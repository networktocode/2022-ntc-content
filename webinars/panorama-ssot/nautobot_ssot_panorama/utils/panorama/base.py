"""Base API SDK Class."""
from panos.panorama import DeviceGroup


class BaseAPI:  # pylint: disable=too-few-public-methods
    """Create a base API for reuse."""

    def __init__(self, panorama, device_groups, job=None):
        """Init object with panorama instnace, job, & device group."""
        self.pano = panorama
        self.device_groups = device_groups
        self.job = job

    def _get_all_via_device_groups(self, obj_class, obj_type):
        output = {}
        for group in self.device_groups.values():
            for obj in obj_class.refreshall(group):
                output[obj.name] = {"value": obj, "type": obj_type, "location": group.name}
        for obj in obj_class.refreshall(self.pano):
            output[obj.name] = {"value": obj, "type": obj_type, "location": "shared"}
        return output

    def _get_location(self, location):
        if not location:
            return self.pano
        if isinstance(location, str):
            return self.device_groups[location]
        if isinstance(location, DeviceGroup):
            return location
        raise ValueError("Invalid location.")
