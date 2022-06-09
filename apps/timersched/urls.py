from django.urls import path
from apps.timersched import views

urlpatterns = [
    path('', views.index, name="timerss"),
]
