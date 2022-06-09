import xadmin
from xadmin import views
from apps.users.models import User, Devices, UserFeedback
import time


class BaseSetting(object):
    # 添加主题功能
    enable_themes = True
    use_bootswatch = True


class GlobalSettings(object):
    site_title = "VPN管理后台"
    # 菜单收缩
    menu_style = "accordion"

    def get_site_menu(self):
        return [
            {
                'title': 'VPN统计',
                'icon': 'fa fa-bar-chart-o',
                'menus': (
                    {
                        'title': '数据统计',
                        'icon': 'fa fa-bar-chart-o',
                        'url': "https://datas.9527.click/xadmin"

                    },
                )
            }
        ]


class UserAdmin(object):
    """
        用户
    """
    list_display = [
        'uid', 'email', 'platform', 'member_type', 'set_meal', 'subscription_type', 'member_time',
        'flow_user', 'country', 'white_type', 'login_time'
    ]

    model_icon = 'fa fa-user'

    search_fields = ['uid', 'email']

    list_filter = (
        'member_type', 'white_type', 'country', 'subscription_type', 'first_subscription',
        'platform', 'login_time', 'create_time'
    )

    date_hierarchy = ['create_time']
    list_editable = ['member_type', 'white_type', 'member_time', 'first_subscription']

    list_per_page = 20

    def member_time(self, obj):
        """
        时间戳 重写 格式
        :param obj:
        :return:
        """
        x = time.localtime(obj.member_validity_time)
        return time.strftime('%Y-%m-%d %H:%M:%S', x)

    def subscription_exp_time(self, obj):
        """
        订阅时间戳 重写 格式
        :param obj:
        :return:
        """

        sub_time = obj.subscription_expiration_time

        if not sub_time:
            return ""
        x = time.localtime(sub_time)
        return time.strftime('%Y-%m-%d %H:%M:%S', x)

    def purchase_exp_time(self, obj):
        """
        购买时间戳 重写 格式
        :param obj:
        :return:
        """

        sub_time = obj.purchase_expiration_time

        if not sub_time:
            return ""
        x = time.localtime(sub_time)
        return time.strftime('%Y-%m-%d %H:%M:%S', x)

    subscription_exp_time.short_description = '订阅到期时间'
    purchase_exp_time.short_description = '购买到期时间'
    member_time.short_description = '会员到期时间'


class DevicesAdmin(object):
    """
        设备配置
    """
    model_icon = 'fa fa-bars'
    search_fields = ['id', 'user', 'uuid', "package_id", "device_token"]
    list_filter = (
        'platform', 'login_time', 'create_time'
    )

    list_display = ['uuid', 'platform', 'user', "package_id", "device_token", 'login_time', 'create_time']


class UserFeedbackAdmin(object):
    """
        设备配置
    """
    model_icon = 'fa fa-bars'

    list_display = ['uid', 'email', 'type']


xadmin.site.register(User, UserAdmin)
xadmin.site.register(Devices, DevicesAdmin)
xadmin.site.register(UserFeedback, UserFeedbackAdmin)

xadmin.site.register(views.CommAdminView, GlobalSettings)
