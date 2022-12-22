"""Plugin declaration for nautobot_ssot_panorama."""
# Metadata is inherited from Nautobot. If not including Nautobot in the environment, this should be added
try:
    from importlib import metadata
except ImportError:
    # Python version < 3.8
    import importlib_metadata as metadata

__version__ = metadata.version(__name__)

from nautobot.core.signals import nautobot_database_ready
from nautobot.extras.plugins import PluginConfig

from nautobot_ssot_panorama.signals import nautobot_database_ready_callback


class NautobotSSoTPanoramaConfig(PluginConfig):
    """Plugin configuration for the nautobot_ssot_panorama plugin."""

    name = "nautobot_ssot_panorama"
    verbose_name = "Nautobot SSoT Panorama"
    version = __version__
    author = "Network to Code, LLC"
    description = "SSoT sync capabilities with Nautobot Firewall Models Plugin and Panorama."
    base_url = "ssot-panorama"
    required_settings = []
    min_version = "1.4.0"
    max_version = "1.9999"
    default_settings = {}
    caching_config = {}

    def ready(self):
        """Trigger callback when database is ready."""
        super().ready()

        nautobot_database_ready.connect(nautobot_database_ready_callback, sender=self)


config = NautobotSSoTPanoramaConfig  # pylint:disable=invalid-name
