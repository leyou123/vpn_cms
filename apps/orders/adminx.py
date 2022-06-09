import xadmin
from apps.orders.models import Orders, Product, ProductPlan
import time


class OrderAdmin(object):
    """
        用户节点
    """
    list_display = ["order_id", "user", "app", 'set_meal', "country", 'state', 'order_type', "order_time",
                    'update_time',
                    'subscription_refund_time']

    search_fields = ['order_id', 'user', "package_id"]
    model_icon = 'fa fa-shopping-cart'

    list_filter = ['order_type', "state", "app", 'update_time']
    list_per_page = 20

    def order_time(self, obj):
        """
        时间戳 重写 格式
        :param obj:
        :return:
        """

        x = time.localtime(int(obj.product_time) / 1000)
        return time.strftime('%Y-%m-%d %H:%M:%S', x)

    def subscription_refund_time(self, obj):
        """
        订阅时间戳 重写 格式
        :param obj:
        :return:
        """

        refund_time = obj.refund_time

        if not refund_time:
            return ""
        x = time.localtime(refund_time)
        return time.strftime('%Y-%m-%d %H:%M:%S', x)

    subscription_refund_time.short_description = "退单时间"

    order_time.short_description = '订单时间'


class ProductAdmin(object):
    """
        用户节点
    """
    list_display = ["name", "product_id", "type"]

    model_icon = 'fa fa-shopping-cart'


class ProductPlanAdmin(object):
    """
        用户
    """
    list_display = ["id", "plan_id", "product", "set_meal", "billing_number", "price"]


xadmin.site.register(Orders, OrderAdmin)
xadmin.site.register(Product, ProductAdmin)
xadmin.site.register(ProductPlan, ProductPlanAdmin)
