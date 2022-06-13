"""vpn_cms URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include,re_path
import xadmin
from django.views.static import serve
from vpn_cms import settings
from apps.users.views import Index
# from apps.ios_bj.views import UpdateVersionInfo,SetPackage
from apps.manage.views import GetInduceConfig, GetAdvertising,Version
api = 'v2/'

urlpatterns = [
    path('', Index.as_view()),
    path('xadmin/', xadmin.site.urls),
    path(f'{api}user/', include('users.urls'), name="user"),
    path(f'{api}node/', include('nodes.urls'), name="node"),
    path(f'{api}manage/', include('manage.urls'), name="manage"),
    path(f'{api}orders/', include('orders.urls'), name="orders"),
    path(f'{api}report/', include('report.urls'), name="report"),

    # path(f'api/v1/node/update_version', UpdateVersionInfo.as_view()),
    # path(f'api/v1/user/disposes', SetPackage.as_view()),
    # path(f'version', Version.as_view(), name="update_version"),
    # path(f'{api}manage/advertising', GetAdvertising.as_view(), name="advertising"),
    # path(f'{api}manage/induce_config', GetInduceConfig.as_view(), name="induce_config"),

    # re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),

]

