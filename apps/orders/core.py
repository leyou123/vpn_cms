import time
import json
import requests
import base64
from django.http import JsonResponse
from vpn_cms.settings import mongodb
from apps.manage.models import AppPackage, PayConfig, SetMeal,MembersConfig,Members
from apps.orders.models import Orders
from apps.users.models import User
from utils.google_play import create_token
from pymongo import MongoClient
from requests.auth import HTTPBasicAuth
from django_redis import get_redis_connection

from vpn_cms.settings import MONGODB_HOST, MONGODB_PORT, MONGODB_PASSWORD,client_id,client_secret,paypal_url

mongodb_link = MongoClient(f'mongodb://root:{MONGODB_PASSWORD}@{MONGODB_HOST}:{MONGODB_PORT}/').vpn_cms

db0 = get_redis_connection('default')
# class OrdersLogs(object):
#
#     @staticmethod
#     def ios_insert_one(json_data):
#         res = mongodb.ios_orders_logs.insert_one(json_data)
#         return res
#
#     @staticmethod
#     def ios_notification_insert_one(json_data):
#         res = mongodb.orders_ios_notification_logs.insert_one(json_data)
#         return res
#
#     @staticmethod
#     def google_insert_one(json_data):
#         res = mongodb.google_orders_logs.insert_one(json_data)
#         return res
#
#     @staticmethod
#     def google_notification_insert_one(json_data):
#         res = mongodb.orders_google_notification_logs.insert_one(json_data)
#         return res


class IOSPay(object):

    @classmethod
    def get_data(cls, datas):

        """
        支付回调
        :param request:
        :return:
        """
        print(datas)
        latest_receipt = datas["unified_receipt"].get("latest_receipt", None)
        password = datas.get("password", None)
        environment = datas.get("environment", None)
        auto_renew_status = datas.get("auto_renew_status", None)
        original_transaction_id = datas["unified_receipt"]["pending_renewal_info"][0].get("original_transaction_id",
                                                                                          None)
        first_transaction_id = datas["unified_receipt"]["latest_receipt_info"][0].get("transaction_id", None)
        if not latest_receipt or not password or not environment or not auto_renew_status or not original_transaction_id:
            return None, None, None, None, None

        return password, environment, auto_renew_status, original_transaction_id, first_transaction_id, latest_receipt

    @classmethod
    def request(cls, receipt_data, password, environment, app):
        """
            请求苹果后台数据
        """
        pay_config = PayConfig.objects.filter(app=app).first()

        url = None
        order_type = 0
        if environment == "Production" or environment == "PROD":  # 正式环境
            order_type = 1
            url = pay_config.buy_url
        elif environment == "Sandbox":  # 沙盒
            order_type = 0
            url = pay_config.sandbox_url

        headers = {"Content-type": "application/json"}
        data = {
            "receipt-data": receipt_data,
            'password': password,
            "exclude-old-transactions": True
        }
        try:
            response = requests.post(url=url, data=json.dumps(data), headers=headers)
        except Exception as e:
            print(e)
            return {"code": 404, "message": "request error"}
        if response.status_code != 200:
            return {"code": 404, "message": response.text}
        datas = json.loads(response.text)
        status = datas.get("status")
        if status != 0:
            return {"code": 404, "message": response.text}
        datas["order_type"] = order_type
        return {"code": 200, "data": datas}

    @classmethod
    def auto_renew_renewal(cls, request_data, original_transaction_id, app, package_id):
        """
            订阅事件
        """
        code = request_data.get("code", "")
        if code != 200:
            message = request_data.get("message", "")
            return JsonResponse({"code": code, "message": message})
        order_data = request_data.get("data", "")

        orders = order_data['receipt'].get("in_app", None)
        order_type = order_data.get("order_type", "")

        user_first_orders = Orders.objects.filter(order_id=original_transaction_id).first()

        if not user_first_orders:
            return JsonResponse({"code": 404, "message": f"not found {original_transaction_id}"})

        user = User.objects.filter(uid=user_first_orders.user).first()

        if not user:
            return JsonResponse({"code": 404, "message": f"not found user_id {user_first_orders.user}"})

        for order in orders:
            transaction_id = order.get("transaction_id", "")
            orders = Orders.objects.filter(order_id=transaction_id).first()
            if orders:
                # print(f"重复原始订单{transaction_id}")
                continue
            product_id = order.get("product_id", None)
            product_time = order.get("purchase_date_ms", None)
            expires_date = order.get("expires_date_ms", None)

            if not product_id or not product_time or not expires_date:
                continue
            # print(f"商品id{product_id}")
            set_meal = SetMeal.objects.filter(goods_id=product_id).first()
            # print(f"用户:{user}")
            # print(f"商品金额:{dispose_meal.money}")
            # print(f"商品名:{dispose_meal.name}")
            # print(f"商品类型:{dispose_meal.goods_type}")
            # print(f"订单类型:{order_type}")
            # print(f"过期时间:{int(product_time)}")
            is_trial_period = order.get("is_trial_period", "")

            try:
                state = 1
                if is_trial_period == "true":
                    state = 0
                Orders.objects.create(
                    user=user.uid,
                    app=app,
                    set_meal=set_meal,
                    package_id=package_id,
                    order_id=transaction_id,
                    product_time=int(product_time),
                    order_type=order_type,
                    state=state,
                    country=user.country
                )
            except Exception as e:
                print(e)
                return JsonResponse({"code": 404, "message": e})
            # print(f"订阅刷新会员时间{int(product_time)}")
            # 会员时间

            exp_datetime = int(expires_date) / 1000
            if exp_datetime > int(user.member_validity_time):
                user.member_validity_time = exp_datetime
            user.set_meal = set_meal
            user.member_type = set_meal.members
            user.subscription_type = 1
            user.first_subscription = 1
            user.save()
        return JsonResponse({"code": 200, "message": "ok"})

    @classmethod
    def auto_renew_close(cls, request_data, original_transaction_id, first_transaction_id, app):
        """
            订阅订单关闭
        """
        code = request_data.get("code", "")
        if code != 200:
            message = request_data.get("message", "")
            return JsonResponse({"code": code, "message": message})
        order_data = request_data.get("data", "")
        orders = order_data['receipt'].get("in_app", None)

        original_order = Orders.objects.filter(order_id=original_transaction_id).first()
        if not original_order:
            return JsonResponse({"code": 404, "message": f"not found {original_transaction_id}"})

        user = User.objects.filter(uid=original_order.user).first()
        if not user:
            return JsonResponse({"code": 404, "message": "not found user"})
        expires_date = orders[0].get("expires_date_ms", None)
        # transaction_id = orders[0].get("transaction_id", None)

        expires_date_amend = int(expires_date) / 1000


        first_orders = Orders.objects.filter(order_id=first_transaction_id).first()
        # 判断支付状态类型

        if not first_orders:
            print(f"没有发现此订单{first_transaction_id}")
            return JsonResponse({"code": 404, "message": f"not found {first_transaction_id}"})

        if first_orders.state:
            Orders.objects.filter(order_id=first_transaction_id).update(state=3, refund_time=int(time.time()))
            user.member_validity_time = expires_date_amend

        else:
            Orders.objects.filter(order_id=first_transaction_id).update(state=2, refund_time=int(time.time()))
            user.member_validity_time = int(time.time()) + 60*60*24*7
        user.subscription_type = 0
        user.save()

        return JsonResponse({"code": 200, "message": "ok"})

    # @classmethod
    # def auto_renew_close(cls, request_data, original_transaction_id, first_transaction_id, app):
    #     """
    #         订阅订单关闭
    #     """
    #     code = request_data.get("code", "")
    #     if code != 200:
    #         message = request_data.get("message", "")
    #         return JsonResponse({"code": code, "message": message})
    #     order_data = request_data.get("data", "")
    #     orders = order_data['receipt'].get("in_app", None)
    #
    #     original_order = Orders.objects.filter(order_id=original_transaction_id).first()
    #     if not original_order:
    #         return JsonResponse({"code": 404, "message": f"not found {original_transaction_id}"})
    #
    #     user = User.objects.filter(uid=original_order.user).first()
    #     if not user:
    #         return JsonResponse({"code": 404, "message": "not found user"})
    #     expires_date = orders[0].get("expires_date_ms", None)
    #     # transaction_id = orders[0].get("transaction_id", None)
    #
    #     expires_date_amend = int(expires_date) / 1000
    #     user.member_validity_time = expires_date_amend
    #     user.subscription_type = 0
    #     user.save()
    #
    #     # 判断是否有原订单
    #     if original_order:
    #         if original_order.total_amount:
    #             Orders.objects.filter(order_id=original_transaction_id).update(state=3, refund_time=int(time.time()))
    #         else:
    #             Orders.objects.filter(order_id=original_transaction_id).update(state=2, refund_time=int(time.time()))
    #
    #     first_orders = Orders.objects.filter(order_id=first_transaction_id).first()
    #
    #     if first_orders:
    #         if first_orders.total_amount:
    #             Orders.objects.filter(order_id=first_transaction_id).update(state=3, refund_time=int(time.time()))
    #         else:
    #             Orders.objects.filter(order_id=first_transaction_id).update(state=2, refund_time=int(time.time()))
    #
    #     return JsonResponse({"code": 200, "message": "ok"})

    @classmethod
    def start(cls, datas, package_id):
        password, environment, auto_renew_status, original_transaction_id, first_transaction_id, latest_receipt = IOSPay.get_data(
            datas)
        if not password:
            return JsonResponse({"code": 404, "message": "not found data"})

        app = AppPackage.objects.filter(package_id=package_id).first()
        if not app:
            return JsonResponse({"code": 404, "message": "not found app"})
        request_data = IOSPay.request(latest_receipt, password, environment, app)

        # 订阅状态
        if auto_renew_status == "true":
            return IOSPay.auto_renew_renewal(request_data, original_transaction_id, app, package_id)
        elif auto_renew_status == "false":
            return IOSPay.auto_renew_close(request_data, original_transaction_id, first_transaction_id, app)


class GooglePay(object):

    @classmethod
    def get_data(cls, data):
        uid = data.get("uid", "")
        package_name = data.get("package_name")
        product_id = data.get("product_id", "")
        purchase_token = data.get("purchase_token", "")

        user = User.objects.filter(uid=uid).first()
        app = AppPackage.objects.filter(package_id=package_name).first()
        pay_config = PayConfig.objects.filter(app=app).first()

        if not user or not app or not pay_config:
            return {"status": False, "message": "not found PayConfig or user or app"}

        header = create_token(pay_config)
        if not header:
            return {"status": False, "message": "token error"}

        return user, app

    @classmethod
    def acknowledgement(cls, url, package_name, product_id, purchase_token, header):
        """
            商品确认
        """
        query_url = f"{url}/{package_name}/purchases/subscriptions/{product_id}/tokens/{purchase_token}:acknowledge"
        response_query = requests.post(url=query_url, headers=header, timeout=15)

        if response_query.status_code != 204:
            return False
        else:
            return True

    @classmethod
    def request_google_query(cls, url, package_name, product_id, purchase_token, header):
        """
            查询订阅详细信息
        """
        query_url = f"{url}/{package_name}/purchases/subscriptions/{product_id}/tokens/{purchase_token}"
        try:
            response_query = requests.get(url=query_url, headers=header, timeout=15)
            if response_query.status_code == 200:
                return True, response_query
        except Exception as e:
            return False, None
        return False, None


class GoogleNotice(object):
    """
        goole通知
    """

    @classmethod
    def get_request_data(cls, data):
        """
            处理数据
        """
        datas = base64.b64decode(data)
        purchase_token = None
        package_name = None
        notification_type = None
        subscription_id = None
        if isinstance(datas, bytes):
            try:
                conv_datas = json.loads(str(datas, "utf-8"))
                # print(conv_datas)
                purchase_token = conv_datas["subscriptionNotification"].get("purchaseToken", "")
                package_name = conv_datas.get("packageName", "")
                notification_type = conv_datas["subscriptionNotification"].get("notificationType", "")
                subscription_id = conv_datas["subscriptionNotification"].get("subscriptionId", "")
            except Exception as e:
                print("数据出错")

        return purchase_token, package_name, notification_type, subscription_id

    @classmethod
    def orders_cancel(cls, origin_product, current_product):
        if not origin_product.total_amount:
            Orders.objects.filter(order_id=origin_product.order_id).update(state=2, refund_time=int(time.time()))
        if current_product:
            Orders.objects.filter(order_id=current_product.order_id).update(state=3, refund_time=int(time.time()))

    @classmethod
    def create_order(cls, user, order_id, order_type, set_meal, auto_renewing, expiry_time, app, package_id):
        # print("谷歌通知完成")

        try:
            Orders.objects.create(
                user=user.uid,
                app=app,
                set_meal=set_meal,
                order_id=order_id,
                package_id=package_id,
                product_time=int(time.time() * 1000),
                order_type=order_type,
                country=user.country,
                state=1
            )

            if auto_renewing:
                user.member_validity_time = int(expiry_time) / 1000
                user.member_type = set_meal.members
                user.white_type = 0
                user.subscription_type = 1
                user.first_subscription = 1
                user.save()
            else:
                user.member_validity_time = int(expiry_time) / 1000
                user.white_type = 0
                user.subscription_type = 0
                user.save()
            return JsonResponse({"code": 200, "message": "success"})
        except Exception as e:
            print(e)
            return JsonResponse({"code": 404, "message": "error"})

    @classmethod
    def start(cls, json_data):
        data = json_data["message"].get("data", "")
        if not data:
            return JsonResponse({"code": 404, "message": "not foun data"})

        purchase_token, package_name, notification_type, subscription_id = cls.get_request_data(data)

        if not package_name or not purchase_token or not subscription_id or not notification_type:
            return JsonResponse({"code": 404,
                                 "message": "not found package_name or purchase_token or subscription_id or notification_type"})

        if notification_type == 3:
            pass
            # self.orders_cancel()
        if notification_type == 4:
            # print(f"首次订单")
            return JsonResponse({"code": 200, "message": "first orders"})
        app = AppPackage.objects.filter(package_id=package_name).first()
        pay_config = PayConfig.objects.filter(app=app).first()
        header = create_token(pay_config)
        if not header:
            return JsonResponse({"status": False, "message": "token error"})
        status, response = GooglePay.request_google_query(pay_config.api_url, package_name, subscription_id,
                                                          purchase_token, header)
        if not status:
            return JsonResponse({"status": False, "message": "requests error"})
        query_datas = json.loads(response.text)

        expiry_time = query_datas.get("expiryTimeMillis", None)
        auto_renewing = query_datas.get("autoRenewing")
        order_id = query_datas.get("orderId", None)

        if ".." not in order_id:
            return JsonResponse({"code": 404, "message": "orders_id error"})

        # price_currency_code = response.get("priceCurrencyCode", "")
        # price = response.get("priceAmountMicros", 0)

        if not order_id or not expiry_time:
            return JsonResponse({"code": 404, "message": "data error"})

        origin_order_id = str(order_id).split("..")[0].strip()
        product_id = Orders.objects.filter(order_id=origin_order_id).first()
        if not product_id:
            print(f"没有原订单{product_id}")
            return JsonResponse({"code": 404, "message": "not found origin_order_id"})
        user = User.objects.filter(uid=product_id.user).first()
        if not user:
            return JsonResponse({"code": 404, "message": "not found user"})
        # set_meal = SetMeal.objects.filter(goods_id=product_id).first()
        query_orders = Orders.objects.filter(order_id=order_id).first()

        if query_orders:
            # print(f"订单存在{order_id}")
            return JsonResponse({"code": 404, "message": "orders exits"})

        order_type = 1
        if int(product_id.user) == int(pay_config.test_id):
            order_type = 0

        return cls.create_order(user, order_id, order_type, product_id.set_meal, auto_renewing, expiry_time, app, package_name)


class UserData(object):

    @classmethod
    def save(cls, orders_data, app, user, transaction_id, order_type, package_id):
        product_id = orders_data.get("product_id", "")
        product_time = orders_data.get("purchase_date_ms", "")
        expires_date = orders_data.get("expires_date_ms", "")
        is_trial_period = orders_data.get("is_trial_period", "")
        set_meal = SetMeal.objects.filter(goods_id=product_id).first()
        product_time = int(product_time)
        exp_datetime = int(int(expires_date) / 1000)
        try:
            state = 0
            if is_trial_period == "false":
                state = 1

            Orders.objects.create(
                user=user.uid,
                package_id=package_id,
                app=app,
                set_meal=set_meal,
                order_id=transaction_id,
                product_time=int(product_time),
                order_type=order_type,
                state=state,
                country=user.country
            )
            members = Members.objects.filter(type=1).first()
            members_config = MembersConfig.objects.filter(members=members).first()
            print(members_config.device_count)
            User.objects.filter(id=user.id).update(
                member_validity_time=exp_datetime,
                member_type=1,
                subscription_type=1,
                first_subscription=1,
                set_meal=set_meal,
                white_type=0,
                max_device_count=members_config.device_count
            )
        except Exception as e:
            print(e)
            return {"code": 404, "message": str(e)}
        return {"code": 200, "message": "ok"}

    @classmethod
    def Recover_save(cls, orders_data, app, user, transaction_id, order_type, package_id):
        product_id = orders_data.get("product_id", "")
        product_time = orders_data.get("purchase_date_ms", "")
        expires_date = orders_data.get("expires_date_ms", "")
        is_trial_period = orders_data.get("is_trial_period", "")
        set_meal = SetMeal.objects.filter(goods_id=product_id).first()
        product_time = int(product_time)
        exp_datetime = int(int(expires_date) / 1000)
        try:
            state = 0
            if is_trial_period == "false":
                state = 1
            Orders.objects.create(
                user=user.uid,
                package_id=package_id,
                app=app,
                set_meal=set_meal,
                order_id=transaction_id,
                product_time=int(product_time),
                order_type=order_type,
                state=state,
                country=user.country
            )

            members = Members.objects.filter(type=1).first()
            members_config = MembersConfig.objects.filter(members=members).first()

            vip_time = user.member_validity_time
            if exp_datetime > user.member_validity_time:
                vip_time = exp_datetime

            User.objects.filter(id=user.id).update(
                member_validity_time=vip_time,
                member_type=1,
                subscription_type=1,
                first_subscription=1,
                set_meal=set_meal,
                white_type=0,
                max_device_count=members_config.device_count

            )
        except Exception as e:
            print(e)
            return {"code": 404, "message": str(e)}
        return {"code": 200, "message": "ok"}


class IosRequest(object):

    @classmethod
    def post(cls, url, password, receipt_data):
        """
            请求ios 数据
        """
        headers = {"Content-type": "application/json"}
        data = {
            "receipt-data": receipt_data,
            'password': password,
            "exclude-old-transactions": True
        }
        response = requests.post(url=url, data=json.dumps(data), headers=headers)
        return response

    @classmethod
    def notification_post(cls, url, receipt_data, password, environment):
        """
            请求苹果后台数据
        """
        url = None
        order_type = 0
        if environment == "Production" or environment == "PROD":
            order_type = 1
        elif environment == "Sandbox":
            order_type = 0

        headers = {"Content-type": "application/json"}
        data = {
            "receipt-data": receipt_data,
            'password': password,
            "exclude-old-transactions": True
        }
        try:
            response = requests.post(url=url, data=json.dumps(data), headers=headers)
        except Exception as e:
            print(e)
            return {"code": 404, "message": "request error"}
        if response.status_code != 200:
            return {"code": 404, "message": response.text}
        datas = json.loads(response.text)
        status = datas.get("status")
        if status != 0:
            return {"code": 404, "message": response.text}
        datas["order_type"] = order_type
        return {"code": 200, "data": datas}


class OrdersLogs(object):

    @staticmethod
    def request(json_data, type_data):
        json_data["time"] = time.time()
        json_data["type"] = type_data
        json_data["state"] = "request"
        try:
            res = mongodb_link.orders_request.insert_one(json_data)
            return res
        except Exception as e:
            return None

    @staticmethod
    def error(json_data, type_data, error_info):
        json_data["type"] = type_data
        json_data["time"] = time.time()
        json_data["error_info"] = str(error_info)
        json_data["state"] = "error"
        try:
            res = mongodb_link.orders_error.insert_one(json_data)
            return res
        except Exception as e:
            return None

    @staticmethod
    def succeed(json_data, type_data):
        json_data["type"] = type_data

        json_data["time"] = time.time()
        json_data["state"] = "succeed"
        try:
            res = mongodb_link.orders_succeed.insert_one(json_data)
            return res

        except Exception as e:
            return None

    @staticmethod
    def refund(json_data, type_data):
        json_data["type"] = type_data

        json_data["time"] = time.time()
        json_data["state"] = "succeed"
        try:
            res = mongodb_link.orders_refund.insert_one(json_data)
            return res

        except Exception as e:
            return None

    @staticmethod
    def subscribe_cancel(json_data, type_data):
        json_data["type"] = type_data

        json_data["time"] = time.time()
        json_data["state"] = "succeed"
        try:
            res = mongodb_link.orders_subscribe_cancel.insert_one(json_data)
            return res

        except Exception as e:
            return None

    #
    # @staticmethod
    # def google_notification_insert_one(json_data):
    #     res = mongodb_link.orders_google_notification_logs.insert_one(json_data)
    #     return res



class Paypal(object):

    @classmethod
    def create_access_token(cls):
        """
            paypal 令牌接口
        :return:
        """
        redis_data = db0.get("access_token")

        if redis_data:
            access_token = redis_data.decode('utf-8')
            return access_token
        else:
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            data = {
                "grant_type": "client_credentials"
            }
            url = f"{paypal_url}/v1/oauth2/token"
            reponse = requests.post(url, headers=headers, data=data, auth=HTTPBasicAuth(client_id, client_secret))

            if reponse.status_code == 200:
                datas = json.loads(reponse.text)
                access_token = datas.get("access_token", "")
                if not access_token:
                    return None
                db0.set("access_token", access_token, ex=60 * 60)
                return access_token
            # print(reponse.status_code)
            # print(reponse.text)

