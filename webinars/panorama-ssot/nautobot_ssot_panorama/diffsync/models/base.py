"""DiffSyncModel subclasses for Nautobot-to-Panorama data sync."""
from typing import List, Optional
from diffsync import DiffSyncModel


class Firewall(DiffSyncModel):
    """DiffSync model for Panorama Firewall."""

    _modelname = "firewall"
    _identifiers = ("serial",)
    _attributes = ("name", "interfaces", "device_group")

    name: str
    serial: str
    device_group: Optional[str]
    interfaces: Optional[list]


class Vsys(DiffSyncModel):
    """DiffSync model for Panorama Vsys."""

    _modelname = "vsys"
    _identifiers = ("parent", "name")
    _attributes = ("interfaces",)

    name: str
    parent: str
    interfaces: Optional[list]


class DeviceGroup(DiffSyncModel):
    """DiffSync model for Panorama DeviceGroup."""

    _modelname = "devicegroup"
    _identifiers = ("name",)
    _attributes = ("parent", "vsys", "firewalls", "panorama", "pre_policy", "post_policy")

    name: str
    panorama: Optional[str]
    parent: Optional[str]
    vsys: Optional[list]
    firewalls: Optional[list]
    pre_policy: Optional[str]
    post_policy: Optional[str]


class AddressObject(DiffSyncModel):
    """DiffSync model for Panorama AddressObject."""

    _modelname = "addressobject"
    _identifiers = ("name",)
    _attributes = (
        "address",
        "type",
    )

    name: str
    address: str
    type: str


class AddressGroup(DiffSyncModel):
    """DiffSync model for Panorama AddressGroup."""

    _modelname = "addressgroup"
    _identifiers = ("name",)
    _attributes = ("addressobjects", "type", "filter")

    name: str
    addressobjects: list
    type: Optional[str]
    filter: Optional[str]


class Application(DiffSyncModel):
    """DiffSync model for Panorama Application."""

    _modelname = "application"
    _identifiers = ("name",)
    _attributes = (
        "category",
        "subcategory",
        "technology",
        "risk",
        "default_type",
        "default_ip_protocol",
        "description",
        "type",
        "members",
    )

    name: str
    category: Optional[str]
    subcategory: Optional[str]
    technology: Optional[str]
    risk: Optional[int]
    default_type: Optional[str]
    default_ip_protocol: Optional[str]
    description: Optional[str]
    type: Optional[str]
    members: Optional[list]


class ApplicationGroup(DiffSyncModel):
    """DiffSync model for Panorama ApplicationGroup."""

    _modelname = "applicationgroup"
    _identifiers = ("name",)
    _attributes = ("applications",)

    name: str
    applications: list


class ServiceObject(DiffSyncModel):
    """DiffSync model for Panorama ServiceObject."""

    _modelname = "serviceobject"
    _identifiers = ("name",)
    _attributes = (
        "port",
        "protocol",
    )

    name: str
    port: Optional[str]
    protocol: str


class ServiceGroup(DiffSyncModel):
    """DiffSync model for Panorama ServiceGroup."""

    _modelname = "servicegroup"
    _identifiers = ("name",)
    _attributes = ("serviceobjects",)

    name: str
    serviceobjects: list


class UserObjectGroup(DiffSyncModel):
    """DiffSync model for Panorama UserObjectGroup."""

    _modelname = "userobjectgroup"
    _identifiers = ("name",)

    name: str


class Zone(DiffSyncModel):
    """DiffSync model for Panorama Zone."""

    _modelname = "zone"
    _identifiers = ("name",)
    _attributes = ("firewalls",)

    name: str
    firewalls: dict


class PolicyRule(DiffSyncModel):
    """DiffSync model for Panorama PolicyRule."""

    _modelname = "policyrule"
    _identifiers = ("name", "parent", "pre_post")
    _attributes = (
        "sourceserviceobjects",
        "sourceservicegroups",
        "destserviceobjects",
        "destservicegroups",
        "sourcezone",
        "destzone",
        "sourceaddressobjects",
        "sourceaddressgroups",
        "destaddressobjects",
        "destaddressgroups",
        "action",
        "usergroups",
        "log",
        "index",
        "applications",
        "applicationgroups",
    )

    # Required
    action: str
    log: bool
    name: str
    index: int
    parent: str
    pre_post: str

    # Optional Source, empty translates to any
    sourceaddressgroups: Optional[list]
    sourceaddressobjects: Optional[list]
    sourceservicegroups: Optional[list]
    sourceserviceobjects: Optional[list]
    sourcezone: Optional[str]
    usergroups: Optional[list]

    # Optional Destination, empty translates to any
    destaddressgroups: Optional[list]
    destaddressobjects: Optional[list]
    destservicegroups: Optional[list]
    destserviceobjects: Optional[list]
    applications: Optional[list]
    applicationgroups: Optional[list]
    destzone: Optional[str]


class Policy(DiffSyncModel):
    """DiffSync model for Panorama Policy."""

    _modelname = "policy"
    _identifiers = ("name",)
    _attributes = ("policyrule_names",)

    name: str
    policyrule_names: Optional[list]
