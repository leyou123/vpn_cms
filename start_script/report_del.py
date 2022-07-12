import datetime
import requests

from apscheduler.schedulers.blocking import BlockingScheduler

base_url = "https://api.9527.click/"
# test_url = "http://54.177.55.54:8000/"
test_url = "http://54.177.55.54:10050/"


def delete_report():
    try:
        url = base_url + "v2/report/del_report"
        # url = test_url + "v2/report/del_report"
        res = requests.post(url=url)
    except Exception as e:
        print("delete_report:", e)
    else:
        print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} -- delete result : {res}")


def main():

    scheduler = BlockingScheduler()
    # 每个周一的早上10点删除一次数据
    scheduler.add_job(delete_report, 'cron', day_of_week='0', hour=(10-8), minute=0)
    # scheduler.add_job(delete_report, 'cron', day_of_week='1', hour=(17-8), minute=56)

    try:
        # 定时任务启动
        print("启动定时任务")
        scheduler.start()
    except Exception as e:
        print(e)
        print("启动错误")

if __name__ == '__main__':
    main()