"""ServiceObject API."""
from nautobot_firewall_models.choices import IP_PROTOCOL_CHOICES
from panos.objects import ServiceGroup, ServiceObject
from panos.predefined import Predefined

from .base import BaseAPI


class PanoramaService(BaseAPI):
    """Service Objects API SDK."""

    services = {}

    def _delete_instance(self, name):
        """Deletes an instance of an ServiceGroup or ServiceObject."""
        obj = self.services.pop(name)
        obj.delete()

    def get(self, name):
        """Returns a prefetched instance."""
        return self.services[name]["value"]

    def find_proper_protocol(self, desired_protocol):  # pylint: disable=no-self-use, inconsistent-return-statements
        """Returns Nautobot formatted protocol."""
        for protocol in IP_PROTOCOL_CHOICES:
            if protocol[0].lower() == desired_protocol.lower():
                return protocol[0]

    #####################
    # ServiceGroup
    #####################

    def create_service_group(self, name, svc_objs, location=None):
        """Creates ServiceObjects."""
        location = self._get_location(location)
        group = ServiceGroup(name, value=svc_objs)
        location.add(group)
        group.create()
        self.services[group.name] = {
            "value": group,
            "type": "group",
            "location": "shared" if location == self.pano else location.name,
        }
        return group

    def retrieve_service_groups(self):
        """Returns all ServiceGroups."""
        self.services.update(self._get_all_via_device_groups(ServiceGroup, "group"))
        return self.services

    def update_service_group(self, name, svc_objs):
        """Updates a single ServiceGroup."""
        group = self.get(name)
        group.value = svc_objs
        group.apply()
        self.services[name]["value"] = group
        return group

    def delete_service_group(self, name):
        """Deletes a single ServiceGroup."""
        self._delete_instance(name)

    #####################
    # ServiceObject
    #####################

    def create_service_object(self, name, port, protocol, location=None):
        """Creates ServiceObjects."""
        location = self._get_location(location)
        svc = ServiceObject(
            name,
            protocol=protocol.lower(),
            destination_port=port,
        )
        location.add(svc)
        svc.create()
        self.services[svc.name] = {
            "value": svc,
            "type": "object",
            "location": "shared" if location == self.pano else location.name,
        }
        return svc

    def retrieve_service_objects(self):
        """Returns all ServiceObjects."""
        predefined = Predefined(self.pano)
        predefined.refreshall_services()
        self.services.update(
            {
                name: {"value": svc, "type": "object", "location": "predefined"}
                for name, svc in predefined.service_objects.items()
            }
        )
        self.services.update(self._get_all_via_device_groups(ServiceObject, "object"))
        return self.services

    def update_service_object(self, name, port=None, protocol=None):
        """Updates a single ServiceObject."""
        if self.services[name]["location"] == "predefined":
            raise ValueError("Unable to update predefined service.")
        svc = self.get(name)
        if port:
            svc.destination_port = port
        if protocol:
            svc.protocol = protocol
        svc.apply()
        self.services[name]["value"] = svc
        return svc

    def delete_service_object(self, name):
        """Deletes a single ServiceObject."""
        if self.services[name]["location"] == "predefined":
            raise ValueError("Unable to delete predefined application")
        self._delete_instance(name)
