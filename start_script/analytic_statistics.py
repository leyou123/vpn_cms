from pymongo import MongoClient
import datetime
import time
import redis
import requests
import json


REDIS_HOST = "3.101.19.69"
MONGODB_HOST = "13.52.97.173"
DATA_HOST = "https://datas.9527.click"


mongodb_link = MongoClient(f'mongodb://root:leyou2021@{MONGODB_HOST}:27017/').vpn_cms
pool2 = redis.ConnectionPool(host=REDIS_HOST, port=6379, password="leyou2020", db=2)
r2 = redis.Redis(connection_pool=pool2)


class Statisitics(object):
    """
        线路统计
    """
    def __init__(self):
        self.mongodb_link = mongodb_link
        self.today = int(time.mktime(datetime.date.today().timetuple())) + (60 * 60 * 3) + 1
        self.exp_time = self.today + (60 * 60 * 24)
        self.r2 = r2
        self.time_range = {"$gt": self.today, "$lt": self.exp_time}

    def redis_conv(self):
        ip = []
        keys = self.r2.keys()

        for key in keys:
            ip.append(str(key, "utf-8"))
        return ip

    def calculate_success(self, host):
        query = {"host": host, "time": self.time_range}
        success_count = mongodb_link.connect_suc.count_documents(query)
        return success_count

    def calculate_failure(self, host):
        # 失败状态码 0 开始,1.发送失败 2.接收成功 3.接收不到包 4.超时 5.错误 6.完成
        # failure_code = [1, 3, 4, 5]
        # failure_count = 0
        query = {"host": host, "time": self.time_range}
        failure_count = mongodb_link.connect_fail.count_documents(query)
        return failure_count

    def send_data(self, data):
        url = f"{DATA_HOST}/servers/line_statistics"
        response = requests.post(url=url, json=data)
        print(response.status_code)

    def get_country(self, id):
        redis_data = r2.get(id)
        datas = json.loads(str(redis_data, "utf-8"))
        country = datas.get("name")
        host = datas.get("host")

        return country,host

    def ip_count(self):
        id_list = self.redis_conv()
        for id in id_list:
            country,host = self.get_country(id)
            success_count = self.calculate_success(host)
            failure_count = self.calculate_failure(host)
            total_count = success_count + failure_count
            try:
                success_rate = round(success_count / total_count * 100, 2)
            except Exception as e:
                success_rate = 0
            data = {
                "host": host,
                "country": country,
                "success_count": success_count,
                "failure_count": failure_count,
                "success_rate": f"{success_rate}%",
                "time": self.today,
            }
            print(data)
            # print(f"{host},成功:{success_count}次,失败:{failure_count}次,成功率:{success_rate}%，{time}")

            self.send_data(data)


def main():
    mongodb = Statisitics()
    mongodb.ip_count()


def test():
    datas = mongodb_link.orders_request.find()

    for data in datas:
        cancellation_date_ms = data.get("cancellation_date")
        if cancellation_date_ms:
            print(data)
        # print(data)

    pass

if __name__ == '__main__':

    while True:
        try:
            main()
        except Exception as e:
            print(e)
        time.sleep(60*5)

