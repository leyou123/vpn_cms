import json
import re
import datetime
import geoip2.database
from threading import Thread

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


class Countryrate(View):
    """
        获取所有国家成功率
    """

    def get_country_results(self, item):
        """
            统计国家成功率
        """
        results = []

        # 获取所有国家列表
        country_list = PingFeedback.objects.values('country').distinct()
        for query in country_list:
            country = query.get("country", "")
            if not country:
                continue
            item["country"] = country
            ping = self.get_ping_results(item)
            connect = self.get_connect_results(item)
            results.append({
                "country":country,
                "ping_rate":ping,
                "connect_rate":connect
            })
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
            failed_total = PingFeedback.objects.filter(ping_result=0, ping_time__range=(start_date, end_date), country=country).count()

        if total > 0:
            ping_rate = failed_total / total
            print(ping_rate)

        return ping_rate


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
            failed_total = LinkageRecord.objects.filter(connect_result=0, connect_time__year=year, connect_time__month=month,
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
        return connect_rate



    def post(self, request):

        data = json.loads(request.body.decode(encoding="utf-8"))

        results = []
        type = data.get("type", "")

        if type == "today":
            # 当天成功率
            today = datetime.date.today()
            data = {
                "year":today.year,
                "month":today.month,
                "day":today.day,
                "type":"day"
            }
            results = self.get_country_results(data)
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
            start_date = datetime.date(2022, 6, 10)
            end_date = datetime.date(2022, 6, 13)
            data = {
                "start_date":start_date,
                "end_date":end_date,
                "type":"range"
            }
            results = self.get_country_results(data)

        return JsonResponse({"code": 200, "message": "success", "data":{"res":results}})