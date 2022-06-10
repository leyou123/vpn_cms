import socket
import time

from django.db import transaction
from django_redis import get_redis_connection

from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore, register_events, register_job

from apps.report.models import LinkageRecord, PingFeedback

db13 = get_redis_connection('DB13')

try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 8000))
except socket.error:
    print("!!!scheduler already started, DO NOTHING")
else:

    # 开启定时工作
    try:
        # 实例化调度器
        scheduler = BackgroundScheduler()
        # 调度器使用DjangoJobStore()
        scheduler.add_jobstore(DjangoJobStore(), "default")


        # 设置定时任务，选择方式为interval，时间间隔为10s
        # 另一种方式为每天固定时间执行任务，对应代码为：
        # @register_job(scheduler, 'cron', day_of_week='mon-fri', hour='9', minute='30', second='10',id='task_time')
        @register_job(scheduler, "interval", minutes=10, replace_existing=True, id="connect_job_func")
        def connect_job():
            # 这里写你要执行的任务
            # format_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
            connect_task()
            # print(format_time)


        @register_job(scheduler, "interval", minutes=10, replace_existing=True, id="ping_job_func")
        def ping_job():
            # 这里写你要执行的任务
            # format_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
            ping_task()
            # print(format_time)


        # register_events(scheduler)
        scheduler.start()
    except Exception as e:
        print(e)
        # 有错误就停止定时器
        scheduler.shutdown()



from django.http import JsonResponse
def index(request):

    return JsonResponse({"code": 404, "message": "request body error"})



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

# 定时更新连接记录数据
def connect_task():

    length = db13.llen("connect_data")
    for i in range(0, length):
        data = get_redis_list("connect_data")

        # 开启事务
        with transaction.atomic():
            # 创建事务保存点
            save_id = transaction.savepoint()

            try:
                create_reuslt = LinkageRecord.objects.create(
                    user_uuid=data.get("uuid", ""),
                    user_ip=data.get("user_ip", ""),
                    country=data.get("country", ""),
                    city=data.get("city", ""),
                    node_ip=data.get("node_ip", ""),
                    node_name=data.get("node_name", ""),
                    ping_result=data.get("ping_result", 1),
                    connect_result=data.get("connect_result", 1),
                    connect_time=data.get("connect_time", None),
                    dev_name=data.get("dev_name", ""),
                    network=data.get("network", ""),
                    operator=data.get("operator", "")
                )
            except Exception as e:
                transaction.savepoint_rollback(save_id)
                db13.lpush("connect_data", str(data))
                print("connect task create error", e)


        if not create_reuslt:
            transaction.savepoint_rollback(save_id)
            db13.lpush("connect_data", str(data))
            print("connect create error")

        # 显式的提交一次事务
        transaction.savepoint_commit(save_id)


# 定时更新连接记录数据
def ping_task():

    length = db13.llen("ping_data")
    for i in range(0, length):
        data = get_redis_list("ping_data")

        # 开启事务
        with transaction.atomic():
            # 创建事务保存点
            save_id = transaction.savepoint()

            try:
                create_reuslt = PingFeedback.objects.create(
                    user_uuid=data.get("uuid", ""),
                    user_ip=data.get("user_ip", ""),
                    country=data.get("country", ""),
                    city=data.get("city", ""),
                    node_ip=data.get("node_ip", ""),
                    node_name=data.get("node_name", ""),
                    ping_val1=data.get("ping_val1", ""),
                    ping_val2=data.get("ping_val2", ""),
                    ping_val3=data.get("ping_val3", ""),
                    ping_result=data.get("ping_result", 1),
                    ping_time=data.get("ping_time", "")
                )
            except Exception as e:
                transaction.savepoint_rollback(save_id)
                db13.lpush("ping_data", str(data))
                print("ping task create error", e)


        if not create_reuslt:
            transaction.savepoint_rollback(save_id)
            db13.lpush("ping_data", str(data))
            print("ping create error")

        # 显式的提交一次事务
        transaction.savepoint_commit(save_id)