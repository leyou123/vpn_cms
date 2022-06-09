
import requests
import time
from apscheduler.schedulers.blocking import BlockingScheduler

NODE_HOST = "https://api.9527.click"

def check_user_status():
    """
        jiance
    """
    url = f"{NODE_HOST}/v2/user/check_user_status"

    json_data = {
        "key": "leyou2021"
    }
    requests.post(url=url, json=json_data)



def synchronization_user():
    """
        jiance
    """
    url = f"{NODE_HOST}/v2/user/sync_user"

    json_data = {
        "type": 2
    }
    requests.post(url=url, json=json_data)


def clear_advertising():
    """
        jiance
    """
    url = f"{NODE_HOST}/v2/user/clear_advertising_count"

    json_data = {

    }
    requests.post(url=url, json=json_data)


def start():
    # try:
    #     check_user_status()
    #     synchronization_user()
    #     clear_advertising()
    # except Exception as e:
    #     print(e)


    while True:
        try:
            synchronization_user()
            clear_advertising()
        except Exception as e:
            print(e)
        print("睡眠24分钟")
        time.sleep(60*60*24)


def main():
    scheduler = BlockingScheduler()
    print("启动")
    scheduler.add_job(start, 'cron', hour='10', minute=00)
    scheduler.start()


if __name__ == '__main__':
    start()
    # main()