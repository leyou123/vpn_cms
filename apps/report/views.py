import json
import geoip2.database

from django.http import JsonResponse
from django.views.generic.base import View
from django_redis import get_redis_connection

from apps.report.models import Switch
from vpn_cms import settings

# Create your views here.
db13 = get_redis_connection('DB13')

def get_ip(request):
    """
        获取请求ip
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]  # 所以这里是真实的ip
    else:
        ip = request.META.get('REMOTE_ADDR')  # 这里获得代理ip
    return ip


def get_address(ip):

    """
        获取地理位置信息
    """
    country = ""
    region = ""
    try:
        path = f"{settings.BASE_DIR}/GeoLite2-City.mmdb"
        reader = geoip2.database.Reader(path)
        response = reader.city(ip)
        country = response.registered_country.names.get("zh-CN", "")
        region = response.subdivisions[0].names.get("zh-CN", "")
    except Exception as e:
        print(e)
    return {"region": region, "country": country}


class ConnectView(View):

    """
        连接记录表
    """


    def post(self, request):

        # api的控制开关
        # if not db13.exists("connect_flag"):
        #     db13.set("connect_flag", 1)
        #
        # if not db13.get("connect_flag"):
        #     return JsonResponse({"code": 404, "message": "connect api error"})
        bflag = False
        try:
            switch_info = Switch.objects.get(key="connect_flag")
            bflag = switch_info.switch
        except Switch.DoesNotExist:
            res = Switch.objects.create(
                key="connect_flag",
                switch=True,
                comment="report/connect api的开关"
            )
            if res:
                bflag = True

        if not bflag:
            return JsonResponse({"code": 404, "message": "api close"})

        # 根据ip获取位置信息
        ip = get_ip(request)
        geo_info = get_address(ip)

        if not request.body:
            return JsonResponse({"code": 404, "message": "request body error"})

        # 获取前端的数据
        data = json.loads(request.body.decode(encoding="utf-8"))

        # 组装入库数据
        push_data = {
            "user_uuid": data.get("uuid", ""),
            "user_ip": ip,
            "country": geo_info.get("country", ""),
            "city": geo_info.get("region", ""),
            "node_ip": data.get("node_ip", ""),
            "node_name": data.get("node_name", ""),
            "ping_result": data.get("ping_result", 1),
            "connect_result": data.get("connect_result", 1),
            "connect_time": data.get("connect_time", None),
            "dev_name": data.get("dev_name", ""),
            "network": data.get("network", ""),
            "operator": data.get("operator", "")
        }

        # 存储至redis列表
        db13.rpush("connect_data", str(push_data))


        return JsonResponse({"code": 200, "message": "success", "status": True})


class PingFeedbackView(View):

    """
        ping 反馈表
    """


    def post(self, request):

        # if not db13.exists("ping_flag"):
        #     db13.set("ping_flag", 1)
        #
        # if not db13.get("ping_flag"):
        #     return JsonResponse({"code": 404, "message": "ping api error"})
        bflag = False
        try:
            switch_info = Switch.objects.get(key="ping_flag")
            bflag = switch_info.switch
        except Switch.DoesNotExist:
            res = Switch.objects.create(
                key="ping_flag",
                switch=True,
                comment="report/ping api的开关"
            )
            if res:
                bflag = True

        if not bflag:
            return JsonResponse({"code": 404, "message": "api close"})

        ip = get_ip(request)
        geo_info = get_address(ip)

        if not request.body:
            return JsonResponse({"code": 404, "message": "request body error"})

        # 获取数据
        data = json.loads(request.body.decode(encoding="utf-8"))
        items = data.get("items", [])

        for item in items:
            # 组装入库数据
            push_data = {
                "user_uuid": item.get("uuid", ""),
                "user_ip": ip,
                "country": geo_info.get("country", ""),
                "city": geo_info.get("region", ""),
                "node_ip": item.get("node_ip", ""),
                "node_name": item.get("node_name", ""),
                "ping_val1": item.get("ping_val1", ""),
                "ping_val2": item.get("ping_val2", ""),
                "ping_val3": item.get("ping_val3", ""),
                "ping_result": item.get("ping_result", 1),
                "ping_time": item.get("ping_time", "")
            }

            # 存储至redis列表
            db13.rpush("ping_data", str(push_data))


        return JsonResponse({"code": 200, "message": "success", "status": True})



