"""Nautobot Adapter for Panorama SSoT plugin."""
from diffsync import DiffSync, DiffSyncModel
from diffsync.exceptions import ObjectNotFound
from django.contrib.contenttypes.models import ContentType
from nautobot.extras.models import Relationship, RelationshipAssociation
from nautobot.ipam.models import IPAddress, Prefix
from nautobot_firewall_models.models import (
    AddressObject,
    ApplicationObject,
    ApplicationObjectGroup,
    FQDN,
    IPRange,
    AddressObjectGroup,
    ServiceObject,
    ServiceObjectGroup,
    Zone,
    Policy,
)

from nautobot_ssot_panorama.diffsync.models.nautobot import (
    NautobotAddressObject,
    NautobotAddressGroup,
    NautobotApplicationObject,
    NautobotApplicationGroup,
    NautobotDeviceGroup,
    NautobotFirewall,
    NautobotServiceObject,
    NautobotServiceGroup,
    NautobotUserObjectGroup,
    NautobotZone,
    NautobotPolicy,
    NautobotPolicyRule,
    NautobotVsys,
)


class NautobotAdapter(DiffSync):
    """DiffSync adapter for Nautobot."""

    addressobject = NautobotAddressObject
    addressgroup = NautobotAddressGroup
    application = NautobotApplicationObject
    applicationgroup = NautobotApplicationGroup
    serviceobject = NautobotServiceObject
    servicegroup = NautobotServiceGroup
    userobjectgroup = NautobotUserObjectGroup
    firewall = NautobotFirewall
    zone = NautobotZone
    vsys = NautobotVsys
    policyrule = NautobotPolicyRule
    policy = NautobotPolicy
    devicegroup = NautobotDeviceGroup

    top_level = [
        "addressobject",
        "addressgroup",
        "serviceobject",
        "servicegroup",
        "userobjectgroup",
        "application",
        "applicationgroup",
        "firewall",
        "zone",
        "vsys",
        "policyrule",
        "policy",
        "devicegroup",
    ]

    def __init__(self, *args, job=None, sync=None, **kwargs):
        """Initialize Nautobot.

        Args:
            job (object, optional): Nautobot job. Defaults to None.
            sync (object, optional): Nautobot DiffSync. Defaults to None.
        """
        super().__init__(*args, **kwargs)
        self.job = job
        self.sync = sync
        self._backend = "Nautobot"
        self._app_relationship = Relationship.objects.get(name="Application Container")
        self._app_content_type = ContentType.objects.get_for_model(ApplicationObject)

    def get_or_add(self, obj: "DiffSyncModel") -> "DiffSyncModel":
        """Ensures a model is added.

        Args:
            obj (DiffSyncModel): Instance of model

        Returns:
            DiffSyncModel: Instance of model that has been added
        """
        model = obj.get_type()
        ids = obj.get_unique_id()
        try:
            return self.store.get(model=model, identifier=ids)
        except ObjectNotFound:
            self.add(obj=obj)
            return obj

    def load(self):
        """Load data from Nautobot into DiffSync models."""
        self.job.log_info(None, f"Loading data from {self._backend}")
        self.load_device_groups()

    def sync_complete(self, source, diff, *args, **kwargs):
        """Creates custom relationship for app containters."""
        if source._backend == "Nautobot":
            return
        self.job.log_info(None, "Creating Custom Relationship For App Containers")
        apps = source.get_all("application")
        for pan_app in apps:
            if pan_app.type != "container":
                continue
            n_app = self.get("application", pan_app.name)
            src_app = ApplicationObject.objects.get(name=n_app.name)
            pan_members = pan_app.members if pan_app.members else []
            n_members = n_app.members if n_app.members else []
            if sorted(n_members) == sorted(pan_members):
                continue
            missing = [app for app in pan_members if app not in n_members]
            extra = [app for app in n_members if app not in pan_members]
            if extra:
                RelationshipAssociation.objects.filter(
                    relationship_id=self._app_relationship.id,
                    source_id=src_app.id,
                    destination_id__in=ApplicationObject.objects.filter(name__in=extra).values_list("id", flat=True),
                ).delete()
            if missing:
                for i in missing:
                    RelationshipAssociation.objects.create(
                        relationship_id=self._app_relationship.id,
                        source_id=src_app.id,
                        source_type=self._app_content_type,
                        destination_id=ApplicationObject.objects.get(name=i).id,
                        destination_type=self._app_content_type,
                    )

    def load_device_groups(self):
        """Load Nautobot DeviceGroup."""
        for group in self.job.kwargs["panorama"].logical_groups.all():
            firewalls = []
            vsyss = []
            parent = None
            if group.parent:
                parent = group.parent.name
            for firewall in group.devices.all():
                self.add(
                    self.firewall(
                        name=firewall.name,
                        serial=firewall.serial,
                        interfaces=sorted([i.name for i in firewall.interfaces.all()]),
                        device_group=group.name,
                    )
                )
                firewalls.append(firewall.serial)
            for vsys in group.virtual_systems.all():
                self.add(
                    self.vsys(
                        name=vsys.name,
                        parent=vsys.device.serial,
                        interfaces=sorted([i.name for i in vsys.interfaces.all()]),
                    )
                )
                vsyss.append({"parent": vsys.device.serial, "name": vsys.name})
            pre_policy = None
            post_policy = None
            if group.pre_policy:
                self.load_policy(group.pre_policy, group.name, "PRE")
                pre_policy = group.pre_policy.name
            if group.post_policy:
                self.load_policy(group.post_policy, group.name, "POST")
                post_policy = group.post_policy.name
            device_group = self.devicegroup(
                name=group.name,
                panorama=str(group.control_plane.id),
                vsys=sorted(vsyss),
                firewalls=sorted(firewalls),
                pre_policy=pre_policy,
                post_policy=post_policy,
                parent=parent,
            )
            self.add(device_group)

    def load_policy(self, policy: "Policy", group_name, pre_post) -> "NautobotPolicy":
        """Loads a policy.

        Args:
            policy (Policy): Nautobot Policy object

        Returns:
            NautobotPolicy: DiffSyncModel isntance
        """
        rules = []
        for rule in policy.policy_rules.all():
            applications = []
            applicationgroups = []
            usergroups = []
            destserviceobjects = []
            destservicegroups = []
            sourcezone = None
            destzone = None
            sourceaddressobjects = []
            sourceaddressgroups = []
            destaddressobjects = []
            destaddressgroups = []

            # Load Applications
            for app in rule.applications.all():
                self.load_application(app)
                applications.append(app.name)
            for group in rule.application_groups.all():
                self.load_application_group(group)
                applicationgroups.append(group.name)

            # Load User
            for user_group in rule.source_user_groups.all():
                self.get_or_add(self.userobjectgroup(name=user_group.name))
                usergroups.append(user_group.name)

            # Load Addresses
            for address in rule.source_addresses.all():
                self.load_address_object(address)
                sourceaddressobjects.append(address.name)
            for group in rule.source_address_groups.all():
                self.load_address_group(group)
                sourceaddressgroups.append(group.name)
            for address in rule.destination_addresses.all():
                self.load_address_object(address)
                destaddressobjects.append(address.name)
            for group in rule.destination_address_groups.all():
                self.load_address_group(group)
                destaddressgroups.append(group.name)

            # Load Services
            for service in rule.destination_services.all():
                self.load_service_object(service)
                destserviceobjects.append(service.name)
            for group in rule.destination_service_groups.all():
                self.load_service_group(group)
                destservicegroups.append(group.name)

            # Load Zone
            if rule.source_zone:
                self.load_zone(rule.source_zone)
                sourcezone = rule.source_zone.name
            if rule.destination_zone:
                self.load_zone(rule.destination_zone)
                destzone = rule.destination_zone.name
            self.get_or_add(
                self.policyrule(
                    name=rule.name,
                    action=rule.action,
                    log=rule.log,
                    index=rule.index,
                    applications=sorted(applications),
                    applicationgroups=sorted(applicationgroups),
                    usergroups=sorted(usergroups),
                    destserviceobjects=sorted(destserviceobjects),
                    destservicegroups=sorted(destservicegroups),
                    sourcezone=sourcezone,
                    destzone=destzone,
                    sourceaddressobjects=sorted(sourceaddressobjects),
                    sourceaddressgroups=sorted(sourceaddressgroups),
                    destaddressobjects=sorted(destaddressobjects),
                    destaddressgroups=sorted(destaddressgroups),
                    parent=group_name,
                    pre_post=pre_post,
                )
            )
            rules.append(rule.name)

        pol_obj = self.policy(name=policy.name, policyrule_names=sorted(rules))
        return self.get_or_add(pol_obj)

    def load_zone(self, zone: "Zone") -> "NautobotZone":
        """Loads zone.

        Args:
            zone (Zone): Nautobot Zone

        Returns:
            NautobotZone: DiffSyncModel for Zone
        """
        firewalls = {}
        for iface in zone.interfaces.all():
            if not firewalls.get(iface.device.serial):
                firewalls[iface.device.serial] = []
            firewalls[iface.device.serial].append(iface.name)
        return self.get_or_add(self.zone(name=zone.name, firewalls=firewalls))

    def load_service_object(self, service: "ServiceObject") -> "NautobotServiceObject":
        """Loads a service object.

        Args:
            service (ServiceObject): _description_

        Returns:
            NautobotServiceObject: _description_
        """
        return self.get_or_add(self.serviceobject(name=service.name, port=service.port, protocol=service.ip_protocol))

    def load_service_group(self, group: "ServiceObjectGroup") -> "NautobotServiceGroup":
        """Loads a service group.

        Args:
            group (ServiceObjectGroup): _description_

        Returns:
            NautobotServiceGroup: _description_
        """
        services = []
        for service in group.service_objects.all():
            self.load_service_object(service)
            services.append(service.name)
        return self.get_or_add(self.servicegroup(name=group.name, serviceobjects=sorted(services)))

    def load_address_group(self, group: "AddressObjectGroup") -> "NautobotAddressGroup":
        """Loads a address group.

        Args:
            group (AddressObjectGroup): _description_

        Returns:
            NautobotAddressGroup: _description_
        """
        addresses = []
        for address in group.address_objects.all():
            self.load_address_object(address)
            addresses.append(address.name)
        return self.get_or_add(
            self.addressgroup(
                name=group.name,
                type=group.custom_field_data.get("group-type"),
                filter=group.custom_field_data.get("dynamic-address-group-filter"),
                addressobjects=sorted(addresses),
            )
        )

    def load_address_object(self, address: "AddressObject") -> "NautobotAddressObject":
        """Loads a address object.

        Args:
            address (AddressObject): _description_

        Returns:
            NautobotAddressObject: _description_
        """
        if isinstance(address.address, FQDN):
            address_object = self.addressobject(name=address.name, address=address.address.name, type="fqdn")
        elif isinstance(address.address, IPRange):
            address_object = self.addressobject(name=address.name, address=str(address.address), type="ip-range")
        elif isinstance(address.address, IPAddress):
            if (address.address.family == 4 and address.address.prefix_length == 32) or (
                address.address.family == 6 and address.address.prefix_length == 64
            ):
                addr = address.address.host
            else:
                addr = str(address.address)
            address_object = self.addressobject(name=address.name, address=addr, type="ip-netmask")
        elif isinstance(address.address, Prefix):
            address_object = self.addressobject(name=address.name, address=str(address.address), type="ip-netmask")
        return self.get_or_add(address_object)

    def load_application_group(self, group: "ApplicationObjectGroup") -> "NautobotApplicationGroup":
        """Loads a application group.

        Args:
            group (ApplicationObjectGroup): _description_

        Returns:
            NautobotApplicationGroup: _description_
        """
        apps = []
        for app in group.application_objects.all():
            self.load_application(app)
            apps.append(app.name)
        return self.get_or_add(self.applicationgroup(name=group.name, applications=sorted(apps)))

    def load_application(self, app: "ApplicationObject") -> "NautobotApplicationObject":
        """Loads a application object.

        Args:
            app (ApplicationObject): _description_

        Returns:
            NautobotApplicationObject: _description_
        """
        members = [
            i.get_destination().name
            for i in RelationshipAssociation.objects.filter(source_id=app.id, relationship_id=self._app_relationship.id)
            if i.get_destination()
        ]
        for i in members:
            nested_app = ApplicationObject.objects.get(name=i)
            self.get_or_add(
                self.application(
                    name=nested_app.name,
                    category=nested_app.category,
                    subcategory=nested_app.subcategory,
                    technology=nested_app.technology,
                    risk=nested_app.risk,
                    default_ip_protocol=nested_app.default_ip_protocol,
                    default_type=nested_app.default_type,
                    description=nested_app.description,
                    type=nested_app.custom_field_data.get("application-type"),
                    members=[],
                )
            )
        return self.get_or_add(
            self.application(
                name=app.name,
                category=app.category,
                subcategory=app.subcategory,
                technology=app.technology,
                risk=app.risk,
                default_ip_protocol=app.default_ip_protocol,
                default_type=app.default_type,
                description=app.description,
                type=app.custom_field_data.get("application-type"),
                members=sorted(members),
            )
        )
