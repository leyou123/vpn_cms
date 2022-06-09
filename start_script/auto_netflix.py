import paramiko
import requests
import json
import time

class AutoNetflixServer(object):

    def __init__(self):
        self.sys_ip = ''
        self.port = 22
        self.username = 'root'
        self.password = 'Leyou2020'

    def exec_cmd(self, cmds):
        try:
            client = paramiko.SSHClient()

            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            client.connect(self.sys_ip, 22, username=self.username, password=self.password, timeout=20)
            stdin, stdout, stderr = client.exec_command(cmds)
            results = stdout.readlines()
            return results

        except Exception as e:
            print(e)
            return 404
        finally:
            client.close()

    def modify_network(self):
        network_path = "/etc/sysconfig/network-scripts/ifcfg-eth0"
        order_one = 'PEERDNS="no"'
        network_cmds = f"sed -i '$a\{order_one}' {network_path}"
        res = self.exec_cmd(network_cmds)
        if res is 404:
            print("修改网络失败")
        else:
            print("修改网络成功")

    def modify_dns(self):
        dns_path = "/etc/resolv.conf"
        repalne_dns = f"sed -i 's/108.61.10.10/206.119.175.69/' {dns_path}"
        res = self.exec_cmd(repalne_dns)
        if res is 404:
            print("修改DNS失败")
        else:
            print("修改DNS成功")

    def reboot_server(self):
        """
            重启
        :return:
        """
        reboot_cmd = "reboot"
        res = self.exec_cmd(reboot_cmd)
        if res is 404:
            print("重启失败")
        else:
            print("重启成功")

    def restart_trojan_server(self):
        """
            重启trojan nginx 服务器
        :return:
        """
        nginx_cmd = "/etc/nginx/sbin/nginx"
        trojan_cmd = "systemctl start trojan.service"
        self.exec_cmd(nginx_cmd)
        res = self.exec_cmd(trojan_cmd)

        if res is 404:
            print("重启trojan失败")
        else:
            print("重启成功")

    def modify_server_status(self):
        """
            修改服务器状态
        :return:
        """
        url = "https://nodes.9527.click/modify_node"

        datas = {
            "username": "getnodes",
            "password": "TxPo4gNO3FpEiWYT9bgp",
            "ip":self.sys_ip
        }

        print(datas)
        response = requests.post(url, data=datas)
        print(response.status_code)
        if response.status_code == 200:
            print("修改成功")
        else:
            print("修改失败")

    def get_datas(self):
        url = "https://nodes.9527.click/get_netflix_node"

        datas = {
            "username": "getnodes",
            "password": "TxPo4gNO3FpEiWYT9bgp"
        }
        response = requests.post(url, data=datas)
        if response.status_code == 200:
            return json.loads(response.text)
        return None

    def start(self):
        node_datas = self.get_datas()
        if not node_datas:
            print("没有可用ip")
            return
        self.sys_ip = node_datas["nodes"].get("ip","")
        self.modify_network()
        self.modify_dns()
        self.reboot_server()
        print("等待重启30秒")
        time.sleep(30)
        self.restart_trojan_server()
        self.modify_server_status()


def main():
    while True:
        try:
            auto_netflix = AutoNetflixServer()
            auto_netflix.start()
        except Exception as e:
            print(e)
        print("睡眠60秒")
        time.sleep(60*30)

if __name__ == '__main__':

    main()


