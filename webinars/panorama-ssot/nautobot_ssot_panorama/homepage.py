"""Adds plugin items to homepage."""
from nautobot.core.apps import HomePageItem, HomePagePanel

from nautobot_ssot_panorama.models import VirtualSystem, LogicalGroup, ControlPlaneSystem

layout = (
    HomePagePanel(
        weight=150,
        name="Security",
        items=(
            HomePageItem(
                name="Control Plane Systems",
                model=ControlPlaneSystem,
                weight=100,
                link="plugins:nautobot_ssot_panorama:controlplanesystem_list",
                description="Firewall Control Plane Systems",
                permissions=["nautobot_ssot_panorama.view_controlplanesystem"],
            ),
            HomePageItem(
                name="Virtual Systems",
                model=VirtualSystem,
                weight=100,
                link="plugins:nautobot_ssot_panorama:virtualsystem_list",
                description="Firewall Virtual Systems",
                permissions=["nautobot_ssot_panorama.view_virtualsystem"],
            ),
            HomePageItem(
                name="Logical Groups",
                model=LogicalGroup,
                weight=100,
                link="plugins:nautobot_ssot_panorama:logicalgroup_list",
                description="Firewall Logical Groups",
                permissions=["nautobot_ssot_panorama.view_logicalgroup"],
            ),
        ),
    ),
)
