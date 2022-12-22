"""Plugin forms."""
from django import forms

from nautobot.dcim.models import Device, Interface
from nautobot.extras.forms import NautobotModelForm
from nautobot.extras.models import SecretsGroup
from nautobot.utilities.forms import (
    BootstrapMixin,
    DynamicModelChoiceField,
    DynamicModelMultipleChoiceField,
)
from nautobot_firewall_models.models import Policy

from nautobot_ssot_panorama.models import VirtualSystem, LogicalGroup, ControlPlaneSystem


class ControlPlaneSystemFilterForm(BootstrapMixin, forms.Form):
    """Filtering/search form for `ControlPlaneSystem` objects."""

    model = ControlPlaneSystem
    q = forms.CharField(required=False, label="Search")
    name = forms.CharField(max_length=20, required=False)
    device = DynamicModelChoiceField(queryset=Device.objects.all(), required=False)


class ControlPlaneSystemForm(NautobotModelForm):  # pylint: disable=too-many-ancestors
    """Generic create/update form for `ControlPlaneSystem` objects."""

    device = DynamicModelChoiceField(queryset=Device.objects.all(), required=False)
    secrets_group = DynamicModelChoiceField(
        queryset=SecretsGroup.objects.all(), required=True, label="Secrets Group (API user/pass)"
    )

    class Meta:
        """Meta class."""

        model = ControlPlaneSystem
        fields = ["name", "device", "port", "fqdn_or_ip", "verify_ssl", "secrets_group"]


class VirtualSystemFilterForm(BootstrapMixin, forms.Form):
    """Filtering/search form for `VirtualSystem` objects."""

    model = VirtualSystem
    q = forms.CharField(required=False, label="Search")
    name = forms.CharField(max_length=20, required=False)
    system_id = forms.IntegerField(required=False)
    device = DynamicModelChoiceField(queryset=Device.objects.all(), label="Parent Device", required=False)


class VirtualSystemForm(NautobotModelForm):  # pylint: disable=too-many-ancestors
    """Generic create/update form for `VirtualSystem` objects."""

    device = DynamicModelChoiceField(queryset=Device.objects.all(), label="Parent Device", required=True)
    interfaces = DynamicModelMultipleChoiceField(
        queryset=Interface.objects.all(),
        label="Assigned Interfaces",
        required=True,
        query_params={"device_id": "$device"},
    )

    class Meta:
        """Meta class."""

        model = VirtualSystem
        fields = ["name", "system_id", "device", "interfaces"]


class LogicalGroupFilterForm(BootstrapMixin, forms.Form):
    """Filtering/search form for `LogicalGroup` objects."""

    model = LogicalGroup
    q = forms.CharField(required=False, label="Search")
    name = forms.CharField(max_length=20, required=False)


class LogicalGroupForm(NautobotModelForm):  # pylint: disable=too-many-ancestors
    """Generic create/update form for `LogicalGroup` objects."""

    devices = DynamicModelMultipleChoiceField(queryset=Device.objects.all(), label="Assigned Devices", required=False)
    virtual_systems = DynamicModelMultipleChoiceField(
        queryset=VirtualSystem.objects.all(), label="Assigned Virtual Systems", required=False
    )
    control_plane = DynamicModelChoiceField(queryset=ControlPlaneSystem.objects.all(), required=False)
    pre_policy = DynamicModelChoiceField(queryset=Policy.objects.all(), required=False)
    post_policy = DynamicModelChoiceField(queryset=Policy.objects.all(), required=False)

    class Meta:
        """Meta class."""

        model = LogicalGroup
        fields = ["name", "parent", "devices", "virtual_systems", "control_plane", "pre_policy", "post_policy"]
