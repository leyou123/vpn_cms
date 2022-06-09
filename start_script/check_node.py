import subprocess
import requests


class ConnectStatus(object):

    def check_ping(self, ip):
        cmd = f"ping -c 4 {ip}"
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        res1 = p.stdout.read()

        condition_one = "icmp_seq"
        condition_two = "0% packet loss"
        datas = str(res1, encoding="utf-8")
        if condition_one in datas and condition_two in datas:
            return "open"
        else:
            return "close"

    def submit_data(self):
        """
            提交数据
        """
        list_data = []

        url = "https://nodes.9527.click/connect_status"
        ip_all = ["107.191.44.114","199.247.16.5"]
        # "199.247.16.5"
        check_type = "ping"
        # check_type = "connect"

        state = "US"

        for ip in ip_all:
            temp_data = {
                "ip": ip,
                "state": state,
                "check_type": check_type,
                # "check_result": self.check_ping(ip),
                "check_result": "close"
            }
            list_data.append(temp_data)

        datas = {
            "username": "getnodes",
            "password": "TxPo4gNO3FpEiWYT9bgp",
            "datas": list_data,
        }
        print(datas)
        response = requests.post(url, json=datas)
        if response.status_code == 200:
            print("数据提交成功")
        else:
            print("数据提交失败")


if __name__ == '__main__':
    connect = ConnectStatus()
    connect.submit_data()


