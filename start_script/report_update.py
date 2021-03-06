import datetime
import requests

from apscheduler.schedulers.blocking import BlockingScheduler

base_url = "https://api.9527.click/v2/"
test_url = "http://54.177.55.54:10050/v2/"

# 定时更新连接记录数据
def connect_task():

    try:
        url = base_url + "report/connect_update"
        # url = test_url + "report/connect_update"
        res = requests.post(url)
    except Exception as e:
        print("connect task error:", e)
    else:
        print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} -- connect task : {res}")



# 定时更新连接记录数据
def ping_task():
    try:
        url = base_url + "report/ping_update"
        # url = test_url + "report/ping_update"
        res = requests.post(url)
    except Exception as e:
        print("ping task error:", e)
    else:
        print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} -- ping task : {res}")



def main():

    scheduler = BlockingScheduler()
    scheduler.add_job(ping_task, 'interval', seconds=60 * 10)
    scheduler.add_job(connect_task, 'interval', seconds=60 * 10)

    try:
        # 定时任务启动
        scheduler.start()
    except Exception as e:
        print(e)
        print("启动错误")

if __name__ == '__main__':
    main()