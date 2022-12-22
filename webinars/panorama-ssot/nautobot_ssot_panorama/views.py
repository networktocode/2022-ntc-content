"""Plugin UI Views."""
from nautobot.core.views import generic, mixins
from nautobot.dcim.models import Device

from nautobot_ssot_panorama.models import VirtualSystem, LogicalGroup, ControlPlaneSystem
from nautobot_ssot_panorama import filters, forms, tables
from nautobot_ssot_panorama.api.serializers import (
    VirtualSystemSerializer,
    LogicalGroupSerializer,
    ControlPlaneSystemSerializer,
)


class ControlPlaneSystemUIViewSet(
    mixins.ObjectDetailViewMixin,
    mixins.ObjectListViewMixin,
    mixins.ObjectEditViewMixin,
    mixins.ObjectDestroyViewMixin,
    mixins.ObjectBulkDestroyViewMixin,
):
    """ViewSet for the ControlPlaneSystem model."""

    filterset_class = filters.ControlPlaneSystemFilterSet
    filterset_form_class = forms.ControlPlaneSystemFilterForm
    form_class = forms.ControlPlaneSystemForm
    queryset = ControlPlaneSystem.objects.all()
    serializer_class = ControlPlaneSystemSerializer
    table_class = tables.ControlPlaneSystemTable
    action_buttons = ("add",)

    lookup_field = "pk"

    def _process_bulk_create_form(self, form):
        """Bulk creating (CSV import) is not supported."""
        raise NotImplementedError()


class VirtualSystemUIViewSet(
    mixins.ObjectDetailViewMixin,
    mixins.ObjectListViewMixin,
    mixins.ObjectEditViewMixin,
    mixins.ObjectDestroyViewMixin,
    mixins.ObjectBulkDestroyViewMixin,
):
    """ViewSet for the VirtualSystem model."""

    filterset_class = filters.VirtualSystemFilterSet
    filterset_form_class = forms.VirtualSystemFilterForm
    form_class = forms.VirtualSystemForm
    queryset = VirtualSystem.objects.all()
    serializer_class = VirtualSystemSerializer
    table_class = tables.VirtualSystemTable
    action_buttons = ("add",)

    lookup_field = "pk"

    def _process_bulk_create_form(self, form):
        """Bulk creating (CSV import) is not supported."""
        raise NotImplementedError()


class LogicalGroupUIViewSet(
    mixins.ObjectDetailViewMixin,
    mixins.ObjectListViewMixin,
    mixins.ObjectEditViewMixin,
    mixins.ObjectDestroyViewMixin,
    mixins.ObjectBulkDestroyViewMixin,
):
    """ViewSet for the LogicalGroup model."""

    filterset_class = filters.LogicalGroupFilterSet
    filterset_form_class = forms.LogicalGroupFilterForm
    form_class = forms.LogicalGroupForm
    queryset = LogicalGroup.objects.all()
    serializer_class = LogicalGroupSerializer
    table_class = tables.LogicalGroupTable
    action_buttons = ("add",)

    lookup_field = "pk"

    def _process_bulk_create_form(self, form):
        """Bulk creating (CSV import) is not supported."""
        raise NotImplementedError()


class DeviceVirtualSystemTabView(generic.ObjectView):
    """Add tab to Device view for VirtualSystem."""

    queryset = Device.objects.all()
    template_name = "nautobot_ssot_panorama/device_virtual_systems.html"


class DeviceLogicalGroupTabView(generic.ObjectView):
    """Add tab to Device view for LogicalGroup."""

    queryset = Device.objects.all()
    template_name = "nautobot_ssot_panorama/device_logical_groups.html"
