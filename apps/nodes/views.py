import json
import requests
import time

from django.http import JsonResponse
from django.views.generic.base import View
from django_redis import get_redis_connection

from apps.users.models import User
from utils.crypto import Aescrypt
from vpn_cms.settings import NODE_HOST

aes = Aescrypt()

db2 = get_redis_connection('DB2')
db0 = get_redis_connection('default')
db10 = get_redis_connection('DB10')
db3 = get_redis_connection('DB3')


class Node(View):

    def post(self, request):
        """
        获取所有trojan节点
        :param request:
        :return:
        """

        data = json.loads(request.body.decode(encoding="utf-8"))
        key = data.get("key", "")
        aes_result = aes.aesdecrypt(key)
        if aes_result != "leyou2021":
            return JsonResponse({"code": 404, "message": 'key error'})

        redis_key = db2.keys()
        hosts = []
        if not redis_key:
            return JsonResponse({"code": 404, "message": 'not hosts'})

        uid = data.get("uid", "")
        if not uid:
            return JsonResponse({"code": 404, "message": 'not fount uid'})

        # if not user or not user.country:
        #     for key in redis_key:
        #         str_key = str(key, "utf-8")
        #         json_data = json.loads(db2.get(str_key))
        #         hosts.append(json_data)
        #
        #     # hosts.sort(key=lambda x: x["weights"])
        #     # hosts.reverse()
        #     return JsonResponse({"code": 200, "message": "success", "data": hosts})
        user = User.objects.filter(uid=int(uid)).first()

        if not user:
            return JsonResponse({"code": 404, "message": "not found user"})

        country = ""

        if user.country:
            country = user.country

        if not country:
            for key in redis_key:
                str_key = str(key, "utf-8")
                json_data = json.loads(db2.get(str_key))
                hosts.append(json_data)
            return JsonResponse({"code": 200, "message": "success", "data": hosts})

        for key in redis_key:
            str_key = str(key, "utf-8")

            node_result = db2.get(str_key)
            if not node_result:
                continue
            json_data = json.loads(node_result)
            black = json_data.get("black", "")
            white = json_data.get("white", "")
            if black:
                if country in black:
                    continue
            if white:
                if country not in white:
                    continue
            hosts.append(json_data)
        # hosts.sort(key=lambda x: x["weights"])
        # hosts.reverse()

        return JsonResponse({"code": 200, "message": "success", "data": hosts})


class Register(View):
    def post(self, request):
        """
        连接节点
        :param request:
        :return:
        """
        data = json.loads(request.body.decode(encoding="utf-8"))
        key = data.get("key", "")
        aes_result = aes.aesdecrypt(key)
        if aes_result != "leyou2021":
            return JsonResponse({"code": 404, "message": 'key error'})
        uuid = data.get("uuid", "")
        ip = data.get("ip", "")
        if not uuid or not ip:
            return JsonResponse({"code": 404, "message": 'not found ip or uuid'})
        user_ip = data.get("user_ip", "")
        if user_ip:
            try:
                conv_data = json.dumps(data)
                db0.lpush("register", conv_data)
            except Exception as e:
                print(e)

        if not uuid or not ip:
            return JsonResponse({"code": 404, "message": 'not found uuid or ip'})

        data = {
            "password": uuid,
            "ip": ip
        }
        # 'https://nodes.9527.click'
        url = f"{NODE_HOST}/user/create_single_user"
        try:
            response = requests.post(url=url, data=data, timeout=15)
        except Exception as e:
            return JsonResponse({"code": 404, "message": str(e)})
        if response:
            result = json.loads(response.text)
            code = int(result.get("code", 404))
            message = result.get("message", "")
            return JsonResponse({"code": code, "message": message})
        else:
            return JsonResponse({"code": 404, "message": 'request error'})


class CountryNode(View):

    def get_all_node(self):

        redis_key = db2.keys()
        hosts = []
        if not redis_key:
            return hosts
        for key in redis_key:
            str_key = str(key, "utf-8")
            json_data = json.loads(db2.get(str_key))
            hosts.append(json_data)
        return hosts

    def check_country_status(self, country, connect_data):

        country_json = {
            "中国": "China",
            "印度": "India",
            "印度尼西亚": "Indonesia"
        }
        try:
            get_country = country_json.get(country, "")
            json_connect_data = json.loads(connect_data)
            status = json_connect_data[get_country].get("connect", "")
        except Exception as e:
            print(e)
            return False

        if status == "open":
            return True
        else:
            return False

    def post(self, request):
        """
            获取所有过滤节点trojan节点
        """

        data = json.loads(request.body.decode(encoding="utf-8"))
        key = data.get("key", "")
        aes_result = aes.aesdecrypt(key)
        if aes_result != "leyou2021":
            return JsonResponse({"code": 404, "message": 'key error'})
        uid = data.get("uid", "")
        country = data.get("country", "")
        hosts = []
        if not uid:
            return JsonResponse({"code": 404, "message": 'not fount uid'})

        user = User.objects.filter(uid=int(uid)).first()
        if not country:
            # 数据库获取用户国家
            # user = User.objects.filter(uid=int(uid)).first()
            if not user:
                return JsonResponse({"code": 404, "message": 'not fount uid'})

            try:
                if user.country:
                    country = user.country
            except Exception as e:
                country = ""

        if not country:
            # 如果没有拿到就返回所有节点
            hosts = self.get_all_node()
            return JsonResponse({"code": 200, "message": "success", "data": hosts})

        # 如果有国家节点缓存
        # redis_key = db2.keys()
        # for key in redis_key:
        #     str_key = str(key, "utf-8")
        #     json_data = json.loads(db2.get(str_key))
        #     keys = json_data.get('country')
        #     id = json_data.get("id")
        #     db10.set(str(keys)+str(id), json.dumps(json_data))
        # 如果有国家节点缓存
        # country_node_data = db10.get(country)

        hosts = self.get_all_node()
        new_hosts = []
        result = []
        cache_nodes = ""
        for host in hosts:
            black = host.get("black", "")
            white = host.get("white", "")
            connect_data = host.get("connect_data", "")
            host_country = host.get("country", "")
            node_type = host.get("node_type", "")
            # if not node_type
            try:
                if user.member_type_id != int(node_type):
                    continue
            except Exception as e:
                print("nodes -- CountryNode error:", e)
            if country in black:
                continue
            print(country)
            print(host_country)
            if str(country) == str(host_country):
                # host['connect_data'] = ""
                # json_host = json.dumps(host)
                # cache_nodes += f"{json_host}|"
                result.append(host)
            else:
                continue

        if new_hosts:
            cache_nodes[:-1]
            # db10.set(country, cache_nodes, ex=60 * 60)
            return JsonResponse({"code": 200, "message": "success", "data": result})
        else:
            return JsonResponse({"code": 200, "message": "success", "data": result})
