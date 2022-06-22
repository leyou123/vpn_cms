import datetime
import requests

from apscheduler.schedulers.blocking import BlockingScheduler

base_url = "https://api.9527.click/v2/"
test_url = "http://54.177.55.54:10050/v2/"


def check_all_node():
    # 定时检查节点成功率
    try:
        url = base_url + "report/check_all_node"
        # url = test_url + "report/check_all_node"
        res = requests.post(url)
    except Exception as e:
        print("connect task error:", e)
    else:
        print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} -- connect task : {res}")




def main():

    scheduler = BlockingScheduler()
    scheduler.add_job(check_all_node, 'interval', seconds=60 * 30)

    try:
        # 定时任务启动
        scheduler.start()
    except Exception as e:
        print(e)
        print("启动错误")

if __name__ == '__main__':
    main()