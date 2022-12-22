"""Jobs for Panorama SSoT integration."""

from diffsync import DiffSyncFlags
from django.templatetags.static import static
from django.urls import reverse
from nautobot.extras.jobs import BooleanVar, Job, ObjectVar
from nautobot_golden_config.models import ConfigCompliance, ComplianceRule, ComplianceFeature
from nautobot_ssot.jobs.base import DataSource, DataTarget, DataMapping

from nautobot_ssot_panorama.diffsync.adapters import panorama, nautobot
from nautobot_ssot_panorama.models import ControlPlaneSystem


name = "Panorama SSoT"  # pylint: disable=invalid-name


class PanoramaDataSource(DataSource, Job):
    """Panorama SSoT Data Source."""

    debug = BooleanVar(description="Enable for more verbose debug logging", default=False)
    panorama = ObjectVar(model=ControlPlaneSystem)
    compliance = BooleanVar(
        description="Run Golden Config Compliance (adapters may resync if not set to dry run).", default=True
    )

    def __init__(self):
        """Initialize Panorama Data Source."""
        super().__init__()
        self.diffsync_flags = (
            self.diffsync_flags | DiffSyncFlags.CONTINUE_ON_FAILURE
        )  # | DiffSyncFlags.SKIP_UNMATCHED_DST

    class Meta:  # pylint: disable=too-few-public-methods
        """Meta data for Panorama."""

        name = "Panorama to Nautobot"
        data_source = "Panorama"
        data_target = "Nautobot"
        data_source_icon = static("nautobot_ssot_panorama/panorama.png")
        description = "Sync information from Panorama to Nautobot"

    @classmethod
    def config_information(cls):
        """Dictionary describing the configuration of this DataSource."""
        return {}

    @classmethod
    def data_mappings(cls):
        """List describing the data mappings involved in this DataSource."""
        return (
            DataMapping(
                "Address Object - Parent",
                None,
                "Address Object",
                reverse("plugins:nautobot_firewall_models:addressobject_list"),
            ),
            DataMapping(
                "Address Object - ip-range", None, "IP Range", reverse("plugins:nautobot_firewall_models:iprange_list")
            ),
            DataMapping("Address Object - fqdn", None, "FQDN", reverse("plugins:nautobot_firewall_models:fqdn_list")),
            DataMapping("Address Object - net-mask (Prefix)", None, "Prefix", reverse("ipam:prefix_list")),
            DataMapping("Address Object - net-mask (Host)", None, "IP Address", reverse("ipam:ipaddress_list")),
            DataMapping("Address Object - ip-wildcard", None, "Not Supported", None),
            DataMapping(
                "Address Object Group",
                None,
                "Address Object Group",
                reverse("plugins:nautobot_firewall_models:addressobjectgroup_list"),
            ),
            DataMapping(
                "Dynamic Address Object Group",
                None,
                "Address Object Group + Custom Field",
                reverse("plugins:nautobot_firewall_models:addressobjectgroup_list"),
            ),
            DataMapping(
                "Service Object", None, "Service Object", reverse("plugins:nautobot_firewall_models:serviceobject_list")
            ),
            DataMapping(
                "Service Object Group",
                None,
                "Service Object Group",
                reverse("plugins:nautobot_firewall_models:serviceobjectgroup_list"),
            ),
            DataMapping(
                "Application Object",
                None,
                "Application Object",
                reverse("plugins:nautobot_firewall_models:applicationobject_list"),
            ),
            DataMapping(
                "Application Container",
                None,
                "Application Object + Relationship",
                reverse("plugins:nautobot_firewall_models:applicationobject_list"),
            ),
            DataMapping(
                "Application Object Group",
                None,
                "Application Object Group",
                reverse("plugins:nautobot_firewall_models:applicationobjectgroup_list"),
            ),
            DataMapping(
                "Dynamic User Object Group",
                None,
                "User Object Group + Custom Field",
                reverse("plugins:nautobot_firewall_models:applicationobjectgroup_list"),
            ),
            DataMapping("Zone", None, "Zone", reverse("plugins:nautobot_firewall_models:zone_list")),
            DataMapping("Rule", None, "Policy Rule", reverse("plugins:nautobot_firewall_models:policyrule_list")),
            DataMapping("Policy", None, "Policy", reverse("plugins:nautobot_firewall_models:policy_list")),
            DataMapping(
                "Device Group", None, "Logical Group", reverse("plugins:nautobot_ssot_panorama:logicalgroup_list")
            ),
            DataMapping("VSYS", None, "Virtual System", reverse("plugins:nautobot_ssot_panorama:virtualsystem_list")),
            DataMapping("Firewall", None, "Device", reverse("dcim:device_list")),
            DataMapping(
                "Panorama",
                None,
                "Control Plane System",
                reverse("plugins:nautobot_ssot_panorama:controlplanesystem_list"),
            ),
        )

    def load_source_adapter(self):
        """Load data from Panorama into DiffSync models."""
        self.source_adapter = panorama.PanoramaAdapter(job=self, sync=self.sync, pan=self.kwargs["panorama"])
        self.source_adapter.load()
        self.source_value = self.source_adapter.dict()

    def load_target_adapter(self):
        """Load data from Nautobot into DiffSync models."""
        self.target_adapter = nautobot.NautobotAdapter(job=self, sync=self.sync)
        self.target_adapter.load()

    def post_run(self):
        """Overloaded to add compliance."""
        if self.kwargs["compliance"]:
            if not self.kwargs["dry_run"]:
                self.target_adapter = nautobot.NautobotAdapter(job=self, sync=self.sync)
                self.target_adapter.load()
            nautobot_adpt = self.target_adapter.dict()
            pan_adpt = self.source_adapter.dict()
            device = self.kwargs["panorama"].device
            for model in [
                "addressobject",
                "addressgroup",
                "application",
                "applicationgroup",
                "devicegroup",
                "userobjectgroup",
                "firewall",
                "policy",
                "policyrule",
                "serviceobject",
                "servicegroup",
                "vsys",
                "zone",
            ]:
                rule = ComplianceRule.objects.get(feature__slug=model)
                intended = nautobot_adpt.get(model, {})
                actual = pan_adpt.get(model, {})
                try:
                    comp_obj = ConfigCompliance.objects.get(device=device, rule=rule)
                    comp_obj.intended = intended
                    comp_obj.actual = actual
                    comp_obj.validated_save()
                except ConfigCompliance.DoesNotExist:
                    ConfigCompliance.objects.create(device=device, rule=rule, intended=intended, actual=actual)


# TODO: Implement this.
class PanoramaDataTarget(DataTarget, Job):
    """Panorama SSoT Data Target."""

    debug = BooleanVar(description="Enable for more verbose debug logging", default=False)
    panorama = ObjectVar(model=ControlPlaneSystem)
    compliance = BooleanVar(
        description="Run Golden Config Compliance (adapters may resync if not set to dry run).", default=True
    )

    def __init__(self):
        """Initialize Panorama Data Target."""
        super().__init__()
        self.diffsync_flags = (
            self.diffsync_flags | DiffSyncFlags.CONTINUE_ON_FAILURE
        )  # | DiffSyncFlags.SKIP_UNMATCHED_DST

    class Meta:  # pylint: disable=too-few-public-methods
        """Meta data for Panorama."""

        name = "Nautobot to Panorama"
        data_source = "Nautobot"
        data_target = "Panorama"
        data_target_icon = static("nautobot_ssot_panorama/panorama.png")
        description = "Sync information from Nautobot to Panorama"

    @classmethod
    def config_information(cls):
        """Dictionary describing the configuration of this DataTarget."""
        return {}

    @classmethod
    def data_mappings(cls):
        """List describing the data mappings involved in this DataSource."""
        return ()

    def load_source_adapter(self):
        """Load data from Nautobot into DiffSync models."""
        self.source_adapter = nautobot.NautobotAdapter(job=self, sync=self.sync)
        self.source_adapter.load()
        self.source_value = self.source_adapter.dict()

    def load_target_adapter(self):
        """Load data from Panorama into DiffSync models."""
        try:
            self.target_adapter = panorama.PanoramaAdapter(job=self, sync=self.sync, pan=self.kwargs["panorama"])
            self.target_adapter.load()
        except:
            self.log_failure(self.kwargs["panorama"], "Authentication Error, please validate credentials.")

    def post_run(self):
        """Overloaded to add compliance."""
        if self.kwargs["compliance"]:
            if not self.kwargs["dry_run"]:
                self.target_adapter = panorama.PanoramaAdapter(job=self, sync=self.sync, pan=self.kwargs["panorama"])
                self.target_adapter.load()
            nautobot_adpt = self.source_adapter.dict()
            pan_adpt = self.target_adapter.dict()
            device = self.kwargs["panorama"].device
            for model in [
                "zone",
                "policyrule",
                "userobjectgroup",
                "firewall",
                "addressgroup",
                "vsys",
                "addressobject",
                "devicegroup",
                "application",
                "serviceobject",
                "policy",
            ]:
                rule = ComplianceRule.objects.get(feature__slug=model)
                intended = nautobot_adpt.get(model, {})
                actual = pan_adpt.get(model, {})
                try:
                    comp_obj = ConfigCompliance.objects.get(device=device, rule=rule)
                    comp_obj.intended = intended
                    comp_obj.actual = actual
                    comp_obj.validated_save()
                except ConfigCompliance.DoesNotExist:
                    ConfigCompliance.objects.create(device=device, rule=rule, intended=intended, actual=actual)


jobs = [PanoramaDataSource, PanoramaDataTarget]
