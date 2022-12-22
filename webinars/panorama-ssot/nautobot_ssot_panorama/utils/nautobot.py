"""Utility functions for working with Nautobot."""
from ipaddress import ip_address, ip_network
import re

from nautobot.dcim.models import Device, DeviceType, DeviceRole, Site, Interface
from nautobot.extras.models import Status
from nautobot.ipam.models import IPAddress, Prefix
from nautobot_firewall_models.models import (
    IPRange,
    FQDN,
    AddressObject,
    AddressObjectGroup,
    ApplicationObject,
    ApplicationObjectGroup,
    ServiceObject,
    ServiceObjectGroup,
    Zone,
    UserObjectGroup,
    PolicyRule,
    Policy,
)

from nautobot_ssot_panorama.models import ControlPlaneSystem, LogicalGroup, VirtualSystem


class Nautobot:  # pylint: disable=too-many-public-methods
    """Helper methods for interacting with Django ORM."""

    def create_vsys(self, ids, attrs):  # pylint: disable=no-self-use
        """Creates Vsys."""
        device = Device.objects.get(serial=ids["parent"])
        ifaces = device.interfaces.filter(name__in=attrs["interfaces"])
        sysid = int(re.sub("[^0-9]", "", ids["name"]))
        vsys, _ = VirtualSystem.objects.get_or_create(name=ids["name"], device=device, system_id=sysid)
        vsys.interfaces.set(list(ifaces))
        return vsys

    def update_vsys(self, name, parent, attrs):  # pylint: disable=no-self-use
        """Upates Vsys."""
        vsys = VirtualSystem.objects.get(name=name, device=parent)
        if "interfaces" in attrs:
            ifaces = Interface.objects.filter(device__id=parent, name__in=attrs["interfaces"])
            vsys.interfaces.clear()
            vsys.interfaces.set(list(ifaces))
        return vsys

    def create_firewall(self, ids, attrs):  # pylint: disable=no-self-use
        """Creates a Firewall."""
        if Device.objects.filter(serial=ids["serial"]).exists():
            return Device.objects.get(serial=ids["serial"])

        device = Device.objects.create(
            status=Status.objects.get(name="Staging"),
            serial=ids["serial"],
            name=attrs["name"],
            device_role=DeviceRole.objects.get(name="Panorama Staging"),
            device_type=DeviceType.objects.get(model="Panorama Staging"),
            site=Site.objects.get(name="Panorama Staging"),
        )
        for i in attrs.get("interfaces", []):
            Interface.objects.create(device=device, name=i)
        return device

    def update_firewall(self, serial, attrs):  # pylint: disable=no-self-use
        """Updates a Firewall."""
        device = Device.objects.get(name=serial)
        if "name" in attrs:
            device.name = attrs["name"]
            device.validated_save()
        if "interfaces" in attrs:
            Interface.objects.filter(device=device).exclude(name__in=attrs["interfaces"]).delete()
            for i in attrs["interfaces"]:
                Interface.objects.get_or_create(name=i, device=device)
        return device

    def create_address_object(self, ids, attrs):  # pylint: disable=no-self-use
        """Creates an AddressObject and any child objects."""
        if AddressObject.objects.filter(name=ids["name"]).exists():
            return AddressObject.objects.get(name=ids["name"])

        status = Status.objects.get(name="Active")
        addr_type = attrs["type"]

        if addr_type == "ip-wildcard":
            raise ValueError("IP Wildcard is not supported.")

        if addr_type == "fqdn":
            addr, _ = FQDN.objects.get_or_create(name=attrs["address"], status=status)
            return AddressObject.objects.create(name=ids["name"], fqdn=addr, status=status)

        if addr_type == "ip-range":
            addr_range = attrs["address"].split("-")
            addr, _ = IPRange.objects.get_or_create(
                start_address=addr_range[0], end_address=addr_range[1], status=status
            )
            return AddressObject.objects.create(name=ids["name"], ip_range=addr, status=status)

        try:
            ip_address(attrs["address"])
            addr, _ = IPAddress.objects.get_or_create(address=attrs["address"])
            return AddressObject.objects.create(name=ids["name"], ip_address=addr, status=status)
        except ValueError:
            pass
        try:
            ip_net = ip_network(attrs["address"])
            addr, _ = Prefix.objects.get_or_create(network=str(ip_net.network_address), prefix_length=ip_net.prefixlen)
            return AddressObject.objects.create(name=ids["name"], prefix=addr, status=status)
        except ValueError:
            ip_address(attrs["address"].split("/")[0])
            addr, _ = IPAddress.objects.get_or_create(address=attrs["address"])
            return AddressObject.objects.create(name=ids["name"], ip_address=addr, status=status)

    def update_address_object(self, name, type, attrs):  # pylint: disable=no-self-use,redefined-builtin
        """Updates an AddressObject and any child objects."""
        addr_type = type

        if addr_type == "ip-wildcard":
            raise ValueError("IP Wildcard is not supported.")

        obj = AddressObject.objects.get(name=name)
        obj.fqdn = None
        obj.ip_range = None
        obj.ip_address = None
        obj.prefix = None

        if addr_type == "fqdn":
            addr = FQDN.objects.get(name=attrs["address"])
            obj.fqdn = addr

        elif addr_type == "ip-range":
            addr_range = attrs["address"].split("-")
            addr = IPRange.objects.get(start_address=addr_range[0], end_address=addr_range[1])
            obj.ip_range = addr

        else:
            try:
                ip_address(attrs["address"])
                addr = IPAddress.objects.get(address=attrs["address"])
                obj.ip_address = addr
            except ValueError:
                pass
            try:
                ip_net = ip_network(attrs["address"])
                addr = Prefix.objects.get(network=str(ip_net.network_address), prefix_length=ip_net.prefixlen)
                obj.prefix = addr
            except ValueError:
                ip_address(attrs["address"].split("/")[0])
                addr = IPAddress.objects.get(address=attrs["address"])
                obj.ip_address = addr

        obj.validated_save()
        return obj

    def create_address_group(self, ids, attrs):
        """Creates an AddressObjectGroup and any child objects."""
        group, _ = AddressObjectGroup.objects.get_or_create(name=ids["name"])

        group.custom_field_data.update(
            {"group-type": attrs.get("type"), "dynamic-address-group-filter": attrs.get("filter")}
        )
        self._set_many_to_many(group, AddressObject, "address_objects", attrs, "addressobjects")
        group.validated_save()
        return group

    def update_address_group(self, name, attrs):
        """Updates an AddressObjectGroup and any child objects."""
        group = AddressObjectGroup.objects.get(name=name)
        self._set_many_to_many(group, AddressObject, "address_objects", attrs, "addressobjects")
        if "type" in attrs:
            group.custom_field_data.update({"group-type": attrs.get("type")})
        if "filter" in attrs:
            group.custom_field_data.update({"dynamic-address-group-filter": attrs.get("filter")})
        group.validated_save()
        return group

    def create_application_object(self, ids, attrs):
        """Creates an Application and any child objects."""
        if ApplicationObject.objects.filter(name=ids["name"]).exists():
            return ApplicationObject.objects.get(name=ids["name"])
        app_members = attrs.pop("members")
        obj = ApplicationObject.objects.create(name=ids["name"])
        obj = self._set_application_attrs(obj, attrs)
        obj.validated_save()
        return obj, app_members

    def update_application_object(self, name, attrs):
        """Updates an Application and any child objects."""
        app_members = attrs.pop("members")
        obj = self._set_application_attrs(ApplicationObject.objects.get(name=name), attrs)
        obj.validated_save()
        return obj, app_members

    def _set_application_attrs(self, obj, attrs):  # pylint: disable=no-self-use
        """Helper method to reduce repeated code."""
        for attr, value in attrs.items():
            if attr == "type":
                obj.custom_field_data.update({"application-type": value})
            else:
                setattr(obj, attr, value)
        return obj

    def create_application_group(self, ids, attrs):
        """Creates an ApplicationGroup and any child objects."""
        group, _ = ApplicationObjectGroup.objects.get_or_create(name=ids["name"])
        self._set_many_to_many(group, ApplicationObject, "application_objects", attrs, "applications")
        return group

    def update_application_group(self, name, attrs):
        """Updates an ApplicationGroup and any child objects."""
        group = ApplicationObjectGroup.objects.get(name=name)
        self._set_many_to_many(group, ApplicationObject, "application_objects", attrs, "applications")
        return group

    def create_device_group(self, ids, attrs):  # pylint: disable=no-self-use
        """Creates an DeviceGroup and any child objects."""
        group, _ = LogicalGroup.objects.get_or_create(name=ids["name"])
        if attrs.get("parent"):
            group.parent, _ = LogicalGroup.objects.get_or_create(name=attrs["parent"])
        group.control_plane = ControlPlaneSystem.objects.get(id=attrs["panorama"])

        if "firewalls" in attrs:
            group.devices.clear()
            if isinstance(attrs["firewalls"], list):
                for i in attrs["firewalls"]:
                    group.devices.add(Device.objects.get(serial=i))

        if "vsys" in attrs:
            group.virtual_systems.clear()
            if isinstance(attrs["vsys"], list):
                for i in attrs["vsys"]:
                    group.virtual_systems.add(VirtualSystem.objects.get(name=i["name"], device__serial=i["parent"]))

        if attrs.get("pre_policy"):
            group.pre_policy = Policy.objects.get(name=attrs["pre_policy"])
        if attrs.get("post_policy"):
            group.post_policy = Policy.objects.get(name=attrs["post_policy"])
        group.validated_save()
        return group

    def update_device_group(self, name, attrs):  # pylint: disable=no-self-use
        """Updates an DeviceGroup and any child objects."""
        group = LogicalGroup.objects.get(name=name)
        if "parent" in attrs and attrs["parent"]:
            group.parent = LogicalGroup.objects.get(name=attrs["parent"])
        elif "parent" in attrs:
            group.parent = None
        if not group.control_plane and attrs.get("panorama"):
            group.control_plane = ControlPlaneSystem.objects.get(id=attrs["panorama"])
        if "firewalls" in attrs:
            group.devices.clear()
            if isinstance(attrs["firewalls"], list):
                for i in attrs["firewalls"]:
                    group.devices.add(Device.objects.get(serial=i))
        if "vsys" in attrs:
            group.virtual_systems.clear()
            if isinstance(attrs["vsys"], list):
                for i in attrs["vsys"]:
                    group.virtual_systems.add(VirtualSystem.objects.get(name=i["name"], device__serial=i["parent"]))
        if attrs.get("pre_policy"):
            group.pre_policy = Policy.objects.get(name=attrs["pre_policy"])
        if attrs.get("post_policy"):
            group.post_policy = Policy.objects.get(name=attrs["post_policy"])
        group.validated_save()
        return group

    def create_service_group(self, ids, attrs):
        """Creates an ServiceObjectGroup and any child objects."""
        group, _ = ServiceObjectGroup.objects.get_or_create(name=ids["name"])
        self._set_many_to_many(group, ServiceObject, "service_objects", attrs, "serviceobjects")
        return group

    def update_service_group(self, name, attrs):
        """Updates an ServiceObjectGroup and any child objects."""
        group = ServiceObjectGroup.objects.get(name=name)
        self._set_many_to_many(group, ServiceObject, "service_objects", attrs, "serviceobjects")
        return group

    def create_service_object(self, ids, attrs):  # pylint: disable=no-self-use
        """Creates a ServiceObject and any child objects."""
        if ServiceObject.objects.filter(name=ids["name"]).exists():
            return ServiceObject.objects.get(name=ids["name"])

        status = Status.objects.get(name="Active")
        port = attrs["port"]
        protocol = attrs["protocol"]
        return ServiceObject.objects.create(name=ids["name"], port=port, ip_protocol=protocol, status=status)

    def update_service_object(self, name, attrs):  # pylint: disable=no-self-use
        """Updates an AddressObject and any child objects."""
        obj = ServiceObject.objects.get(name=name)

        if attrs.get("port"):
            obj.port = attrs["port"]
        if attrs.get("protocol"):
            obj.ip_protocol = attrs["protocol"]

        obj.validated_save()
        return obj

    def create_user_object_group(self, ids):  # pylint: disable=no-self-use
        """Creates a UserObjectGroup and any child objects."""
        if UserObjectGroup.objects.filter(name=ids["name"]).exists():
            return UserObjectGroup.objects.get(name=ids["name"])
        status = Status.objects.get(name="Active")
        return UserObjectGroup.objects.create(name=ids["name"], status=status)

    def create_zone(self, ids, firewalls):  # pylint: disable=no-self-use
        """Creates Zone."""
        if Zone.objects.filter(name=ids["name"]).exists():
            return Zone.objects.get(name=ids["name"])
        status = Status.objects.get(name="Active")
        ifaces = []
        for firewall, iface_list in firewalls.items():
            ifaces += list(Device.objects.get(serial=firewall).interfaces.filter(name__in=iface_list))
        zone = Zone.objects.create(name=ids["name"], status=status)
        zone.interfaces.set(ifaces)
        return zone

    def create_policy_rule(self, ids, attrs):
        """Creates PolicyRule."""
        if PolicyRule.objects.filter(name=ids["name"]).exists():
            return PolicyRule.objects.get(name=ids["name"])
        status = Status.objects.get(name="Active")
        rule = PolicyRule.objects.create(
            name=ids["name"], log=attrs["log"], action=attrs["action"], index=attrs["index"], status=status
        )
        return self._set_policy_rules_data(rule, attrs)

    def _set_policy_rules_data(self, rule, attrs):
        """Wrapper to deduplication code."""
        self._set_many_to_many(rule, AddressObject, "source_addresses", attrs, "sourceaddressobjects")
        self._set_many_to_many(rule, AddressObjectGroup, "source_address_groups", attrs, "sourceaddressgroups")
        self._set_many_to_many(rule, AddressObject, "destination_addresses", attrs, "destaddressobjects")
        self._set_many_to_many(rule, AddressObjectGroup, "destination_address_groups", attrs, "destaddressgroups")

        self._set_many_to_many(rule, ServiceObject, "source_services", attrs, "sourceserviceobjects")
        self._set_many_to_many(rule, ServiceObjectGroup, "source_service_groups", attrs, "sourceservicegroups")
        self._set_many_to_many(rule, ServiceObject, "destination_services", attrs, "destserviceobjects")
        self._set_many_to_many(rule, ServiceObjectGroup, "destination_service_groups", attrs, "destservicegroups")

        self._set_many_to_many(rule, ApplicationObject, "applications", attrs, "applications")
        self._set_many_to_many(rule, ApplicationObjectGroup, "application_groups", attrs, "applicationgroups")

        self._set_many_to_many(rule, UserObjectGroup, "source_user_groups", attrs, "usergroups")

        if attrs.get("sourcezone"):
            rule.source_zone = Zone.objects.get(name=attrs["sourcezone"])
        elif "sourcezone" in attrs:
            rule.source_zone = None

        if attrs.get("destzone"):
            rule.destination_zone = Zone.objects.get(name=attrs["destzone"])
        elif "destzone" in attrs:
            rule.destination_zone = None

        rule.validated_save()
        return rule

    def _set_many_to_many(
        self, parent_obj, child_obj, parent_attr, attrs, attrs_key
    ):  # pylint: disable=no-self-use,too-many-arguments
        """Helper for setting ManyToManyFields."""
        if attrs_key not in attrs:
            return parent_obj
        if not attrs[attrs_key]:
            getattr(parent_obj, parent_attr).clear()
        else:
            child_attr = getattr(parent_obj, parent_attr)
            child_attr.set(list(child_obj.objects.filter(name__in=attrs[attrs_key])))
        return parent_obj

    def update_policy_rule(self, name, attrs):  # pylint: disable=no-self-use
        """Updates PolicyRule."""
        rule = PolicyRule.objects.get(name=name)
        return self._set_policy_rules_data(rule, attrs)

    def create_policy(self, ids, attrs):
        """Creates Policy."""
        policy, _ = Policy.objects.get_or_create(name=ids["name"])
        self._set_many_to_many(policy, PolicyRule, "policy_rules", attrs, "policyrule_names")
        return policy

    def update_policy(self, name, attrs):
        """Updates Policy."""
        obj = Policy.objects.get(name=name)
        self._set_many_to_many(obj, PolicyRule, "policy_rules", attrs, "policyrule_names")
        return obj
