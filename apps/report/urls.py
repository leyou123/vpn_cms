from django.urls import path
from apps.report.views import PingUpdate, ConnectUpdate, ConnectView, PingFeedbackView

urlpatterns = [
    path('connect', ConnectView.as_view(), name="connect"),
    path('ping', PingFeedbackView.as_view(), name="ping"),
    path('ping_update', PingUpdate.as_view(), name="ping_update"),
    path('connect_update', ConnectUpdate.as_view(), name="connect_update"),
]
