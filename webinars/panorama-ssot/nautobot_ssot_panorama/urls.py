"""Plugin URLS."""
from django.urls import path
from nautobot.core.views.routers import NautobotUIViewSetRouter
from nautobot.extras.views import ObjectChangeLogView, ObjectNotesView

from nautobot_ssot_panorama.views import (
    VirtualSystemUIViewSet,
    LogicalGroupUIViewSet,
    ControlPlaneSystemUIViewSet,
    DeviceVirtualSystemTabView,
    DeviceLogicalGroupTabView,
)
from nautobot_ssot_panorama.models import VirtualSystem, LogicalGroup, ControlPlaneSystem

router = NautobotUIViewSetRouter()
router.register("virtual-system", VirtualSystemUIViewSet)
router.register("control-plane-system", ControlPlaneSystemUIViewSet)
router.register("logical-group", LogicalGroupUIViewSet)
urlpatterns = [
    path(
        "control-plane-system/<uuid:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="controlplanesystem_changelog",
        kwargs={"model": ControlPlaneSystem},
    ),
    path(
        "control-plane-system/<uuid:pk>/notes/",
        ObjectNotesView.as_view(),
        name="controlplanesystem_notes",
        kwargs={"model": ControlPlaneSystem},
    ),
    path(
        "virtual-system/<uuid:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="virtualsystem_changelog",
        kwargs={"model": VirtualSystem},
    ),
    path(
        "virtual-system/<uuid:pk>/notes/",
        ObjectNotesView.as_view(),
        name="virtualsystem_notes",
        kwargs={"model": VirtualSystem},
    ),
    path(
        "virtual-system/<uuid:pk>/device/",
        DeviceVirtualSystemTabView.as_view(),
        name="virtualsystem_device_tab",
    ),
    path(
        "logical-group/<uuid:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="logicalgroup_changelog",
        kwargs={"model": LogicalGroup},
    ),
    path(
        "logical-group/<uuid:pk>/notes/",
        ObjectNotesView.as_view(),
        name="logicalgroup_notes",
        kwargs={"model": LogicalGroup},
    ),
    path(
        "logical-group/<uuid:pk>/device/",
        DeviceLogicalGroupTabView.as_view(),
        name="logicalgroup_device_tab",
    ),
]
urlpatterns += router.urls
