"""Plugin tables."""
import django_tables2 as tables

from nautobot.utilities.tables import (
    BaseTable,
    ButtonsColumn,
    ToggleColumn,
)

from nautobot_ssot_panorama.models import VirtualSystem, LogicalGroup, ControlPlaneSystem


class ControlPlaneSystemTable(BaseTable):
    """Table for list view of `ControlPlaneSystem` objects."""

    pk = ToggleColumn()
    name = tables.LinkColumn()
    actions = ButtonsColumn(ControlPlaneSystem)
    verify_ssl = tables.BooleanColumn(verbose_name="Verify SSL")
    device = tables.LinkColumn()
    fqdn_or_ip = tables.Column(verbose_name="FQDN/IP")

    class Meta(BaseTable.Meta):  # pylint: disable=too-few-public-methods
        """Meta class."""

        model = ControlPlaneSystem
        fields = ["pk", "name", "device", "verify_ssl", "port", "fqdn_or_ip"]


class VirtualSystemTable(BaseTable):
    """Table for list view of `VirtualSystem` objects."""

    pk = ToggleColumn()
    name = tables.LinkColumn()
    actions = ButtonsColumn(VirtualSystem)
    system_id = tables.Column(verbose_name="System ID")
    device = tables.LinkColumn()
    interfaces = tables.ManyToManyColumn(linkify_item=True)

    class Meta(BaseTable.Meta):  # pylint: disable=too-few-public-methods
        """Meta class."""

        model = VirtualSystem
        fields = ["pk", "name", "system_id", "device", "interfaces"]


class LogicalGroupTable(BaseTable):
    """Table for list view of `LogicalGroup` objects."""

    pk = ToggleColumn()
    name = tables.LinkColumn()
    actions = ButtonsColumn(LogicalGroup)
    parent = tables.LinkColumn()
    devices = tables.ManyToManyColumn(linkify_item=True)
    virtual_systems = tables.ManyToManyColumn(linkify_item=True)

    class Meta(BaseTable.Meta):  # pylint: disable=too-few-public-methods
        """Meta class."""

        model = LogicalGroup
        fields = ["pk", "name", "parent", "devices", "virtual_systems"]
