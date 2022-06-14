from django.db import models

# Create your models here.

class LinkageRecord(models.Model):

    """
    连接记录表
    """

    # 连接记录表：格式为：用户IP，用户国家，用户城市，节点ip，节点名称，ping结果【成功 / 失败】，连接结果【成功 / 失败】，连接时间，设备名称，网络，运营商

    PING_RESULT_CHOICES = (
        (1, "成功"),
        (0, "失败"),
    )
    CONNECT_RESULT_CHOICES = (
        (1, "成功"),
        (0, "失败"),
    )

    user_uuid = models.CharField(u'uuid', max_length=128, null=True, default=None, blank=True, db_index=True)
    user_ip = models.CharField(u"用户IP", max_length=128, blank=True, null=True, db_index=True)
    country = models.CharField(u"用户国家", max_length=128, blank=True, null=True, db_index=True)
    city = models.CharField(u"用户城市", max_length=128, blank=True, null=True, db_index=True)
    node_ip = models.CharField(u"节点ip", max_length=128, blank=True, null=True, db_index=True)
    node_name = models.CharField(u"节点名称", max_length=128, blank=True, null=True, db_index=True)
    ping_result = models.IntegerField(u"ping结果", choices=PING_RESULT_CHOICES, default=1, db_index=True)
    connect_result = models.IntegerField(u"连接结果", choices=CONNECT_RESULT_CHOICES, default=1, db_index=True)
    connect_time = models.DateTimeField(u"连接时间", blank=True, null=True)
    dev_name = models.CharField(u"设备名称", max_length=128, blank=True, null=True)
    network = models.CharField(u"网络", max_length=128, blank=True, null=True)
    operator = models.CharField(u"运营商", max_length=128, blank=True, null=True)

    class Meta:
        verbose_name = '连接记录表'
        verbose_name_plural = verbose_name

class PingFeedback(models.Model):

    """
    ping反馈表
    """

    # ping反馈表：格式为：用户IP，用户国家，用户城市，节点ip，节点名称，ping返回值，ping结果【成功 / 失败】，ping时间
    PING_RESULT_CHOICES = (
        (1, "成功"),
        (0, "失败"),
    )

    user_uuid = models.CharField(u'uuid', max_length=128, null=True, default=None, blank=True, db_index=True)
    user_ip = models.CharField(u"用户IP", max_length=128, blank=True, null=True, db_index=True)
    country = models.CharField(u"用户国家", max_length=128, blank=True, null=True, db_index=True)
    city = models.CharField(u"用户城市", max_length=128, blank=True, null=True, db_index=True)
    node_ip = models.CharField(u"节点ip", max_length=128, blank=True, null=True, db_index=True)
    node_name = models.CharField(u"节点名称", max_length=128, blank=True, null=True, db_index=True)
    ping_val1 = models.CharField(u"ping返回值1", max_length=128, blank=True, null=True)
    ping_val2 = models.CharField(u"ping返回值2", max_length=128, blank=True, null=True)
    ping_val3 = models.CharField(u"ping返回值3", max_length=128, blank=True, null=True)
    ping_result = models.IntegerField(u"ping结果", choices=PING_RESULT_CHOICES, default=1, db_index=True)
    ping_time = models.DateTimeField(u"ping时间", blank=True, null=True)

    class Meta:
        verbose_name = 'ping反馈表'
        verbose_name_plural = verbose_name


class Switch(models.Model):
    """
        控制api的开关
    """
    key = models.CharField(max_length=100)
    switch = models.BooleanField()
    comment = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'api开关'
        verbose_name_plural = verbose_name