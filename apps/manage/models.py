from django.db import models
from django_redis import get_redis_connection

db4 = get_redis_connection('DB4')

class AppPlatform(models.Model):
    """
    App包名
    """
    id = models.AutoField(primary_key=True, auto_created=True)
    name = models.CharField(u"平台名字", max_length=128, null=True, default=None, blank=True)
    platform_id = models.CharField(u"平台id", max_length=64, null=True, default=None, blank=True, unique=True,db_index=True)

    class Meta:
        verbose_name = 'APP平台'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class AppPackage(models.Model):
    """
    App包名
    """
    DEVICE = (
        (1, "IOS"),
        (2, "Android"),
        (3, "PC"),
        (4, "MAC"),
    )

    id = models.AutoField(primary_key=True, auto_created=True)
    platform = models.ForeignKey(AppPlatform, on_delete=models.SET_NULL, verbose_name='应用平台', blank=True, null=True)
    name = models.CharField(u"app名字", max_length=128, null=True, default=None, blank=True)
    package_id = models.CharField(u"AppID", max_length=64, null=True, default=None, blank=True, unique=True,
                                  db_index=True)
    device = models.IntegerField(u"设备平台", default=1, choices=DEVICE)

    class Meta:
        verbose_name = 'APP'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class ApiVersion(models.Model):
    """
      应用版本
    """
    id = models.AutoField(primary_key=True, auto_created=True)
    app = models.ForeignKey(AppPackage, on_delete=models.CASCADE, verbose_name='APP_ID', blank=True, null=True)
    version = models.CharField(u"线上版本号", max_length=32, null=True, default=None, blank=True)
    upgrade_version = models.CharField(u"强制升级版本号", max_length=32, null=True, default=None, blank=True)

    class Meta:
        verbose_name = '应用版本配置'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.app.name

    def get_info(self):
        """
        获取用户信息
        :return:
        """
        info = {
            "current_version": self.version,
            "upgrade_version": self.upgrade_version,
        }
        return info


class Advertising(models.Model):
    ADV_TYPE = (
        (1, "第三方广告"),
        (2, "诱导付费"),
    )
    id = models.AutoField(primary_key=True, auto_created=True)
    app = models.ForeignKey(AppPackage, on_delete=models.CASCADE, verbose_name='APP_ID', blank=True, null=True)
    type = models.IntegerField(verbose_name="类型", default=1, choices=ADV_TYPE)
    description = models.CharField(u"描述", max_length=255, null=True, default="", blank=True)
    skip_url = models.CharField(u"跳转连接", max_length=255, null=True, default="", blank=True)
    background_image_url = models.CharField(u"背景图片", max_length=255, null=True, default="", blank=True)
    image_url = models.CharField(u"图片", max_length=255, null=True, default="", blank=True)
    version = models.CharField(u"版本号", max_length=32, null=True, default="", blank=True)
    induction_pay = models.BooleanField(u"诱导付费", default=False)
    status = models.BooleanField(u"状态", default=False)

    def get_info(self):
        image_url = ""
        background_image_url = ""
        version = ""
        if self.image_url:
            image_url = self.image_url

        if self.background_image_url:
            background_image_url = self.background_image_url

        if self.version:
            version = self.version
        obj = {
            "icon": image_url,
            "background_image_url": background_image_url,
            "skip_url": self.skip_url,
            "description": self.description,
            "induction_pay": self.induction_pay,
            "version": version,
            "status": self.status
        }
        return obj

    class Meta:
        verbose_name = '广告版本配置'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.app.name


class Members(models.Model):
    id = models.AutoField(primary_key=True, auto_created=True)
    name = models.CharField(u"名字", max_length=128, blank=True, null=True, db_index=True)
    type = models.IntegerField(verbose_name="类型", default=0)

    class Meta:
        verbose_name = '会员类型'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class MembersConfig(models.Model):
    id = models.AutoField(primary_key=True, auto_created=True)
    members = models.ForeignKey(Members, on_delete=models.SET_NULL, verbose_name='会员类型', blank=True, null=True)
    limit_flow = models.IntegerField(u"流量限制 单位:G", default=0)
    device_count = models.IntegerField(verbose_name="最大设备数", default=0)

    class Meta:
        verbose_name = '会员配置'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.members.name


class UsersConfig(models.Model):
    id = models.AutoField(primary_key=True, auto_created=True)
    platform = models.ForeignKey(AppPlatform, on_delete=models.SET_NULL, verbose_name='应用平台', blank=True, null=True)
    temp_day = models.IntegerField(u"试用天数 单位:天", default=0)
    adv_count = models.IntegerField(verbose_name="广告次数", default=0)

    class Meta:
        verbose_name = '用户配置'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.platform.name

    def info(self):
        info = {
            "platform": self.platform.name,
            "temp_day": self.temp_day,
            "adv_count": 5 - self.adv_count
        }
        return info


class SetMealType(models.Model):
    id = models.AutoField(primary_key=True, auto_created=True)
    name = models.CharField(u"名字", max_length=128, blank=True, null=True, db_index=True)
    type = models.IntegerField(verbose_name="类型", default=0)

    class Meta:
        verbose_name = '套餐类型'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class SetMeal(models.Model):
    """
        套餐表配置表
    """
    platform = models.ForeignKey(AppPlatform, on_delete=models.SET_NULL, verbose_name='应用平台', blank=True, null=True)
    set_meal_type = models.ForeignKey(SetMealType, verbose_name='套餐类型', on_delete=models.SET_NULL, blank=True,null=True)
    members = models.ForeignKey(MembersConfig, verbose_name='会员类型', on_delete=models.SET_NULL, blank=True, null=True)
    goods_id = models.CharField(verbose_name="商品id", max_length=64, blank=True, null=True)
    name = models.CharField(u'商品名称', max_length=150, null=True, help_text='请输入商品名称')
    money = models.DecimalField(verbose_name="金额", default=0, decimal_places=2, max_digits=20, blank=True, null=True)
    day = models.IntegerField(verbose_name="会员天数", default=0, blank=True, null=True)

    class Meta:
        verbose_name = '套餐配置'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.set_meal_type.name

    def get_info(self):
        return {
            "name": self.name,
            "money": self.money,
        }


class InduceConfig(models.Model):
    """
      诱导配置
    """

    id = models.AutoField(primary_key=True, auto_created=True)
    app = models.ForeignKey(AppPackage, on_delete=models.CASCADE, verbose_name='APP_ID', blank=True, null=True)
    version = models.CharField(u"线上版本号", max_length=128, null=True, default=None, blank=True)
    json_config = models.TextField(u"json配置", default="")

    class Meta:
        verbose_name = '诱导配置'
        verbose_name_plural = verbose_name

    def get_info(self):
        json_data = ""
        if self.json_config:
            json_data = str(self.json_config).replace("\r\n", "")

        info = {
            "current_version": self.version,
            "json_config": json_data
        }
        return info

    def save(self, *args, **kwargs):
        redis_key_name = f"version_{self.app.package_id}_{self.version}"
        db4.delete(redis_key_name)
        super().save(*args, **kwargs)



    def __str__(self):
        return self.app.name


class PayConfig(models.Model):
    """
      支付配置
    """
    id = models.AutoField(primary_key=True, auto_created=True)
    app = models.ForeignKey(AppPackage, on_delete=models.CASCADE, verbose_name='APP_ID', blank=True, null=True)
    buy_url = models.CharField(u"IOS正式支付url", max_length=255, null=True, default=None, blank=True)
    sandbox_url = models.CharField(u"IOS沙盒url", max_length=255, null=True, default=None, blank=True)
    pay_password = models.CharField(u"IOS支付秘钥", max_length=128, null=True, default=None, blank=True)
    do_main = models.CharField(u"服务器域名", max_length=255, null=True, default=None, blank=True)
    notify_url = models.CharField(u"ios通知url", max_length=255, null=True, default=None, blank=True)
    api_url = models.CharField(u"谷歌API", max_length=255, null=True, default=None, blank=True)
    token_url = models.CharField(u"谷歌token", max_length=255, null=True, default=None, blank=True)
    grant_type = models.CharField(u"谷歌grant_type", max_length=128, null=True, default=None, blank=True)
    client_id = models.CharField(u"谷歌client_id", max_length=128, null=True, default=None, blank=True)
    client_secret = models.CharField(u"谷歌client_secret", max_length=128, null=True, default=None, blank=True)
    refresh_token = models.CharField(u"谷歌refresh_token", max_length=255, null=True, default=None, blank=True)
    test_id = models.CharField(u"谷歌支付测试ID", max_length=255, null=True, default=None, blank=True)

    GRANT_TYPE = "refresh_token"

    class Meta:
        verbose_name = '支付配置'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.app.name


class ShareConfig(models.Model):
    id = models.AutoField(primary_key=True, auto_created=True)
    day = models.IntegerField(u"分享天数 单位:天", default=0)

    class Meta:
        verbose_name = '分享配置'
        verbose_name_plural = verbose_name


class TimeConfig(models.Model):
    """
       时长配置
    """
    id = models.AutoField(primary_key=True, auto_created=True)
    name = models.CharField(u"名称", max_length=128, null=True, default=None, blank=True)
    type = models.IntegerField(u"类型", default=0)
    time = models.BigIntegerField(u"时间 单位:秒", default=0)
    avd_count = models.IntegerField(u"广告计数 单位：次", default=0)


    class Meta:
        verbose_name = '时间配置'
        verbose_name_plural = verbose_name

    def get_info(self):
        info = {
            "name": self.name,
            "type": self.type,
            "time": self.time
        }
        return info

