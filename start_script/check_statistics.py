import time
import redis
import json
import requests
from pymongo import MongoClient

REDIS_HOST = "3.101.19.69"
MONGODB_HOST = "13.52.97.173"
NODE_HOST = "https://api.9527.click"

pool = redis.ConnectionPool(host=REDIS_HOST, port=6379, password="leyou2020", db=0)
pool1 = redis.ConnectionPool(host=REDIS_HOST, port=6379, password="leyou2020", db=1)
pool2 = redis.ConnectionPool(host=REDIS_HOST, port=6379, password="leyou2020", db=2)

r = redis.Redis(connection_pool=pool)
r1 = redis.Redis(connection_pool=pool1)
r2 = redis.Redis(connection_pool=pool2)

mongodb_link = MongoClient(f'mongodb://root:leyou2021@{MONGODB_HOST}:27017/').vpn_cms


def get_country(uid):
    url = f"{NODE_HOST}/v2/user/query_one_user"
    response = requests.post(url=url, json={"uid": uid})

    if response.status_code == 200:
        datas = json.loads(response.text)
        country = datas.get("data", "")
        return country
    else:
        return None


def node_data(node):
    datas = r1.get(str(node))
    if not datas:
        datas = r2.get(str(node))
    if not datas:
        return None
    json_data = json.loads(str(datas, "utf-8"))
    return json_data


def connect_fail(datas, user_uuid, device_type, host, host_country, user_time):
    node_id = datas.get("node_id", "")
    err_code = datas.get("err_code", "")
    err_msg = datas.get("err_msg", "")

    json_data = {
        "uuid": user_uuid,
        "device_type": device_type,
        "feature": "connect_fail",
        "host": host,
        "host_country": host_country,
        "node_id": node_id,
        "err_code": err_code,
        "err_msg": err_msg,
        "time": user_time
    }
    res = mongodb_link.connect_fail.insert_one(json_data)
    if res:
        print(f"插入数据:{user_uuid},特征:connect_fail,host:{host},host国家:{host_country}")


def connect_suc(user_uuid, device_type, host, host_country, user_time):
    json_data = {
        "uuid": user_uuid,
        "device_type": device_type,
        "feature": "connect_suc",
        "host": host,
        "host_country": host_country,
        "time": user_time
    }
    res = mongodb_link.connect_suc.insert_one(json_data)
    if res:
        print(f"插入数据:{user_uuid},特征:connect_suc,host:{host},host国家:{host_country},time:{user_time}")


def connect_suc_new(json_data):
    res = mongodb_link.connect_suc_new.insert_one(json_data)
    if res:
        print(json_data)


def app_inited(json_data):
    res = mongodb_link.app_inited.insert_one(json_data)
    if res:
        print(json_data)



def connect_cms_start(json_data):
    res = mongodb_link.connect_cms_start.insert_one(json_data)
    if res:
        print(json_data)


def connect_cms_suc(json_data):
    res = mongodb_link.connect_cms_suc.insert_one(json_data)
    if res:
        print(json_data)



def install_config_start(json_data):
    res = mongodb_link.install_config_start.insert_one(json_data)
    if res:
        print(json_data)

def install_config_suc(json_data):
    res = mongodb_link.install_config_suc.insert_one(json_data)
    if res:
        print(json_data)


def connect_start_new(json_data):
    res = mongodb_link.connect_start_new.insert_one(json_data)
    if res:
        print(json_data)



def main(redis_data):
    datas = json.loads(redis_data)
    user_uuid = datas.get("__u", "")
    device_type = datas.get("__p", "")
    feature = datas.get("__k", "")
    user_time = datas.get("time", 0)
    platform_id = datas.get("platform_id", "")
    package_id = datas.get("package_id", "")
    if not user_uuid or not device_type or not feature:
        return
    # country = get_country(user_uuid)

    host = ""
    host_country = ""

    features = ['connect_start', 'connect_fail', 'connect_suc', 'connect_cancel', 'ping', 'network_speed',
                'app_inited', 'connect_cms_start', 'connect_cms_suc', 'install_config_start', 'install_config_suc']
    if feature in features:
        node_id = datas.get("node_id", "")
        host_data = node_data(node_id)
        if host_data:
            host = host_data.get("host", "")
            host_country = host_data.get("country", "")

    json_data = {
        "uuid": user_uuid,
        "device_type": device_type,
        "feature": "connect_suc",
        "host": host,
        "host_country": host_country,
        "time": user_time,
        "platform_id": platform_id,
        "package_id": package_id
    }
    if feature == "ping":
        return

    # 失败
    elif feature == "connect_fail":
        connect_fail(datas, user_uuid, device_type, host, host_country, user_time)

    # 成功
    elif feature == "connect_suc":
        connect_suc(user_uuid, device_type, host, host_country, user_time)

    # 开始连接cms
    elif feature == "connect_cms_start_New":
        connect_cms_start(json_data)

    # 连接cms成功
    elif feature == "connect_cms_suc_New":
        connect_cms_suc(json_data)


    # 进入home页面
    elif feature == "app_inited_New":
        app_inited(json_data)

    # 新用户开始连接
    elif feature == "connect_start_New":
        connect_start_new(json_data)


    # 初始化配置开始
    elif feature == "install_config_start_New":
        install_config_start(json_data)

    # 初始化配置成功
    elif feature == "install_config_suc_New":
        install_config_suc(json_data)

    # 新用户成功连接
    elif feature == "connect_suc_New":
        connect_suc_new(json_data)


if __name__ == '__main__':

    while True:
        try:
            redis_data = r.lpop("statistics")
            if not redis_data:
                print("睡眠1分钟")
                time.sleep(60)
            main(redis_data)
        except Exception as e:
            print(e)
