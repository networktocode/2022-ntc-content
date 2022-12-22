"""Panorama SDK."""
from panos.panorama import Panorama as PanOsPanorama

from .address import PanoramaAddress
from .application import PanoramaApplication
from .device_group import PanoramaDeviceGroup
from .firewall import PanoramaFirewall
from .policy import PanoramaPolicy
from .service import PanoramaService
from .user import PanoramaUser


class Panorama:  # pylint: disable=too-many-instance-attributes,too-few-public-methods
    """Wrapper on Panorama python SDK."""

    def __init__(
        self, url=None, username=None, password=None, verify=True, port=443
    ):  # pylint: disable=too-many-arguments
        """Create base connectivity to Panorama."""
        self.pano = PanOsPanorama(url, api_username=username, api_password=password, port=port, verify=verify)
        self.device_group = PanoramaDeviceGroup(self.pano, {})
        device_groups = self.device_group.retrieve_device_groups()
        self.address = PanoramaAddress(self.pano, device_groups)
        self.application = PanoramaApplication(self.pano, device_groups)
        self.firewall = PanoramaFirewall(self.pano, device_groups)
        self.policy = PanoramaPolicy(self.pano, device_groups)
        self.service = PanoramaService(self.pano, device_groups)
        self.user = PanoramaUser(self.pano, device_groups)
