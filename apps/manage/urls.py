from django.urls import path

from apps.manage.views import GetInduceConfig, GetAdvertising,Version,AddTimeConfig

urlpatterns = [
    path('version', Version.as_view(), name="update_version"),
    path('advertising', GetAdvertising.as_view(), name="advertising"),
    path('induce_config', GetInduceConfig.as_view(), name="induce_config"),
    path('time_config', AddTimeConfig.as_view(), name="time_config")
]
