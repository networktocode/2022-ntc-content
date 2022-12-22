"""DynamicUserGroup API."""
from panos.objects import DynamicUserGroup

from .base import BaseAPI


class PanoramaUser(BaseAPI):
    """DynamicUserGroup Objects API SDK."""

    users = {}

    #####################
    # DynamicUserGroup
    #####################

    def get(self, name):
        """Returns a prefetched instance."""
        return self.users[name]["value"]

    def create_dynamic_user_group(self, name, location=None):
        """Create DynamicUserGroup."""
        location = self._get_location(location)
        group = DynamicUserGroup(name)
        location.add(group)
        group.create()
        self.users[group.name] = {
            "value": group,
            "type": "group",
            "location": "shared" if location == self.pano else location.name,
        }
        return group

    def retrieve_dynamic_user_groups(self):
        """Returns all DynamicUserGroup."""
        self.users.update(self._get_all_via_device_groups(DynamicUserGroup, "group"))
        return self.users

    def update_dynamic_user_group(self):
        """Not implemented."""
        raise NotImplementedError("Not implemented.")

    def delete_dynamic_user_group(self, name):
        """Deletes an instance of an DynamicUserGroup."""
        obj = self.users.pop(name)
        obj.delete()
