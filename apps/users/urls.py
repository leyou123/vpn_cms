from django.urls import path
from apps.users.views import QrCodeLogin, QrCode
from apps.users.views import GetDevice, DeleteDevice
from apps.users.views import Register, Login, SendEmail, VerifyCode, Password, Logout, EmailUnbinding
from apps.users.views import QueryUser, UploadFlow, AddUserTime, ClearAdvertisingCount, SyncSingleUser
from apps.users.views import Statistics, QueryOneUser, CheckUserStatus, VerifyShareCode, DelDevice, AddTime, Feedback
from apps.users.views import DelTempUser, TestHello,ShareTask,ShareTaskStatus,ReceiveAward,QueryUserUid,AddDeviceToken,CheckLoginData,CheckBinding


urlpatterns = [

    # 登录
    path('login', Login.as_view(), name="login"),

    # 注册
    path('register', Register.as_view(), name="register"),
    # 登出
    path('logout', Logout.as_view(), name="logout"),
    # 邮箱解绑
    path('email_unbinding', EmailUnbinding.as_view(), name="email_unbinding"),

    # 添加时间 新旧接口
    path('add_time', AddUserTime.as_view(), name="add_user_time"),
    path('add_vip_time', AddTime.as_view(), name="add_vip_time"),

    # 发送邮件
    path('send_email', SendEmail.as_view(), name="send_email"),

    # 验证code
    path('verify_code', VerifyCode.as_view(), name="verify_code"),
    path('password', Password.as_view(), name="password"),
    # path('sync_user', SyncUser.as_view(), name="sync_user"),
    # path('sync_orders', SyncOrders.as_view(), name="sync_orders"),

    path('get_device', GetDevice.as_view(), name="get_device"),
    path('delete_device', DeleteDevice.as_view(), name="delete_device"),

    path('query', QueryUser.as_view(), name="query"),
    path('query_one_user', QueryOneUser.as_view(), name="query_one_user"),
    path('upload_flow', UploadFlow.as_view(), name="upload_flow"),
    path('check_user_status', CheckUserStatus.as_view(), name="check_user_status"),
    path('statistics', Statistics.as_view(), name="statistics"),
    # path('sync_user', SyncUser.as_view(), name="sync_user"),
    path('clear_advertising_count', ClearAdvertisingCount.as_view(), name="clear_advertising_count"),

    path('verify_share_code', VerifyShareCode.as_view(), name="verify_share_code"),
    path('del_device', DelDevice.as_view(), name="del_device"),
    # path('check_user', CheckUser.as_view(), name="check_user"),

    path('sync_single_user', SyncSingleUser.as_view(), name="sync_single_user"),

    path('qr_code_login', QrCodeLogin.as_view(), name="check_qr_code"),
    path('qr_code', QrCode.as_view(), name="qr_code"),
    path('feed_back', Feedback.as_view(), name="feed_back"),
    path('del_temp_user', DelTempUser.as_view(), name="del_temp_user"),

    path('test_hello', TestHello.as_view(), name="test_hello"),
    path('share_task', ShareTask.as_view(), name="share_task"),
    path('share_task_status', ShareTaskStatus.as_view(), name="share_task_status"),
    path('receive_award', ReceiveAward.as_view(), name="receive_award"),
    path('query_user_uid', QueryUserUid.as_view(), name="query_user_uid"),
    path('add_device_token', AddDeviceToken.as_view(), name="add_device_token"),

    # 检测用户登录
    path('check_login_data', CheckLoginData.as_view(), name="check_login_data"),

    # 检测绑定用户
    path('check_binding', CheckBinding.as_view(), name="check_binding"),

]
