
from django.urls import include, path

from utilities.urls import get_model_urls

from . import views  # noqa: F401

app_name = 'netbox_cross_connects'

urlpatterns = [
    path('cross-connects/next-id/', views.CrossConnectNextIDView.as_view(), name='crossconnect_next_id'),
    path('cross-connects/', include(get_model_urls(app_name, 'crossconnect', detail=False))),
    path('cross-connects/<int:pk>/', include(get_model_urls(app_name, 'crossconnect'))),
    path('attachments/', include(get_model_urls(app_name, 'crossconnectattachment', detail=False))),
    path('attachments/<int:pk>/', include(get_model_urls(app_name, 'crossconnectattachment'))),
]
