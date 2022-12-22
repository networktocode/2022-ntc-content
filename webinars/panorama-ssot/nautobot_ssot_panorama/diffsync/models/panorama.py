"""Nautobot SSoT Panorama DiffSync models for Nautobot SSoT Panorama SSoT."""

from nautobot_ssot_panorama.diffsync.models.base import (
    AddressObject,
    AddressGroup,
    Application,
    ApplicationGroup,
    DeviceGroup,
    Firewall,
    ServiceObject,
    ServiceGroup,
    Zone,
    UserObjectGroup,
    PolicyRule,
    Policy,
    Vsys,
)


class PanoramaVsys(Vsys):
    """Panorama implementation of Vsys model."""

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Vsys in Panorama from PanoramaVsys object."""
        return super().create(diffsync=diffsync, ids=ids, attrs=attrs)

    def update(self, attrs):
        """Update Vsys in Panorama from PanoramaVsys object."""
        return super().update(attrs)

    def delete(self):
        """Delete Vsys in Panorama from PanoramaVsys object."""
        return self


class PanoramaFirewall(Firewall):
    """Panorama implementation of Firewall model."""

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Firewall in Panorama from PanoramaFirewall object."""
        diffsync.pano.firewall.create_firewall(
            name=attrs["name"],
            serial=ids["serial"],
            interfaces=attrs.get("interfaces", []),
            group=attrs["device_group"],
        )
        return super().create(diffsync=diffsync, ids=ids, attrs=attrs)

    def update(self, attrs):
        """Update Firewall in Panorama from PanoramaFirewall object."""
        return super().update(attrs)

    def delete(self):
        """Delete Firewall in Panorama from PanoramaFirewall object."""
        return self


class PanoramaDeviceGroup(DeviceGroup):
    """Panorama implementation of DeviceGroup model."""

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create DeviceGroup in Panorama from PanoramaDeviceGroup object."""
        diffsync.pano.device_group.create_device_group(name=ids["name"], parent=attrs.get("parent"))
        return super().create(diffsync=diffsync, ids=ids, attrs=attrs)

    def update(self, attrs):
        """Update DeviceGroup in Nautobot from PanoramaDeviceGroup object."""
        return super().update(attrs)

    def delete(self):
        """Delete DeviceGroup in Nautobot from PanoramaDeviceGroup object."""
        return self


class PanoramaAddressObject(AddressObject):
    """Panorama implementation of AddressObject DiffSync model."""

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Device in Panorama from PanoramaAddressObject object."""
        diffsync.pano.address.create_address_object(name=ids["name"], address=attrs["address"], addr_type=attrs["type"])
        return super().create(diffsync=diffsync, ids=ids, attrs=attrs)

    def update(self, attrs):
        """Update Device in Panorama from PanoramaAddressObject object."""
        self.diffsync.pano.address.update_address_object(name=self.name, attrs=attrs)
        return super().update(attrs)

    def delete(self):
        """Delete Device in Panorama from PanoramaAddressObject object."""
        return self


class PanoramaAddressGroup(AddressGroup):
    """Panorama implementation of AddressGroup DiffSync model."""

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Device in Panorama from PanoramaAddressObject object."""
        diffsync.pano.address.create_address_group(
            name=ids["name"], addrs=attrs["addressobjects"], grp_type=attrs["type"], filter=attrs["filter"]
        )
        return super().create(diffsync=diffsync, ids=ids, attrs=attrs)

    def update(self, attrs):
        """Update Device in Panorama from PanoramaAddressObject object."""
        return super().update(attrs)

    def delete(self):
        """Delete Device in Panorama from PanoramaAddressObject object."""
        return self


class PanoramaApplication(Application):
    """Panorama implementation of ApplicationObject DiffSync model."""

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Device in Panorama from PanoramaApplication object."""
        diffsync.pano.application.create_application(name=ids["name"], attrs=attrs)
        return super().create(diffsync=diffsync, ids=ids, attrs=attrs)

    def update(self, attrs):
        """Update Device in Panorama from PanoramaApplication object."""
        return super().update(attrs)

    def delete(self):
        """Delete Device in Panorama from PanoramaApplication object."""
        return self


class PanoramaApplicationGroup(ApplicationGroup):
    """Panorama implementation of ApplicationGroup DiffSync model."""

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create application group in Panorama from PanoramaApplicationGroup object."""
        diffsync.pano.application.create_application_group(name=ids["name"], applications=attrs["applications"])
        return super().create(diffsync=diffsync, ids=ids, attrs=attrs)

    def update(self, attrs):
        """Update application group in Panorama from PanoramaApplicationGroup object."""
        self.diffsync.pano.application.update_application_group(name=self.name, applications=attrs["applications"])
        return super().update(attrs)

    def delete(self):
        """Delete application in Panorama from PanoramaApplicationGroup object."""
        return self


class PanoramaServiceObject(ServiceObject):
    """Panorama implementation of Device DiffSync model."""

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Device in Panorama from PanoramaServiceObject object."""
        diffsync.pano.service.create_service_object(
            name=ids["name"],
            port=attrs["port"],
            protocol=attrs["protocol"],
        )
        return super().create(diffsync=diffsync, ids=ids, attrs=attrs)

    def update(self, attrs):
        """Update Device in Panorama from PanoramaServiceObject object."""
        return super().update(attrs)

    def delete(self):
        """Delete Device in Panorama from PanoramaServiceObject object."""
        return self


class PanoramaServiceGroup(ServiceGroup):
    """Panorama implementation of ServiceGroup DiffSync model."""

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Device in Panorama from PanoramaServiceGroup object."""
        diffsync.pano.service.create_service_group(name=ids["name"], svc_objs=attrs["serviceobjects"])
        return super().create(diffsync=diffsync, ids=ids, attrs=attrs)

    def update(self, attrs):
        """Update Device in Panorama from PanoramaServiceGroup object."""
        return super().update(attrs)

    def delete(self):
        """Delete Device in Panorama from PanoramaServiceGroup object."""
        return self


class PanoramaUserObjectGroup(UserObjectGroup):
    """Panorama implementation of UserObjectGroup DiffSync model."""

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create DynamicUserGroup in Panorama from PanoramaUserObjectGroup object."""
        diffsync.pano.user.create_dynamic_user_group(name=ids["name"])
        return super().create(diffsync=diffsync, ids=ids, attrs=attrs)

    def update(self, attrs):
        """Update DynamicUserGroup in Panorama from PanoramaUserObjectGroup object."""
        return super().update(attrs)

    def delete(self):
        """Delete DynamicUserGroup in Panorama from PanoramaUserObjectGroup object."""
        return self


class PanoramaZone(Zone):
    """Panorama implementation of Zone DiffSync model."""

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Device in Panorama from PanoramaZone object."""
        diffsync.pano.firewall.create_zone(name=ids["name"], firewalls=attrs["firewalls"])
        return super().create(diffsync=diffsync, ids=ids, attrs=attrs)

    def update(self, attrs):
        """Update Device in Panorama from PanoramaZone object."""
        return super().update(attrs)

    def delete(self):
        """Delete Device in Panorama from PanoramaZone object."""
        return self


class PanoramaPolicyRule(PolicyRule):
    """Panorama implementation of PolicyRule DiffSync model."""

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Device in Panorama from PanoramaPolicyRule object."""
        parent = diffsync.pano.policy.device_groups[ids["parent"]]
        pre_post = ids["pre_post"]
        source = attrs["sourceaddressobjects"] + attrs["sourceaddressgroups"]
        destination = attrs["destaddressobjects"] + attrs["destaddressgroups"]
        service = attrs["destserviceobjects"] + attrs["destservicegroups"]
        application = attrs["applications"] + attrs["applicationgroups"]
        diffsync.pano.policy.create_security_rule(
            parent,
            pre_post,
            name=ids["name"],
            source=source if source else ["any"],
            destination=destination if destination else ["any"],
            service=service if service else ["any"],
            application=application if application else ["any"],
            tozone=[attrs["sourcezone"]] if attrs.get("sourcezone") else ["any"],
            fromzone=[attrs["destzone"]] if attrs.get("destzone") else ["any"],
            action=attrs["action"],
        )
        return super().create(diffsync=diffsync, ids=ids, attrs=attrs)

    def update(self, attrs):
        """Update Device in Panorama from PanoramaPolicyRule object."""
        parent = self.diffsync.pano.policy.device_groups[self.parent]
        updates = {}
        source = attrs.get("sourceaddressobjects", []) + attrs.get("sourceaddressgroups", [])
        if source:
            updates.update({"source": source})
        destination = attrs.get("destaddressobjects", []) + attrs.get("destaddressobjects", [])
        if destination:
            updates.update({"destination": destination})
        service = attrs.get("destserviceobjects", []) + attrs.get("destservicegroups", [])
        if service:
            updates.update({"service": service})
        application = attrs.get("applications", []) + attrs.get("applicationgroups", [])
        if application:
            updates.update({"application": application})
        if "sourcezone" in attrs:
            updates.update({"fromzone": [attrs["sourcezone"]] if attrs.get("sourcezone") else ["any"]})
        if "destzone" in attrs:
            updates.update({"tozone": [attrs["destzone"]] if attrs.get("destzone") else ["any"]})
        if attrs.get("action"):
            updates.update({"action": attrs["action"]})
        self.diffsync.pano.policy.update_security_rule(parent, self.pre_post, name=self.name, **updates)
        return super().update(attrs)

    def delete(self):
        """Delete Device in Panorama from PanoramaPolicyRule object."""
        return self


class PanoramaPolicy(Policy):
    """Panorama implementation of Policy DiffSync model."""

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Device in Panorama from PanoramaPolicy object."""
        return super().create(diffsync=diffsync, ids=ids, attrs=attrs)

    def update(self, attrs):
        """Update Device in Panorama from PanoramaPolicy object."""
        return super().update(attrs)

    def delete(self):
        """Delete Device in Panorama from PanoramaPolicy object."""
        return self
