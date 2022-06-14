import xadmin

from apps.report.models import Switch, LinkageRecord, PingFeedback

class SwitchAdmin(object):

    list_display = ["key", "switch", "comment"]


class LinkageRecordAdmin(object):

    list_display = ["user_ip", "country", "city", "node_ip", "node_name", "ping_result", "connect_result", "connect_time", "dev_name", "network", "operator", "user_uuid"]


class PingFeedbackAdmin(object):

    list_display = ["user_ip", "country", "city", "node_ip", "node_name", "ping1", "ping2", "ping3", "ping_result", "ping_time", "user_uuid"]

    # 自定义admin后台显示字段
    def ping1(self, obj):
        val = obj.ping_val1
        try:
            val = val.split(".")[0]
        except Exception as e:
            return obj.ping_val1
        return val
    def ping2(self, obj):
        val = obj.ping_val2
        try:
            val = val.split(".")[0]
        except Exception as e:
            return obj.ping_val2
        return val
    def ping3(self, obj):
        val = obj.ping_val3
        try:
            val = val.split(".")[0]
        except Exception as e:
            return obj.ping_val3
        return val

xadmin.site.register(Switch, SwitchAdmin)
xadmin.site.register(LinkageRecord, LinkageRecordAdmin)
xadmin.site.register(PingFeedback, PingFeedbackAdmin)
