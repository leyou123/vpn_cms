from locust import HttpUser, SequentialTaskSet, task, between
import time, urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class MyTaskWebLive(SequentialTaskSet):
    # 当类里面的任务请求有先后顺序时继承SequentialTaskSet类；
    # 没有先后顺序，可以使用继承TaskSet类

    @task(1)
    def open_blog(self):
        # 定义requests的请求头
        json_data = {
            "key": "Ntfk03xVGfbmYuWayVW83w==",
            "uuid": "22A29D001FEBBD74DD48B3C2A8CED487EEAB46F0",
            "uid": "1478650118625435648",
            "platform_id": "super_vpn.2021",
            "package_id": "com.superoversea.vpn"
        }
        r = self.client.post("/v2/user/login", json=json_data,verify=False)
        print(r._content)


        # print(r.status_code)

        assert r.status_code == 200

# 定义一个运行类 继承HttpUser类， 所以要从locust中引入 HttpUser类
class MyUser(HttpUser):
    tasks = [MyTaskWebLive]  # 指定用户运行的任务类
    # 设置运行过程中间隔时间 需要从locust中 引入 between
    min_wait = 3000  # 单位毫秒
    max_wait = 6000  # 单位毫秒

if __name__ == "__main__":
    import os
    #输入你的地址
    os.system("/usr/local/python3/bin/locust -f test_data.py --host=https://test.9527.click")

