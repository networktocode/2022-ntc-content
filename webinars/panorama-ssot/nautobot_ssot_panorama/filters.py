"""Plugin filters."""
from nautobot.utilities.filters import BaseFilterSet, SearchFilter

from nautobot_ssot_panorama.models import VirtualSystem, LogicalGroup, ControlPlaneSystem


class ControlPlaneSystemFilterSet(BaseFilterSet):
    """API filter for filtering ControlPlaneSystem objects."""

    q = SearchFilter(
        filter_predicates={
            "name": "icontains",
            "system_id": "icontains",
        },
    )

    class Meta:
        """Meta class."""

        model = ControlPlaneSystem
        fields = ["name", "device", "fqdn_or_ip"]


class VirtualSystemFilterSet(BaseFilterSet):
    """API filter for filtering VirtualSystem objects."""

    q = SearchFilter(
        filter_predicates={
            "name": "icontains",
            "system_id": "icontains",
        },
    )

    class Meta:
        """Meta class."""

        model = VirtualSystem
        fields = [
            "name",
            "system_id",
        ]


class LogicalGroupFilterSet(BaseFilterSet):
    """API filter for filtering LogicalGroup objects."""

    q = SearchFilter(
        filter_predicates={
            "name": "icontains",
        },
    )

    class Meta:
        """Meta class."""

        model = LogicalGroup
        fields = ["name", "parent", "children"]
