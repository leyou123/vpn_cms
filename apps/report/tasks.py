
from django.db import transaction

from django_redis import get_redis_connection

from apps.report.models import LinkageRecord, PingFeedback

db13 = get_redis_connection('DB13')

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

    for i in range(0, 1):
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