"""Extensions of baseline Nautobot views."""
from django.urls import reverse
from nautobot.extras.plugins import PluginTemplateExtension


class DeviceExtensions(PluginTemplateExtension):  # pylint: disable=abstract-method
    """Add VirtualSystem & LogicalGroup to the tabs on the Device page."""

    model = "dcim.device"

    def detail_tabs(self):
        """Add tabs to the Devices detail view."""
        return [
            {
                "title": "Virtual Systems",
                "url": reverse(
                    "plugins:nautobot_ssot_panorama:virtualsystem_device_tab", kwargs={"pk": self.context["object"].pk}
                ),
            },
            {
                "title": "Logical Group",
                "url": reverse(
                    "plugins:nautobot_ssot_panorama:logicalgroup_device_tab", kwargs={"pk": self.context["object"].pk}
                ),
            },
        ]


template_extensions = [DeviceExtensions]
