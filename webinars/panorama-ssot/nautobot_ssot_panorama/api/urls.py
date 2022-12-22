"""Django API urlpatterns declaration for firewall model plugin."""

from nautobot.core.api import OrderedDefaultRouter

from nautobot_ssot_panorama.api import views


router = OrderedDefaultRouter()
router.register("control-plane-system", views.ControlPlaneSystemViewSet)
router.register("virtual-system", views.VirtualSystemViewSet)
router.register("logical-group", views.LogicalGroupViewSet)

urlpatterns = router.urls
