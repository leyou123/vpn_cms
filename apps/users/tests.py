from django.test import TestCase
from apps.manage.models import Advertising, InduceConfig, ApiVersion, AppPackage, TimeConfig, AppPlatform, \
    MembersConfig, Members, UsersConfig
from utils.crypto import Aescrypt


class TestUser(TestCase):

    def setUp(self) -> None:
        platform_data = self.create_platform()
        self.create_app(platform_data)
        self.create_member()
        self.create_user_config(platform_data)

    def test_api(self):
        print("-------------------------------------------------------------------------")
        register_data = self.do_register()
        if not register_data:
            return
        print("-------------------------------------------------------------------------")
        self.do_login(register_data)
        self.do_logout(register_data)
        self.do_share_task(register_data)

    def create_platform(self):
        """
            创建平台
        :return:
        """
        name = "Super VPN"
        res = AppPlatform.objects.create(
            name=name,
            platform_id="super_vpn.2021"
        )
        if res:
            print(f"{name}平台创建成功")

        return res

    def create_app(self, platform_data):
        """
        创建app
        :return:
        """
        name = "IOS Super VPN"
        package_id = "com.superoversea"
        res = AppPackage.objects.create(
            name=name,
            platform=platform_data,
            package_id=package_id,
            device=1
        )
        if res:
            print(f"{name}APP创建成功")

    def create_member(self):

        datas = [
            {"name": "正式会员", "type": 1, "device_count": 4},
            {"name": "赠送会员", "type": 2, "device_count": 1},
            {"name": "非会员", "type": 3, "device_count": 1},
            {"name": "时长会员", "type": 4, "device_count": 4}
        ]

        for data in datas:
            name = data.get("name", "")
            vip_type = data.get("type", "")
            device_count = data.get("device_count", "")

            member = Members.objects.create(
                name=name,
                type=vip_type
            )

            if member:
                print(f"{name}增加成功")
                self.create_member_config(name, member, device_count)

    def create_member_config(self, name, members, device_count):
        members_config = MembersConfig.objects.create(
            members=members,
            device_count=device_count
        )

        if members_config:
            print(f"{name}配置增加成功")

    def create_user_config(self, platform_data):
        """
        用户配置
        :param platform_data:
        :return:
        """
        user_config = UsersConfig.objects.create(
            platform=platform_data,
            temp_day=4,
            adv_count=4
        )
        if user_config:
            print(f"用户{platform_data.name}配置增加成功")


    def send_request(self,url,data,suc_info,error_info):

        response = self.client.post(url, data=data, content_type='application/json')

        if response.status_code == 200:
            datas = response.json()
            user_data = datas.get("data", "")
            print(suc_info)
            return user_data
        else:
            print(error_info)
            return None


    def do_register(self):
        url = '/v2/user/register'
        data = {
            "key": "Ntfk03xVGfbmYuWayVW83w==",
            "platform_id": "super_vpn.2021",
            "uuid": "22A29D001FEBBD74DD48B3C2A8CED487EEAB46F0",
            "package_id": "com.superoversea"
        }
        suc_info = "注册接口正常"
        error_info = "创建失败"
        response_data = self.send_request(url, data, suc_info,error_info)
        return response_data


    def do_login(self, data):
        url = '/v2/user/login'
        uid = data.get("uid", "")
        uuid = data.get("uuid", "")
        data = {
            "key": "Ntfk03xVGfbmYuWayVW83w==",
            "uid": uid,
            "uuid": uuid,
            "email": "",
            "platform_id": "super_vpn.2021",
            "package_id": "com.superoversea",
            "unbundling_uid": "",
            "unbundling_uuid": ""

        }
        suc_info = "登录正常"
        error_info = "登录失败"
        self.send_request(url, data, suc_info,error_info)


    def do_logout(self, data):
        """
            登出
        :param data:
        :return:
        """
        url = '/v2/user/logout'
        uid = data.get("uid", "")
        uuid = data.get("uuid", "")
        data = {
            "key": "Ntfk03xVGfbmYuWayVW83w==",
            "uid": uid,
            "uuid": uuid,
            "package_id": "com.superoversea",
        }

        suc_info = "登出正常"
        error_info = "登出失败"
        self.send_request(url, data, suc_info, error_info)

    def do_send_email(self, data):
        url = '/v2/user/logout'
        uid = data.get("uid", "")
        platform_id = data.get("platform_id", "")

        data = {
            "key": "Ntfk03xVGfbmYuWayVW83w==",
            "uid": uid,
            "email": "",
            "email_type": 1,
            "package_id": "com.superoversea",
            "platform_id": platform_id
        }

        suc_info = "发送成功"
        error_info = "登出失败"
        self.send_request(url, data, suc_info, error_info)


    def do_email_unbinding(self, data):
        url = '/v2/user/logout'
        uid = data.get("uid", "")
        uuid = data.get("uuid", "")
        platform_id = data.get("platform_id","'")

        """
                email = data.get("email", "")
        password = data.get("password", "")
        """
        data = {
            "key": "Ntfk03xVGfbmYuWayVW83w==",
            "uid": uid,
            "uuid": uuid,
            "package_id": "com.superoversea",
            "platform_id": platform_id
        }

        suc_info = "登出正常"
        error_info = "登出失败"
        self.send_request(url, data, suc_info, error_info)


    def do_share_task(self, data):

        uid = data.get("uid", "")
        test = {
            "task_name": "test",
            "package_id": "com.superoversea",
            "uid": uid,
            "url": "https://www.baidu.com"
        }

        aes = Aescrypt()
        datas = aes.aesencrypt(str(test))
        print(datas)

        url = f'/v2/user/share_task?data={datas}'

        response = self.client.get(url)
        print(response.status_code)

        if response.status_code==302:
            print("创建分享成功")
        else:
            print("创建分享失败")

    # def test_hello(self):
    #     url = '/v2/user/test_hello'
    #     info = {
    #         "username": "13978414080"
    #     }
    #     response = self.client.post(url, data=info, content_type='application/json')
    #
    #     # self.assertEqual(response.status_code, 200)
    #     print(response.status_code)
    #     print(response.json())
