import time
import requests
import json
import redis

REDIS_HOST = "3.101.19.69"
REDIS_PASSWORD = "leyou2020"
NODE_HOST = "https://nodes.9527.click"


class RedisTool(object):
    pool_data = redis.ConnectionPool(host=REDIS_HOST, port=6379, password=REDIS_PASSWORD, db=0)
    db0 = redis.Redis(connection_pool=pool_data)

    pool_two = redis.ConnectionPool(host=REDIS_HOST, port=6379, password=REDIS_PASSWORD, db=2)
    db2 = redis.Redis(connection_pool=pool_two)

    pool10 = redis.ConnectionPool(host=REDIS_HOST, port=6379, password=REDIS_PASSWORD, db=10)
    db10 = redis.Redis(connection_pool=pool10)

class UpdateNode(object):

    def get_trojan_note(self):
        """
            获取trojan节点
        """
        url = f'{NODE_HOST}/get_trajon_node'

        response = requests.post(url=url,
                                 data={"username": "getnodes",
                                       "password": "TxPo4gNO3FpEiWYT9bgp"}
                                 )
        if response.status_code == 200:
            return json.loads(response.content.decode('utf-8'))
        return None

    def node_sort(self, data):
        """
            根据权重排序
        """
        data.sort(key=lambda x: x["weights"])
        data.reverse()
        return data

    def base_node_sort(self, nodes):
        """
            基础节点排序
        """
        us_node_number = 1
        base_node_number = 4

        other = 5
        base_node = []  # 基础节点
        us_node = []  # 美国节点
        for node in nodes:
            country = node.get("country")
            if country == "United States":
                us_node.append(node)
            else:
                base_node.append(node)

        # 权重排序

        us_node = self.node_sort(us_node)
        base_node = self.node_sort(base_node)
        # 获取 2个美国节点  和3个其他国家节点
        if len(us_node) >= us_node_number and len(base_node) >= us_node_number:
            # all_node = base_node[0:base_node_number] + us_node[0:us_node_number]
            all_node = base_node + us_node
        else:
            sum_node = base_node + us_node

            if len(sum_node) >= other:
                # all_node = sum_node[0:other]
                all_node = sum_node
            else:
                all_node = sum_node
        return all_node

    # def vip_node_sort(self, nodes):
    #     """
    #         基础节点排序
    #     """
    #     United_States= 2
    #     base_node_number = 3
    #     us_node_number = 2
    #     base_node_number = 3
    #     netherlands = 2
    #     base_node_number = 3
    #
    #     other = 10
    #     base_node = []  # 基础节点
    #     us_node = []  # 美国节点
    #     all_country = []
    #     node_dict = {}
    #     for node in nodes:
    #         temp_country = node.get("country")
    #         all_country.append(temp_country)
    #     all_country = list(set(all_country))
    #
    #     # print(all_country)
    #
    #     for country in all_country:
    #         temp_node = []
    #
    #         for node in nodes:
    #             node_country = node.get("country")
    #             if node_country == country:
    #                 temp_node.append(node)
    #
    #         if temp_node:
    #             node_dict[country] = self.node_sort(temp_node)
    #
    #
    #     for k,v in node_dict.items():
    #         print(k,v)
    #
    #     # # 权重排序
    #     #
    #     # us_node = self.node_sort(us_node)
    #     # base_node = self.node_sort(base_node)
    #     # # 获取 2个美国节点  和3个其他国家节点
    #     # if len(us_node) >= us_node_number and len(base_node) >= us_node_number:
    #     #     all_node = base_node[0:base_node_number] + us_node[0:us_node_number]
    #     # else:
    #     #     sum_node = base_node + us_node
    #     #
    #     #     if len(sum_node) >= other:
    #     #         all_node = sum_node[0:other]
    #     #     else:
    #     #         all_node = sum_node
    #     # return all_node

    def all_node(self):
        datas = self.get_trojan_note()

        nodes = datas.get("nodes", "")
        base_nodes = []
        vip_nodes = []

        for node in nodes:
            print(node)
            node_type = node.get("node_type")
            if node_type == 1:
                base_nodes.append(node)
            elif node_type == 2:
                vip_nodes.append(node)

        if base_nodes:
            base_nodes = self.base_node_sort(base_nodes)
            # print(res)

        return base_nodes + vip_nodes

    def start(self):
        """
        节点更新到redis
        :return:
        """

        # 获取最优节点
        trojan_nodes = self.all_node()
        if not trojan_nodes:
            print("无法获取node节点")
            return

        new_hosts = []
        key_hosts = RedisTool.db2.keys()
        old_hosts = []

        if key_hosts:
            for key_host in key_hosts:
                conv_data = int(str(key_host, "utf-8"))
                old_hosts.append(conv_data)

        # 插入新的节点
        for node in trojan_nodes:
            id = node.get("id")
            new_hosts.append(id)
            try:
                redis_staus = RedisTool.db2.set(id, json.dumps(node))
                if redis_staus:
                    print(f"trojan更新{id}成功")
                else:
                    print(f"trojan更新{id}失败")

            except Exception as e:
                print(e)

        # 删除多余ip
        if new_hosts and old_hosts:
            del_hosts = list(set(old_hosts).difference(set(new_hosts)))
            if del_hosts:
                for del_host in del_hosts:
                    del_status = RedisTool.db2.delete(del_host)
                    if del_status:
                        print(f"trojan删除不存在的{del_host}成功")
                    else:
                        print(f"trojan删除不存在的{del_host}失败")


def main():
    update_node = UpdateNode()
    while True:
        print("开始trojan获取节点")
        update_node.start()
        print("睡眠60秒")
        time.sleep(60)


if __name__ == '__main__':
    main()

