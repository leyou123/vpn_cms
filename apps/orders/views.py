import json
import requests
import time
from django.http import JsonResponse
from django.views.generic.base import View
from django.core.paginator import Paginator
from django_redis import get_redis_connection

from apps.users.models import User, Devices
from apps.orders.models import Orders, Product, ProductPlan
from apps.manage.models import AppPackage, PayConfig, SetMeal, ApiVersion, MembersConfig, Members
from apps.orders.core import IOSPay, GooglePay, GoogleNotice, UserData, IosRequest, OrdersLogs, Paypal
from datetime import datetime, timedelta

from vpn_cms.settings import paypal_url
from utils.google_play import create_token
from utils.crypto import Aescrypt

aes = Aescrypt()
db0 = get_redis_connection('default')
db5 = get_redis_connection('DB5')


class GoogleSubscriptions(View):
    """
        安卓订阅接口
    """

    def post(self, request):
        data = json.loads(request.body.decode(encoding="utf-8"))
        uid = data.get("uid", 0)
        uuid = data.get("uuid", "")
        package_name = data.get("package_name")
        product_id = data.get("product_id", "")
        purchase_token = data.get("purchase_token", "")
        if not uid or not package_name or not product_id or not purchase_token:
            return JsonResponse({"code": 404, "message": "not found PayConfig or user or app"})
        user = User.objects.filter(uid=int(uid)).first()
        app = AppPackage.objects.filter(package_id=package_name).first()
        pay_config = PayConfig.objects.filter(app=app).first()

        db5.delete(str(uuid + package_name))

        if not user or not app or not pay_config:
            return JsonResponse({"code": 404, "message": "not found PayConfig or user or app"})
        header = create_token(pay_config)
        if not header:
            return JsonResponse({"code": 404, "message": "token error"})

        acknowledgement_result = GooglePay.acknowledgement(pay_config.api_url, package_name, product_id, purchase_token,
                                                           header)

        if acknowledgement_result is False:
            return JsonResponse({"code": 404, "data": 'Request error'})

        query_order_status, response = GooglePay.request_google_query(pay_config.api_url, package_name,
                                                                      product_id, purchase_token, header)

        if not query_order_status:
            return JsonResponse({"code": 404, "data": 'Response Query error'})
        query_datas = json.loads(response.text)
        product_time = query_datas.get("expiryTimeMillis", "")
        order_id = query_datas.get("orderId", "")
        # price_currency_code = query_datas.get("priceCurrencyCode", "")
        # payment_state = query_datas.get("paymentState", 0)

        query_order = Orders.objects.filter(order_id=order_id).first()
        if query_order:
            return JsonResponse({"code": 200, "message": f'{order_id} is duplication', "status": False})

        if not product_time:
            return JsonResponse({"code": 404, "message": f'expiryTimeMillis not found'})
        order_type = 1
        if int(uid) == int(pay_config.test_id):
            order_type = 0
        set_meal = SetMeal.objects.filter(goods_id=product_id).first()
        create_reuslt = Orders.objects.create(
            user=user.uid,
            app=app,
            package_id=package_name,
            product_time=int(product_time),
            set_meal=set_meal,
            order_type=order_type,
            order_id=order_id,
            country=user.country,
            state=1
        )
        if not create_reuslt:
            return JsonResponse({"code": 404, "message": "create error"})
        # 修改会员
        members = Members.objects.filter(type=1).first()
        members_config = MembersConfig.objects.filter(members=members).first()
        exp_datetime = int(product_time) / 1000
        if exp_datetime > int(user.member_validity_time):
            user.member_validity_time = exp_datetime
            user.white_type = 0
            user.first_subscription = 1
            user.subscription_type = 1
        user.max_device_count = members_config.device_count
        user.member_type = set_meal.members
        user.set_meal = set_meal
        user.save()
        return JsonResponse({"code": 200, "message": "success", "status": True})


class GoogleNotification(View):

    def post(self, request):
        json_data = json.loads(request.body.decode(encoding="utf-8"))
        # print("谷歌通知")
        # print(json_data)
        # return JsonResponse({"code": 200, "message": "not foun data"})
        return GoogleNotice.start(json_data)


class IosSubscriptions(View):

    def post(self, request):
        """
        ios 创建订单
        :param request:
        :return:
        """
        datas = json.loads(request.body.decode(encoding="utf-8"))
        uid = datas.get("uid", "")
        uuid = datas.get("uuid", "")
        receipt_data = datas.get("receipt_data", "")
        transaction_id = datas.get("transaction_id", "")
        version = datas.get("version", "")
        package_id = datas.get("package_id", "")
        device = Devices.objects.filter(uuid=uuid, package_id=package_id).first()
        db5.delete(str(uuid + package_id))

        if not device:
            return JsonResponse({"code": 404, f"message": f"not found {uuid}"})

        if not uid:
            user = device.user
        else:
            user = User.objects.filter(uid=int(uid)).first()

        if not user:
            return JsonResponse({"code": 404, "message": "not fount user"})

        app = AppPackage.objects.filter(package_id=package_id).first()
        api_version = ApiVersion.objects.filter(app=app).first()
        pay_config = PayConfig.objects.filter(app=app).first()

        if not app or not api_version or not pay_config:
            return JsonResponse({"code": 404, "message": "not fount app or api or config"})

        if version <= api_version.version:
            url = pay_config.buy_url
            order_type = 1
        else:
            url = pay_config.sandbox_url
            order_type = 0
        return self.create_orders(user, receipt_data, url, order_type, app, pay_config.pay_password, package_id)

    def create_orders(self, user, receipt_data, url, order_type, app, password, package_id):
        # 请求苹果后台数据
        res = IosRequest.post(url, password, receipt_data)
        datas = json.loads(res.text)
        status = datas.get("status")
        if res.status_code != 200 or status != 0:
            OrdersLogs.error(datas, "subscription", res.text)
            return JsonResponse({"code": 404, "message": res.text})

        orders_data = datas['latest_receipt_info'][0]
        original_transaction_id = orders_data.get("original_transaction_id")
        transaction_id = orders_data.get("transaction_id")
        orders = Orders.objects.filter(order_id=transaction_id).first()

        if orders:
            pending_renewal_info = datas.get("pending_renewal_info", "")
            if not pending_renewal_info:
                return JsonResponse({"code": 404, "message": "data error"})

            auto_renew_product_id = pending_renewal_info[0].get("auto_renew_product_id", "")
            product_id = pending_renewal_info[0].get("product_id", "")

            if auto_renew_product_id != product_id:
                return JsonResponse({"code": 201, "message": "Subscription status changed"})

            OrdersLogs.error(datas, "subscription", "orders is exist")
            return JsonResponse({"code": 200, "message": "ok"})

        result = UserData.save(orders_data, app, user, transaction_id, order_type, package_id)

        return JsonResponse(result)


class IosRecoverOrder(View):
    def post(self, request):
        """
        支付恢复订单
        :param request:
        :return:
        """
        datas = json.loads(request.body.decode(encoding="utf-8"))

        uid = datas.get("uid", "")
        uuid = datas.get("uuid", "")
        receipt_data = datas.get("receipt_data", "")
        version = datas.get("version", "")
        package_id = datas.get("package_id", "")
        user = User.objects.filter(uid=uid).first()
        app = AppPackage.objects.filter(package_id=package_id).first()
        api_version = ApiVersion.objects.filter(app=app).first()
        pay_config = PayConfig.objects.filter(app=app).first()

        if not user or not app or not api_version or not pay_config:
            return JsonResponse({"code": 404, "message": "data error"})

        if version <= api_version.version:
            url = pay_config.buy_url
            order_type = 1
        else:
            url = pay_config.sandbox_url
            order_type = 0

        return self.create_orders(user, receipt_data, url, order_type, app, pay_config.pay_password, package_id)

    def create_orders(self, user, receipt_data, url, order_type, app, password, package_id):
        """
        创建订单
        :return
        """
        response = IosRequest.post(url, password, receipt_data)
        datas = json.loads(response.text)
        status = datas.get("status")
        if response.status_code != 200 or status != 0:
            return JsonResponse({"code": 404, "message": response.text})

        orders = datas['receipt']['in_app']
        count = 0
        user = User.objects.filter(uid=user.uid).first()

        for order in orders:
            transaction_id = order.get("transaction_id")
            orders = Orders.objects.filter(order_id=transaction_id).first()
            if orders:
                continue
            UserData.Recover_save(order, app, user, transaction_id, order_type, package_id)
            count += 1
        if count:
            return JsonResponse({"code": 200, "message": "ok"})
        else:
            return JsonResponse({"code": 404, "message": "not found orders"})


class IosOrderNotifications(View):

    def post(self, request):
        """
            strom vpn通知
        """
        datas = json.loads(request.body.decode(encoding="utf-8"))
        package_id = "com.strom.vpn"
        return IOSPay.start(datas, package_id)


class OrderCallbackNotifications(View):
    def post(self, request):
        """
            super vpn通知
        """
        datas = json.loads(request.body.decode(encoding="utf-8"))
        print(datas)
        package_id = "com.superoversea"
        return IOSPay.start(datas, package_id)


class RadarCallbackNotifications(View):
    def post(self, request):
        """
            super vpn通知
        """
        datas = json.loads(request.body.decode(encoding="utf-8"))
        print(datas)
        package_id = "com.leyou.radarvpn"
        return IOSPay.start(datas, package_id)


class IosNotifications(View):
    def post(self, request):
        """
            super vpn通知
        """
        try:
            notify_path = request.path
        except Exception as e:
            return JsonResponse({"code": 404, "message": "error info"})

        if not notify_path:
            return JsonResponse({"code": 404, "message": "error info"})
        pay_config = PayConfig.objects.filter(notify_url=notify_path).first()

        if not pay_config:
            return JsonResponse({"code": 404, "message": "error info"})

        # print(datas)
        try:
            package_id = pay_config.app.package_id
            datas = json.loads(request.body.decode(encoding="utf-8"))
            return IOSPay.start(datas, package_id)
        except Exception as e:
            return JsonResponse({"code": 404, "message": "error info"})

class QueryOrder(View):
    def post(self, request):
        data = json.loads(request.body.decode(encoding="utf-8"))
        uid = data.get("uid", "")
        package_id = data.get("package_id", "")
        app = AppPackage.objects.filter(package_id=package_id).first()

        if not app or not uid:
            return JsonResponse({"code": 404, "message": "not found package_id not uid"})

        page = data.get('page', 1)
        size = data.get('size', 10)

        datas = []
        user = User.objects.filter(uid=int(uid)).first()

        if not user:
            return JsonResponse({"code": 404, "message": "not found uid"})

        user_orders = Orders.objects.filter(user=user.uid, state=1, app=app).order_by('-product_time')

        if not user_orders.count():
            page_info = {
                "count": 0,
                "pages": 0  # 总页数
            }
            return JsonResponse({"code": 200, "message": "success", 'data': [], "page_info": page_info})

        for order in user_orders:
            datas.append(order.get_info())

        paginator = Paginator(datas, size)
        page = paginator.page(page)
        data_list = page.object_list

        page_info = {
            "count": paginator.count,
            "pages": paginator.num_pages  # 总页数
        }
        return JsonResponse({"code": 200, "message": "success", 'data': data_list, "page_info": page_info})


class SyncSingleOrder(View):

    def save(self, orders_data, app, user, transaction_id, order_type, package_id):
        product_id = orders_data.get("product_id", "")
        product_time = orders_data.get("purchase_date_ms", "")
        expires_date = orders_data.get("expires_date_ms", "")
        is_trial_period = orders_data.get("is_trial_period", "")
        set_meal = SetMeal.objects.filter(goods_id=product_id).first()
        product_time = int(product_time)
        exp_datetime = int(int(expires_date) / 1000)
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

    def post(self, request):
        data = json.loads(request.body.decode(encoding="utf-8"))
        return JsonResponse({"code": 200, "message": "success"})


class PaypalProducts(View):

    def post(self, request):
        """
            创建商品
        """
        access_token = Paypal.create_access_token()

        if not access_token:
            return JsonResponse({"code": 404, "message": "not found access_token"})

        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + access_token
            # "PayPal-Request-Id":"PRODUCT-18062020-004"
        }

        name = "VPN"
        description = "vpn pay"
        vpn_type = "SERVICE"
        vpn_category = "SOFTWARE"
        data = {
            "name": name,
            "description": description,
            "type": vpn_type,
            "category": vpn_category,
            "image_url": "https://example.com/streaming.jpg",
            "home_url": "https://example.com/home"
        }

        # url = f"{paypal_url}/v1/catalogs/products"
        url = f"{paypal_url}/v1/catalogs/products"
        reponse = requests.post(url, headers=headers, data=json.dumps(data))
        if reponse.status_code == 200:
            datas = json.loads(reponse.text)
            product_id = datas.get("id", "")
            Product.objects.create(
                product_id=product_id,
                name=name,
                type=vpn_type,
                category=vpn_category
            )
            return JsonResponse({"code": 200, "message": "success", "data": json.loads(reponse.text)})
        print(reponse.status_code)
        print(reponse.text)
        return JsonResponse({"code": 200, "message": "success"})


class PalpalProductsPlan(View):

    def post(self, request):

        datas = [
            {
                "name": "one day",
                "description": "Help you access all sources you want",
                "price": 0.01,
                "interval_unit": "DAY",
                "interval_count": 1,
                "currency_code": "USD",
                "total_cycles": 99,
                "goods_id": "paypal.vpn.1"
            }

            # {
            #     "name": "Monthly VPN Subscription",
            #     "description": "Help you access all sources you want",
            #     "price": 9.99,
            #     "interval_unit": "MONTH",
            #     "interval_count": 1,
            #     "currency_code": "USD",
            #     "total_cycles": 99,
            #     "goods_id": "paypal.vpn.30"
            # },
            # {
            #     "name": "90 days",
            #     "description": "Help you access all sources you want",
            #     "price": 29.99,
            #     "interval_unit": "MONTH",
            #     "interval_count": 3,
            #     "currency_code": "USD",
            #     "total_cycles": 99,
            #     "goods_id": "paypal.vpn.90"
            # },
            # {
            #     "name": "180 days",
            #     "description": "Help you access all sources you want",
            #     "price": 59.99,
            #     "interval_unit": "MONTH",
            #     "interval_count": 6,
            #     "currency_code": "USD",
            #     "total_cycles": 99,
            #     "goods_id": "paypal.vpn.180"
            # },
            # {
            #     "name": "Annual VPN subscription",
            #     "description": "Discount on the monthly subscription",
            #     "price": 29.99,
            #     "interval_unit": "YEAR",
            #     "interval_count": 1,
            #     "currency_code": "USD",
            #     "total_cycles": 99,
            #     "goods_id": "paypal.vpn.360"
            # }
        ]
        product = Product.objects.first()

        for data in datas:
            name = data.get("name")
            description = data.get("description")
            price = data.get("price")
            interval_unit = data.get("interval_unit")
            interval_count = data.get("interval_count")
            currency_code = data.get("currency_code")
            total_cycles = data.get("total_cycles")
            goods_id = data.get("goods_id")
            set_meal = SetMeal.objects.filter(goods_id=goods_id).first()

            self.create(product, set_meal, name, description, price, interval_unit, interval_count, currency_code,
                        total_cycles)

        return JsonResponse({"code": 200, "message": "success"})

    def create(self, product, set_meal, name, description, price, interval_unit, interval_count, currency_code,
               total_cycles):
        """
            创建商品
        """
        access_token = Paypal.create_access_token()
        product = Product.objects.first()

        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + access_token,
            'Accept': 'application/json'
            # "PayPal-Request-Id":"PRODUCT-18062020-004"
        }

        data = {
            "product_id": product.product_id,  # 产品ID
            "name": name,  # 计划名
            "description": description,  # 描述
            "billing_cycles": [  # 用于试用计费和常规计费的计费周期数组。 一个计划最多只能有两个试验周期和一个常规周期。
                # {
                #     "frequency": {  # 此计费周期的频率详细信息
                #         "interval_unit": "MONTH",  # 订阅收费或计费的时间间隔。  1.DAY 365 2.WEEK  52  3.MONTH  12 4.YEAR 1
                #         "interval_count": 1
                #         # 对订阅者计费的间隔数。 例如，如果interval_unit为DAY，且interval_count为2，则订阅将每两天计费一次。 下表列出了每个interval_unit允许的interval_count的最大值
                #     },
                #     "tenure_type": "TRIAL",  # 计费周期的保留期类型。 如果计划有试验周期，每个计划只允许2个试验周期。  1.REGULAR 定期计费周期 2. TRIAL 试用计费周期
                #     "sequence": 1,  # 此周期在其他计费周期中运行的顺序。 例如，试用计费周期的序列为   1.而常规计费周期的序列为 2.因此试用周期在常规周期之前运行
                #     "total_cycles": 1
                #     # 执行此计费周期的次数。 试用计费周期只能执行有限次(total_cycles的值在1到999之间)。 常规计费周期可以执行无限次(total_cycles的值为0)或有限次(total_cycles的值在1到999之间)
                # },
                {
                    "frequency": {  # 此计费周期的频率详细信息
                        "interval_unit": interval_unit,  # 订阅收费或计费的时间间隔。  1.DAY 365 2.WEEK  52  3.MONTH  12 4.YEAR 1
                        "interval_count": interval_count
                    },
                    "tenure_type": "REGULAR",  # 计费周期的保留期类型。 如果计划有试验周期，每个计划只允许2个试验周期。  1.REGULAR 定期计费周期 2. TRIAL 试用计费周期
                    "sequence": 1,  # 此周期在其他计费周期中运行的顺序。 例如，试用计费周期的序列为   1.而常规计费周期的序列为 2.因此试用周期在常规周期之前运行
                    "total_cycles": total_cycles,
                    # 执行此计费周期的次数。 试用计费周期只能执行有限次(total_cycles的值在1到999之间)。 常规计费周期可以执行无限次(total_cycles的值为0)或有限次(total_cycles的值在1到999之间)
                    "pricing_scheme": {  # 定价方案
                        "fixed_price": {  # 为认购而收取的固定金额。 对固定金额的更改适用于现有和未来的订阅。 对于现有的订阅，在价格变动后10天内付款不受影响。
                            "value": f"{price}",  # 价格
                            "currency_code": currency_code  # 货币单元
                        }
                    }
                }
            ],
            "payment_preferences": {  # 订阅的支付首选项
                "auto_bill_outstanding": True,  # 是否在下一个计费周期自动对未结算的金额进行计费。
                "setup_fee": {  # 服务的初始设置费用
                    "value": f"{0}",  # 价格
                    "currency_code": currency_code  # 货币单元
                },
                "setup_fee_failure_action": "CONTINUE",  # 如果初始设置付款失败，则执行订阅的操作
                "payment_failure_threshold": 3
                # 订阅暂停前的最大付款失败数。 例如，如果payment_failure_threshold为2，则如果连续两次支付失败，订阅将自动更新到SUSPEND状态
            },
            "taxes": {  # 税费
                "percentage": f"{0}",  # 开票金额的税率。
                "inclusive": False  # 指示税费是否已包含在计费金额中。
            }
        }

        url = f"{paypal_url}/v1/billing/plans"
        reponse = requests.post(url, headers=headers, data=json.dumps(data))
        if reponse.status_code == 201:
            user_data = json.loads(reponse.text)
            plan_id = user_data.get("id", "")
            ProductPlan.objects.create(
                set_meal=set_meal,
                product=product,
                plan_id=plan_id,
                name=name,
                description=description,
                billing_number=total_cycles,
                currency_code=currency_code,
                price=price
            )

            datas = json.loads(reponse.text)
            return JsonResponse({"code": 200, "message": "success", "data": datas})

        print(reponse.status_code)
        print(reponse.text)

        return JsonResponse({"code": 404, "message": "request error"})


class PaypalSubscriptions(View):

    def post(self, request):
        """
            查询订单
        """
        access_token = Paypal.create_access_token()
        datas = json.loads(request.body.decode(encoding="utf-8"))
        print(datas)
        uid = datas.get("uid", "")
        package_id = datas.get("package_id", "")
        product_id = datas.get("product_id", "")
        plan_id = datas.get("plan_id", "")
        plan = ProductPlan.objects.filter(plan_id=plan_id).first()

        if not uid or not package_id or not product_id:
            return JsonResponse({"code": 404, "message": "not found uid or package_id or product_id"})

        order = Orders.objects.filter(order_id=product_id).first()
        if order:
            return JsonResponse({"code": 404, "message": f"{product_id} is exist"})

        app = AppPackage.objects.filter(package_id=package_id).first()

        if not app:
            return JsonResponse({"code": 404, "message": f"not found {package_id}"})

        user = User.objects.filter(uid=uid).first()
        if not user:
            return JsonResponse({"code": 404, "message": f"not found {uid}"})

        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + access_token
        }

        url = f"{paypal_url}/v1/billing/subscriptions/{product_id}"
        # print(headers)
        try:
            reponse = requests.get(url, headers=headers)
        except Exception as e:
            return JsonResponse({"code": 404, "message": "request error"})

        datas = json.loads(reponse.text)
        if reponse.status_code == 200:
            status = datas.get("status","")  # 状态
            product_time_str = str(datas.get("status_update_time","")) # 状态更新
            product_time = self.user_time(product_time_str)
            exp_datetime = int(time.time()) + 60 * 60 * 24 * plan.set_meal.day
            if status != "ACTIVE":
                return JsonResponse({"code": 404, "message": "status not active"})
            print(datas)
            state = 1
            order_type = 1
            if paypal_url == "https://api-m.sandbox.paypal.com":
                order_type = 0
            create_res = self.create_order(uid, app, plan, package_id, product_id, product_time, order_type, state, user.country,exp_datetime)
            if create_res:
                return JsonResponse({"code": 200, "message": "success"})
            else:
                return JsonResponse({"code": 404, "message": "create error"})
        message = datas.get("message","request error")
        return JsonResponse({"code": 404, "message": message})

    def user_time(self, target_time):
        user_date = datetime.strptime(target_time, "%Y-%m-%dT%H:%M:%SZ")
        this_date = int(time.mktime(user_date.timetuple()))
        return this_date

    def create_order(self, uid, app, plan, package_id, product_id, product_time, order_type, state, country,exp_datetime):
        order_state = Orders.objects.create(
            user=uid,
            app=app,
            set_meal=plan.set_meal,
            package_id=package_id,
            order_id=product_id,
            product_time=int(product_time) * 1000,
            order_type=order_type,
            state=state,
            country=country
        )

        if order_state:
            update_user_status = User.objects.filter(uid=uid).update(
                member_validity_time=exp_datetime,
                member_type=1,
                subscription_type=1,
                first_subscription=1,
                set_meal=plan.set_meal,
                white_type=0,
                max_device_count=4
            )
            if update_user_status:
                return True
        return False


class ProductsPlan(View):

    def post(self, request):
        """
            获取商品计划
        """
        data = json.loads(request.body.decode(encoding="utf-8"))
        # key = data.get("key", "")
        # aes_result = aes.aesdecrypt(key)
        # if aes_result != "leyou2021":
        #     return JsonResponse({"code": 404, "message": 'key error'})
        plans = ProductPlan.objects.all()
        data = []
        for plan in plans:
            data.append(plan.get_info())
        return JsonResponse({"code": 200, "message": "success", "data": data})


class PaypalNotification(View):

    def create_order(self, uid, app, set_meal, package_id, transaction_id, product_time, order_type, state, country):
        Orders.objects.create(
            user=uid,
            app=app,
            set_meal=set_meal,
            package_id=package_id,
            order_id=transaction_id,
            product_time=int(product_time),
            order_type=order_type,
            state=state,
            country=country
        )


    def post(self, request):
        datas = json.loads(request.body.decode(encoding="utf-8"))
        print(datas)
        event_type = datas.get("PAYMENT.SALE.COMPLETED", "")

        if event_type == "PAYMENT.SALE.COMPLETED":

            product_id = datas["resource"].get("id", "")

            user_order = Orders.objects.filter(order_id=product_id).first()
            if user_order:
                return JsonResponse({"code": 404, "message": "orders is exits"})

            billing_agreement_id = datas["resource"].get("billing_agreement_id", "")
            create_time = datas.get("create_time", "")
            product_time = self.user_time(create_time)
            orders = Orders.objects.filter(order_id=billing_agreement_id).first()
            if not orders:
                return JsonResponse({"code": 404, "message": "not found orders"})
            user = User.objects.filter(uid=orders.uid).first()
            if not user:
                return JsonResponse({"code": 404, "message": "not found user"})

            exp_datetime = int(time.time()) + 60*60*24 * orders.set_meal.day
            create_res = self.create_order(orders.uid, orders.app, orders, orders.package_id, product_id, product_time, orders.order_type, orders.state, user.country,exp_datetime)
            if create_res:
                return JsonResponse({"code": 200, "message": "success"})
            else:
                return JsonResponse({"code": 404, "message": "create error"})

        return JsonResponse({"code": 200, "message": "success"})


    def user_time(self, target_time):
        user_date = datetime.strptime(target_time, "%Y-%m-%dT%H:%M:%S.%fZ")
        this_date = int(time.mktime(user_date.timetuple()))
        return this_date

    def create_orders(self, uid, app, plan, package_id, product_id, product_time, order_type, state, country,exp_datetime):
        order_state = Orders.objects.create(
            user=uid,
            app=app,
            set_meal=plan.set_meal,
            package_id=package_id,
            order_id=product_id,
            product_time=int(product_time) * 1000,
            order_type=order_type,
            state=state,
            country=country
        )

        if order_state:
            update_user_status = User.objects.filter(uid=uid).update(
                member_validity_time=exp_datetime,
                member_type=1,
                subscription_type=1,
                first_subscription=1,
                set_meal=plan.set_meal,
                white_type=0,
                max_device_count=4
            )
            if update_user_status:
                return True
        return False
