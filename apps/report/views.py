import json
import geoip2.database

from django.http import JsonResponse
from django.views.generic.base import View
from django_redis import get_redis_connection
from django.db import transaction

from .models import Switch, PingFeedback, LinkageRecord
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


def get_redis_list(key):
    # 获取数据
    data = db13.blpop(key)  # data是一个二进制元组，（b'key_name, b'{"api_key":"1234"}）
    # 所以如果想得到value值，得先进行解包
    key_name, value_dict = data
    # value_dict = b'{"api_key":"1234"}
    # 需要强调一下，任何从redis取出来的数据，都是二进制，要先进行二进制解码
    value_dict = value_dict.decode("UTF-8")
    # 解码后value_dict的类型是string, 如果想要得到其中字典的值，就需要进行转换
    value_dict = eval(value_dict)  # eval可以智能地根据字符串中的数据类型进行转换。
    return value_dict


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


class PingUpdate(View):

    """
        更新ping数据
    """

    def post(self, request):
        max_number = 50000
        target = ["AM", "am", "pm", "PM", "p.m", "a.m", "P.M", "A.M"]
        length = db13.llen("ping_data")
        if length >= max_number:
            length = max_number
        for i in range(0, length):
            data = get_redis_list("ping_data")

            ping_time = data.get("ping_time", "")
            for tar in target:
                if tar in ping_time:
                    ping_time = ping_time[:-3]
                    break
            # 开启事务
            with transaction.atomic():
                # 创建事务保存点
                save_id = transaction.savepoint()

                try:
                    create_reuslt = PingFeedback.objects.create(
                        user_uuid=data.get("user_uuid", ""),
                        user_ip=data.get("user_ip", ""),
                        country=data.get("country", ""),
                        city=data.get("city", ""),
                        node_ip=data.get("node_ip", ""),
                        node_name=data.get("node_name", ""),
                        ping_val1=data.get("ping_val1", ""),
                        ping_val2=data.get("ping_val2", ""),
                        ping_val3=data.get("ping_val3", ""),
                        ping_result=data.get("ping_result", 1),
                        ping_time=ping_time
                    )
                except Exception as e:
                    transaction.savepoint_rollback(save_id)
                    db13.rpush("ping_data", str(data))
                    print("ping update error", e)
                    return JsonResponse({"code": 404, "message": "update ping error"})

            if not create_reuslt:
                transaction.savepoint_rollback(save_id)
                db13.rpush("ping_data", str(data))
                print("ping update error")
                return JsonResponse({"code": 404, "message": "update ping error"})

            # 显式的提交一次事务
            transaction.savepoint_commit(save_id)

        return JsonResponse({"code": 200, "message": "success"})


class ConnectUpdate(View):
    """
        更新连接数据
    """
    def post(self, request):
        max_number = 50000
        target = ["AM", "am", "pm", "PM", "p.m", "a.m", "P.M", "A.M"]
        length = db13.llen("connect_data")
        if length >= max_number:
            length = max_number
        for i in range(0, length):
            data = get_redis_list("connect_data")
            connect_time = data.get("connect_time", "")
            for tar in target:
                if tar in connect_time:
                    connect_time = connect_time[:-3]
                    break
            # 开启事务
            with transaction.atomic():
                # 创建事务保存点
                save_id = transaction.savepoint()

                try:
                    create_reuslt = LinkageRecord.objects.create(
                        user_uuid=data.get("user_uuid", ""),
                        user_ip=data.get("user_ip", ""),
                        country=data.get("country", ""),
                        city=data.get("city", ""),
                        node_ip=data.get("node_ip", ""),
                        node_name=data.get("node_name", ""),
                        ping_result=data.get("ping_result", 1),
                        connect_result=data.get("connect_result", 1),
                        connect_time=connect_time,
                        dev_name=data.get("dev_name", ""),
                        network=data.get("network", ""),
                        operator=data.get("operator", "")
                    )
                except Exception as e:
                    transaction.savepoint_rollback(save_id)
                    db13.rpush("connect_data", str(data))
                    print("connect update error", e)
                    return JsonResponse({"code": 404, "message": "update connect error"})

            if not create_reuslt:
                transaction.savepoint_rollback(save_id)
                db13.rpush("connect_data", str(data))
                print("connect update error")
                return JsonResponse({"code": 404, "message": "update connect error"})

            # 显式的提交一次事务
            transaction.savepoint_commit(save_id)
        return JsonResponse({"code": 200, "message": "success"})


# class CountryView(View):
#     """
#         获取所有国家成功率
#     """
#     def post(self, request):
#
#         data = json.loads(request.body.decode(encoding="utf-8"))
#
#         # PingFeedback.objects.filter(ping_time=)
#
#         return JsonResponse({"code": 200, "message": "success", "data":{}})