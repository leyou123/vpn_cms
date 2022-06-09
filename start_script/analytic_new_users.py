from pymongo import MongoClient
import datetime
import time
import requests

MONGODB_HOST = "13.52.97.173"
DATA_HOST = "https://datas.9527.click"
mongodb_link = MongoClient(f'mongodb://root:leyou2021@{MONGODB_HOST}:27017/').vpn_cms


class Statisitics(object):
    """
        新用户漏斗统计
    """

    def __init__(self):
        self.mongodb_link = mongodb_link
        self.yesterday = int(time.mktime(datetime.date.today().timetuple())) + (60 * 60 * 3) + 1 - 60 * 60 * 24
        self.exp_time = self.yesterday + (60 * 60 * 24)
        self.time_range = {"$gt": self.yesterday, "$lt": self.exp_time}

        print(self.yesterday,self.exp_time)
        self.apps = ['com.superoversea', 'com.superoversea.vpn', 'com.yanji.trojan_vpn.yanJiVPN', 'com.strom.vpn',
                     'com.superoversea.mac', 'com.superoversea.windows', 'com.strom.mac', 'com.strom.windows']

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

    def connect_suc_new(self, package_id):
        query = {"time": self.time_range, "package_id": package_id}
        datas = mongodb_link.connect_suc_new.find(query)

        users_count = 0
        for data in datas:
            uuid = data.get("uuid", "")
            package_id = data.get("package_id", "")
            query_data = {"package_id": package_id, "uuid": uuid}
            user_count = mongodb_link.connect_suc_new.count_documents(query_data)

            if user_count == 1:
                users_count += 1
        return users_count

    def app_inited(self, package_id):
        query = {"time": self.time_range, "package_id": package_id}
        datas = mongodb_link.app_inited.find(query)

        users_count = 0
        for data in datas:
            uuid = data.get("uuid", "")
            package_id = data.get("package_id", "")
            query_data = {"package_id": package_id, "uuid": uuid}
            user_count = mongodb_link.app_inited.count_documents(query_data)

            if user_count == 1:
                users_count += 1
        return users_count

    def connect_cms_start(self, package_id):
        query = {"time": self.time_range, "package_id": package_id}
        datas = mongodb_link.connect_cms_start.find(query)

        users_count = 0
        for data in datas:
            uuid = data.get("uuid", "")
            package_id = data.get("package_id", "")
            query_data = {"package_id": package_id, "uuid": uuid}
            user_count = mongodb_link.connect_cms_start.count_documents(query_data)

            if user_count == 1:
                users_count += 1
            else:
                print(query_data)
        return users_count

    def connect_cms_suc(self, package_id):
        query = {"time": self.time_range, "package_id": package_id}
        datas = mongodb_link.connect_cms_suc.find(query)

        users_count = 0
        for data in datas:
            uuid = data.get("uuid", "")
            package_id = data.get("package_id", "")
            query_data = {"package_id": package_id, "uuid": uuid}
            user_count = mongodb_link.connect_cms_suc.count_documents(query_data)

            if user_count == 1:
                users_count += 1
        return users_count

    def install_config_start(self, package_id):
        query = {"time": self.time_range, "package_id": package_id}
        datas = mongodb_link.install_config_start.find(query)

        users_count = 0
        for data in datas:
            uuid = data.get("uuid", "")
            package_id = data.get("package_id", "")
            query_data = {"package_id": package_id, "uuid": uuid}
            user_count = mongodb_link.install_config_start.count_documents(query_data)

            if user_count == 1:
                users_count += 1
        return users_count

    def install_config_suc(self, package_id):
        query = {"time": self.time_range, "package_id": package_id}
        datas = mongodb_link.install_config_suc.find(query)

        users_count = 0
        for data in datas:
            uuid = data.get("uuid", "")
            package_id = data.get("package_id", "")
            query_data = {"package_id": package_id, "uuid": uuid}
            user_count = mongodb_link.install_config_suc.count_documents(query_data)

            if user_count == 1:
                users_count += 1
        return users_count

    def connect_start_new(self, package_id):
        query = {"time": self.time_range, "package_id": package_id}
        datas = mongodb_link.connect_start_new.find(query)

        users_count = 0
        for data in datas:
            uuid = data.get("uuid", "")
            package_id = data.get("package_id", "")
            query_data = {"package_id": package_id, "uuid": uuid}
            user_count = mongodb_link.connect_start_new.count_documents(query_data)

            if user_count == 1:
                users_count += 1
        return users_count

    def send_data(self, data):
        url = f"{DATA_HOST}/manage/upload_user_funnel_data"
        response = requests.post(url=url, json=data)
        # print(response.status_code)

    def exec_data(self):

        for package_id in self.apps:

            link_cms = self.connect_cms_start(package_id)  # 开始连接cms
            cms_success = self.connect_cms_suc(package_id)  # 连接cms成功
            home_count = self.app_inited(package_id)

            connect_start_new = self.connect_start_new(package_id)

            vpn_config = self.install_config_start(package_id)
            vpn_config_success = self.install_config_suc(package_id)
            connect_suc_new = self.connect_suc_new(package_id)

            # print(f"新用户:{link_cms}，home:{home_count},link_cms:{link_cms},cms_success:{cms_success},vpn_config:{vpn_config},vpn_config_success：{vpn_config_success}")

            link_cms_ratio = "0%"
            cms_success_ratio = "0%"
            home_ratio = "0%"
            connect_start_new_ratio = "0%"
            vpn_config_ratio = "0%"
            vpn_config_success_ratio = "0%"
            connect_suc_new_ratio = "0%"

            if link_cms:
                link_cms_ratio = f"{round(link_cms / link_cms * 100, 2)}%"

            if link_cms and cms_success:
                cms_success_ratio = f"{round(cms_success / link_cms * 100, 2)}%"

            if cms_success and home_count:
                home_ratio = f"{round(home_count / cms_success * 100, 2)}%"


            if connect_start_new and home_count:
                connect_start_new_ratio = f"{round(connect_start_new / home_count * 100, 2)}%"

            if connect_start_new and vpn_config:
                vpn_config_ratio = f"{round(vpn_config / connect_start_new * 100, 2)}%"

            if vpn_config and vpn_config_success:
                vpn_config_success_ratio = f"{round(vpn_config_success / vpn_config * 100, 2)}%"

            if vpn_config_success and connect_suc_new:
                connect_suc_new_ratio = f"{round(connect_suc_new / vpn_config_success * 100, 2)}%"

            data = {
                "day_time": self.yesterday,
                "app": package_id,
                "user_count": link_cms,

                "link_cms": link_cms,
                "link_cms_ratio": link_cms_ratio,

                "cms_success": cms_success,
                "cms_success_ratio": cms_success_ratio,

                "home_count": home_count,
                "home_ratio": home_ratio,

                "connect_start_new": connect_start_new,
                "connect_start_new_ratio": connect_start_new_ratio,

                "vpn_config": vpn_config,
                "vpn_config_ratio": vpn_config_ratio,

                "vpn_config_success": vpn_config_success,
                "vpn_config_success_ratio": vpn_config_success_ratio,

                "link_success": connect_suc_new,
                "link_success_ratio": connect_suc_new_ratio

            }

            print(data)
            self.send_data(data)


def main():
    mongodb = Statisitics()
    mongodb.exec_data()


if __name__ == '__main__':

    while True:
        try:
            main()
        except Exception as e:
            print(e)
        time.sleep(60 * 60 * 24)
