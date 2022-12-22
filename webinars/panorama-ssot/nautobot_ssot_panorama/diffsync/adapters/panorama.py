"""Nautobot SSoT Panorama Adapter for Panorama SSoT plugin."""
from diffsync import DiffSync, DiffSyncModel
from diffsync.exceptions import ObjectNotFound
from panos.device import Vsys
from panos.errors import PanDeviceXapiError
from panos.firewall import Firewall
from panos.policies import SecurityRule
from nautobot.extras.choices import SecretsGroupAccessTypeChoices, SecretsGroupSecretTypeChoices


from nautobot_ssot_panorama.diffsync.models.panorama import (
    PanoramaAddressObject,
    PanoramaAddressGroup,
    PanoramaApplication,
    PanoramaApplicationGroup,
    PanoramaDeviceGroup,
    PanoramaFirewall,
    PanoramaServiceObject,
    PanoramaServiceGroup,
    PanoramaUserObjectGroup,
    PanoramaZone,
    PanoramaPolicy,
    PanoramaPolicyRule,
    PanoramaVsys,
)
from nautobot_ssot_panorama.utils.panorama import Panorama


class PanoramaAdapter(DiffSync):
    """DiffSync adapter for Panorama."""

    addressobject = PanoramaAddressObject
    addressgroup = PanoramaAddressGroup
    application = PanoramaApplication
    applicationgroup = PanoramaApplicationGroup
    devicegroup = PanoramaDeviceGroup
    firewall = PanoramaFirewall
    serviceobject = PanoramaServiceObject
    servicegroup = PanoramaServiceGroup
    userobjectgroup = PanoramaUserObjectGroup
    zone = PanoramaZone
    policy = PanoramaPolicy
    policyrule = PanoramaPolicyRule
    vsys = PanoramaVsys

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

    def __init__(self, *args, job=None, sync=None, pan=None, **kwargs):
        """Initialize Panorama.

        Args:
            job (object, optional): Panorama job. Defaults to None.
            sync (object, optional): Panorama DiffSync. Defaults to None.
            pan (ControlPlaneSystem, optional): Panoroama instance.
        """
        super().__init__(*args, **kwargs)
        self.job = job
        self.sync = sync
        self.pan = pan
        self.job.log_info(pan, "Using selected Panorama for connection.")
        self.pano = Panorama(
            url=pan.fqdn_or_ip,
            username=pan.secrets_group.get_secret_value(
                access_type=SecretsGroupAccessTypeChoices.TYPE_HTTP,
                secret_type=SecretsGroupSecretTypeChoices.TYPE_USERNAME,
            ),
            password=pan.secrets_group.get_secret_value(
                access_type=SecretsGroupAccessTypeChoices.TYPE_HTTP,
                secret_type=SecretsGroupSecretTypeChoices.TYPE_PASSWORD,
            ),
            port=pan.port,
            verify=pan.verify_ssl,
        )
        self._backend = "Panorama"
        self._loaded_apps = []

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
        """Load data from Panorama into DiffSync models."""
        self.job.log_info(self.pan, f"Caching Address Groups from {self._backend}")
        self.pano.address.retrieve_address_groups()
        self.job.log_info(self.pan, f"Caching Address Objects from {self._backend}")
        self.pano.address.retrieve_address_objects()
        self.job.log_info(self.pan, f"Caching Service Groups from {self._backend}")
        self.pano.service.retrieve_service_groups()
        self.job.log_info(self.pan, f"Caching Service Objects from {self._backend}")
        self.pano.service.retrieve_service_objects()
        self.job.log_info(self.pan, f"Caching Application Groups from {self._backend}")
        self.pano.application.retrieve_application_groups()
        self.job.log_info(self.pan, f"Caching Application Objects from {self._backend}")
        self.pano.application.retrieve_application_objects()
        self.job.log_info(self.pan, f"Caching User Groups from {self._backend}")
        self.pano.user.retrieve_dynamic_user_groups()
        self.job.log_info(self.pan, f"Caching Zones from {self._backend}")
        self.pano.firewall.retrieve_zones()
        self.job.log_info(self.pan, f"Caching Policies & Rules from {self._backend}")
        self.pano.policy.retrieve_security_rules()
        self.job.log_info(self.pan, f"Caching Firewalls from {self._backend}")
        self.pano.firewall.retrieve_firewalls()
        self.job.log_info(self.pan, f"Caching Vsys from {self._backend}")
        self.pano.firewall.retrieve_vsys()
        self.job.log_info(self.pan, f"Loading objects from {self._backend} via cache")
        self.load_cached_objects()

    def load_cached_objects(self):
        """Load objects from cache."""
        for group_name, group in self.pano.device_group.device_groups.items():
            parent = self.pano.device_group.get_parent(group_name)
            if not parent:
                parent = "shared"
            vsyss = []
            firewalls = []
            for child in group.children:
                if isinstance(child, Vsys):
                    self.get_or_add(
                        self.vsys(name=child.name, parent=child.parent.serial, interfaces=sorted(child.interface))
                    )
                    vsyss.append({"parent": child.parent.serial, "name": child.name})
                elif isinstance(child, Firewall):
                    ifaces = []
                    try:
                        for vsys in Vsys.refreshall(child):
                            self.get_or_add(
                                self.vsys(name=vsys.name, parent=child.serial, interfaces=sorted(vsys.interface))
                            )
                            ifaces += vsys.interface
                            vsyss.append({"parent": child.serial, "name": vsys.name})
                    except PanDeviceXapiError:
                        pass
                    self.get_or_add(
                        self.firewall(
                            name=self.pano.firewall.get_hostname(child),
                            serial=child.serial,
                            device_group=group.name,
                            interfaces=sorted(ifaces),
                        )
                    )
                    firewalls.append(child.serial)
            self.add(
                self.devicegroup(
                    name=group_name,
                    panorama=str(self.pan.id),
                    vsys=sorted(vsyss),
                    firewalls=sorted(firewalls),
                    pre_policy=self.load_policy("PRE", group_name),
                    post_policy=self.load_policy("POST", group_name),
                    parent=parent,
                )
            )
        self.add(
            self.devicegroup(
                name="shared",
                panorama=str(self.pan.id),
                pre_policy=self.load_policy("PRE", "shared"),
                post_policy=self.load_policy("POST", "shared"),
                vsys=[],
                firewalls=[],
            )
        )

    def load_policy(self, pre_post: str, group_name: str):
        """Get or adds Policy and returns to be added to DeviceGroup.

        Args:
            pre_post (str): Policy is pre or post
            group_name (str): DeviceGroup name for easy lookup

        Returns:
            PanoramaPolicy: DiffSyncModel of a Policy
        """
        rulebase = self.pano.policy.policies[group_name][pre_post]
        if len(rulebase) == 0:
            return None
        rules = []
        for rule in rulebase[0].children:
            if not isinstance(rule, SecurityRule):
                continue

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
            rules.append(rule.name)

            # Load Apps
            if rule.application != ["any"]:
                for app in rule.application:
                    if self.pano.application.applications[app]["type"] == "container":
                        applications.append(app)
                        for nested in self.pano.application.applications[app]["value"].applications:
                            self.load_application(nested)
                        self.load_application(app)
                    elif self.pano.application.applications[app]["type"] == "object":
                        applications.append(app)
                        self.load_application(app)
                    else:
                        self.load_application_group(app)
                        applicationgroups.append(app)

            # Load Services
            if rule.service != ["any"]:
                for svc in rule.service:
                    if svc == "application-default":
                        continue
                    if self.pano.service.services[svc]["type"] == "object":
                        self.load_service_object(svc)
                        destserviceobjects.append(svc)
                    else:
                        self.load_service_group(svc)
                        destservicegroups.append(svc)

            # Load User
            if rule.source_user != ["any"]:
                for user in rule.source_user:
                    self.load_user_group(user)
                    usergroups.append(user)

            # Load Zones
            if rule.fromzone != ["any"]:
                self.load_zone(rule.fromzone[0])
                sourcezone = rule.fromzone[0]
            if rule.tozone != ["any"]:
                self.load_zone(rule.tozone[0])
                destzone = rule.tozone[0]

            # Load Source Address
            if rule.source != ["any"]:
                for addr in rule.source:
                    if self.pano.address.addresses[addr]["type"] == "object":
                        self.load_address_object(addr)
                        sourceaddressobjects.append(addr)
                    else:
                        self.load_address_group(addr)
                        sourceaddressgroups.append(addr)

            # Load Destination Address
            if rule.destination != ["any"]:
                for addr in rule.destination:
                    if self.pano.address.addresses[addr]["type"] == "object":
                        self.load_address_object(addr)
                        destaddressobjects.append(addr)
                    else:
                        self.load_address_group(addr)
                        destaddressgroups.append(addr)

            # Create base rule
            self.get_or_add(
                self.policyrule(
                    name=rule.name,
                    action=rule.action,
                    log=True if rule.log_end or rule.log_start else False,
                    index=rulebase[0].children.index(rule) + 1,
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
        if not rules:
            return None
        self.get_or_add(self.policy(name=f"{group_name}-{pre_post}", policyrule_names=sorted(rules)))
        return f"{group_name}-{pre_post}"

    def load_address_object(self, name: str) -> "PanoramaAddressObject":
        """Loads a address object.

        Args:
            name (str): Name of the object

        Returns:
            PanoramaAddressObject: _description_
        """
        address = self.pano.address.addresses[name]["value"]
        if address.type == "ip-wildcard":
            raise ValueError("Not Supported")
        return self.get_or_add(self.addressobject(name=address.name, address=address.value, type=address.type))

    def load_address_group(self, name: str) -> "PanoramaAddressGroup":
        """Loads a address group.

        Args:
            name (str): Name of the object

        Returns:
            PanoramaAddressGroup: _description_
        """
        group = self.pano.address.addresses[name]["value"]
        for addr in group.static_value:
            self.load_address_object(addr)
        return self.get_or_add(
            self.addressgroup(
                name=group.name,
                type="static" if isinstance(group.static_value, list) else "dynamic",
                filter=group.dynamic_value,
                addressobjects=sorted(group.static_value) if isinstance(group.static_value, list) else [],
            )
        )

    def load_zone(self, name: str) -> "PanoramaZone":
        """Loads a zone.

        Args:
            name (str): Name of the object.
            to_from (str): To or from.

        Returns:
            PanoramaZone: _description_
        """
        firewalls = {}
        for firewall, zones in self.pano.firewall.zones.items():
            if zones.get(name):
                firewalls[firewall] = zones[name].interface
        return self.get_or_add(self.zone(name=name, firewalls=firewalls))

    def load_service_group(self, name: str) -> "PanoramaServiceGroup":
        """Loads a service group.

        Args:
            name (str): Name of the object.

        Returns:
            PanoramaServiceGroup: _description_
        """
        group = self.pano.service.services[name]["value"]
        for svc in group.value:
            self.load_service_object(svc)
        return self.get_or_add(
            self.servicegroup(name=group.name, serviceobjects=sorted(group.value if group.value else []))
        )

    def load_service_object(self, name: str) -> "PanoramaServiceObject":
        """Loads a service object.

        Args:
            name (str): Name of the object.

        Returns:
            PanoramaServiceObject: _description_
        """
        service = self.pano.service.services[name]["value"]
        return self.get_or_add(
            self.serviceobject(
                name=service.name,
                port=service.destination_port,
                protocol=self.pano.service.find_proper_protocol(service.protocol),
            )
        )

    def load_user_group(self, name: str) -> "PanoramaUserObjectGroup":
        """Loads a user group.

        Args:
            name (str): Name of the object.

        Returns:
            PanoramaUserObjectGroup: _description_
        """
        return self.get_or_add(self.userobjectgroup(name=self.pano.user.users[name]["value"].name))

    def load_application(self, name: str) -> "PanoramaApplication":
        """Loads a application object.

        Args:
            name (str): Name of the object.

        Returns:
            PanoramaApplication: _description_
        """
        app_obj = self.pano.application.applications[name]["value"]
        if self.pano.application.applications[name]["type"] == "container":
            app = self.application(
                name=app_obj.name,
                type=self.pano.application.applications[name]["type"],
                members=sorted(app_obj.applications),
            )
        else:
            app = self.application(
                name=app_obj.name,
                category=app_obj.category,
                subcategory=app_obj.subcategory,
                technology=app_obj.technology,
                risk=app_obj.risk,
                default_ip_protocol=app_obj.default_ip_protocol,
                default_type=" ".join(app_obj.default_port),
                description=app_obj.description,
                type=self.pano.application.applications[name]["type"],
                members=[],
            )

        return self.get_or_add(app)

    def load_application_group(self, name: str) -> "PanoramaApplicationGroup":
        """Loads a application group.

        Args:
            name (str): Name of app group

        Returns:
            PanoramaApplicationGroup: _description_
        """
        group = self.pano.application.applications[name]["value"]
        for app in group.value:
            self.load_application(app)
        return self.get_or_add(
            self.applicationgroup(name=group.name, applications=sorted(group.value if group.value else []))
        )
