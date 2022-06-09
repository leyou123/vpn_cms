import requests
import json
import time

NODE_HOST= "https://nodes.9527.click"
DATAS_HOST = "https://datas.9527.click"


class UpdateNodeStatus(object):

    def get_ip(self):
        user_url = f"{NODE_HOST}/get_trajon_node"
        data = {
            "username": "getnodes",
            "password": "TxPo4gNO3FpEiWYT9bgp"
        }
        user_response = requests.post(user_url, data=data)

        if user_response.status_code != 200:
            return
        host_all = []
        datas = json.loads(user_response.text)
        print(datas)
        nodes = datas.get("nodes", None)
        for node in nodes:
            ip = node.get("ip", "")
            if ip in host_all:
                continue
            host_all.append(node)

        return host_all

    def update(self):
        nodes = self.get_ip()
        url = f"{DATAS_HOST}/servers/upload_server_data"
        json_data = {
            "nodes": nodes,
        }
        print(json_data)
        user_response = requests.post(url=url, json=json_data)
        print(user_response.status_code)


if __name__ == '__main__':

    while True:
        try:
            node = UpdateNodeStatus()
            node.update()
        except Exception as e:
            print(e)
        print("睡眠2分钟")
        time.sleep(60*2)
