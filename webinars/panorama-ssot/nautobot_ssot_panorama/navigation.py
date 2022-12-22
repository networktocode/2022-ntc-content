"""Menu items."""

from nautobot.core.apps import NavMenuAddButton, NavMenuGroup, NavMenuItem, NavMenuTab

menu_items = (
    NavMenuTab(
        name="Security",
        # weight=150,
        groups=[
            NavMenuGroup(
                name="Firewall",
                weight=300,
                items=[
                    NavMenuItem(
                        link="plugins:nautobot_ssot_panorama:controlplanesystem_list",
                        name="Control Plane Systems",
                        permissions=["nautobot_ssot_panorama.view_controlplanesystem"],
                        buttons=[
                            NavMenuAddButton(
                                link="plugins:nautobot_ssot_panorama:controlplanesystem_add",
                                permissions=["nautobot_ssot_panorama.add_controlplanesystem"],
                            ),
                        ],
                    ),
                    NavMenuItem(
                        link="plugins:nautobot_ssot_panorama:virtualsystem_list",
                        name="Virtual Systems",
                        permissions=["nautobot_ssot_panorama.view_virtualsystem"],
                        buttons=[
                            NavMenuAddButton(
                                link="plugins:nautobot_ssot_panorama:virtualsystem_add",
                                permissions=["nautobot_ssot_panorama.add_virtualsystem"],
                            ),
                        ],
                    ),
                    NavMenuItem(
                        link="plugins:nautobot_ssot_panorama:logicalgroup_list",
                        name="Logical Groups",
                        permissions=["nautobot_ssot_panorama.view_logicalgroup"],
                        buttons=[
                            NavMenuAddButton(
                                link="plugins:nautobot_ssot_panorama:logicalgroup_add",
                                permissions=["nautobot_ssot_panorama.add_logicalgroup"],
                            ),
                        ],
                    ),
                ],
            ),
        ],
    ),
)
