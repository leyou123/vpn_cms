import time
import datetime
from django.db import models
from apps.manage.models import AppPackage, SetMeal, MembersConfig, UsersConfig,AppPlatform
from django_redis import get_redis_connection

db5 = get_redis_connection('DB5')



class User(models.Model):
    SUBSCRIPTION_TYPE = (
        (0, "否"),
        (1, "是")
    )

    FIRST_SUBSCRIPTION = (
        (0, "否"),
        (1, "是")
    )

    NEW_USER = (
        (0, "否"),
        (1, "是")
    )

    EXCHANGE = (
        (0, "否"),
        (1, "是")
    )

    WHITE_TYPE = (
        (0, "正常"),
        (1, "拦截")
    )

    id = models.AutoField(primary_key=True, auto_created=True)
    platform = models.ForeignKey(AppPlatform, on_delete=models.SET_NULL, verbose_name='应用平台', blank=True, null=True)

    # app = models.ForeignKey(AppPackage, verbose_name='APP平台', on_delete=models.SET_NULL, blank=True, null=True,
    #                         db_index=True)
    set_meal = models.ForeignKey(SetMeal, verbose_name='套餐类型', on_delete=models.SET_NULL, blank=True, null=True,
                                 db_index=True)
    member_type = models.ForeignKey(MembersConfig, verbose_name='会员类型', on_delete=models.SET_NULL, blank=True,
                                    null=True)

    uid = models.BigIntegerField(u'uid', default=0, unique=True, db_index=True)
    email = models.EmailField(u"邮箱", default=None, blank=True, null=True, db_index=True)
    password = models.CharField(u"用户密码", max_length=128, blank=True, null=True, db_index=True)
    # device_token = models.CharField(u"通知Token", max_length=255, default=None, blank=True, null=True, db_index=True)
    member_validity_time = models.BigIntegerField(u"会员有效期", default=0, blank=True, null=True, db_index=True)
    first_subscription = models.IntegerField(u"已订阅过", default=0, choices=FIRST_SUBSCRIPTION, db_index=True)
    subscription_type = models.IntegerField(u"订阅状态", default=2, choices=SUBSCRIPTION_TYPE, db_index=True)
    new_user = models.IntegerField(u"新用户", default=0, choices=NEW_USER, db_index=True)
    exchange = models.IntegerField(u"兑换", default=0, choices=EXCHANGE, db_index=True)
    white_type = models.IntegerField(u"白名单", default=0, choices=WHITE_TYPE)
    flow_user = models.FloatField(u"已用流量单位GB", default=0, blank=True, db_index=True)
    country = models.CharField(u"国家", max_length=128, blank=True, null=True, db_index=True)
    region = models.CharField(u"地区", max_length=128, blank=True, null=True)
    adv_count = models.IntegerField(verbose_name="广告计数", default=0)
    device_count = models.IntegerField(verbose_name="设备数", default=0)
    max_device_count = models.IntegerField(verbose_name="最大设备数", default=0)
    code = models.CharField(u"分享码", max_length=128, blank=True, null=True, db_index=True)
    exchange_count = models.IntegerField(u"兑换次数", default=0)
    create_time = models.DateTimeField(u"创建时间", auto_now_add=True, blank=True, null=True, db_index=True)
    login_time = models.DateTimeField(u"登录时间", auto_now_add=True, blank=True, null=True, db_index=True)


    class Meta:
        db_table = 'users'
        verbose_name = '用户'
        verbose_name_plural = verbose_name

    def conv_date(self):
        if self.login_time:
            this_date = str(self.login_time.strftime('%Y-%m-%d %H:%M:%S'))
            str_date = datetime.datetime.strptime(this_date, '%Y-%m-%d %H:%M:%S')
            # 把datetime转变为时间戳
            this_date = int(time.mktime(str_date.timetuple()))
            return this_date
        else:
            return None

    def create_date(self):
        if self.create_time:
            this_date = str(self.create_time.strftime('%Y-%m-%d %H:%M:%S'))
            str_date = datetime.datetime.strptime(this_date, '%Y-%m-%d %H:%M:%S')
            # 把datetime转变为时间戳
            this_date = int(time.mktime(str_date.timetuple()))
            return this_date
        else:
            return None



    def get_info(self):
        """
        获取用户信息
        :return:
        """
        config = UsersConfig.objects.first()

        set_meal = ""
        if self.set_meal:
            set_meal = self.set_meal.goods_id

        email = ""
        if self.email:
            email = self.email


        info = {
            "uid": self.uid,
            "white_type": self.white_type,
            "email":email,
            "member_type": self.member_type.members.type,
            "set_meal":set_meal,
            "subscription": self.first_subscription,
            "subscription_status": self.subscription_type,
            "member_validity_time": self.member_validity_time,
            "max_device_count":self.max_device_count,
            "device_count":self.device_count,
            "country": self.country,
            "code":self.code,
            "is_exchange":self.exchange,
            "adv_count": config.adv_count - self.adv_count,
            "login_time":int(time.time())
        }
        return info

    def get_uuid(self):
        """
        获取用户信息
        :return:
        """
        info = {
            "uid": self.uid,
            "create_time":self.create_date()
        }
        return info

    def save(self, *args, **kwargs):
        deviecs = Devices.objects.filter(user=self.uid).all()
        for one_device in deviecs:
            redis_key_name = str(one_device.uuid + one_device.package_id)
            db5.delete(redis_key_name)
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.uid)



class Devices(models.Model):
    id = models.AutoField(primary_key=True, auto_created=True)
    platform = models.ForeignKey(AppPlatform, on_delete=models.SET_NULL, verbose_name='应用平台', blank=True, null=True)
    user = models.BigIntegerField(u"用户ID", default=0, blank=True, null=True, db_index=True)
    uuid = models.CharField(u'uuid', max_length=128, null=True, default=None, blank=True, db_index=True)
    package_id = models.CharField(u"App_id", max_length=64, null=True, default=None, blank=True,db_index=True)
    flow = models.FloatField(u"已用流量(单位:GB)", default=0, blank=True, db_index=True)
    device_token = models.CharField(u"通知Token", max_length=255, default=None, blank=True, null=True, db_index=True)
    create_time = models.DateTimeField(u"创建时间", auto_now_add=True, blank=True, null=True, db_index=True)
    login_time = models.DateTimeField(u"登录时间", auto_now_add=True, blank=True, null=True, db_index=True)

    class Meta:
        verbose_name = '设备管理'
        verbose_name_plural = verbose_name

    def get_info(self):
        """
        获取用户信息
        :return:
        """
        package_id =""
        if self.package_id:
            package_id = self.package_id

        info = {
            "id": self.id,
            "uid":self.user,
            "uuid": self.uuid,
            "package_id":package_id,
            "flow": self.flow
        }
        return info



class UserFeedback(models.Model):


    id = models.AutoField(primary_key=True, auto_created=True)
    uid = models.BigIntegerField(u'uid', default=0,db_index=True)
    type = models.CharField(u"类型", max_length=255, null=True, default=None, blank=True)
    email = models.CharField(u"邮箱", max_length=255, null=True, default=None, blank=True)
    content = models.TextField(u"内容", null=True, default=None, blank=True)
    create_time = models.DateTimeField(u"创建时间", auto_now_add=True, blank=True, null=True, db_index=True)

    name = models.CharField(u"产品名称", max_length=128, null=True, default=None, blank=True)
    country = models.CharField(u"国家", max_length=128, null=True, default=None, blank=True)
    vip_name = models.CharField(u"会员类型", max_length=128, null=True, default=None, blank=True)


    class Meta:
        verbose_name = '用户反馈'
        verbose_name_plural = verbose_name



class UserShareTask(models.Model):
    TASK_TYPE = (
        (0, "未完成"),
        (1, "完成未领取"),
        (2, "已领取")
    )

    id = models.AutoField(primary_key=True, auto_created=True)

    name = models.CharField(u"任务名", max_length=255, null=True, default=None, blank=True)
    uid = models.BigIntegerField(u'uid', default=0, db_index=True)
    platform = models.ForeignKey(AppPlatform, on_delete=models.SET_NULL, verbose_name='应用平台', blank=True, null=True)
    app = models.ForeignKey(AppPackage, verbose_name='APP平台', on_delete=models.SET_NULL, blank=True, null=True,
                            db_index=True)
    status = models.IntegerField(u"状态", default=0, choices=TASK_TYPE, db_index=True)
    create_time = models.DateTimeField(u"创建时间", auto_now_add=True, blank=True, null=True, db_index=True)

    class Meta:
        verbose_name = '用户分享任务'
        verbose_name_plural = verbose_name

    def get_info(self):
        """
        获取用户信息
        :return:
        """
        info = {
            "id":self.id,
            "uid": self.uid,
            "name": self.name,
            "status": self.status
        }
        return info


