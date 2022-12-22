"""ApplicationObject API."""
from panos.objects import ApplicationGroup, ApplicationObject
from panos.predefined import Predefined

from .base import BaseAPI


class PanoramaApplication(BaseAPI):
    """Application Objects API SDK."""

    applications = {}

    def _delete_instance(self, name):
        """Deletes an instance of an ApplicationGroup or ApplicationObject."""
        obj = self.applications.pop(name)
        obj.delete()

    def get(self, name):
        """Returns a prefetched instance."""
        return self.applications[name]["value"]

    #####################
    # ApplicationGroup
    #####################

    def create_application_group(self, location=None, name=None, applications=None):
        """Create ApplicationGroup."""
        location = self._get_location(location)
        group = ApplicationGroup(name, value=applications)
        location.add(group)
        group.create()
        self.applications[group.name] = {
            "value": group,
            "type": "group",
            "location": "shared" if location == self.pano else location.name,
        }
        return group

    def retrieve_application_groups(self):
        """Returns all ApplicationGroups."""
        self.applications.update(self._get_all_via_device_groups(ApplicationGroup, "group"))
        return self.applications

    def update_application_group(self, name, applications):
        """Updates a single instance of an applicationgroup."""
        group = self.applications[name]["value"]
        group.value = applications
        group.apply()
        self.applications[name]["value"] = group
        return group

    def delete_application_group(self, name):
        """Deletes a single ApplicationGroup."""
        self._delete_instance(name)

    #####################
    # ApplicationObject
    #####################

    def create_application_object(
        self,
        name,
        category,
        subcategory,
        technology,
        risk,
        default_ports,
        default_ip_protocol,
        description,
        default_type="port",
        location=None,
    ):  # pylint: disable=too-many-arguments
        """Creates ApplicationObject."""
        location = self._get_location(location)
        app = ApplicationObject(
            name,
            category=category,
            subcategory=subcategory,
            technology=technology,
            risk=risk,
            default_ports=default_ports,
            default_ip_protocol=default_ip_protocol,
            description=description,
            default_port=default_ports,
            default_type=default_type,
        )
        location.add(app)
        app.create()
        self.applications[app.name] = {
            "value": app,
            "type": "object",
            "location": "shared" if location == self.pano else location.name,
        }
        return app

    def retrieve_application_objects(self):
        """Returns all ApplicationObjects."""
        predefined = Predefined(self.pano)
        predefined.refreshall_applications()
        self.applications.update(
            {
                name: {"value": app, "type": "object", "location": "predefined"}
                for name, app in predefined.application_objects.items()
            }
        )
        self.applications.update(
            {
                name: {"value": app, "type": "container", "location": "predefined"}
                for name, app in predefined.application_container_objects.items()
            }
        )

        self.applications.update(self._get_all_via_device_groups(ApplicationObject, "object"))
        return self.applications

    def update_application_object(self, name, **kwargs):
        """Updates a single ApplicationObject."""
        if self.applications[name]["location"] == "predefined":
            raise ValueError("Unable to update predefined application")
        app = self.applications[name]["value"]
        for attr, value in kwargs.items():
            if hasattr(app, attr):
                setattr(app, attr, value)
            else:
                raise ValueError(f"Unsupported attribute {attr}")

    def delete_application_object_object(self, name):
        """Deletes a single ApplicationObject."""
        if self.applications[name]["location"] == "predefined":
            raise ValueError("Unable to delete predefined application")
        self._delete_instance(name)
