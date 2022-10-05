"""Job to create a new site of type POP."""
import re
from ipaddress import IPv4Network

from django.contrib.contenttypes.models import ContentType
from django.utils.text import slugify

from nautobot.extras.jobs import Job
from nautobot.dcim.models import Region, Site, Device, DeviceType, DeviceRole, Interface, Cable, Rack, Platform
from nautobot.dcim.choices import RackTypeChoices, InterfaceTypeChoices
from nautobot.ipam.models import VLAN, IPAddress, Prefix, Role
from nautobot.circuits.models import Circuit, Provider, CircuitType, CircuitTermination
from nautobot.extras.models import Status, CustomField, Relationship, RelationshipAssociation
from nautobot.extras.choices import RelationshipTypeChoices
from nautobot.extras.jobs import *
from nautobot.tenancy.models import Tenant

from ipaddress import IPv4Network

ROLES = {
    "edge": {
        "nbr": 2,
        "device_type": "dcs-7280cr2-60",
        "platform": "arista_eos",
        "rack_elevation": 40,
        "color": "ff9800",
        "interfaces": [
            ("peer", 2),
            ("leaf", 12),
            ("external", 8),
        ],
    },
    "leaf": {
        "nbr": 6,
        "device_type": "dcs-7150s-24",
        "platform": "arista_eos",
        "rack_elevation": 44,
        "color": "3f51b5",
        "interfaces": [
            ("edge", 4),
            ("access", 20),
        ],
    },
}

CUSTOM_FIELDS = {
    "role": {"models": [Interface], "label": "Role"},
    "site_type": {"models": [Site], "label": "Type of Site"},
}

RELATIONSHIPS = {
    "Device to Vlan": {
        "source_type": Device,
        "destination_type": VLAN,
        "type": RelationshipTypeChoices.TYPE_MANY_TO_MANY,
    },
    "Rack to Vlan": {
        "source_type": Rack,
        "destination_type": VLAN,
        "type": RelationshipTypeChoices.TYPE_ONE_TO_MANY,
    },
}

TOP_LEVEL_PREFIX_ROLE = "POP Global Pool"
PREFIX_ROLES = ["point-to-point", "loopback", "server", "mgmt", "pop"]

P2P_PREFIX_SIZE = 31
SITE_PREFIX_SIZE = 16

VLANS = {
    "server": {
        "vlan_id": 1000,
    },
    "mgmt": {
        "vlan_id": 99,
    },
}

RACK_HEIGHT = 48
RACK_TYPE = RackTypeChoices.TYPE_4POST


TRANSIT_PROVIDERS = ["Telia Carrier", "NTT"]


name = "Create POP"


def create_custom_fields():
    """Create all relationships defined in CUSTOM_FIELDS."""
    for cf_name, field in CUSTOM_FIELDS.items():
        try:
            cf = CustomField.objects.get(name=cf_name)
        except CustomField.DoesNotExist:
            cf = CustomField.objects.create(name=cf_name)
            if "label" in field:
                cf.label = field.get("label")
            cf.validated_save()

        for model in field["models"]:
            ct = ContentType.objects.get_for_model(model)
            cf.content_types.add(ct)
            cf.validated_save()


def create_relationships():
    """Create all relationships defined in RELATIONSHIPS."""
    for rel_name, relationship in RELATIONSHIPS.items():
        try:
            rel = Relationship.objects.get(name=rel_name)
        except Relationship.DoesNotExist:
            rel = Relationship.objects.create(
                name=rel_name,
                slug=slugify(rel_name),
                type=relationship.get("type", RelationshipTypeChoices.TYPE_MANY_TO_MANY),
                source_type=ContentType.objects.get_for_model(relationship.get("source_type")),
                destination_type=ContentType.objects.get_for_model(relationship.get("destination_type")),
            )
            rel.validated_save()


def create_prefix_roles():
    """Create all Prefix Roles defined in PREFIX_ROLES."""
    for role in PREFIX_ROLES:
        Role.objects.get_or_create(name=role, slug=slugify(role))


class CreatePop(Job):
    """Job to create a new site of type POP."""

    class Meta:
        """Meta class for CreatePop."""

        name = "Create a POP"
        description = """
        Create a new Site of Type POP with 2 Edge Routers and N leaf switches.
        A new /16 will automatically be allocated from the 'POP Global Pool' Prefix
        """
        label = "POP"
        field_order = [
            "tenant",
            "region",
            "site_name",
            "site_code",
            "site_facility",
            "leaf_count",
        ]

    tenant = ObjectVar(model=Tenant)

    region = ObjectVar(model=Region)

    site_name = StringVar(description="Name of the new site", label="Site Name")

    site_code = StringVar(description="Slug of the new site", label="Site Slug")

    site_facility = StringVar(description="Facility of the new site", label="Site Facility")

    leaf_count = IntegerVar(description="Number of Leaf Switch", label="Leaf switches count", min_value=1, max_value=12)

    def create_p2p_link(self, intf1, intf2):
        """Create a Point to Point link between 2 interfaces.
        This function will:
        - Connect the 2 interfaces with a cable
        - Generate a new Prefix from a "point-to-point" container associated with this site
        - Assign one IP address to each interface from the previous prefix
        """
        if intf1.cable or intf2.cable:
            self.log_warning(
                message=f"Unable to create a P2P link between {intf1.device.name}::{intf1} and {intf2.device.name}::{intf2}"
            )
            return False

        status = Status.objects.get_for_model(Cable).get(slug="connected")
        cable = Cable.objects.create(termination_a=intf1, termination_b=intf2, status=status)
        cable.save()

        # Find Next available Network
        container_status = Status.objects.get_for_model(Prefix).get(slug="container")
        prefix = Prefix.objects.filter(site=self.site, role__name="point-to-point", status=container_status).first()
        first_avail = prefix.get_first_available_prefix()
        subnet = list(first_avail.subnet(P2P_PREFIX_SIZE))[0]

        prefix_status = Status.objects.get_for_model(Prefix).get(slug="p2p")
        prefix_role, _ = Role.objects.get_or_create(name="point-to-point")
        Prefix.objects.create(
            prefix=str(subnet), status=prefix_status, role=prefix_role, site=self.site, tenant=self.tenant
        )

        # Create IP Addresses on both sides
        ip_status = Status.objects.get_for_model(IPAddress).get(slug="active")
        ip1 = IPAddress.objects.create(
            address=str(subnet[0]),
            assigned_object=intf1,
            status=ip_status,
            tenant=self.tenant,
            dns_name=f"ip-{str(subnet[0]).replace('.', '-')}.p2p.{self.site.slug}.{self.tenant.description}",
        )
        ip2 = IPAddress.objects.create(
            address=str(subnet[1]),
            assigned_object=intf2,
            status=ip_status,
            tenant=self.tenant,
            dns_name=f"ip-{str(subnet[1]).replace('.', '-')}.p2p.{self.site.slug}.{self.tenant.description}",
        )

    def run(self, data=None, commit=None):
        """Main function for CreatePop."""
        self.devices = {}

        # ----------------------------------------------------------------------------
        # Initialize the database with all required objects
        # ----------------------------------------------------------------------------
        create_custom_fields()
        create_relationships()
        create_prefix_roles()

        # ----------------------------------------------------------------------------
        # Find or Create Site
        # ----------------------------------------------------------------------------
        site_name = data["site_name"]
        site_facility = data["site_facility"]
        site_code = data["site_code"].lower()
        region = data["region"]
        self.tenant = data["tenant"]
        site_status = Status.objects.get_for_model(Site).get(slug="active")
        self.site, created = Site.objects.get_or_create(
            name=site_name,
            region=region,
            slug=site_code,
            status=site_status,
            facility=site_facility,
            tenant=self.tenant,
        )
        self.site.custom_field_data["site_type"] = "POP"
        self.site.validated_save()
        self.log_success(self.site, f"Site {site_code} successfully created")

        ROLES["leaf"]["nbr"] = data["leaf_count"]

        # ----------------------------------------------------------------------------
        # Allocate Prefixes for this POP
        # ----------------------------------------------------------------------------
        # Search if there is already a POP prefix associated with this side
        # if not search the Top Level Prefix and create a new one
        pop_role, _ = Role.objects.get_or_create(name="pop")
        container_status = Status.objects.get_for_model(Prefix).get(slug="container")
        p2p_status = Status.objects.get_for_model(Prefix).get(slug="p2p")
        prefix_status = Status.objects.get_for_model(Prefix).get(slug="active")
        pop_prefix = Prefix.objects.filter(site=self.site, status=container_status, role=pop_role).first()

        if not pop_prefix:
            top_level_prefix = Prefix.objects.filter(
                role__slug=slugify(TOP_LEVEL_PREFIX_ROLE), status=container_status
            ).first()

            if not top_level_prefix:
                raise Exception("Unable to find the top level prefix to allocate a Network for this site")

            first_avail = top_level_prefix.get_first_available_prefix()
            prefix = list(first_avail.subnet(SITE_PREFIX_SIZE))[0]
            pop_prefix = Prefix.objects.create(
                prefix=prefix, site=self.site, status=container_status, role=pop_role, tenant=self.tenant
            )

        iter_subnet = IPv4Network(str(pop_prefix.prefix)).subnets(new_prefix=18)

        # Allocate the subnet by block of /18
        server_block = next(iter_subnet)
        mgmt_block = next(iter_subnet)
        loopback_subnet = next(iter_subnet)
        p2p_subnet = next(iter_subnet)

        pop_role, _ = Role.objects.get_or_create(name="pop")

        # Create Server & Mgmt Block
        server_role, _ = Role.objects.get_or_create(name="server")
        Prefix.objects.get_or_create(
            prefix=str(server_block), site=self.site, role=server_role, status=container_status, tenant=self.tenant
        )

        mgmt_role, _ = Role.objects.get_or_create(name="mgmt")
        Prefix.objects.get_or_create(
            prefix=str(mgmt_block), site=self.site, role=mgmt_role, status=container_status, tenant=self.tenant
        )

        loopback_role, _ = Role.objects.get_or_create(name="loopback")
        Prefix.objects.get_or_create(
            prefix=str(loopback_subnet),
            site=self.site,
            role=loopback_role,
            status=container_status,
            tenant=self.tenant,
        )

        p2p_role, _ = Role.objects.get_or_create(name="point-to-point")
        Prefix.objects.get_or_create(
            prefix=str(p2p_subnet),
            site=self.site,
            role=p2p_role,
            status=container_status,
            tenant=self.tenant,
        )

        rel_device_vlan = Relationship.objects.get(name="Device to Vlan")
        rel_rack_vlan = Relationship.objects.get(name="Rack to Vlan")

        # ----------------------------------------------------------------------------
        # Create Racks
        # ----------------------------------------------------------------------------
        rack_status = Status.objects.get_for_model(Rack).get(slug="active")
        for i in range(1, ROLES["leaf"]["nbr"] + 1):
            rack_name = f"{site_code}-{100 + i}"
            rack = Rack.objects.get_or_create(
                name=rack_name,
                site=self.site,
                u_height=RACK_HEIGHT,
                type=RACK_TYPE,
                status=rack_status,
                tenant=self.tenant,
            )

        # ----------------------------------------------------------------------------
        # Create Devices
        # ----------------------------------------------------------------------------
        ip_status = Status.objects.get_for_model(IPAddress).get(slug="active")
        vlan_status = Status.objects.get_for_model(VLAN).get(slug="active")
        for role, data in ROLES.items():
            for i in range(1, data.get("nbr", 2) + 1):

                rack_name = f"{site_code}-{100 + i}"
                rack = Rack.objects.filter(name=rack_name, site=self.site).first()
                platform = Platform.objects.filter(slug=data["platform"]).first()

                device_name = f"{site_code}-{role}-{i:02}"

                device = Device.objects.filter(name=device_name).first()
                if device:
                    self.devices[device_name] = device
                    if not device.platform and platform:
                        device.platform = platform
                        device.validated_save()

                    self.log_success(obj=device, message=f"Device {device_name} already present")
                    continue

                device_status = Status.objects.get_for_model(Device).get(slug="active")
                device_role, _ = DeviceRole.objects.get_or_create(
                    name=role, slug=slugify(role), color=ROLES[role]["color"]
                )
                device = Device.objects.create(
                    device_type=DeviceType.objects.get(slug=data.get("device_type")),
                    name=device_name,
                    site=self.site,
                    status=device_status,
                    device_role=device_role,
                    rack=rack,
                    platform=platform,
                    position=data.get("rack_elevation"),
                    face="front",
                    tenant=self.tenant,
                )

                device.clean()
                device.validated_save()
                self.devices[device_name] = device
                self.log_success(device, f"Device {device_name} successfully created")

                # Generate Loopback interface and assign Loopback
                loopback_intf = Interface.objects.create(
                    name="Loopback0", type=InterfaceTypeChoices.TYPE_VIRTUAL, device=device
                )

                loopback_prefix = Prefix.objects.get(
                    site=self.site,
                    role__name="loopback",
                )

                available_ips = loopback_prefix.get_available_ips()
                address = list(available_ips)[0]
                loopback_ip = IPAddress.objects.create(
                    address=str(address),
                    assigned_object=loopback_intf,
                    status=ip_status,
                    tenant=self.tenant,
                    dns_name=f"{role}-{i:02}.{site_code}.{self.tenant.description}",
                )
                device.primary_ip4 = loopback_ip
                device.clean()
                device.validated_save()

                # Assign Role to Interfaces
                intfs = iter(Interface.objects.filter(device=device))
                for int_role, cnt in data["interfaces"]:
                    for i in range(0, cnt):
                        intf = next(intfs)
                        intf._custom_field_data = {"role": int_role}
                        intf.validated_save()

                if role == "leaf":
                    for vlan_name, vlan_data in VLANS.items():
                        prefix_role = Role.objects.get(slug=vlan_name)
                        vlan = VLAN.objects.create(
                            vid=vlan_data["vlan_id"],
                            name=f"{rack_name}-{vlan_name}",
                            site=self.site,
                            role=prefix_role,
                            status=vlan_status,
                            tenant=self.tenant,
                        )
                        vlan_block = Prefix.objects.filter(
                            site=self.site, status=container_status, role=prefix_role
                        ).first()

                        # Find Next available Network
                        first_avail = vlan_block.get_first_available_prefix()
                        subnet = list(first_avail.subnet(24))[0]
                        vlan_prefix = Prefix.objects.create(
                            prefix=str(subnet),
                            vlan=vlan,
                            status=prefix_status,
                            role=prefix_role,
                            site=self.site,
                            tenant=self.tenant,
                        )
                        vlan_prefix.validated_save()

                        intf_name = f"vlan{vlan_data['vlan_id']}"
                        intf = Interface.objects.create(
                            name=intf_name, device=device, type=InterfaceTypeChoices.TYPE_VIRTUAL
                        )

                        # Create IP Addresses on both sides
                        vlan_ip = IPAddress.objects.create(
                            address=str(subnet[0]),
                            assigned_object=intf,
                            status=ip_status,
                            tenant=self.tenant,
                            dns_name=f"ip-{str(subnet[0]).replace('.', '-')}.{vlan_name}.{site_code}.{self.tenant.description}",
                        )

                        RelationshipAssociation.objects.create(
                            relationship=rel_device_vlan,
                            source_type=rel_device_vlan.source_type,
                            source_id=device.id,
                            destination_type=rel_device_vlan.destination_type,
                            destination_id=vlan.id,
                        )

                        RelationshipAssociation.objects.create(
                            relationship=rel_rack_vlan,
                            source_type=rel_rack_vlan.source_type,
                            source_id=rack.id,
                            destination_type=rel_rack_vlan.destination_type,
                            destination_id=vlan.id,
                        )

        # ----------------------------------------------------------------------------
        # Cabling
        # ----------------------------------------------------------------------------
        # Connect Edge Routers Together
        edge_01 = self.devices[f"{site_code}-edge-01"]
        edge_02 = self.devices[f"{site_code}-edge-02"]
        peer_intfs_01 = iter(Interface.objects.filter(device=edge_01, _custom_field_data__role="peer"))
        peer_intfs_02 = iter(Interface.objects.filter(device=edge_02, _custom_field_data__role="peer"))

        for link in range(0, 2):
            self.create_p2p_link(next(peer_intfs_01), next(peer_intfs_02))

        # Connect Edge and Leaf Switches together
        leaf_intfs_01 = iter(Interface.objects.filter(device=edge_01, _custom_field_data__role="leaf"))
        leaf_intfs_02 = iter(Interface.objects.filter(device=edge_02, _custom_field_data__role="leaf"))

        for i in range(1, ROLES["leaf"]["nbr"] + 1):
            leaf_name = f"{site_code}-leaf-{i:02}"
            leaf = self.devices[leaf_name]
            edge_intfs = iter(Interface.objects.filter(device=leaf, _custom_field_data__role="edge"))

            self.create_p2p_link(next(leaf_intfs_01), next(edge_intfs))
            self.create_p2p_link(next(leaf_intfs_02), next(edge_intfs))

        # ----------------------------------------------------------------------------
        # Create Circuits and Connect them
        # ----------------------------------------------------------------------------
        external_intfs_01 = iter(Interface.objects.filter(device=edge_01, _custom_field_data__role="external"))
        external_intfs_02 = iter(Interface.objects.filter(device=edge_02, _custom_field_data__role="external"))

        circuit_status = Status.objects.get_for_model(Circuit).get(slug="active")
        for provider in TRANSIT_PROVIDERS:
            try:
                provider = Provider.objects.get(name=provider)
            except Provider.DoesNotExist:
                self.log_warning(f"Unable to find Circuit Provider {provider}, skipping")
                continue

            try:
                circuit_type = CircuitType.objects.get(name="Transit")
            except CircuitType.DoesNotExist:
                self.log_warning(f"Unable to find CircuitType 'Transit', skipping")
                continue

            for intfs_list in [external_intfs_01, external_intfs_02]:

                intf = next(intfs_list)

                regex = re.compile("[^a-zA-Z0-9]")
                clean_name = regex.sub("", f"{site_code}{intf.device.name[-4:]}{intf.name[-4:]}")
                circuit_id = slugify(f"{provider.name[0:3]}-{int(clean_name, 36)}")
                circuit, created = Circuit.objects.get_or_create(
                    cid=circuit_id, type=circuit_type, provider=provider, status=circuit_status, tenant=self.tenant
                )

                self.log_success(circuit, f"Circuit {circuit_id} successfully created")

                if circuit.termination_a:
                    circuit.termination_a.delete()

                ct = CircuitTermination(
                    circuit=circuit,
                    site=self.site,
                    term_side="A",
                )
                ct.validated_save()

                status = Status.objects.get(slug="connected")
                cable = Cable.objects.create(termination_a=intf, termination_b=ct, status=status)

        # ----------------------------------------------------------------------------
        # Link multiple sites at a single location
        # ----------------------------------------------------------------------------
        if not site_code.endswith("1"):
            site_abreviation = site_code[0:3]
            current_site_num = int(site_code[3:5])
            for other_site_num in range(1, current_site_num):
                other_site = Site.objects.get(tenant=self.tenant, slug=f"{site_abreviation}{other_site_num:02}")
                other_edge_01 = Device.objects.get(
                    name=f"{site_abreviation}{other_site_num:02}-edge-01",
                    site=other_site,
                    tenant=self.tenant,
                )
                other_edge_02 = Device.objects.get(
                    name=f"{site_abreviation}{other_site_num:02}-edge-02",
                    site=other_site,
                    tenant=self.tenant,
                )
                other_external_intfs_01 = iter(
                    Interface.objects.filter(
                        device=other_edge_01, _custom_field_data__role="external", cable__isnull=True
                    )
                )
                other_external_intfs_02 = iter(
                    Interface.objects.filter(
                        device=other_edge_02, _custom_field_data__role="external", cable__isnull=True
                    )
                )
                for provider in TRANSIT_PROVIDERS:
                    try:
                        provider = Provider.objects.get(name=provider)
                    except Provider.DoesNotExist:
                        self.log_warning(f"Unable to find Circuit Provider {provider}, skipping")
                        continue

                    try:
                        circuit_type = CircuitType.objects.get(name="Dark Fiber")
                    except CircuitType.DoesNotExist:
                        self.log_warning(f"Unable to find CircuitType 'Dark Fiber', skipping")
                        continue

                    for intfs_list in [
                        (external_intfs_01, other_external_intfs_01),
                        (external_intfs_02, other_external_intfs_02),
                    ]:
                        intf = next(intfs_list[0])
                        other_intf = next(intfs_list[1])

                        regex = re.compile("[^a-zA-Z0-9]")
                        clean_name = regex.sub("", f"{site_code}{intf.device.name[-4:]}{intf.name[-4:]}")
                        circuit_id = slugify(f"{provider.name[0:3]}-{int(clean_name, 36)}")
                        circuit, created = Circuit.objects.get_or_create(
                            cid=circuit_id,
                            type=circuit_type,
                            provider=provider,
                            status=circuit_status,
                            tenant=self.tenant,
                        )

                        self.log_success(circuit, f"Circuit {circuit_id} successfully created")

                        if circuit.termination_a:
                            circuit.termination_a.delete()

                        ct = CircuitTermination(
                            circuit=circuit,
                            site=self.site,
                            term_side="A",
                        )
                        ct.validated_save()

                        if circuit.termination_z:
                            circuit.termination_z.delete()

                        ctz = CircuitTermination(
                            circuit=circuit,
                            site=other_site,
                            term_side="Z",
                        )
                        ct.validated_save()

                        status = Status.objects.get(slug="connected")
                        cable = Cable.objects.create(termination_a=intf, termination_b=ct, status=status)
                        cable2 = Cable.objects.create(termination_a=other_intf, termination_b=ctz, status=status)
