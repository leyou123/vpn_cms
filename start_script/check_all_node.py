import datetime
import requests

from apscheduler.schedulers.blocking import BlockingScheduler

base_url = "https://nodes.9527.click/"
# test_url = "http://54.177.55.54:9000/"
test_url = "http://54.177.55.54:7000/"


def check_all_node():
    try:
        url = base_url + "node/Node_update"
        # url = test_url + "node/Node_update"
        data = {
            "type": "update_all"
        }
        res = requests.post(url=url, json=data)
    except Exception as e:
        print("check_all_node:", e)
    else:
        print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} -- connect task : {res}")



def main():

    scheduler = BlockingScheduler()
    scheduler.add_job(check_all_node, 'cron', year='*', month='*', day=1)
    # scheduler.add_job(check_all_node, 'cron', year='*', month='*', day=30, hour='*', minute='*/1')

    try:
        # 定时任务启动
        print("启动定时任务")
        scheduler.start()
    except Exception as e:
        print(e)
        print("启动错误")

if __name__ == '__main__':
    main()