from django.db import models
from apps.users.models import User,Devices
from apps.manage.models import AppPackage, SetMeal


class Orders(models.Model):
    ORDER_STATUS_CHOICES = (
        (0, "订阅成功"),
        (1, "支付成功"),
        (2, "订阅取消"),
        (3, "支付但取消"),
    )

    ORDER_TYPE = (
        (0, "沙箱"),
        (1, "正式")
    )

    SUBSCRIPTION_TYPE = (
        (0, "否"),
        (1, "是")
    )

    id = models.AutoField(primary_key=True, auto_created=True)
    order_id = models.CharField(verbose_name="订单编号", max_length=255, blank=True, null=True, unique=True, db_index=True)
    user = models.BigIntegerField(u"用户ID", default=0, blank=True, null=True, db_index=True)
    app = models.ForeignKey(AppPackage, verbose_name='APP平台', on_delete=models.SET_NULL, blank=True, null=True,
                            db_index=True)
    package_id = models.CharField(u"AppID", max_length=64, null=True, default=None, blank=True, db_index=True)

    set_meal = models.ForeignKey(SetMeal, verbose_name='套餐', on_delete=models.SET_NULL, blank=True, null=True,
                                 db_index=True)
    # product_name = models.CharField(verbose_name="商品名", max_length=128, blank=True, null=True, db_index=True)
    # product_id = models.CharField(verbose_name="商品id", max_length=128, blank=True, null=True, db_index=True)
    # product_type = models.CharField(verbose_name="商品类型", max_length=128, blank=True, null=True, db_index=True)
    # total_amount = models.CharField(verbose_name="金额", max_length=64, blank=True, null=True, db_index=True)
    state = models.SmallIntegerField(verbose_name="状态", choices=ORDER_STATUS_CHOICES, default=0, db_index=True)
    order_type = models.IntegerField(verbose_name="订单类型", default=0, choices=ORDER_TYPE, db_index=True)
    refund_time = models.IntegerField(verbose_name="退单时间", default=0, blank=True, null=True, db_index=True)
    country = models.CharField(u"国家", max_length=128, default="", blank=True, null=True, db_index=True)
    product_time = models.CharField(verbose_name="订单时间", max_length=128, blank=True, null=True, db_index=True)
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间", db_index=True)
    update_time = models.DateTimeField(auto_now=True, verbose_name="更新时间", db_index=True)

    class Meta:
        db_table = 'orders'
        verbose_name = '订单明细'
        verbose_name_plural = verbose_name

    def get_info(self):
        return {
            "id": self.id,
            "product_name": self.set_meal.name,
            "product_id": self.set_meal.goods_id,
            'product_type': self.set_meal.members.members.type,
            "product_time": self.product_time,
            "total_amount": self.set_meal.money,
            "state": self.state,
            "update_time": self.create_time.strftime("%Y-%m-%d %H:%M:%S")
        }


class Product(models.Model):
    """
        paypal商品
    """
    id = models.AutoField(primary_key=True, auto_created=True)
    product_id = models.CharField(u"商品ID", max_length=128,  unique=True, blank=True, null=True, db_index=True)
    name = models.CharField(u"名称", max_length=255, blank=True, null=True, db_index=True)
    type = models.CharField(u"类型", max_length=255, blank=True, null=True, db_index=True)
    category = models.CharField(u"分类", max_length=255, default="", blank=True, null=True, db_index=True)
    image_url = models.CharField(u"图片链接", max_length=255, default="", blank=True, null=True)
    home_url = models.CharField(u"主页链接", max_length=255, default="", blank=True, null=True)
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间", db_index=True)

    class Meta:
        db_table = 'Product'
        verbose_name = '商品'
        verbose_name_plural = verbose_name

    def __str__(self):
        return str(self.name)


class ProductPlan(models.Model):
    """
        paypal商品计划
    """
    id = models.AutoField(primary_key=True, auto_created=True)
    plan_id = models.CharField(u"计划ID", max_length=128, unique=True, blank=True, null=True, db_index=True)
    product = models.ForeignKey(Product, verbose_name='商品', on_delete=models.SET_NULL, blank=True, null=True)
    # app = models.ForeignKey(AppPackage, verbose_name='APP平台', on_delete=models.SET_NULL, blank=True, null=True)
    set_meal = models.ForeignKey(SetMeal, verbose_name='套餐', on_delete=models.SET_NULL, blank=True, null=True)
    name = models.CharField(u"名称", max_length=255, blank=True, null=True, db_index=True)
    description = models.CharField(u"描述", max_length=255, blank=True, null=True, db_index=True)
    billing_number = models.IntegerField(verbose_name="计费周期次数", default=0)
    currency_code = models.CharField(u"货币单位", max_length=128, blank=True, null=True, db_index=True)
    price = models.DecimalField(u"价格", decimal_places=2, max_digits=5)
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间", db_index=True)

    class Meta:
        db_table = 'ProductPlan'
        verbose_name = '商品计划'
        verbose_name_plural = verbose_name

    def get_info(self):
        return {
            # "id": self.id,
            "plan_id": self.plan_id,
            "name": self.name,
            "description": self.description,
            # "billing_number": self.billing_number,
            "currency_code": self.currency_code,
            "price": self.price
        }


if __name__ == '__main__':
    pass
    # all_order = TrojanOrders.objects.all()
    #
    # for orders in all_order:
    #
    #     TrojanOrders.objects.filter(id=orders.id).update(
    #         app=2
    #     )
