
from netbox.api.routers import NetBoxRouter

from . import views

router = NetBoxRouter()
router.register('cross-connects', views.CrossConnectViewSet)
router.register('attachments', views.CrossConnectAttachmentViewSet)

app_name = 'netbox_cross_connects-api'
urlpatterns = router.urls
