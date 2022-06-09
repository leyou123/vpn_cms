from django.urls import path
from apps.report.views import ConnectView, PingFeedbackView

urlpatterns = [
    path('connect', ConnectView.as_view(), name="connect"),
    path('ping', PingFeedbackView.as_view(), name="ping"),
]
