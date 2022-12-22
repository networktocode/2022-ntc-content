"""Models extending the Firewall plugin."""
from django.db import models
from django.urls import reverse
from nautobot.core.models import BaseModel
from nautobot.core.models.generics import PrimaryModel
from nautobot.extras.utils import extras_features
from nautobot.utilities.tree_queries import TreeManager
from tree_queries.models import TreeNode


@extras_features(
    "custom_fields",
    "custom_links",
    "custom_validators",
    "export_templates",
    "graphql",
    "relationships",
    "statuses",
    "webhooks",
)
class ControlPlaneSystem(PrimaryModel):  # pylint: disable=too-many-ancestors
    """Models Palo Alto Panorama."""

    name = models.CharField(max_length=100)
    device = models.OneToOneField(to="dcim.Device", null=True, related_name="panorama", on_delete=models.CASCADE)
    verify_ssl = models.BooleanField(default=True, verbose_name="Verify SSL")
    port = models.PositiveSmallIntegerField(default=443)
    fqdn_or_ip = models.CharField(max_length=100, verbose_name="FQDN/IP")
    secrets_group = models.ForeignKey(
        to="extras.SecretsGroup",
        on_delete=models.SET_NULL,
        default=None,
        blank=True,
        null=True,
        verbose_name="Secrets Group (API user/pass)",
    )

    class Meta:
        """Meta class."""

        ordering = ["name"]
        verbose_name = "Control Plane System"
        verbose_name_plural = "Control Plane Systems"

    def get_absolute_url(self):
        """Return detail view URL."""
        return reverse("plugins:nautobot_ssot_panorama:controlplanesystem", args=[self.pk])

    def __str__(self):
        """Stringify instance."""
        return self.name


@extras_features(
    "custom_fields",
    "custom_links",
    "custom_validators",
    "export_templates",
    "graphql",
    "relationships",
    "statuses",
    "webhooks",
)
class VirtualSystem(PrimaryModel):  # pylint: disable=too-many-ancestors
    """Models Palo Alto VSYS."""

    system_id = models.PositiveSmallIntegerField()
    name = models.CharField(max_length=48)
    device = models.ForeignKey(to="dcim.Device", related_name="vsys", on_delete=models.CASCADE)
    interfaces = models.ManyToManyField(
        to="dcim.Interface", related_name="assigned_vsys", through="VirtualSystemAssociation"
    )

    class Meta:
        """Meta class."""

        ordering = ["name"]
        verbose_name = "Virtual System"
        verbose_name_plural = "Virtual Systems"

    def get_absolute_url(self):
        """Return detail view URL."""
        return reverse("plugins:nautobot_ssot_panorama:virtualsystem", args=[self.pk])

    def __str__(self):
        """Stringify instance."""
        return self.name


class VirtualSystemAssociation(BaseModel):
    """Enforce an interface is not assigned more than once."""

    vsys = models.ForeignKey("nautobot_ssot_panorama.VirtualSystem", on_delete=models.CASCADE)
    iface = models.OneToOneField("dcim.Interface", on_delete=models.CASCADE)


@extras_features(
    "custom_fields",
    "custom_links",
    "custom_validators",
    "export_templates",
    "graphql",
    "relationships",
    "statuses",
    "webhooks",
)
class LogicalGroup(TreeNode, PrimaryModel):  # pylint: disable=too-many-ancestors
    """Logical grouping of Devices & VirtualSystems."""

    name = models.CharField(max_length=48)
    devices = models.ManyToManyField(to="dcim.Device", related_name="logical_group", through="LogicalGroupToDevice")
    virtual_systems = models.ManyToManyField(
        to="nautobot_ssot_panorama.VirtualSystem", related_name="logical_group", through="LogicalGroupToVirtualSystem"
    )
    control_plane = models.ForeignKey(
        to="nautobot_ssot_panorama.ControlPlaneSystem",
        null=True,
        blank=True,
        related_name="logical_groups",
        on_delete=models.CASCADE,
    )
    pre_policy = models.ForeignKey(
        to="nautobot_firewall_models.Policy",
        null=True,
        blank=True,
        related_name="pre_policy",
        on_delete=models.SET_NULL,
    )
    post_policy = models.ForeignKey(
        to="nautobot_firewall_models.Policy",
        null=True,
        blank=True,
        related_name="post_policy",
        on_delete=models.SET_NULL,
    )

    objects = TreeManager()

    class Meta:
        """Meta class."""

        ordering = ["name"]
        verbose_name = "Logical Group"
        verbose_name_plural = "Logical Groups"

    def get_absolute_url(self):
        """Return detail view URL."""
        return reverse("plugins:nautobot_ssot_panorama:logicalgroup", args=[self.pk])

    def __str__(self):
        """Stringify instance."""
        return self.name


class LogicalGroupToDevice(BaseModel):
    """Enforce a Device is not assigned more than once."""

    group = models.ForeignKey("nautobot_ssot_panorama.LogicalGroup", on_delete=models.CASCADE)
    device = models.OneToOneField("dcim.Device", on_delete=models.CASCADE)


class LogicalGroupToVirtualSystem(BaseModel):
    """Enforce a VirtualSystem is not assigned more than once."""

    group = models.ForeignKey("nautobot_ssot_panorama.LogicalGroup", on_delete=models.CASCADE)
    vsys = models.OneToOneField("nautobot_ssot_panorama.VirtualSystem", on_delete=models.CASCADE)
