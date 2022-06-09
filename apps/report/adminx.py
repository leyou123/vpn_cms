import xadmin

from apps.report.models import Switch, LinkageRecord, PingFeedback

class SwitchAdmin(object):

    list_display = ["key", "switch", "comment"]


class LinkageRecordAdmin(object):

    list_display = ["user_ip", "country", "city", "node_ip", "node_name", "ping_result", "connect_result", "connect_time", "dev_name", "network", "operator", "user_uuid"]


class PingFeedbackAdmin(object):

    list_display = ["user_ip", "country", "city", "node_ip", "node_name", "ping_val1", "ping_val2", "ping_val3", "ping_result", "ping_time", "user_uuid"]


xadmin.site.register(Switch, SwitchAdmin)
xadmin.site.register(LinkageRecord, LinkageRecordAdmin)
xadmin.site.register(PingFeedback, PingFeedbackAdmin)
