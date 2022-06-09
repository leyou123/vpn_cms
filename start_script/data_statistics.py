import requests
from apscheduler.schedulers.blocking import BlockingScheduler
import time

DATAS_HOST = "https://datas.9527.click"

class Requests(object):

    @classmethod
    def post(cls, url):
        try:
            json_data = {
                "key": "leyou2021"
            }
            response = requests.post(url=url, json=json_data)
            return response
        except Exception as e:
            print(e)
            return None


class Scheduler(object):

    @classmethod
    def start(cls, func, time):
        """
        :param func: 函数
        :param time: 时间 单位:秒
        :return:
        """
        scheduler = BlockingScheduler()
        scheduler.add_job(func, 'interval', seconds=time)
        try:
            # 定时任务启动
            scheduler.start()
        except Exception as e:
            print(e)
            # print("启动错误")


def timing_task():
    urls = {
        # # 新用户
        "new_user": f"{DATAS_HOST}/manage/new_user",

        # # 节点服务器
        "upload_server_data": f"{DATAS_HOST}/servers/upload_server_data",

        # # 用户留存统计
        "user_retention": f"{DATAS_HOST}/manage/user_retention",

        # # 用户追踪统计
        "users_pay_statistical": f"{DATAS_HOST}/manage/users_pay_statistical",

        # 每日付费
        "every_day_amount": f"{DATAS_HOST}/manage/every_day_amount",

        # 每日通知
        "notification": f"{DATAS_HOST}/notification/notification_user",

    }

    for k, v in urls.items():
        response = Requests.post(url=v)
        if response:
            print(v,response.status_code)
        else:
            print(v, response)


def for_timing_task():
    urls = {
        # 活跃用户统计
        "active_user":f"{DATAS_HOST}/manage/active_user",

        # 服务器警告
        # "warning": f"{do_main}/api/v1/servers/warning"
    }

    for k, v in urls.items():
        try:
            response = Requests.post(url=v)
            print(v,response.status_code)
        except Exception as e:
            print(e)

def main():
    scheduler = BlockingScheduler()
    print("启动")
    scheduler.add_job(for_timing_task, 'interval', seconds=60 *60)
    scheduler.add_job(timing_task, 'cron', hour='11', minute=00)
    scheduler.start()

    # while True:
    #     try:
    #         for_timing_task()
    #         timing_task()
    #
    #     except Exception as e:
    #         print(e)
    #     print("睡眠24小时")
    #     time.sleep(60 * 60 * 24)



if __name__ == '__main__':
    # for_timing_task()
    # timing_task()
    main()