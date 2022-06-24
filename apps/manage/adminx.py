import xadmin
from apps.manage.models import AppPackage, ApiVersion, Advertising, SetMeal, InduceConfig, PayConfig, SetMealType
from apps.manage.models import MembersConfig, Members, UsersConfig, AppPlatform, ShareConfig, TimeConfig


class AppPlatformAdmin(object):
    """
        app平台
    """
    list_display = ["id", "name", "platform_id"]
    model_icon = 'fa fa-apple'


class AppPackageAdmin(object):
    """
        app管理
    """
    list_display = ["id", "name", "package_id", "platform", "device"]
    model_icon = 'fa fa-apple'


class ApiVersionAdmin(object):
    """
        版本配置
    """
    list_display = ["id", "app", "version", "upgrade_version"]
    model_icon = 'fa fa-apple'


class AdvertisingAdmin(object):
    """
        广告配置
    """
    model_icon = 'fa fa-info'

    list_display = ['id', 'app', 'description', 'skip_url', 'background_image_url', 'image_url', 'version',
                    'induction_pay', 'status']


class SetMealTypeAdmin(object):
    """
        套餐列表
    """
    model_icon = 'fa fa-bars'

    list_display = ['id', 'name', 'type']


class SetMealAdmin(object):
    """
        套餐列表
    """
    model_icon = 'fa fa-bars'

    list_display = ['id', 'name', 'platform', 'set_meal_type', 'members', 'goods_id', 'day', 'money']


class InduceConfigAdmin(object):
    """
        诱导付费
    """
    list_display = ["id", 'app', "version", "json_config", "switch"]
    model_icon = 'fa fa-info'


class PayConfigAdmin(object):
    """
        支付配置
    """
    list_display = ["id", 'app', "notify_url", "api_url"]
    model_icon = 'fa fa-info'


class MembersAdmin(object):
    """
        会员
    """
    model_icon = 'fa fa-bars'

    list_display = ['id', 'name', 'type']


class MembersConfigAdmin(object):
    model_icon = 'fa fa-bars'

    list_display = ['id', 'members', 'limit_flow', 'device_count']


class UsersConfigAdmin(object):
    """
        用户配置
    """
    model_icon = 'fa fa-bars'

    list_display = ['id', 'platform', 'temp_day', 'adv_count']


class ShareConfigAdmin(object):
    """
        用户配置
    """
    model_icon = 'fa fa-bars'

    list_display = ['id', 'day']


class TimeConfigAdmin(object):
    """
        用户配置
    """
    model_icon = 'fa fa-bars'

    list_display = ['id', 'name', 'type', 'time', "avd_count"]


xadmin.site.register(AppPlatform, AppPlatformAdmin)
xadmin.site.register(AppPackage, AppPackageAdmin)

xadmin.site.register(ApiVersion, ApiVersionAdmin)
xadmin.site.register(Advertising, AdvertisingAdmin)

xadmin.site.register(Members, MembersAdmin)
xadmin.site.register(MembersConfig, MembersConfigAdmin)

xadmin.site.register(SetMealType, SetMealTypeAdmin)
xadmin.site.register(SetMeal, SetMealAdmin)

xadmin.site.register(UsersConfig, UsersConfigAdmin)
xadmin.site.register(InduceConfig, InduceConfigAdmin)
xadmin.site.register(PayConfig, PayConfigAdmin)

xadmin.site.register(ShareConfig, ShareConfigAdmin)

xadmin.site.register(TimeConfig, TimeConfigAdmin)
