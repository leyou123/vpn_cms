import json
import time
from django.http import JsonResponse
from django.views.generic.base import View
from apps.manage.models import Advertising, InduceConfig, ApiVersion, AppPackage,TimeConfig
from django_redis import get_redis_connection
from vpn_cms.settings import EX_TIME
db4 = get_redis_connection('DB4')


class GetAdvertising(View):
    """
        广告
    """

    def post(self, request):
        data = json.loads(request.body.decode(encoding="utf-8"))
        package_id = data.get("package_id", "")
        if not package_id:
            return JsonResponse({"code": 200, "message": 'not found package_id'})

        redis_key_name = f"avd_{package_id}"
        list_data = []
        str_config = ""
        redis_data = db4.get(redis_key_name)

        if redis_data:
            str_data = str(redis_data, "utf-8")
            list_datas = str_data.split("|")
            for one_data in list_datas:
                list_data.append(json.loads(one_data))
            return JsonResponse({"code": 200, "message": 'success', "data": list_data})

        app = AppPackage.objects.filter(package_id=package_id).first()
        datas = Advertising.objects.filter(app=app).all()

        for data in datas:
            data_info = data.get_info()
            list_data.append(data_info)
            str_config += json.dumps(data_info) + "|"
        rep_str = str_config[:-1]
        db4.set(redis_key_name, rep_str, ex=EX_TIME)

        return JsonResponse({"code": 200, "message": "success", "data": list_data})


class Version(View):

    def post(self, request):
        """
            版本号
        """
        time.sleep(2)
        data = json.loads(request.body.decode(encoding="utf-8"))
        package_id = data.get("package_id", "")

        if not package_id:
            return JsonResponse({"code": 200, "message": 'not found package_id'})
        redis_key_name = f"version_{package_id}"

        redis_data = db4.get(redis_key_name)
        if redis_data:
            datas = json.loads(str(redis_data, "utf-8"))
            return JsonResponse({"code": 200, "message": 'success', "data": datas})

        app = AppPackage.objects.filter(package_id=package_id).first()
        version = ApiVersion.objects.filter(app=app).first()
        if not version:
            return JsonResponse({"code": 200, "message": 'not found version'})

        db4.set(redis_key_name, json.dumps(version.get_info()), ex=EX_TIME)
        return JsonResponse({"code": 200, "message": 'success', "data": version.get_info()})


class GetInduceConfig(View):
    """
        诱导配置
    """
    def post(self, request):
        data = json.loads(request.body.decode(encoding="utf-8"))
        package_id = data.get("package_id", "")
        version = data.get("version", "")
        if not package_id:
            return JsonResponse({"code": 200, "message": 'not found package_id'})

        redis_key_name = f"version_{package_id}_{version}"
        redis_data = db4.get(redis_key_name)

        if redis_data:
            datas = json.loads(str(redis_data, "utf-8"))
            return JsonResponse({"code": 200, "message": 'success', "data": datas})

        app = AppPackage.objects.filter(package_id=package_id).first()
        if not app:
            return JsonResponse({"code": 404, "message": "not found app"})
        induce_config = InduceConfig.objects.filter(app=app, version=version).first()

        if not induce_config:
            return JsonResponse({"code": 404, "message": "not found version"})

        db4.set(redis_key_name, json.dumps(induce_config.get_info()), ex=EX_TIME)
        return JsonResponse({"code": 200, "message": "success", "data": induce_config.get_info()})


class AddTimeConfig(View):
    """
        时间配置
    """
    def get(self, request):
        datas = []
        redis_key_name = "time_config"
        str_config = ""

        redis_data = db4.get(redis_key_name)

        if redis_data:
            str_data = str(redis_data, "utf-8")
            list_datas = str_data.split("|")
            for one_data in list_datas:
                datas.append(json.loads(one_data))
            return JsonResponse({"code": 200, "message": 'success', "data": datas})

        user_times = TimeConfig.objects.all()
        for user_time in user_times:
            time_info = user_time.get_info()
            datas.append(time_info)
            str_config += json.dumps(time_info)+"|"

        rep_str = str_config[:-1]
        db4.set(redis_key_name, rep_str, ex=EX_TIME)
        return JsonResponse({"code": 200, "message": "success", "data": datas})