
import requests
import time

NODE_HOST = "https://test.9527.click"

def del_temp_user():
    """
        jiance
    """
    url = f"{NODE_HOST}/v2/user/del_temp_user"

    json_data = {
        "key": "leyou2021"
    }
    res = requests.post(url=url, json=json_data)

    print(res.status_code)


def main():
    while True:
        try:
            del_temp_user()
        except Exception as e:
            print(e)
        print(f"睡眠5分钟")
        time.sleep(60*5)


if __name__ == '__main__':

    main()