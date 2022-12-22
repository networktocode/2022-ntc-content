"""Plugin API serializers."""
from rest_framework import serializers

from nautobot.dcim.api.nested_serializers import NestedDeviceSerializer, NestedInterfaceSerializer
from nautobot.extras.api.serializers import NautobotModelSerializer

from nautobot_ssot_panorama.models import VirtualSystem, LogicalGroup, ControlPlaneSystem


class ControlPlaneSystemSerializer(NautobotModelSerializer):  # pylint: disable=too-many-ancestors
    """Used for normal CRUD operations."""

    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:nautobot_ssot_panorama-api:controlplanesystem-detail"
    )
    device = NestedDeviceSerializer()

    class Meta:
        """Meta class."""

        model = ControlPlaneSystem
        fields = ["url", "id", "name", "device", "port", "fqdn_or_ip", "verify_ssl"]


class VirtualSystemSerializer(NautobotModelSerializer):  # pylint: disable=too-many-ancestors
    """Used for normal CRUD operations."""

    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:nautobot_ssot_panorama-api:virtualsystem-detail")
    device = NestedDeviceSerializer()
    interfaces = NestedInterfaceSerializer(many=True)

    class Meta:
        """Meta class."""

        model = VirtualSystem
        fields = ["url", "id", "name", "system_id", "device", "interfaces"]


class LogicalGroupSerializer(NautobotModelSerializer):  # pylint: disable=too-many-ancestors
    """Used for normal CRUD operations."""

    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:nautobot_ssot_panorama-api:logicalgroup-detail")
    devices = NestedDeviceSerializer(many=True)

    class Meta:
        """Meta class."""

        model = LogicalGroup
        fields = ["url", "id", "name", "parent", "children", "devices", "virtual_systems"]
