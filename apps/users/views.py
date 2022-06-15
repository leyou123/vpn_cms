import json
import time
import datetime
import requests

from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.generic.base import View
from django_redis import get_redis_connection
from apps.manage.models import UsersConfig, MembersConfig, AppPlatform, ShareConfig, TimeConfig
from apps.orders.models import Orders
from apps.users.models import User, Devices, UserFeedback, UserShareTask, UserFeedBack
from apps.users.core import GeoIp, str_as_md5, send_email, random_str, str_as_md5_short, unbinding_send_email
from apps.manage.models import AppPackage, SetMeal
from utils.crypto import Aescrypt
from vpn_cms.settings import USER_KEY
from utils.dingding import DataLoggerAPI

aes = Aescrypt()
db0 = get_redis_connection('default')
db1 = get_redis_connection('DB1')
db3 = get_redis_connection('DB3')
db5 = get_redis_connection('DB5')
db6 = get_redis_connection('DB6')


db10 = get_redis_connection('DB10')
db11 = get_redis_connection('DB11')



class Index(View):
    def get(self, request):
        return redirect('https://www.9527.click')

    def post(self, request):
        return JsonResponse({"code": 200, "message": "success"})


class Register(View):

    def get_token(self):
        """
            获取token
        """
        user_id = db0.get("user_id")
        new_user_id = ""
        if user_id:
            new_user_id = str(user_id, "utf-8")
        return new_user_id

    def redis_check(self, uuid, platform_id, package_id):
        redis_data = db3.get(str(uuid + platform_id + package_id))
        if not redis_data:
            return {}
        redis_user_data = json.loads(str(redis_data, "utf-8"))
        if redis_user_data:
            return redis_user_data
        return {}

    def login_redis_check(self, uuid, package_id):
        redis_data = db5.get(str(uuid + package_id))
        if not redis_data:
            return {}
        redis_user_data = json.loads(str(redis_data, "utf-8"))
        if redis_user_data:
            return redis_user_data
        return {}

    def post(self, request):
        """
        注册用户接口
        :param request:
        :return:+
        """
        time_begin = time.time()
        data = json.loads(request.body.decode(encoding="utf-8"))
        key = data.get("key", "")
        aes_result = aes.aesdecrypt(key)
        if aes_result != "leyou2021":
            return JsonResponse({"code": 404, "message": 'key error'})
        platform_id = data.get("platform_id", "")
        uuid = data.get("uuid", "")
        package_id = data.get("package_id", "")
        try_day = 0
        if not uuid or not package_id or not platform_id:
            return JsonResponse({"code": 404, "message": "not found package_id or uuid or platform_id"})

        check_redis = self.redis_check(uuid, platform_id, package_id)

        if check_redis:
            login_check_redis = self.login_redis_check(uuid, package_id)

            if login_check_redis:
                return JsonResponse({"code": 200, "message": "success", "data": login_check_redis})
            # else:
            #     query_devices = Devices.objects.filter(uuid=uuid, package_id=package_id).first()
            #     if not query_devices:
            #         return JsonResponse({"code": 404, "message": "not found devices"})
            #     user = User.objects.filter(uid=query_devices.user).first()
            #     if not user:
            #         return JsonResponse({"code": 404, "message": "not found user"})
            #     db5.set(str(uuid + package_id), json.dumps(create_user.get_info()))
            #     return JsonResponse({"code": 200, "message": "success", "data": user.get_info()})
        query_devices = Devices.objects.filter(package_id=package_id, uuid=uuid).first()
        platform = AppPlatform.objects.filter(platform_id=platform_id).first()
        user_config = UsersConfig.objects.filter(platform=platform).first()
        if query_devices:
            uid = query_devices.user
            # uid = query_devices[0].get("user")
            user = User.objects.filter(uid=uid).first()
            if not user:
                # return self.register(uid, uuid, request, try_day, package_id, platform)
                Devices.objects.filter(
                    user=uid,
                    uuid=uuid,
                    package_id=package_id,
                ).delete()
                db3.delete(str(uuid + platform.platform_id + package_id))
                return JsonResponse({"code": 404, "message": "Repeated registration"})

            json_data = {
                "package_id": package_id,
                "uid": uid,
                "platform": platform.platform_id
            }
            db3.set(str(uuid + platform.platform_id + package_id), json.dumps(json_data))
            return JsonResponse({"code": 200, "message": "success", "data": user.get_info()})

        if not platform:
            return JsonResponse({"code": 404, "message": "not found platform"})

        if user_config:
            try_day = user_config.temp_day


        return self.register(uuid, request, try_day, package_id, platform)

    def register(self, uuid, request, try_day, package_id, platform):
        expiration_time = int(time.time()) + 60 * 60 * 24 * try_day
        redis_data = db0.lpop("user_id")
        uid = int(str(redis_data, "utf-8"))

        try:
            info = self.country(request)
            country = info.get("country", "")
            region = info.get("region", "")
            white_type = 0
            if country == "中国":
                white_type = 1
            member_type = MembersConfig.objects.filter(id=2).first()
            code = str_as_md5_short(str(uid) + random_str())

            create_user = User.objects.create(
                platform=platform,
                uid=uid,
                member_validity_time=expiration_time,
                member_type=member_type,
                country=country,
                region=region,
                first_subscription=0,
                subscription_type=0,
                white_type=white_type,
                code=code,
                device_count=1,
                max_device_count=member_type.device_count,
                login_time=datetime.datetime.now()
            )

            if not create_user:
                return JsonResponse({"code": 404, "message": "Repeated registration"})

            create_devices = Devices.objects.create(
                platform=platform,
                user=uid,
                uuid=uuid,
                package_id=package_id,
                login_time=datetime.datetime.now()
            )
            if create_user and create_devices:
                json_data = {
                    "package_id": package_id,
                    "uid": uid,
                    "platform": platform.platform_id
                }
                create_data = create_user.get_info()
                db3.set(str(uuid + platform.platform_id + package_id), json.dumps(json_data))
                db5.set(str(uuid + package_id), json.dumps(create_data))
                return JsonResponse({"code": 200, "message": "success", "data": create_data})
            else:
                return JsonResponse({"code": 404, "message": "Repeated registration"})
        except Exception as e:
            # print(e)
            error_info = e
        return JsonResponse({"code": 404, "message": f"Repeated registration {error_info}"})

    def country(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')  # 判断是否使用代理
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]  # 使用代理获取真实的ip
        else:
            ip = request.META.get('REMOTE_ADDR')
        response = GeoIp.get_info(ip)
        return response


class Login(View):

    def redis_check(self, uuid, package_id):
        redis_data = db5.get(str(uuid + package_id))
        if not redis_data:
            return {}
        redis_user_data = json.loads(str(redis_data, "utf-8"))
        if redis_user_data:
            return redis_user_data
        return {}

    def get_device(self, uuid, package_id):
        redis_data = db6.get(str(uuid + package_id))
        if redis_data:
            return True
        devices_data = Devices.objects.filter(uuid=uuid, package_id=package_id).first()
        if devices_data:
            db6.set(str(uuid + package_id), json.dumps(devices_data.get_info()),ex=60*60)
            return True
        return False

    def binding_device(self, uid, uuid, platform_id, package_id):

        if not package_id:
            return JsonResponse({"code": 404, "message": 'not found package_id'})
        device = Devices.objects.filter(uuid=uuid, package_id=package_id).first()
        platform = AppPlatform.objects.filter(platform_id=platform_id).first()
        user = User.objects.filter(platform=platform, uid=uid).first()

        if device:
            device.login_time = datetime.datetime.now()
            device.save()
            return JsonResponse({"code": 200, "message": "success", "data": user.get_info()})

        # 数据库没有此设备要绑定
        else:
            if user.device_count >= user.max_device_count:  # 设备数最大值
                return JsonResponse({"code": 404, "message": "The devices have reached the max. Please sign out the others", "data": user.get_info()})
            else:
                # 绑定设备
                res = Devices.objects.create(
                    platform=platform,
                    user=user.uid,
                    uuid=uuid,
                    package_id=package_id,
                    login_time=datetime.datetime.now()
                )
                if res:
                    devices_count = Devices.objects.filter(user=user.uid, platform=platform).count()
                    # print(f"设备绑定{uuid},包id:{package_id}")
                    user.device_count = devices_count
                    user.save()
                return JsonResponse({"code": 200, "message": "success", "data": user.get_info()})

    def check_device(self, user, uuid, package_id, user_data):
        if user.device_count >= user.max_device_count:
            # 如果设备数相等
            result = self.get_device(uuid,package_id)
            if result:
                # 在数据库中 直接返回用户数据  建立缓存
                db5.set(str(uuid + package_id), json.dumps(user.get_info()))
                self.check_time(user.uid, user.platform.platform_id)

                # db0.lpush("check_users", json.dumps(user_data))
                return JsonResponse({"code": 200, "message": "success", "data": user.get_info()})
            else:
                db5.set(str(uuid + package_id), json.dumps(user.get_info()))
                return JsonResponse(
                    {"code": 404, "message": "The number of devices exceeds the upper limit", "data": user.get_info()})

        else:
            db5.set(str(uuid + package_id), json.dumps(user.get_info()))
            # db0.lpush("check_users", json.dumps(user_data))
            self.check_time(user.uid, user.platform.platform_id)

            # db0.lpush("binding_device", json.dumps(user_data))
            return self.binding_device(user.uid,uuid,user.platform.platform_id,package_id)

    def redis_check_device(self,datas, uuid, package_id,user_data,uid,platform_id):
        max_device_count = datas.get("max_device_count","")
        device_count = datas.get("device_count","")

        if device_count >= max_device_count:
            # 如果设备数相等
            result = self.get_device(uuid,package_id)
            if result:
                # 在数据库中 直接返回用户数据  建立缓存
                # db0.lpush("check_users", json.dumps(user_data))
                self.check_time(uid, platform_id)
                return JsonResponse({"code": 200, "message": "success", "data": datas})
            else:
                return JsonResponse({"code": 404, "message": "The number of devices exceeds the upper limit", "data": datas})
        else:
            # db0.lpush("check_users", json.dumps(user_data))
            self.check_time(uid, platform_id)
            return self.binding_device(uid,uuid,platform_id,package_id)


    def unbundling_user(self, uid, uuid, package_id):
        user = User.objects.filter(uid=uid).first()
        if not user:
            return JsonResponse({"code": 404, "message": 'not found uid'})

        devices = Devices.objects.filter(uuid=uuid, package_id=package_id).delete()
        user_device_count = Devices.objects.filter(uuid=uuid, package_id=package_id).count()
        if devices:
            user.device_count = user_device_count
            user.save()
            db5.delete(str(uuid + package_id))
            db6.delete(str(uuid + package_id))
            return JsonResponse({"code": 200, "message": "success"})
        return JsonResponse({"code": 404, "message": "delete error"})

    def check_time(self, uid, platform_id):

        user = User.objects.filter(uid=int(uid)).first()
        platform = AppPlatform.objects.filter(platform_id=platform_id).first()

        if not user or not platform:
            return None

        if not user.code:
            code = str_as_md5_short(str(user.uid) + random_str())
            user.code = code

        if user.member_type.members.type == 3:
            if user.device_count > 1:
                self.del_device(user.uid, platform)
            user.set_meal = None

        current_time = int(time.time())
        # 购买剩余时间
        vip_time = user.member_validity_time
        if current_time > vip_time:
            if user.device_count > 1:
                self.del_device(user.uid, platform)
            member_type = MembersConfig.objects.filter(id=3).first()
            user.member_type = member_type
            user.subscription_type = 2
            user.device_count = 1
            user.set_meal = None

        user.login_time = datetime.datetime.now()
        user.save()

    def del_device(self, uid, platform):
        devices = Devices.objects.filter(user=uid, platform=platform).all()
        for device in devices:
            Devices.objects.filter(id=device.id).delete()
            db5.delete(str(device.uuid + device.package_id))

    def post(self, request):
        """
        登录接口
        :param request:
        :return:+
        """

        data = json.loads(request.body.decode(encoding="utf-8"))
        key = data.get("key", "")
        aes = Aescrypt()
        aes_result = aes.aesdecrypt(key)
        if aes_result != "leyou2021":
            return JsonResponse({"code": 404, "message": 'key error'})
        uid = data.get("uid", "")
        uuid = data.get("uuid", "")
        platform_id = data.get("platform_id", "")
        password = data.get("password", "")
        email = data.get("email", "")
        package_id = data.get("package_id", "")

        unbundling_uid = data.get("unbundling_uid", "")
        unbundling_uuid = data.get("unbundling_uuid", "")

        if not uid and not email:
            return JsonResponse({"code": 404, "message": 'not found uid or email'})

        if unbundling_uid and unbundling_uuid:
            self.unbundling_user(unbundling_uid, unbundling_uuid, package_id)

        user_data = {
            "uid": uid,
            "uuid": uuid,
            "platform_id": platform_id,
            "package_id": package_id
        }

        if not package_id:
            return JsonResponse({"code": 404, "message": 'not found package_id'})

        platform = AppPlatform.objects.filter(platform_id=platform_id).first()
        if not platform:
            return JsonResponse({"code": 404, "message": "not found platform"})

        if email:
            if not uuid:
                return JsonResponse({"code": 404, "message": 'not found uuid or email'})

            # 邮箱登录
            password = str_as_md5(password)
            user = User.objects.filter(platform=platform, email=email).first()
            if not user:
                return JsonResponse({"code": 404, "message": f"not found {email}"})
            if user.password != password:
                return JsonResponse({"code": 404, "message": f"Incorrect password"})
            user_data["uid"] = user.uid
            return self.check_device(user, uuid, package_id, user_data)

        check_redis = self.redis_check(uuid, package_id)

        if check_redis:
            return self.redis_check_device(check_redis, uuid, package_id,user_data,uid,platform_id)

        if uid:
            try:
                user = User.objects.filter(platform=platform, uid=uid).first()
                user_data["uid"] = user.uid
                if not user:
                    return JsonResponse({"code": 404, "message": f"not found {uid}"})
            except Exception as e:
                return JsonResponse({"code": 404, "message": "uid error"})

            return self.check_device(user, uuid, package_id,user_data)
        #
        # if not uuid or not email:
        #     return JsonResponse({"code": 404, "message": 'not found uuid or email'})
        #
        # # 邮箱登录
        # password = str_as_md5(password)
        # user = User.objects.filter(platform=platform, email=email).first()
        # if not user:
        #     return JsonResponse({"code": 404, "message": f"not found {email}"})
        # if user.password != password:
        #     return JsonResponse({"code": 404, "message": f"Incorrect password"})
        #
        # user_data["uid"] = user.uid
        #
        # return self.check_device(user, uuid, package_id,user_data)

        # db5.set(str(uuid + package_id), json.dumps(user.get_info()))
        # db0.lpush("check_users", json.dumps(user_data))
        # return JsonResponse({"code": 200, "message": "success", "data": user.get_info()})


class CheckLoginData(View):

    def post(self, request):
        """
            异步检测用户数据
        """
        data = json.loads(request.body.decode(encoding="utf-8"))
        uid = data.get("uid", "")
        uuid = data.get("uuid", "")
        platform_id = data.get("platform_id", "")
        package_id = data.get("package_id", "")

        if not package_id:
            return JsonResponse({"code": 404, "message": 'not found package_id'})
        device = Devices.objects.filter(uuid=uuid, package_id=package_id).first()
        platform = AppPlatform.objects.filter(platform_id=platform_id).first()
        user = User.objects.filter(platform=platform, uid=uid).first()
        self.check_time(user, platform)

        if device:
            device.login_time = datetime.datetime.now()
            device.save()
        return JsonResponse({"code": 200, "message": 'success'})

    def check_time(self, user, platform):
        if not user.code:
            code = str_as_md5_short(str(user.uid) + random_str())
            user.code = code

        if user.member_type.members.type == 3:
            if user.device_count > 1:
                self.del_device(user.uid, platform)
            user.set_meal = None

        current_time = int(time.time())
        # 购买剩余时间
        vip_time = user.member_validity_time
        if current_time > vip_time:
            if user.device_count > 1:
                self.del_device(user.uid, platform)
            member_type = MembersConfig.objects.filter(id=3).first()
            user.member_type = member_type
            user.subscription_type = 2
            user.device_count = 1
            user.set_meal = None
        user.login_time = datetime.datetime.now()
        user.save()

    def del_device(self, uid, platform):
        devices = Devices.objects.filter(user=uid, platform=platform).all()
        for device in devices:
            Devices.objects.filter(id=device.id).delete()
            db5.delete(str(device.uuid + device.package_id))

class CheckBinding(View):

    def post(self, request):
        """
            异步检测用户数据
        """
        data = json.loads(request.body.decode(encoding="utf-8"))
        uid = data.get("uid", "")
        uuid = data.get("uuid", "")
        platform_id = data.get("platform_id", "")
        package_id = data.get("package_id", "")

        if not package_id:
            return JsonResponse({"code": 404, "message": 'not found package_id'})
        device = Devices.objects.filter(uuid=uuid, package_id=package_id).first()
        platform = AppPlatform.objects.filter(platform_id=platform_id).first()
        user = User.objects.filter(platform=platform, uid=uid).first()

        if device:
            device.login_time = datetime.datetime.now()
            device.save()
        # 数据库没有此设备要绑定
        else:
            if user.device_count >= user.max_device_count:  # 设备数最大值
                print("The devices have reached the max. Please sign out the others.")
            else:
                # 绑定设备
                res = Devices.objects.create(
                    platform=platform,
                    user=user.uid,
                    uuid=uuid,
                    package_id=package_id,
                    login_time=datetime.datetime.now()
                )
                if res:
                    devices_count = Devices.objects.filter(user=user.uid, platform=platform).count()
                    # print(f"设备绑定{uuid},包id:{package_id}")
                    user.device_count = devices_count
                    user.save()
        return JsonResponse({"code": 200, "message": 'success'})



class AddUserTime(View):

    def post(self, request):
        """
        添加用户时间
        :param request:
        :return:+
        """
        data = json.loads(request.body.decode(encoding="utf-8"))
        key = data.get("key", "")
        aes = Aescrypt()
        aes_result = aes.aesdecrypt(key)
        if aes_result != "leyou2021":
            return JsonResponse({"code": 404, "message": 'key error'})
        uid = data.get("uid", "")
        time_type = int(data.get("time_type", 1))
        if not uid:
            return JsonResponse({"code": 404, "message": "uid is none"})

        # 时间
        all_time_type = {1: 5, 2: 10, 3: 20, 4: 30}
        current_time = time.time()
        user = User.objects.filter(uid=uid).first()
        if not user:
            return JsonResponse({"code": 404, "message": "not found uuid"})
        adv_count = user.adv_count
        config = UsersConfig.objects.first()

        if adv_count >= config.adv_count:
            return JsonResponse({"code": 404, "message": "You have reached the max ADs times today!"})

        now_time = all_time_type.get(time_type, 0)

        if user.member_validity_time < current_time:
            user.member_validity_time = int(current_time) + 60 * now_time
        else:
            user.member_validity_time = int(user.member_validity_time) + 60 * now_time
        if int(user.member_type.id) == 3:
            menmber_config = MembersConfig.objects.filter(id=2).first()
            user.member_type = menmber_config
        user.adv_count += 1
        user.save()

        devices = Devices.objects.filter(user=uid).all()
        for one_devices in devices:
            db5.delete(str(one_devices.uuid + one_devices.package_id))

        new_user = User.objects.filter(uid=uid).first()
        return JsonResponse({"code": 200, "message": "success", "data": new_user.get_info()})


class SendEmail(View):

    def post(self, request):
        """
            发送邮箱
        """
        data = json.loads(request.body.decode(encoding="utf-8"))
        key = data.get("key", "")
        aes = Aescrypt()
        try:
            aes_result = aes.aesdecrypt(key)
            if aes_result != "leyou2021":
                return JsonResponse({"code": 404, "message": 'key error'})
        except Exception as e:
            return JsonResponse({"code": 404, "message": 'key error'})

        email = data.get("email", "")
        uid = data.get("uid", "")
        package_id = data.get("package_id", "")
        email_type = data.get("email_type", "")
        platform_id = data.get("platform_id", "")
        try:
            uid = int(uid)
        except Exception as e:
            return JsonResponse({"code": 404, "message": "uid error"})

        if not email or not uid or not package_id or not email_type:
            return JsonResponse({"code": 404, "message": "data error"})
        platform = AppPlatform.objects.filter(platform_id=platform_id).first()
        app = AppPackage.objects.filter(package_id=package_id).first()
        if not app:
            return JsonResponse({"code": 404, "message": "not found app"})

        email_type = int(email_type)
        if email_type == 1:
            user = User.objects.filter(email=email, platform=platform).first()
            if user:
                return JsonResponse({"code": 404, "message": f"{email} exist"})
        if email_type == 2:
            user = User.objects.filter(email=email, platform=platform).first()
            if not user:
                return JsonResponse({"code": 404, "message": f"not found email"})

        send_status = send_email(email, uid, app.name)
        if not send_status:
            return JsonResponse({"code": 404, "message": "send email error", })

        return JsonResponse({"code": 200, "message": "success"})


class VerifyCode(View):

    def post(self, request):
        """
            验证code
        """
        data = json.loads(request.body.decode(encoding="utf-8"))
        key = data.get("key", "")
        aes = Aescrypt()
        aes_result = aes.aesdecrypt(key)
        if aes_result != "leyou2021":
            return JsonResponse({"code": 404, "message": 'key error'})
        uid = data.get("uid", 0)
        code = data.get("code", "")
        verify_type = data.get("verify_type", "")

        try:
            uid = int(uid)
        except Exception as e:
            return JsonResponse({"code": 404, "message": "uid error"})

        if not code or not verify_type:
            return JsonResponse({"code": 404, "message": "not found code or verify_type"})

        redis_data = db1.get(uid)
        if not redis_data:
            return JsonResponse({"code": 404, "message": "not found code"})

        datas = json.loads(str(redis_data, "utf-8"))
        email = datas.get("email", "")
        verify_code = datas.get("code", "")
        if str(code) != str(verify_code):
            return JsonResponse({"code": 404, "message": "verify code error"})

        if verify_type == 1:
            user = User.objects.filter(uid=uid).first()
            if not user:
                return JsonResponse({"code": 404, "message": "not found the user id"})

            if user.email:
                return JsonResponse({"code": 404, "message": "E-mail has been associated"})
            else:
                user.email = email
                user.save()
                db1.delete(str(uid))

                devices = Devices.objects.filter(user=uid).all()
                for device in devices:
                    db5.delete(str(device.uuid + device.package_id))
                    db6.delete(str(device.uuid + device.package_id))

                return JsonResponse({"code": 200, "message": "success"})

        if verify_type == 2:
            db1.delete(str(uid))
            return JsonResponse({"code": 200, "message": "success"})

        return JsonResponse({"code": 404, "message": "verify type error"})


class Password(View):

    def post(self, request):
        """
            更新密码
        """
        data = json.loads(request.body.decode(encoding="utf-8"))
        key = data.get("key", "")
        aes_result = aes.aesdecrypt(key)
        if aes_result != "leyou2021":
            return JsonResponse({"code": 404, "message": 'key error'})
        uid = data.get("uid", "")
        email = data.get("email", "")
        current_password = data.get("current_password", "")
        password = data.get("password", "")
        password_type = data.get("password_type", "")

        try:
            uid = int(uid)
        except Exception as e:
            return JsonResponse({"code": 404, "message": "uid error"})

        if len(password) < 6:
            return JsonResponse({"code": 404, "message": "The password length should not be less than 6 bits"})

        user = User.objects.filter(uid=int(uid)).first()
        if not user:
            return JsonResponse({"code": 404, "message": "not found user"})
        md5_password = str_as_md5(password)

        if password_type == 1 or password_type == 2:
            result = User.objects.filter(uid=uid).update(
                password=md5_password
            )
            if result:
                return JsonResponse({"code": 200, "message": "success"})

        if password_type == 3:
            correct_md5_password = str_as_md5(current_password)
            user = User.objects.filter(uid=uid, email=email).first()
            if not user:
                return JsonResponse({"code": 404, "message": "not found user"})

            if user.password == correct_md5_password:
                result = User.objects.filter(uid=uid).update(
                    password=md5_password
                )
                if result:
                    return JsonResponse({"code": 200, "message": "success"})
            else:
                return JsonResponse({"code": 404, "message": "password error"})
        return JsonResponse({"code": 404, "message": "data error"})


class ClearAdvertisingCount(View):

    def post(self, request):
        """
            24小时清除一次广告时间
        """
        users = User.objects.filter(adv_count__gt=0)
        for user in users:
            user.adv_count = 0
            user.save()
        return JsonResponse({"code": 200, "message": "success"})


class UploadFlow(View):

    def post(self, request):
        """
        上传流量
        """
        data = json.loads(request.body.decode(encoding="utf-8"))
        uuid = data.get("uuid", "")
        flow = data.get("flow", "")
        device = Devices.objects.filter(uuid=uuid).first()
        if not device:
            return JsonResponse({"code": 200, "message": 'not found user'})

        # 统计用户流量
        user = User.objects.filter(id=device.user).first()
        user.flow_user = flow
        user.save()
        return JsonResponse({"code": 200, "message": 'success'})


class GetDevice(View):

    def post(self, request):
        """
            获取所有用户设备
        """
        data = json.loads(request.body.decode(encoding="utf-8"))
        key = data.get("key", "")
        aes_result = aes.aesdecrypt(key)
        if aes_result != "leyou2021":
            return JsonResponse({"code": 404, "message": 'key error'})
        uid = data.get("uid", 0)
        package_id = data.get("package_id", "")
        try:
            uid = int(uid)
        except Exception as e:
            return JsonResponse({"code": 404, "message": "uid error"})

        user = User.objects.filter(uuid=uid).first()

        devices = Devices.objects.filter(user=user, package_id=package_id).all()
        if not devices:
            return JsonResponse({"code": 404, "message": "user not found"})

        device_info = []

        for device in devices:
            info = device.get_info()
            device_info.append(info)
        return JsonResponse({"code": 200, "message": "success", "data": device_info})


class DeleteDevice(View):
    """
        删除设备
    """

    def post(self, request):
        data = json.loads(request.body.decode(encoding="utf-8"))
        key = data.get("key", "")
        aes_result = aes.aesdecrypt(key)
        if aes_result != "leyou2021":
            return JsonResponse({"code": 404, "message": 'key error'})
        uuid = data.get("uuid", "")
        uid = data.get("uid", "")
        package_id = data.get("package_id", "")

        if not uuid or not uid or not package_id:
            return JsonResponse({"code": 404, "message": 'not found uuid or uid or package_id'})

        devices = Devices.objects.filter(uuid=uuid, package_id=package_id).delete()
        db5.delete(str(uuid + package_id))
        db6.delete(str(uuid + package_id))


        if devices:
            user = User.objects.filter(uid=uid).first()
            if user.device_count > 0:
                devices_count = Devices.objects.filter(user=user, package_id=package_id).count()
                user.device_count = devices_count
            user.save()
            return JsonResponse({"code": 200, "message": "success"})
        return JsonResponse({"code": 404, "message": "delete error"})


class Logout(View):
    """
        登出
    """
    def post(self, request):
        data = json.loads(request.body.decode(encoding="utf-8"))
        key = data.get("key", "")
        aes_result = aes.aesdecrypt(key)
        if aes_result != "leyou2021":
            return JsonResponse({"code": 404, "message": 'key error'})
        uuid = data.get("uuid", "")
        uid = data.get("uid", "")
        package_id = data.get("package_id", "")

        if not uuid or not uid or not package_id:
            return JsonResponse({"code": 404, "message": 'not found uuid or uid or package_id'})
        user = User.objects.filter(uid=uid).first()

        if not user:
            return JsonResponse({"code": 404, "message": 'not found uid'})

        devices = Devices.objects.filter(uuid=uuid, package_id=package_id).delete()
        db5.delete(str(uuid + package_id))
        db6.delete(str(uuid + package_id))
        if devices:
            if user.device_count > 0:
                user.device_count -= 1
                user.save()
            return JsonResponse({"code": 200, "message": "success"})

        return JsonResponse({"code": 404, "message": "delete error"})


class EmailUnbinding(View):
    """
        邮箱解绑
    """

    def del_device(self, uid, platform):
        devices = Devices.objects.filter(user=uid, platform=platform).all()
        for device in devices:
            Devices.objects.filter(id=device.id).delete()
            db5.delete(str(device.uuid + device.package_id))
            db6.delete(str(device.uuid + device.package_id))
        devices_count = Devices.objects.filter(user=uid, platform=platform).count()
        return devices_count

    def post(self, request):
        data = json.loads(request.body.decode(encoding="utf-8"))
        key = data.get("key", "")
        aes_result = aes.aesdecrypt(key)
        if aes_result != "leyou2021":
            return JsonResponse({"code": 404, "message": 'key error'})
        email = data.get("email", "")
        uid = data.get("uid", "")
        password = data.get("password", "")
        uuid = data.get("uuid", "")
        platform_id = data.get("platform_id", "")

        platform = AppPlatform.objects.filter(platform_id=platform_id).first()
        if not platform:
            return JsonResponse({"code": 404, "message": "not found platform"})
        if len(password) < 6:
            return JsonResponse({"code": 404, "message": "The password contains less than 6 characters"})

        if not email or not uid or not uuid:
            return JsonResponse({"code": 404, "message": 'not found email or uid or uuid or package_id'})
        user = User.objects.filter(uid=int(uid), email=email).first()
        if not user:
            return JsonResponse({"code": 404, "message": 'not found uid or email'})

        md5_password = str_as_md5(password)

        if user.password == md5_password:
            user.email = None
            user.password = None
            devices_count = self.del_device(user.uid, platform)
            user.device_count = devices_count
            user.save()
            unbinding_send_email(email, user.uid, platform.name)
            return JsonResponse({"code": 200, "message": "success"})
        else:
            return JsonResponse({"code": 404, "message": "password error"})


class CheckUserStatus(View):
    def post(self, request):
        """
            检测用户是否会员状态
        """
        data = json.loads(request.body.decode(encoding="utf-8"))
        key = data.get("key", "")
        if key != USER_KEY:
            return JsonResponse({"code": 404, "message": 'key error'})

        users = User.objects.filter(member_type__members__type__lt=3).all()
        current_time = int(time.time())

        count = 0
        for user in users:
            validity_time = user.member_validity_time
            if validity_time < current_time:
                platform_id = user.platform.id
                uid = user.uid
                Devices.objects.filter(user=uid, platform_id=platform_id).delete()
                User.objects.filter(id=user.id).update(
                    member_type=3,
                    flow_user=0,
                    subscription_type=2,
                    device_count=0,
                    max_device_count=1,
                    set_meal=None
                )
                count += 1
        return JsonResponse({"code": 200, "message": "success"})


class Statistics(View):

    def post(self, request):
        data = json.loads(request.body.decode(encoding="utf-8"))
        version = data.get("version", "")
        # if version:
        data["time"] = int(time.time())
        conv_data = json.dumps(data)
        db0.lpush("statistics", conv_data)
        return JsonResponse({"code": 200, "message": "success"})


class QueryUser(View):
    def post(self, request):
        """
        查询用户
        """
        users = User.objects.filter(member_type__members__type__lt=3)
        datas = []
        for user in users:
            datas.append(user.get_uuid())
        return JsonResponse({"code": 200, "message": "success", "data": datas})


class QueryOneUser(View):
    def post(self, request):
        """
        查询用户
        """
        data = json.loads(request.body.decode(encoding="utf-8"))

        uid = data.get("uid", "")
        user = User.objects.filter(uid=uid).first()
        try:
            country = user.country
        except Exception as e:
            country = ""
        return JsonResponse({"code": 200, "message": "success", "data": country})


class QueryUserUid(View):
    def post(self, request):
        """
        查询用户
        """
        data = json.loads(request.body.decode(encoding="utf-8"))

        uid = data.get("uid", "")
        # print(uid)
        if not uid:
            return JsonResponse({"code": 404, "message": "not found uid"})

        user = User.objects.filter(uid=uid).first()
        if not user:
            return JsonResponse({"code": 404, "message": "not found user"})

        return JsonResponse({"code": 200, "message": "success", "data": user.get_uuid()})


def page_not_found(request):
    return render(request, '404.html')


class VerifyShareCode(View):
    """
        验证分享code
    """

    def post(self, request):
        data = json.loads(request.body.decode(encoding="utf-8"))
        # key = data.get("key", "")
        # aes_result = aes.aesdecrypt(key)
        # if aes_result != "leyou2021":
        #     return JsonResponse({"code": 404, "message": 'key error'})
        uid = data.get("uid", "")
        code = data.get("code", "")
        package_id = data.get("package_id", "")

        # print(uid, code, package_id)
        if not uid or not package_id or not code:
            return JsonResponse({"code": 404, "message": 'not found uuid or uid or package_id or code'})

        share_user = User.objects.filter(code=code).first()
        user = User.objects.filter(uid=uid).first()
        current_time = datetime.datetime.now()
        ten_day = datetime.timedelta(days=10)
        user_ten_day = user.create_time + ten_day
        if not share_user:
            return JsonResponse({"code": 404, "message": "The code does not exist"})

        if not user:
            return JsonResponse({"code": 404, "message": "not found user"})

        if code == user.code:
            return JsonResponse({"code": 404, "message": "You can't use your code"})

        if user.exchange:
            return JsonResponse({"code": 404, "message": "You have redeemed this type code"})

        if current_time > user_ten_day:
            return JsonResponse({"code": 404, "message": "You're not a new user（within 10 days)"})

        if user.new_user == 1:
            return JsonResponse({"code": 404, "message": "You're not a new user"})

        share_config = ShareConfig.objects.all().first()
        day = share_config.day
        now_time = time.time()
        add_time = 60 * 60 * 24 * int(day)
        if share_user.member_type.members.type != 1:
            user_time = share_user.member_validity_time
            if now_time > user_time:
                share_user.member_validity_time = now_time + add_time
            else:
                share_user.member_validity_time = share_user.member_validity_time + add_time
            share_user.exchange_count += 1
            share_user.exchange = 1

            share_user.save()
            # print(f"会员类型{share_user.member_type.members.type}", type(share_user.member_type.members.type), code, "---",
            #       share_user.uid)

        new_user_time = user.member_validity_time

        if now_time > new_user_time:
            user.member_validity_time = now_time + add_time
        else:
            user.member_validity_time = user.member_validity_time + add_time
        user.exchange = 1
        user.new_user = 1
        user.save()

        try:
            url = "https://datas.9527.click/manage/share_analysis"
            json_data = {
                "package_id": package_id
            }
            requests.post(url=url, json=json_data)
        except Exception as e:
            print(e)
        return JsonResponse({"code": 200, "message": "Redeem succeed"})


class DelDevice(View):
    """
        删除设备
    """

    def delete_user(self, all_user):
        user_count = all_user.count()

        if user_count >= 2:
            for i in all_user:
                # print(f"删除{i.uuid}")
                Devices.objects.filter(id=i.id).delete()

    def post(self, request):
        data = json.loads(request.body.decode(encoding="utf-8"))
        # all_devices = Devices.objects.all()
        # count = 0
        # for one in all_devices:
        #     uuid = one.uuid
        #     device_all = Devices.objects.filter(uuid=uuid).all()
        #     self.delete_user(device_all)
        #     count += 1
        #     print(f"第{count}")

        # print("结束")
        return JsonResponse({"code": 404, "message": "delete error"})


# class CheckUser(View):
#
#     def post(self, request):
#         mysql_session = Session()
#         sql1 = f"select * from users where member_type=1"
#
#         res = mysql_session.query(sql1)
#         count = 0
#         members = MembersConfig.objects.filter(id=1).first()
#
#         for i in res:
#             member_validity_time = i.get("member_validity_time", 0)
#             uid = i.get("uid")
#             user = User.objects.filter(uid=uid).first()
#
#             vip_id = user.member_type.members.id
#
#             new_user_time = user.member_validity_time
#
#             if member_validity_time > new_user_time:
#                 user.member_validity_time = member_validity_time
#                 count += 1
#
#                 User.objects.filter(uid=uid).update(
#                     member_type=members,
#                     member_validity_time=member_validity_time,
#                     max_device_count=members.device_count
#
#                 )
#                 # user.save()
#             if vip_id != 1:
#                 User.objects.filter(uid=uid).update(
#                     member_type=members,
#                     max_device_count=members.device_count
#                 )
#         #     self.save_data(i)
#         #     count += 1
#         # print(f"同步用户数{count}")
#
#         return JsonResponse({"code": 404, "message": "error"})


class SyncSingleUser(View):

    def save_data(self, data):
        uid = data.get("uid", "")
        uuid = data.get("uuid", "")
        member_validity_time = data.get("member_validity_time", "")
        member_type = data.get("member_type", "")
        package_id = data.get("package_id", "")
        white_type = data.get("white_type", "")
        country = data.get("country", "")
        region = data.get("region", "")
        members = MembersConfig.objects.filter(id=member_type).first()
        # app_id = self.app_id(app)
        first_subscription = data.get("first_subscription", 0)
        subscription_type = data.get("subscription_type", 0)
        user = User.objects.filter(uid=uid).first()
        user_device = Devices.objects.filter(uuid=uuid).first()
        app = AppPackage.objects.filter(package_id=package_id).first()

        set_meal = None

        if not user:
            code = str_as_md5_short(str(uid) + random_str())
            create_user = User.objects.create(uid=int(uid),
                                              platform=app.platform,
                                              set_meal=set_meal,
                                              member_type=members,
                                              member_validity_time=member_validity_time,
                                              first_subscription=first_subscription,
                                              subscription_type=subscription_type,
                                              white_type=white_type,
                                              country=country,
                                              region=region,
                                              code=code,
                                              max_device_count=members.device_count
                                              )

            if create_user:
                json_data = {
                    "package_id": package_id,
                    "uid": uid,
                    "platform": app.platform.platform_id
                }
                db3.set(str(uuid + app.platform.platform_id + package_id), json.dumps(json_data))

        if not user_device:
            devices = Devices.objects.create(uuid=uuid,
                                             platform=app.platform,
                                             user=int(uid),
                                             package_id=package_id,
                                             )
            if devices:
                user.device_count += 1
                user.save()

    def post(self, request):
        data = json.loads(request.body.decode(encoding="utf-8"))

        print(data)
        # self.save_data(datas)
        return JsonResponse({"code": 200, "message": "success"})


class QrCode(View):
    def get(self, request):
        """
        生成code
        :param request:
        :return:
        """
        current_time = str(int(time.time()))
        code = random_str(6) + current_time
        db10.set(code, "1", ex=60 * 2)
        json_data = {
            "code": code,
        }

        status = {
            "status": 2
        }
        db11.set(code, json.dumps(status), ex=60 * 2)
        return JsonResponse({"code": 200, "message": "success", "data": json_data})

    def bunding_uuid(self, user, uuid, package_id, platform):

        create_devices = Devices.objects.create(
            platform=platform,
            user=user.uid,
            uuid=uuid,
            package_id=package_id,
            login_time=datetime.datetime.now()
        )
        if create_devices:
            user.device_count += 1
            user.save()

    def post(self, request):
        data = json.loads(request.body.decode(encoding="utf-8"))
        code = data.get("code", "")
        uid = data.get("uid", "")
        uuid = data.get("uuid", "")
        package_id = data.get("package_id", "")

        status = {
            "status": 0
        }
        if not code or not uid:
            db11.set(code, json.dumps(status), ex=60 * 2)
            return JsonResponse({"code": 404, "message": "code or uid not found"})
        redis_code = db10.get(code)
        user = User.objects.filter(uid=uid).first()
        app = AppPackage.objects.filter(package_id=package_id).first()

        platform = AppPlatform.objects.filter(platform_id=app.platform.platform_id).first()

        if not user:
            db11.set(code, json.dumps(status), ex=60 * 2)
            return JsonResponse({"code": 404, "message": "user not found"})

        if not redis_code:
            db11.set(code, json.dumps(status), ex=60 * 2)
            return JsonResponse({"code": 404, "message": "code expires"})

        if user.device_count >= user.max_device_count:
            db11.set(code, json.dumps(status), ex=60 * 2)
            return JsonResponse({"code": 404, "message": "Maximum number of devices bound to a user"})

        devices = Devices.objects.filter(user=user.uid, uuid=uuid, platform=platform).first()

        try:
            if not devices:
                self.bunding_uuid(user, uuid, package_id, platform)
            user_data = user.get_info()
            user_data["status"] = 1
            code = db11.set(code, json.dumps(user_data), ex=60 * 2)
            if code:
                return JsonResponse({"code": 200, "message": "success"})
            else:
                db11.set(code, json.dumps(status), ex=60 * 2)
                return JsonResponse({"code": 404, "message": "redis save failure"})
        except Exception as e:
            db11.set(code, json.dumps(status), ex=60 * 2)
            return JsonResponse({"code": 404, "message": "redis save error"})


class QrCodeLogin(View):
    def post(self, request):
        """
        二维码登录
        :param request:
        :return:
        """
        data = json.loads(request.body.decode(encoding="utf-8"))
        code = data.get("code", "")
        if not code:
            return JsonResponse({"code": 404, "message": "code is none"})
        try:
            redis_data = db11.get(code)
            if not redis_data:
                return JsonResponse({"code": 404, "message": "user not found"})
            json_data = json.loads(redis_data)
            # db11.delete(code)
            return JsonResponse({"code": 200, "message": "success", "data": json_data})
        except Exception as e:
            return JsonResponse({"code": 404, "message": "redis error"})


class AddTime(View):

    def post(self, request):
        """
        添加时长
        :param request:
        :return:+
        """
        data = json.loads(request.body.decode(encoding="utf-8"))
        key = data.get("key", "")
        aes = Aescrypt()
        aes_result = aes.aesdecrypt(key)
        if aes_result != "leyou2021":
            return JsonResponse({"code": 404, "message": 'key error'})
        uid = data.get("uid", "")
        vip_time = data.get("time", "")
        vip_type = data.get("vip_type")
        if not uid or not vip_time or not vip_type:
            return JsonResponse({"code": 404, "message": "not found uid or time_type or vip_type"})

        # 时间
        current_time = int(time.time())
        user = User.objects.filter(uid=uid).first()
        if not user:
            return JsonResponse({"code": 404, "message": "not found uuid"})
        user_time = user.member_validity_time
        adv_count = user.adv_count
        config = UsersConfig.objects.first()

        if adv_count >= config.adv_count:
            return JsonResponse({"code": 404, "message": "You have reached the max ADs times today!"})

        menmber_config = MembersConfig.objects.filter(id=int(vip_type)).first()
        if user.member_validity_time < current_time:
            user.member_validity_time = int(current_time) + vip_time
        else:
            user.member_validity_time = user_time + vip_time
        if user.member_type.members.type != 1:
            user.member_type = menmber_config
        user.save()

        devices = Devices.objects.filter(user=uid).all()
        for one_devices in devices:
            db5.delete(str(one_devices.uuid + one_devices.package_id))
            db6.delete(str(one_devices.uuid + one_devices.package_id))

        new_user = User.objects.filter(uid=uid).first()
        return JsonResponse({"code": 200, "message": "success", "data": new_user.get_info()})


class Feedback(View):

    def get_now_time(self):
        timeStamp = time.time()
        timeArray = time.localtime(timeStamp)
        otherStyleTime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
        return otherStyleTime

    def post(self, request):
        """
        添加时长
        :param request:
        :return:+
        """
        data = json.loads(request.body.decode(encoding="utf-8"))
        key = data.get("key", "")
        aes = Aescrypt()
        aes_result = aes.aesdecrypt(key)
        if aes_result != "leyou2021":
            return JsonResponse({"code": 404, "message": 'key error'})
        content = data.get("content", "")
        email = data.get("email", "")
        uid = data.get("uid", "")
        envet_type = data.get("type", "")
        package_id = data.get("package_id", "")

        vip_type = {1: "正式会员", 2: "赠送会员", 3: "非会员", 4: "时长会员"}
        country = ""
        vip_name = ""
        user_email = data.get("email", "")
        user = User.objects.filter(uid=uid).first()
        if user:
            country = user.country
            v_type = user.member_type.members.type
            vip_name = vip_type.get(v_type)
            # user_email = user.email

        app_name = ""
        app = AppPackage.objects.filter(package_id=package_id).first()
        if app:
            app_name = app.name

        result = UserFeedback.objects.create(
            uid=uid,
            content=content,
            email=email,
            type=envet_type,
            name=app_name,
            country=country,
            vip_name=vip_name
        )

        if result:
            dingding_api = DataLoggerAPI("6543720081", "1mtv8ux938ykgw030vi2tuc3yc201ikr")
            now_time = self.get_now_time()
            message = f" 反馈通知:{now_time} \r\n 产品：{app_name} \r\n 用户：{uid} \r\n 邮箱：{user_email} \r\n 国家：{country}\r\n 会员：{vip_name} \r\n 问题：{envet_type} \r\n 内容：{content}"
            dingding_api.dd_send_message(message[:128], "vpnoperator")
            return JsonResponse({"code": 200, "message": "success"})
        return JsonResponse({"code": 404, "message": "data error"})

"反馈通知:2022-06-15 06:03:01产品：IOS Super VPN用户：1524130504398479360邮箱：1@qq.com国家：中国会员：正式会员问题：Something else内容：123456', 'to_group_name': 'vpnoperator"

class DelTempUser(View):

    def del_redis(self, uuid, platform, package_id):
        user_key = uuid + platform.platform_id + package_id
        res = db3.delete(user_key)
        # if res:
        #     print(f"注册用户删除：{uuid},平台：{platform.platform_id} app:{package_id}")
        # else:
        #     print(f"没发现用户：{uuid},平台：{platform.platform_id} app:{package_id}")

    def query_device(self, uid):
        devices = Devices.objects.filter(uid=uid).all()
        return devices

    def del_device(self, uuid, package_id):
        res = Devices.objects.filter(uuid=uuid, package_id=package_id).delete()
        # if res:
        #     print(f"设备:{uuid} 删除成功")
        # else:
        #     print(f"没发现设备:{uuid}")

    def del_user(self, uid):
        res = User.objects.filter(uid=uid).delete()
        # if res:
        #     print(f"用户:{uid} 删除成功")
        # else:
        #     print(f"没发现用户:{uid}")

    def post(self, request):
        """
        :param request:
        :return:+
        """
        data = json.loads(request.body.decode(encoding="utf-8"))
        key = data.get("key", "")
        if key != "leyou2021":
            return JsonResponse({"code": 404, "message": 'key error'})
        exp_time = int(time.time()) - 60 * 60 * 24 * 90

        member_config = MembersConfig.objects.filter(id=3).first()
        users = User.objects.filter(member_validity_time__lt=exp_time, member_type=member_config).all()[0:1000]

        for user in users:
            platform = user.platform
            devices = Devices.objects.filter(user=user.uid).all()
            for device in devices:
                uuid = device.uuid
                package_id = device.package_id
                self.del_redis(uuid, platform, package_id)
                self.del_device(uuid, package_id)

            self.del_user(user.uid)
        return JsonResponse({"code": 200, "message": "success"})


class ShareTask(View):

    def get(self, request):
        """
        :param request:
        :return:+
        """
        key = request.GET.get("data")
        datas = str(key).replace(" ", "+")
        aes_result = aes.aesdecrypt(datas)
        res = str(aes_result).replace("\'", "\"")

        # print(res)
        json_data = json.loads(res)
        task_name = json_data.get("task_name", "")
        package_id = json_data.get("package_id", "")
        uid = json_data.get("uid", "")
        url = json_data.get("url")
        app = AppPackage.objects.filter(package_id=package_id).first()
        platform = AppPlatform.objects.filter(platform_id=app.platform_id).first()
        UserShareTask.objects.create(
            uid=uid,
            app=app,
            platform=platform,
            name=task_name
        )
        return redirect(url)

        # return JsonResponse({"code": 200, "message": "success"})


class ShareTaskStatus(View):

    def post(self, request):
        data = json.loads(request.body.decode(encoding="utf-8"))
        key = data.get("key", "")
        if key != "leyou2021":
            return JsonResponse({"code": 404, "message": 'key error'})

        package_id = data.get("package_id", "")
        uid = data.get("uid", "")
        app = AppPackage.objects.filter(package_id=package_id).first()

        users_list = []
        users = UserShareTask.objects.filter(
            uid=uid,
            app=app,
        )
        for user in users:
            users_list.append(user.get_info())
        return JsonResponse({"code": 200, "message": "success", "data": users_list})


class ReceiveAward(View):

    def post(self, request):
        data = json.loads(request.body.decode(encoding="utf-8"))
        key = data.get("key", "")
        if key != "leyou2021":
            return JsonResponse({"code": 404, "message": 'key error'})
        task_id = data.get("id", "")
        result = UserShareTask.objects.filter(id=task_id).update(status=2)
        if result:
            return JsonResponse({"code": 200, "message": "success"})
        else:
            return JsonResponse({"code": 404, "message": "error data"})


class AddDeviceToken(View):

    def post(self, request):
        """
        添加设备token
        :param request:
        :return:+
        """
        data = json.loads(request.body.decode(encoding="utf-8"))
        key = data.get("key", "")
        aes = Aescrypt()
        aes_result = aes.aesdecrypt(key)
        if aes_result != "leyou2021":
            return JsonResponse({"code": 404, "message": 'key error'})

        uuid = data.get("uuid", "")
        device_token = data.get("device_token", "")

        devices = Devices.objects.filter(uuid=uuid).first()
        if not devices or not device_token:
            return JsonResponse({"code": 404, "message": 'not found device_token or uid'})

        result = Devices.objects.filter(uuid=uuid).update(
            device_token=device_token
        )

        if result:
            return JsonResponse({"code": 200, "message": "success"})
        else:
            return JsonResponse({"code": 200, "message": "success"})


class TestHello(View):

    def get(self, request):
        return JsonResponse({"code": 200, "message": "success"})

    def post(self, request):
        """
        :param request:
        :return:+
        """
        # uuid = "9832B98F947874EDDBC4F24A723B2CDEB5122796"
        # platform_id = "com.channel_xh.android"
        # package_id = "super_vpn.2021"
        #
        # redis_data = db3.get(str(uuid + platform_id + package_id))
        # print(redis_data,"查看")
        #
        # res = db3.delete(str(uuid + platform_id + package_id))
        # print(res)
        # print(request.path)
        # print("123")
        # users = User.objects.filter(max_device_count__gt=4).all()
        #
        # for user in users:
        #     user.max_device_count = 4
        #     user.save()
            # print(user.uid)


        # member_config = MembersConfig.objects.filter(id=4).first()
        # users = User.objects.filter(member_type=member_config).all()
        #
        # for user in users:
        #     uid = user.uid
        #     res = Orders.objects.filter(user=uid).first()
        #     if not res:
        #         continue
        #     order_type = res.order_type
        #     state = res.state
        #     if res and order_type == 1:
        #         if state == 1 or state==3:
        #             print(uid)

        # try:
        #     data = json.loads(request.body.decode(encoding="utf-8"))
        # except Exception as e:
        #     print(e)
        #     return JsonResponse({"code": 404, "message": f"error:{e}"})
        # username = data.get("username", "")
        return JsonResponse({"code": 200, "message": ""})




# class SyncUser(View):
#     def app_id(self, id):
#         # 对应app
#         app_all = {
#             1: "com.superoversea",
#             2: "com.strom.vpn",
#             3: "com.leyou.ghost.vpn",
#             4: "com.yanji.trojan_vpn.yanJiVPN"
#         }
#         return app_all.get(id, "")
#
#     def get_platform(self, id):
#         # 对应app
#         platform = {
#             1: AppPlatform.objects.filter(id=1).first(),
#             2: AppPlatform.objects.filter(id=2).first(),
#             3: AppPlatform.objects.filter(id=1).first(),
#             4: AppPlatform.objects.filter(id=1).first(),
#         }
#
#         return platform.get(id, "")
#
#     def set_meal_day(self, id):
#         # 对应套餐
#         set_meal_value = {
#             1: 30,
#             2: 180,
#             3: 365,
#             4: 90
#         }
#         return set_meal_value.get(id)
#
#     def save_data(self, data):
#         app = data.get("app", "")
#         platform = self.get_platform(app)
#         app_id = self.app_id(app)
#         uid = data.get("uid", "")
#         uuid = data.get("uuid", "")
#         member_type = data.get("member_type", "")
#         member_validity_time = data.get("member_validity_time", "")
#         country = data.get("country", "")
#         region = data.get("region", "")
#         first_subscription = data.get("first_subscription", "")
#         subscription_type = data.get("subscription_type", 0)
#         white_type = data.get("white_type", "")
#         create_time = data.get("create_time", "")
#         login_time = data.get("login_time", "")
#         set_meal_temp_id = data.get("set_meal", "")
#         # print(app_id)
#         user = User.objects.filter(uid=uid).first()
#         user_device = Devices.objects.filter(uuid=uuid).first()
#         app = AppPackage.objects.filter(package_id=app_id).first()
#         members = MembersConfig.objects.filter(id=member_type).first()
#
#         if set_meal_temp_id:
#             # print(set_meal_temp_id)
#             set_meal_day = self.set_meal_day(set_meal_temp_id)
#             set_meal = SetMeal.objects.filter(platform=platform, day=set_meal_day).first()
#         else:
#             set_meal = None
#
#         if not user:
#             code = str_as_md5_short(str(uid) + random_str())
#             create_user = User.objects.create(uid=int(uid),
#                                               platform=platform,
#                                               set_meal=set_meal,
#                                               member_type=members,
#                                               member_validity_time=member_validity_time,
#                                               first_subscription=first_subscription,
#                                               subscription_type=subscription_type,
#                                               white_type=white_type,
#                                               country=country,
#                                               region=region,
#                                               code=code,
#                                               max_device_count=members.device_count
#                                               )
#             User.objects.filter(id=create_user.pk).update(
#                 create_time=create_time,
#                 login_time=login_time,
#             )
#             if create_user:
#                 json_data = {
#                     "package_id": app_id,
#                     "uid": uid,
#                     "platform": platform.platform_id
#                 }
#                 db3.set(str(uuid + platform.platform_id + app_id), json.dumps(json_data))
#
#             if not user_device:
#                 devices = Devices.objects.create(uuid=uuid,
#                                                  platform=platform,
#                                                  user=int(uid),
#                                                  package_id=app_id,
#                                                  create_time=create_time,
#                                                  login_time=login_time
#                                                  )
#
#                 Devices.objects.filter(id=devices.pk).update(
#                     create_time=create_time,
#                     login_time=login_time,
#                 )
#                 user = User.objects.filter(id=create_user.pk).first()
#                 user.device_count += 1
#                 user.save()
#         else:
#             User.objects.filter(id=user.pk).update(
#                 first_subscription=first_subscription,
#                 subscription_type=subscription_type,
#                 member_validity_time=member_validity_time,
#                 login_time=login_time,
#             )
#             if not user_device:
#                 devices = Devices.objects.create(
#                     platform=platform,
#                     uuid=uuid,
#                     user=user.uid,
#                     package_id=app_id,
#                     create_time=create_time,
#                     login_time=login_time
#                 )
#
#                 Devices.objects.filter(id=devices.pk).update(
#                     create_time=create_time,
#                     login_time=login_time,
#                 )
#
#     def async_all(self):
#         mysql_session = Session()
#         sql1 = f"select * from users where id=(select max(id) from users)"
#         res = mysql_session.query(sql1)
#         end_count = 0
#         for i in res:
#             end_count = i.get("id", 0)
#         sum_count = 1000
#         for i in range(int(end_count / sum_count)):
#             start = i * sum_count
#             median = (i + 1) * sum_count
#             sql1 = f"select * from users  where id between {start} and {median}"
#             res = mysql_session.query(sql1)
#             for i in res:
#                 self.save_data(i)
#
#     def async_yesterday(self):
#         mysql_session = Session()
#         today = datetime.date.today()
#         oneday = datetime.timedelta(days=1)
#         yesterday = today - oneday
#         str_dt = str(yesterday.strftime("%Y-%m-%d"))
#
#         sql1 = f"select * from users where date(create_time)='{str_dt}'"
#
#         # sql1 = f"select * from users where date(create_time) between '2021-09-01' and '2021-10-8'"
#         res = mysql_session.query(sql1)
#         count = 0
#         for i in res:
#             self.save_data(i)
#             count += 1
#         print(f"同步用户数{count}")
#
#     def post(self, request):
#         datas = json.loads(request.body.decode(encoding="utf-8"))
#         data_type = datas.get("type", "")
#         if data_type == 1:
#             self.async_all()
#         if data_type == 2:
#             self.async_yesterday()
#             try:
#                 url = "https://api.9527.click/v2/user/sync_orders"
#                 requests.post(url=url, timeout=15)
#             except Exception as e:
#                 print(e)
#         return JsonResponse({"code": 200, "message": "success"})


# class SyncOrders(View):
#     def app_id(self, id):
#         # 对应app
#         app_all = {
#             1: "com.superoversea",
#             2: "com.strom.vpn",
#             3: "com.leyou.ghost.vpn",
#             4: "com.yanji.trojan_vpn.yanJiVPN"
#         }
#         return app_all.get(id, "")
#
#     def save_data(self, data):
#         app = data.get("app", "")
#         app_id = self.app_id(app)
#
#         user_id = data.get("user_id", 0)
#
#         order_type = data.get("order_type", "")
#         country = data.get("country", "")
#         order_id = data.get("order_id", "")
#         product_id = data.get("product_id", "")
#         refund_time = data.get("refund_time", 0)
#         product_time = data.get("product_time", 0)
#         state = data.get("state", "")
#         create_time = data.get("create_time", "")
#         update_time = data.get("update_time", "")
#         # print(app_id)
#
#         orders = Orders.objects.filter(order_id=order_id).first()
#
#         if orders:
#             return False
#
#         sql1 = f"select * from users  where id={user_id}"
#         res = mysql_session.query(sql1)
#
#         if not res:
#             print(order_id)
#             return False
#
#         uuid = res[0].get("uuid", "")
#         uid = res[0].get("uid", "")
#         if not uuid:
#             return False
#         app = AppPackage.objects.filter(package_id=app_id).first()
#         device = Devices.objects.filter(uuid=uuid).first()
#         set_meal = SetMeal.objects.filter(goods_id=product_id).first()
#         if not device:
#             print(f"没有{uuid}")
#             return False
#         query_order = Orders.objects.filter(order_id=order_id).first()
#
#         if query_order:
#             print(f"重复订单{order_id}")
#             return False
#
#         create_order = Orders.objects.create(
#             user=uid,
#             package_id=app_id,
#             app=app,
#             set_meal=set_meal,
#             order_id=order_id,
#             product_time=int(product_time),
#             order_type=order_type,
#             state=state,
#             refund_time=refund_time,
#             country=country
#         )
#         Orders.objects.filter(id=create_order.id).update(
#             create_time=create_time,
#             update_time=update_time
#         )
#
#     def post(self, request):
#         # datas = json.loads(request.body.decode(encoding="utf-8"))
#         count = 0
#         today = datetime.date.today()
#         oneday = datetime.timedelta(days=1)
#         yesterday = today - oneday
#         str_dt = str(yesterday.strftime("%Y-%m-%d"))
#
#         # str_dt = '2021-10-9'
#
#         sql1 = f"select * from trojan_orders where date(create_time)='{str_dt}'"
#
#         res = mysql_session.query(sql1)
#
#         for i in res:
#             self.save_data(i)
#             count += 1
#         print(f"订单同步数{count}")
#
#         # sql1 = f"select * from trojan_orders  where order_id='550000878246187'"
#         # res = mysql_session.query(sql1)
#         # self.save_data(res[0])
#         return JsonResponse({"code": 200, "message": "success"})
