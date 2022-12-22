"""Nautobot DiffSync models for Panorama SSoT."""
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
from nautobot_ssot_panorama.utils.nautobot import Nautobot


NAUTOBOT = Nautobot()


class NautobotVsys(Vsys):
    """Nautobot implementation of Panorama Vsys model."""

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Vsys in Nautobot from NautobotVsys object."""
        NAUTOBOT.create_vsys(ids, attrs)
        return super().create(diffsync=diffsync, ids=ids, attrs=attrs)

    def update(self, attrs):
        """Update Vsys in Nautobot from NautobotVsys object."""
        NAUTOBOT.update_vsys(self.name, self.parent, attrs)
        return super().update(attrs)

    def delete(self):
        """Delete Vsys in Nautobot from NautobotVsys object."""
        return self


class NautobotFirewall(Firewall):
    """Nautobot implementation of Panorama Firewall model."""

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Firewall in Nautobot from NautobotFirewall object."""
        NAUTOBOT.create_firewall(ids, attrs)
        return super().create(diffsync=diffsync, ids=ids, attrs=attrs)

    def update(self, attrs):
        """Update Firewall in Nautobot from NautobotFirewall object."""
        NAUTOBOT.update_firewall(self.serial, attrs)
        return super().update(attrs)

    def delete(self):
        """Delete Firewall in Nautobot from NautobotFirewall object."""
        return self


class NautobotDeviceGroup(DeviceGroup):
    """Nautobot implementation of Panorama DeviceGroup model."""

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create DeviceGroup in Nautobot from NautobotDeviceGroup object."""
        NAUTOBOT.create_device_group(ids, attrs)
        return super().create(diffsync=diffsync, ids=ids, attrs=attrs)

    def update(self, attrs):
        """Update DeviceGroup in Nautobot from NautobotDeviceGroup object."""
        NAUTOBOT.update_device_group(self.name, attrs)
        return super().update(attrs)

    def delete(self):
        """Delete DeviceGroup in Nautobot from NautobotDeviceGroup object."""
        return self


class NautobotAddressObject(AddressObject):
    """Nautobot implementation of Panorama AddressObject model."""

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create AddressObject in Nautobot from NautobotAddressObject object."""
        NAUTOBOT.create_address_object(ids, attrs)
        return super().create(diffsync=diffsync, ids=ids, attrs=attrs)

    def update(self, attrs):
        """Update AddressObject in Nautobot from NautobotAddressObject object."""
        NAUTOBOT.update_address_object(self.name, self.type, attrs)
        return super().update(attrs)

    def delete(self):
        """Delete AddressObject in Nautobot from NautobotAddressObject object."""
        return self


class NautobotAddressGroup(AddressGroup):
    """Nautobot implementation of Panorama AddressGroup model."""

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create AddressGroup in Nautobot from NautobotAddressGroup object."""
        NAUTOBOT.create_address_group(ids, attrs)
        return super().create(diffsync=diffsync, ids=ids, attrs=attrs)

    def update(self, attrs):
        """Update AddressGroup in Nautobot from NautobotAddressGroup object."""
        NAUTOBOT.update_address_group(self.name, attrs)
        return super().update(attrs)


class NautobotApplicationObject(Application):
    """Nautobot implementation of Panorama ApplicationObject model."""

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create ApplicationObject in Nautobot from NautobotApplicationObject object."""
        NAUTOBOT.create_application_object(ids, attrs)
        return super().create(diffsync=diffsync, ids=ids, attrs=attrs)

    def update(self, attrs):
        """Update ApplicationObject in Nautobot from NautobotApplicationObject object."""
        NAUTOBOT.update_application_object(self.name, attrs)
        return super().update(attrs)

    def delete(self):
        """Delete ApplicationObject in Nautobot from NautobotApplicationObject object."""
        return self


class NautobotApplicationGroup(ApplicationGroup):
    """Nautobot implementation of Panorama ApplicationGroup model."""

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create ApplicationGroup in Nautobot from NautobotApplicationGroup object."""
        NAUTOBOT.create_application_group(ids, attrs)
        return super().create(diffsync=diffsync, ids=ids, attrs=attrs)

    def update(self, attrs):
        """Update ApplicationGroup in Nautobot from NautobotApplicationGroup object."""
        NAUTOBOT.update_application_group(self.name, attrs)
        return super().update(attrs)


class NautobotServiceObject(ServiceObject):
    """Nautobot implementation of Panorama ServiceObject model."""

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create ServiceObject in Nautobot from NautobotServiceObject object."""
        NAUTOBOT.create_service_object(ids, attrs)
        return super().create(diffsync=diffsync, ids=ids, attrs=attrs)

    def update(self, attrs):
        """Update ServiceObject in Nautobot from NautobotServiceObject object."""
        NAUTOBOT.update_service_object(self.name, attrs)
        return super().update(attrs)

    def delete(self):
        """Delete ServiceObject in Nautobot from NautobotServiceObject object."""
        return self


class NautobotServiceGroup(ServiceGroup):
    """Nautobot implementation of Panorama ServiceGroup model."""

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create ServiceGroup in Nautobot from NautobotServiceGroup object."""
        NAUTOBOT.create_service_group(ids, attrs)
        return super().create(diffsync=diffsync, ids=ids, attrs=attrs)

    def update(self, attrs):
        """Update ServiceGroup in Nautobot from NautobotServiceGroup object."""
        NAUTOBOT.update_service_group(self.name, attrs)
        return super().update(attrs)

    def delete(self):
        """Delete ServiceGroup in Nautobot from NautobotServiceGroup object."""
        return self


class NautobotUserObjectGroup(UserObjectGroup):
    """Nautobot implementation of Panorama UserObjectGroup model."""

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create UserObjectGroup in Nautobot from NautobotUserObjectGroup object."""
        NAUTOBOT.create_user_object_group(ids)
        return super().create(diffsync=diffsync, ids=ids, attrs=attrs)

    def update(self, attrs):
        """Update UserObjectGroup in Nautobot from NautobotUserObjectGroup object."""
        self.diffsync.job.log_info("User Object Groups do not support update.")
        return super().update(attrs)


class NautobotZone(Zone):
    """Nautobot implementation of Panorama Zone model."""

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Zone in Nautobot from NautobotZone object."""
        NAUTOBOT.create_zone(ids, attrs["firewalls"])
        return super().create(diffsync=diffsync, ids=ids, attrs=attrs)

    def update(self, attrs):
        """Update Zone in Nautobot from NautobotZone object."""
        self.diffsync.job.log_info("Zones do not support update.")
        return super().update(attrs)


class NautobotPolicyRule(PolicyRule):
    """Nautobot implementation of Panorama PolicyRule model."""

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create PolicyRule in Nautobot from NautobotPolicyRule object."""
        NAUTOBOT.create_policy_rule(ids, attrs)
        return super().create(diffsync=diffsync, ids=ids, attrs=attrs)

    def update(self, attrs):
        """Update PolicyRule in Nautobot from NautobotPolicyRule object."""
        NAUTOBOT.update_policy_rule(self.name, attrs)
        return super().update(attrs)


class NautobotPolicy(Policy):
    """Nautobot implementation of Panorama Policy model."""

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Policy in Nautobot from NautobotPolicy object."""
        NAUTOBOT.create_policy(ids, attrs)
        return super().create(diffsync=diffsync, ids=ids, attrs=attrs)

    def update(self, attrs):
        """Update Policy in Nautobot from NautobotPolicy object."""
        NAUTOBOT.update_policy(self.name, attrs)
        return super().update(attrs)
