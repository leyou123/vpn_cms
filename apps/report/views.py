import json
import re
import datetime
import random
import time
import requests
import geoip2.database
from threading import Thread


from django.http import JsonResponse
from django.views.generic.base import View
from django_redis import get_redis_connection
from django.db import transaction
from django.db.models import Count, Q
from django.db.models import Func, Value

from .models import Switch, PingFeedback, LinkageRecord, PingFeedback2
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


# def get_redis_list(key):
#     # 获取数据
#     data = db13.blpop(key)  # data是一个二进制元组，（b'key_name, b'{"api_key":"1234"}）
#     # 所以如果想得到value值，得先进行解包
#     key_name, value_dict = data
#     # value_dict = b'{"api_key":"1234"}
#     # 需要强调一下，任何从redis取出来的数据，都是二进制，要先进行二进制解码
#     value_dict = value_dict.decode("UTF-8")
#     # 解码后value_dict的类型是string, 如果想要得到其中字典的值，就需要进行转换
#     value_dict = eval(value_dict)  # eval可以智能地根据字符串中的数据类型进行转换。
#     return value_dict
def get_redis_list(key, start, end):
    res = []
    # 获取数据
    rlist = db13.lrange(key, start, end - 1)
    for data in rlist:
        # data是一个二进制元组，（b'key_name, b'{"api_key":"1234"}）
        # 所以如果想得到value值，得先进行解包
        value_dict = data.decode("UTF-8")
        # 解码后value_dict的类型是string, 如果想要得到其中字典的值，就需要进行转换
        value_dict = eval(value_dict)  # eval可以智能地根据字符串中的数据类型进行转换。
        res.append(value_dict)
    # 删除redis
    db13.ltrim(key, end, -1)
    return res



class Update_to_report:
    """
    使用装饰器实现多线程的异步非阻塞
    """

    def start_async(*args):
        fun = args[0]

        def start_thread(*args, **kwargs):
            """
            启动线程（内部方法）
            """
            t = Thread(target=fun, args=args, kwargs=kwargs)
            t.start()

        return start_thread


    @start_async
    def update_to_ping(*args, **kwargs):
        """
            更新数据到report_ping数据表
        """
        datas = kwargs.get("datas", [])
        for data in datas:
            ping_time = data.get("ping_time", "")

            re_time = r"(\d{4}-\d{1,2}-\d{1,2}\s\d{1,2}:\d{1,2}:\d{1,2})"
            # print(re.search(re_time, ping_time, re.S).group())
            rep = re.search(re_time, ping_time, re.S)
            if rep:
                ping_time = rep.group()
            else:
                print("report pingupdate view: ping time is error")
                print("data:", data)
                continue

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
                    # db13.rpush("ping_data", str(data))
                    print("ping create data error", e)
                    # return JsonResponse({"code": 404, "message": "update ping error"})
                    continue

            if not create_reuslt:
                transaction.savepoint_rollback(save_id)
                # db13.rpush("ping_data", str(data))
                print("ping update error")
                print("data", data)
                # return JsonResponse({"code": 404, "message": "update ping error"})
                continue

            # 显式的提交一次事务
            transaction.savepoint_commit(save_id)

    @start_async
    def update_to_connect(*args, **kwargs):
        datas = kwargs.get("datas", [])

        for data in datas:
            connect_time = data.get("connect_time", "")

            re_time = r"(\d{4}-\d{1,2}-\d{1,2}\s\d{1,2}:\d{1,2}:\d{1,2})"
            # print(re.search(re_time, ping_time, re.S).group())
            rep = re.search(re_time, connect_time, re.S)
            if rep:
                connect_time = rep.group()
            else:
                print("report ConnectUpdate view: connect time is error")
                print("data:",data)
                continue
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
                    # db13.rpush("connect_data", str(data))
                    print("connect update error", e)
                    # return JsonResponse({"code": 404, "message": "update connect error"})
                    continue

            if not create_reuslt:
                transaction.savepoint_rollback(save_id)
                # db13.rpush("connect_data", str(data))
                print("connect update error")
                # return JsonResponse({"code": 404, "message": "update connect error"})
                continue

            # 显式的提交一次事务
            transaction.savepoint_commit(save_id)


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
            "ping_result": data.get("ping_result", 0),
            "connect_result": data.get("connect_result", 0),
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
                "ping_result": item.get("ping_result", 0),
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
        length = db13.llen("ping_data")

        if length >= max_number:
            length = max_number

        datas = get_redis_list("ping_data", 0, length)
        if datas:
            Update_to_report().update_to_ping(datas=datas)
            return JsonResponse({"code": 200, "message": "success"})
        else:
            return JsonResponse({"code": 404, "message": "ping_data is error"})


class ConnectUpdate(View):
    """
        更新连接数据
    """
    def post(self, request):
        max_number = 50000
        length = db13.llen("connect_data")

        if length >= max_number:
            length = max_number

        datas = get_redis_list("connect_data", 0, length)

        if datas:
            Update_to_report().update_to_connect(datas=datas)
            return JsonResponse({"code": 200, "message": "success"})
        else:
            return JsonResponse({"code": 404, "message": "connect_data is error"})
        # for i in range(0, length):
        #     data = get_redis_list("connect_data")
        #     connect_time = data.get("connect_time", "")
        #
        #     re_time = r"(\d{4}-\d{1,2}-\d{1,2}\s\d{1,2}:\d{1,2}:\d{1,2})"
        #     # print(re.search(re_time, ping_time, re.S).group())
        #     rep = re.search(re_time, connect_time, re.S)
        #     if rep:
        #         connect_time = rep.group()
        #     else:
        #         print("report ConnectUpdate view: connect time is error")
        #     # 开启事务
        #     with transaction.atomic():
        #         # 创建事务保存点
        #         save_id = transaction.savepoint()
        #
        #         try:
        #             create_reuslt = LinkageRecord.objects.create(
        #                 user_uuid=data.get("user_uuid", ""),
        #                 user_ip=data.get("user_ip", ""),
        #                 country=data.get("country", ""),
        #                 city=data.get("city", ""),
        #                 node_ip=data.get("node_ip", ""),
        #                 node_name=data.get("node_name", ""),
        #                 ping_result=data.get("ping_result", 1),
        #                 connect_result=data.get("connect_result", 1),
        #                 connect_time=connect_time,
        #                 dev_name=data.get("dev_name", ""),
        #                 network=data.get("network", ""),
        #                 operator=data.get("operator", "")
        #             )
        #         except Exception as e:
        #             transaction.savepoint_rollback(save_id)
        #             db13.rpush("connect_data", str(data))
        #             print("connect update error", e)
        #             return JsonResponse({"code": 404, "message": "update connect error"})
        #
        #     if not create_reuslt:
        #         transaction.savepoint_rollback(save_id)
        #         db13.rpush("connect_data", str(data))
        #         print("connect update error")
        #         return JsonResponse({"code": 404, "message": "update connect error"})
        #
        #     # 显式的提交一次事务
        #     transaction.savepoint_commit(save_id)


class Countryrate2(View):
    """
        统计所有国家成功率
    """

    def get_country_results(self, item):
        """
            统计国家成功率
        """
        results = []
        itype = item.get("type", "")

        # 获取所有国家列表
        # country_list = PingFeedback.objects.values('country').distinct()
        # for query in country_list:
        #     country = query.get("country", "")
        #     if not country:
        #         continue
        #     item["country"] = country
        #     ping = self.get_ping_results(item)
        #     connect = self.get_connect_results(item)
        #     results.append({
        #         "country":country,
        #         "ping_rate":ping,
        #         "connect_rate":connect
        #     })
        if itype == "today":
            # 当天成功率
            today = datetime.date.today()
            data = {
                "year": today.year,
                "month": today.month,
                "day": today.day,
                "type": "day"
            }

        # elif type == "yesterday":
        #     # 昨天成功率
        #     today = datetime.date.today()
        #     yesterday = today - datetime.timedelta(days=1)
        #     data = {
        #         "year":yesterday.year,
        #         "month":yesterday.month,
        #         "day":yesterday.day,
        #         "type":"day"
        #     }
        #     results = self.get_country_results(data)
        # elif type == "week":
        #     # 本周成功率
        #     today = datetime.date.today()
        #     this_week_start = today - datetime.timedelta(days=today.weekday())
        #     this_week_end = today
        #     if (today - this_week_start).days > 7:
        #         this_week_end = today + datetime.timedelta(days=6 - today.weekday())
        #     data = {
        #         "start_date":this_week_start,
        #         "end_date":this_week_end,
        #         "type":"range"
        #     }
        #     results = self.get_country_results(data)
        # elif type == "last_week":
        #     # 上周成功率
        #     today = datetime.date.today()
        #     last_week_start = today - datetime.timedelta(days=today.weekday() + 7)
        #     last_week_end = today - datetime.timedelta(days=today.weekday() + 1)
        #     data = {
        #         "start_date":last_week_start,
        #         "end_date":last_week_end,
        #         "type":"range"
        #     }
        #     results = self.get_country_results(data)
        # elif type == "month":
        #     # 本月成功率
        #     today = datetime.date.today()
        #     data = {
        #         "year": today.year,
        #         "month": today.month,
        #         "type": "month"
        #     }
        #     results = self.get_country_results(data)
        # elif type == "last_month":
        #     # 上月成功率
        #     today = datetime.date.today()
        #     # 获取本月的第一天
        #     end_day_in_mouth = today.replace(day=1)
        #     # 获取上月的最后一天
        #     next_mouth = end_day_in_mouth - datetime.timedelta(days=1)
        #     data = {
        #         "year": next_mouth.year,
        #         "month": next_mouth.month,
        #         "type": "month"
        #     }
        #     results = self.get_country_results(data)
        # elif type == "range":
        #     # 自定义区间
        #     try:
        #         start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
        #         end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
        #     except Exception as e:
        #         return JsonResponse({"code": 404, "message": "input date error"})
        #     data = {
        #         "start_date":start_date,
        #         "end_date":end_date,
        #         "type":"range"
        #     }
        #     results = self.get_country_results(data)
        results = self.get_country_results(data)

        totals = LinkageRecord.objects.filter(connect_time__year="2022", connect_time__month="6",
                                              connect_time__day="16").values("country").annotate(count=Count("id"))
        failed_totals = LinkageRecord.objects.filter(connect_time__year="2022", connect_time__month="6",
                                                     connect_time__day="16", connect_result=0).values(
            "country").annotate(count=Count("id"))
        return results

    def get_ping_results(self, param):
        """
            获取指定国家在指定时间段的ping成功率
        """
        # ping成功率 = 某国家ping失败总数/某国家ping总数
        ping_rate = 0
        total = 0
        failed_total = 0
        country = param.get("country", "")
        year = param.get("year", "")
        month = param.get("month", "")
        day = param.get("day", "")
        type = param.get("type", "")
        start_date = param.get("start_date", "")
        end_date = param.get("end_date", "")

        if type == "month":
            # 查询本月或上月
            # 总数
            total = PingFeedback.objects.filter(ping_time__year=year, ping_time__month=month,
                                                country=country).count()
            # 失败总数
            failed_total = PingFeedback.objects.filter(ping_result=0, ping_time__year=year, ping_time__month=month,
                                                       country=country).count()
        elif type == "week":
            # 查询本周或上周
            pass
        elif type == "day":
            # 查询昨天或当天
            # 总数
            total = PingFeedback.objects.filter(ping_time__year=year, ping_time__month=month,
                                                ping_time__day=day, country=country).count()
            # 失败总数
            failed_total = PingFeedback.objects.filter(ping_result=0, ping_time__year=year, ping_time__month=month,
                                                       ping_time__day=day, country=country).count()
        elif type == "range":
            # 自定义时间段
            # 总数
            total = PingFeedback.objects.filter(ping_time__range=(start_date, end_date), country=country).count()
            # 失败总数
            failed_total = PingFeedback.objects.filter(ping_result=0, ping_time__range=(start_date, end_date),
                                                       country=country).count()

        if total > 0:
            ping_rate = failed_total / total
            # print(ping_rate)

        return str(ping_rate)[:4]

    def get_connect_results(self, param):
        """
            获取指定国家在指定时间段的连接成功率
        """
        # 连接成功率 = 某国家连接失败总数/某国家连接总数
        connect_rate = 0
        total = 0
        failed_total = 0
        country = param.get("country")
        year = param.get("year")
        month = param.get("month")
        day = param.get("day")
        type = param.get("type")
        start_date = param.get("start_date", "")
        end_date = param.get("end_date", "")

        if type == "month":
            # 查询本月或上月
            # 总数
            total = LinkageRecord.objects.filter(connect_time__year=year, connect_time__month=month,
                                                 country=country).count()
            # 失败总数
            failed_total = LinkageRecord.objects.filter(connect_result=0, connect_time__year=year,
                                                        connect_time__month=month,
                                                        country=country).count()
        elif type == "week":
            # 查询本周或上周
            pass
        elif type == "day":
            # 查询昨天或当天
            # 总数
            total = LinkageRecord.objects.filter(connect_time__year=year, connect_time__month=month,
                                                 connect_time__day=day, country=country).count()
            # 失败总数
            failed_total = LinkageRecord.objects.filter(connect_result=0, connect_time__year=year,
                                                        connect_time__month=month,
                                                        connect_time__day=day, country=country).count()

        elif type == "range":
            # 自定义时间段
            # 总数
            total = LinkageRecord.objects.filter(connect_time__range=(start_date, end_date), country=country).count()
            # 失败总数
            failed_total = LinkageRecord.objects.filter(connect_result=0, connect_time__range=(start_date, end_date),
                                                        country=country).count()

        if total > 0:
            connect_rate = failed_total / total
        return str(connect_rate)[:4]

    def post(self, request):

        # data = json.loads(request.body.decode(encoding="utf-8"))

        results = []
        type = request.POST.get("type", "")
        start_date = request.POST.get("start_date", "")
        end_date = request.POST.get("end_date", "")

        # if type == "today":
        #     # 当天成功率
        #     today = datetime.date.today()
        #     data = {
        #         "year":today.year,
        #         "month":today.month,
        #         "day":today.day,
        #         "type":"day"
        #     }
        #     results = self.get_country_results(data)
        # elif type == "yesterday":
        #     # 昨天成功率
        #     today = datetime.date.today()
        #     yesterday = today - datetime.timedelta(days=1)
        #     data = {
        #         "year":yesterday.year,
        #         "month":yesterday.month,
        #         "day":yesterday.day,
        #         "type":"day"
        #     }
        #     results = self.get_country_results(data)
        # elif type == "week":
        #     # 本周成功率
        #     today = datetime.date.today()
        #     this_week_start = today - datetime.timedelta(days=today.weekday())
        #     this_week_end = today
        #     if (today - this_week_start).days > 7:
        #         this_week_end = today + datetime.timedelta(days=6 - today.weekday())
        #     data = {
        #         "start_date":this_week_start,
        #         "end_date":this_week_end,
        #         "type":"range"
        #     }
        #     results = self.get_country_results(data)
        # elif type == "last_week":
        #     # 上周成功率
        #     today = datetime.date.today()
        #     last_week_start = today - datetime.timedelta(days=today.weekday() + 7)
        #     last_week_end = today - datetime.timedelta(days=today.weekday() + 1)
        #     data = {
        #         "start_date":last_week_start,
        #         "end_date":last_week_end,
        #         "type":"range"
        #     }
        #     results = self.get_country_results(data)
        # elif type == "month":
        #     # 本月成功率
        #     today = datetime.date.today()
        #     data = {
        #         "year": today.year,
        #         "month": today.month,
        #         "type": "month"
        #     }
        #     results = self.get_country_results(data)
        # elif type == "last_month":
        #     # 上月成功率
        #     today = datetime.date.today()
        #     # 获取本月的第一天
        #     end_day_in_mouth = today.replace(day=1)
        #     # 获取上月的最后一天
        #     next_mouth = end_day_in_mouth - datetime.timedelta(days=1)
        #     data = {
        #         "year": next_mouth.year,
        #         "month": next_mouth.month,
        #         "type": "month"
        #     }
        #     results = self.get_country_results(data)
        # elif type == "range":
        #     # 自定义区间
        #     try:
        #         start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
        #         end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
        #     except Exception as e:
        #         return JsonResponse({"code": 404, "message": "input date error"})
        #     data = {
        #         "start_date":start_date,
        #         "end_date":end_date,
        #         "type":"range"
        #     }
        #     results = self.get_country_results(data)

        # for i in range(100):
        #     results.append({
        #         "country": "国家" + str(i),
        #         "ping_rate": str(random.random())[:4],
        #         "connect_rate": str(random.random())[:4]
        #     })

        totals = LinkageRecord.objects.filter(connect_time__year="2022", connect_time__month="6",
                                              connect_time__day="16").values("country").annotate(count=Count("id"))
        failed_totals = LinkageRecord.objects.filter(connect_time__year="2022", connect_time__month="6",
                                                     connect_time__day="16", connect_result=0).values(
            "country").annotate(count=Count("id"))

        return JsonResponse({"code": 200, "message": "success", "data": {"results": results}})


class Countryrate(View):
    """
        统计所有国家成功率
    """

    def get_country_results2(self, param):
        """
            统计国家成功率
            ping成功率 = 某国家ping失败总数/某国家ping总数
            连接成功率 = 某国家连接失败总数/某国家连接总数
        """

        ping_rate = 0
        total = 0
        failed_total = 0

        country = param.get("country", "")
        year = param.get("year", "")
        month = param.get("month", "")
        day = param.get("day", "")
        type = param.get("type", "")
        start_date = param.get("start_date", "")
        end_date = param.get("end_date", "")

        if type == "day":
            # 查询昨天或当天

            connect_total = Count('id', filter=Q(connect_time__year=year, connect_time__month=month, connect_time__day=day))
            connect_failed_total = Count('id', filter=Q(connect_result=0, connect_time__year=year, connect_time__month=month,
                                                connect_time__day=day))
            ping_total = Count('id', filter=Q(ping_time__year=year, ping_time__month=month, ping_time__day=day))
            ping_failed_total = Count('id', filter=Q(ping_result=0, ping_time__year=year, ping_time__month=month,
                                                ping_time__day=day))

            begin_time = time.time()
            r1 = LinkageRecord.objects.values("country").annotate(connect_total=connect_total).annotate(connect_failed_total=connect_failed_total)
            print(f"r1 time: {time.time() - begin_time}")
            r2 = PingFeedback2.objects.values("country").annotate(ping_total=ping_total).annotate(ping_failed_total=ping_failed_total)
            print(f"r2 time: {time.time() - begin_time}")

            results = [{**x, **y} for x, y in zip(r1, r2)]
            return results
        elif type == "month":
            # 查询本月或上月
            # 总数
            total = PingFeedback.objects.filter(ping_time__year=year, ping_time__month=month,
                                                country=country).count()
            # 失败总数
            failed_total = PingFeedback.objects.filter(ping_result=0, ping_time__year=year, ping_time__month=month,
                                                       country=country).count()
        elif type == "week":
            # 查询本周或上周
            pass
        elif type == "range":
            # 自定义时间段

            connect_total = Count('id', filter=Q(connect_time__range=(start_date, end_date)))
            connect_failed_total = Count('id', filter=Q(connect_result=0, connect_time__range=(start_date, end_date)))
            ping_total = Count('id', filter=Q(ping_time__range=(start_date, end_date)))
            ping_failed_total = Count('id', filter=Q(ping_result=0, ping_time__range=(start_date, end_date)))

            begin_time = time.time()
            r1 = LinkageRecord.objects.values("country").annotate(connect_total=connect_total).annotate(connect_failed_total=connect_failed_total)
            print(f"r1 time: {time.time() - begin_time}")
            r2 = PingFeedback2.objects.values("country").annotate(ping_total=ping_total).annotate(ping_failed_total=ping_failed_total)
            print(f"r2 time: {time.time() - begin_time}")

            results = [{**x, **y} for x, y in zip(r1, r2)]
            return results
        return []

    def pos2t(self, request):

        # data = json.loads(request.body.decode(encoding="utf-8"))

        results = []
        data = {}
        type = request.POST.get("type", "")
        start_date = request.POST.get("start_date", "")
        end_date = request.POST.get("end_date", "")

        if type == "today":
            # 当天成功率
            today = datetime.date.today()
            data = {
                "year":today.year,
                "month":today.month,
                "day":today.day,
                "type":"day"
            }
        elif type == "yesterday":
            # 昨天成功率
            today = datetime.date.today()
            yesterday = today - datetime.timedelta(days=1)
            data = {
                "year":yesterday.year,
                "month":yesterday.month,
                "day":yesterday.day,
                "type":"day"
            }
            results = self.get_country_results(data)
        elif type == "week":
            # 本周成功率
            today = datetime.date.today()
            this_week_start = today - datetime.timedelta(days=today.weekday())
            this_week_end = today
            if (today - this_week_start).days > 7:
                this_week_end = today + datetime.timedelta(days=6 - today.weekday())
            data = {
                "start_date":this_week_start,
                "end_date":this_week_end,
                "type":"range"
            }
            results = self.get_country_results(data)
        elif type == "last_week":
            # 上周成功率
            today = datetime.date.today()
            last_week_start = today - datetime.timedelta(days=today.weekday() + 7)
            last_week_end = today - datetime.timedelta(days=today.weekday() + 1)
            data = {
                "start_date":last_week_start,
                "end_date":last_week_end,
                "type":"range"
            }
            results = self.get_country_results(data)
        elif type == "month":
            # 本月成功率
            today = datetime.date.today()
            data = {
                "year": today.year,
                "month": today.month,
                "type": "month"
            }
            results = self.get_country_results(data)
        elif type == "last_month":
            # 上月成功率
            today = datetime.date.today()
            # 获取本月的第一天
            end_day_in_mouth = today.replace(day=1)
            # 获取上月的最后一天
            next_mouth = end_day_in_mouth - datetime.timedelta(days=1)
            data = {
                "year": next_mouth.year,
                "month": next_mouth.month,
                "type": "month"
            }
            results = self.get_country_results(data)
        elif type == "range":
            # 自定义区间
            try:
                start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
            except Exception as e:
                return JsonResponse({"code": 404, "message": "input date error"})
            data = {
                "start_date":start_date,
                "end_date":end_date,
                "type":"range"
            }
            # results = self.get_country_results(data)

        # for i in range(100):
        #     results.append({
        #         "country": "国家" + str(i),
        #         "ping_rate": str(random.random())[:4],
        #         "connect_rate": str(random.random())[:4]
        #     })
        if not data:
            return JsonResponse({"code": 404, "message": "data is empty!"})
        results = self.get_country_results(data)
        # results = serializers.serialize("json", results)
        print(results)

        return JsonResponse({"code": 200, "message": "success", "data":{"results":list(results)}})

    def get_country_results(self, param):
        """
            统计国家成功率
            ping成功率 = 某国家ping失败总数/某国家ping总数
            连接成功率 = 某国家连接失败总数/某国家连接总数
        """

        year = param.get("year", "")
        month = param.get("month", "")
        day = param.get("day", "")
        if db13.get(f"report_{year}_{month}_{day}"):
            return {}


        connect_total = Count('id', filter=Q(connect_time__year=year, connect_time__month=month, connect_time__day=day))
        connect_failed_total = Count('id', filter=Q(connect_result=1, connect_time__year=year, connect_time__month=month,
                                            connect_time__day=day))
        ping_total = Count('id', filter=Q(connect_time__year=year, connect_time__month=month, connect_time__day=day))
        ping_failed_total = Count('id', filter=Q(ping_result=1, connect_time__year=year, connect_time__month=month,
                                            connect_time__day=day))
        # ping_total = Count('id', filter=Q(ping_time__year=year, ping_time__month=month, ping_time__day=day))
        # ping_failed_total = Count('id', filter=Q(ping_result=0, ping_time__year=year, ping_time__month=month,
        #                                     ping_time__day=day))

        begin_time = time.time()
        r1 = LinkageRecord.objects.values("country").annotate(connect_total=connect_total).annotate(
            connect_failed_total=connect_failed_total).annotate(ping_total=ping_total).annotate(
            ping_failed_total=ping_failed_total)
        print(f"r1 time: {time.time() - begin_time}")
        # r2 = PingFeedback2.objects.values("country").annotate(ping_total=ping_total).annotate(ping_failed_total=ping_failed_total)
        # print(f"r2 time: {time.time() - begin_time}")
        # results = [{**x, **y} for x, y in zip(r1, r2)]
        # print(f"zip time: {time.time() - begin_time}")
        data = {
            "date":f"{year}-{month}-{day}",
            "connect_list":list(r1)
        }

        db13.set(f"report_{year}_{month}_{day}", json.dumps(data))
        # extime = datetime.datetime(2015, 9, 8, 15, 19, 10)
        # print
        # r.expire('ex1', 10)
        # print
        # extime.strftime('%Y-%m-%d %H:%M:%S %f')
        # print
        # r.expireat('ex2', extime)
        return data

    def get_day_list(self, start_date, end_date):
        date_list = []
        for i in range((end_date - start_date).days + 1):
            day = start_date + datetime.timedelta(days=i)
            date_list.append({
                "year":day.year,
                "month":day.month,
                "day":day.day
            })
        return date_list

    def get(self, request):
        """
            获取所有国家
        """
        countrys = LinkageRecord.objects.values("country").distinct().order_by(Convert('country', 'gbk').asc())

        return JsonResponse({"code": 200, "message": "success", "data":{"countrys":list(countrys)}})

    def post(self, request):

        results = []
        start_date = request.POST.get("start_date", "")
        end_date = request.POST.get("end_date", "")

        try:
            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
        except Exception as e:
            return JsonResponse({"code": 404, "message": "input date error"})
        else:
            date_list = self.get_day_list(start_date, end_date)
            for vdate in date_list:
                one_day = db13.get(f"report_{vdate.get('year')}_{vdate.get('month')}_{vdate.get('day')}")
                print(type(one_day))
                if not one_day:
                    one_day = self.get_country_results(vdate)
                else:
                    # 需要强调一下，任何从redis取出来的数据，都是二进制，要先进行二进制解码
                    value_dict = one_day.decode("UTF-8")
                    # 解码后value_dict的类型是string, 如果想要得到其中字典的值，就需要进行转换
                    one_day = eval(value_dict)  # eval可以智能地根据字符串中的数据类型进行转换。

                results.append(one_day)

        print(results)
        return JsonResponse({"code": 200, "message": "success", "data":{"results":results}})


class Noderate(View):
    """
        统计所有节点成功率
    """


    def get_results(self, param):
        """
            统计国家成功率
            ping成功率 = 某国家ping失败总数/某国家ping总数
            连接成功率 = 某国家连接失败总数/某国家连接总数
        """

        year = param.get("year", "")
        month = param.get("month", "")
        day = param.get("day", "")
        if db13.get(f"node_{year}_{month}_{day}"):
            return {}


        connect_total = Count('id', filter=Q(connect_time__year=year, connect_time__month=month, connect_time__day=day))
        connect_failed_total = Count('id', filter=Q(connect_result=1, connect_time__year=year, connect_time__month=month,
                                            connect_time__day=day))
        ping_total = Count('id', filter=Q(connect_time__year=year, connect_time__month=month, connect_time__day=day))
        ping_failed_total = Count('id', filter=Q(ping_result=1, connect_time__year=year, connect_time__month=month,
                                            connect_time__day=day))

        begin_time = time.time()
        r1 = LinkageRecord.objects.values("country", "node_ip", "node_name").annotate(connect_total=connect_total).annotate(
            connect_failed_total=connect_failed_total).annotate(ping_total=ping_total).annotate(
            ping_failed_total=ping_failed_total)
        print(f"r1 time: {time.time() - begin_time}")

        data = {
            "date":f"{year}-{month}-{day}",
            "connect_list":list(r1)
        }

        db13.set(f"node_{year}_{month}_{day}", json.dumps(data))

        return data

    def get_day_list(self, start_date, end_date):
        date_list = []
        for i in range((end_date - start_date).days + 1):
            day = start_date + datetime.timedelta(days=i)
            date_list.append({
                "year":day.year,
                "month":day.month,
                "day":day.day
            })
        return date_list

    def get(self, request):
        """
            获取所有国家
        """
        countrys = LinkageRecord.objects.values("country").distinct().order_by(Convert('country', 'gbk').asc())

        return JsonResponse({"code": 200, "message": "success", "data":{"countrys":list(countrys)}})

    def post(self, request):

        results = []
        start_date = request.POST.get("start_date", "")
        end_date = request.POST.get("end_date", "")

        try:
            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
        except Exception as e:
            return JsonResponse({"code": 404, "message": "input date error"})
        else:
            date_list = self.get_day_list(start_date, end_date)
            for vdate in date_list:
                one_day = db13.get(f"node_{vdate.get('year')}_{vdate.get('month')}_{vdate.get('day')}")
                if not one_day:
                    one_day = self.get_results(vdate)
                else:
                    # 需要强调一下，任何从redis取出来的数据，都是二进制，要先进行二进制解码
                    value_dict = one_day.decode("UTF-8")
                    # 解码后value_dict的类型是string, 如果想要得到其中字典的值，就需要进行转换
                    one_day = eval(value_dict)  # eval可以智能地根据字符串中的数据类型进行转换。

                results.append(one_day)

        print(results)
        return JsonResponse({"code": 200, "message": "success", "data":{"results":results}})


class Userrate(View):
    """
        统计所有用户成功率
    """


    def get_results(self, param):
        """
            统计国家成功率
            ping成功率 = 某国家ping失败总数/某国家ping总数
            连接成功率 = 某国家连接失败总数/某国家连接总数
        """

        year = param.get("year", "")
        month = param.get("month", "")
        day = param.get("day", "")
        if db13.get(f"user_{year}_{month}_{day}"):
            return {}


        connect_total = Count('id', filter=Q(connect_time__year=year, connect_time__month=month, connect_time__day=day))
        connect_failed_total = Count('id', filter=Q(connect_result=1, connect_time__year=year, connect_time__month=month,
                                            connect_time__day=day))
        ping_total = Count('id', filter=Q(connect_time__year=year, connect_time__month=month, connect_time__day=day))
        ping_failed_total = Count('id', filter=Q(ping_result=1, connect_time__year=year, connect_time__month=month,
                                            connect_time__day=day))

        begin_time = time.time()
        r1 = LinkageRecord.objects.values("country", "user_uuid").annotate(connect_total=connect_total).annotate(
            connect_failed_total=connect_failed_total).annotate(ping_total=ping_total).annotate(
            ping_failed_total=ping_failed_total)
        print(f"r1 time: {time.time() - begin_time}")

        data = {
            "date":f"{year}-{month}-{day}",
            "connect_list":list(r1)
        }

        db13.set(f"user_{year}_{month}_{day}", json.dumps(data))

        return data

    def get_day_list(self, start_date, end_date):
        date_list = []
        for i in range((end_date - start_date).days + 1):
            day = start_date + datetime.timedelta(days=i)
            date_list.append({
                "year":day.year,
                "month":day.month,
                "day":day.day
            })
        return date_list

    def get(self, request):
        """
            获取所有国家
        """
        countrys = LinkageRecord.objects.values("country").distinct().order_by(Convert('country', 'gbk').asc())

        return JsonResponse({"code": 200, "message": "success", "data":{"countrys":list(countrys)}})

    def post(self, request):

        results = []
        start_date = request.POST.get("start_date", "")
        end_date = request.POST.get("end_date", "")

        try:
            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
        except Exception as e:
            return JsonResponse({"code": 404, "message": "input date error"})
        else:
            date_list = self.get_day_list(start_date, end_date)
            for vdate in date_list:
                one_day = db13.get(f"user_{vdate.get('year')}_{vdate.get('month')}_{vdate.get('day')}")
                if not one_day:
                    one_day = self.get_results(vdate)
                else:
                    # 需要强调一下，任何从redis取出来的数据，都是二进制，要先进行二进制解码
                    value_dict = one_day.decode("UTF-8")
                    # 解码后value_dict的类型是string, 如果想要得到其中字典的值，就需要进行转换
                    one_day = eval(value_dict)  # eval可以智能地根据字符串中的数据类型进行转换。

                results.append(one_day)

        print(results)
        return JsonResponse({"code": 200, "message": "success", "data":{"results":results}})


class NodeHead(View):
    """
        统计所有节点热度
    """


    def get_results(self, param):
        """
            统计国家成功率
            ping成功率 = 某国家ping失败总数/某国家ping总数
            连接成功率 = 某国家连接失败总数/某国家连接总数
        """

        year = param.get("year", "")
        month = param.get("month", "")
        day = param.get("day", "")
        if db13.get(f"node_head_{year}_{month}_{day}"):
            return {}

        ping_total = Count('id', filter=Q(connect_time__year=year, connect_time__month=month, connect_time__day=day))
        connect_total = Count('id', filter=Q(connect_time__year=year, connect_time__month=month, connect_time__day=day))

        r1 = LinkageRecord.objects.values("country", "node_ip", "node_name").annotate(
            connect_total=connect_total).annotate(ping_total=ping_total)
        data = {
            "date":f"{year}-{month}-{day}",
            "connect_list":list(r1)
        }

        db13.set(f"node_head_{year}_{month}_{day}", json.dumps(data))

        return data

    def get_day_list(self, start_date, end_date):
        date_list = []
        for i in range((end_date - start_date).days + 1):
            day = start_date + datetime.timedelta(days=i)
            date_list.append({
                "year":day.year,
                "month":day.month,
                "day":day.day
            })
        return date_list

    def get(self, request):
        """
            获取所有国家
        """
        countrys = LinkageRecord.objects.values("country").distinct().order_by(Convert('country', 'gbk').asc())

        return JsonResponse({"code": 200, "message": "success", "data":{"countrys":list(countrys)}})

    def post(self, request):

        results = []
        start_date = request.POST.get("start_date", "")
        end_date = request.POST.get("end_date", "")

        try:
            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
        except Exception as e:
            return JsonResponse({"code": 404, "message": "input date error"})
        else:
            date_list = self.get_day_list(start_date, end_date)
            for vdate in date_list:
                one_day = db13.get(f"node_head_{vdate.get('year')}_{vdate.get('month')}_{vdate.get('day')}")
                if not one_day:
                    one_day = self.get_results(vdate)
                else:
                    # 需要强调一下，任何从redis取出来的数据，都是二进制，要先进行二进制解码
                    value_dict = one_day.decode("UTF-8")
                    # 解码后value_dict的类型是string, 如果想要得到其中字典的值，就需要进行转换
                    one_day = eval(value_dict)  # eval可以智能地根据字符串中的数据类型进行转换。

                results.append(one_day)

        print(results)
        return JsonResponse({"code": 200, "message": "success", "data":{"results":results}})


class Convert(Func):
    def __init__(self, expression, transcoding_name, **extra):
        super(Convert, self).__init__(
            expression=expression, transcoding_name=transcoding_name, **extra)

    def as_mysql(self, compiler, connection):
        self.function = 'CONVERT'
        self.template = ' %(function)s(%(expression)s USING  %(transcoding_name)s)'
        return super(Convert, self).as_sql(compiler, connection)


class CheckAllNode(View):


    def post(self, request):
        """
            统计过去三小时的所有成功率
        """
        hour = 3
        now_time = datetime.datetime.now() + datetime.timedelta(hours=8)
        last_time = now_time - datetime.timedelta(hours=hour)

        connect_total = Count('id', filter=Q(connect_time__lte=now_time, connect_time__gte=last_time))
        connect_failed_total = Count('id', filter=Q(connect_result=1, connect_time__lte=now_time, connect_time__gte=last_time))
        ping_total = Count('id', filter=Q(connect_time__lte=now_time, connect_time__gte=last_time))
        ping_failed_total = Count('id', filter=Q(ping_result=1, connect_time__lte=now_time, connect_time__gte=last_time))

        r1 = LinkageRecord.objects.filter(connect_time__lte=now_time, connect_time__gte=last_time).values(
            "country", "node_ip", "connect_time").annotate(connect_total=connect_total).annotate(
            connect_failed_total=connect_failed_total).annotate(ping_total=ping_total).annotate(
            ping_failed_total=ping_failed_total)

        r = []
        for item in r1:
            if item.get("country") == "中国":
                connect_rate = 0
                ping_rate = 0
                if item.get("connect_failed_total") > 0:
                    connect_rate = item.get("connect_failed_total") / item.get("connect_total") * 100
                if item.get("ping_failed_total") > 0:
                    ping_rate = item.get("ping_failed_total") / item.get("ping_total") * 100
                r.append(item)
                if ping_rate < 80 or connect_rate < 70:
                    print({
                        "ping_rate": ping_rate,
                        "connect_rate": connect_rate,
                        "item": item
                    })
                    # 写入黑名单
                    data = {
                        "node_ip":item.get("node_ip", ""),
                        "country":item.get("country", ""),
                    }
                    response = requests.post(settings.DEBUG_TEST_CMS_BASE_URL + "node/node_update_blacklist", data)
                    if response.status_code == 200:
                        print(f"{data.get('node_ip')} -- 已加入黑名单")

        print(len(r))
        return JsonResponse({"code":200})