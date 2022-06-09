import re
import random
import json
import pymysql
import hashlib
import geoip2.database
from random import Random
from vpn_cms.settings import EMAIL_FROM
from django_redis import get_redis_connection
from django.core.mail import EmailMultiAlternatives

db1 = get_redis_connection('DB1')


def str_as_md5(data):
    data_str = data.encode("utf-8")
    m = hashlib.md5()
    m.update(data_str)
    return m.hexdigest()



def str_as_md5_short(data):
    data_str = data.encode("utf-8")
    m = hashlib.md5()
    m.update(data_str)
    res = m.hexdigest()[8: -8].upper()
    return res


def random_str(random_length=6):
    # 生成随机字符串
    str = ''
    # 生成字符串的可选字符串
    chars = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789'
    length = len(chars) - 1
    random = Random()
    for i in range(random_length):
        str += chars[random.randint(0, length)]
    return str



def validateEmail(email):
    if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", email) != None:
        return True
    else:
        return False




# 发送邮件
def send_email(email, uid, app_name):
    # 定义邮件内容:

    code = ""
    redis_status = False
    for i in range(10):

        code = random.randint(100000, 999999)
        res = db1.exists(code)
        if res:
            continue
        else:
            data = {
                "email": email,
                "code":code
            }
            res = db1.set(uid, json.dumps(data), ex=60 * 60)
            if res:
                redis_status = True
                break
            else:
                continue

    if not code or not redis_status:
        return False

    email_title = f"{app_name} Account"

    msg_html = '''<!DOCTYPE html>
    <html>
    <meta charset="UTF-8">
    <head>
    <title></title>
    </head>
    <body>
        <div>
             <p>Dear {app_name} user, please use this code to verify：</p>
             <span style="color:blue;font-size:24px;">{code}</span>
             <p>The code will expire in 60 minutes. You can only use it once.</p>
             <p>No need to reply this message.</p>
        </div>
    </body>
    </html>
    '''.format(app_name=app_name, code=code)


    # 使用Django内置函数完成邮件发送。四个参数：主题，邮件内容，从哪里发，接受者list

    msg = EmailMultiAlternatives(email_title, msg_html, EMAIL_FROM, [email])
    msg.attach_alternative(msg_html, "text/html")
    send_status = msg.send()
    if not send_status:
        return False
    return True


def unbinding_send_email(email, uid, app_name):
    # 定义邮件内容:

    email_title = f"{app_name} Account"

    msg_html = '''<!DOCTYPE html>
    <html>
    <meta charset="UTF-8">
    <head>
    <title></title>
    </head>
    <body>
        <div>
             <p>Your {app_name} account uid: {uid} has been disassociated from the E-mail.</p>
             <p>If it is not your own operation, please note the account security. For example, use a more safe password.</p>
        </div>
    </body>
    </html>
    '''.format(app_name=app_name, uid=uid)


    # 使用Django内置函数完成邮件发送。四个参数：主题，邮件内容，从哪里发，接受者list

    msg = EmailMultiAlternatives(email_title, msg_html, EMAIL_FROM, [email])
    msg.attach_alternative(msg_html, "text/html")
    send_status = msg.send()
    if not send_status:
        return False
    return True



class GeoIp(object):

    @classmethod
    def get_info(cls, ip):
        """
            获取地理位置信息
        """
        country = ""
        region = ""
        try:
            reader = geoip2.database.Reader('./GeoLite2-City.mmdb')
            response = reader.city(ip)
            country = response.registered_country.names.get("zh-CN", "")
            region = response.subdivisions[0].names.get("zh-CN", "")
        except Exception as e:
            print(e)
        return {"region": region, "country": country}



# class Session(object):
#     # 初始化对象，产生一个mysql连接
#     def __init__(self):
#         self._ip = OLD_HOST
#         self._user = "root"
#         self._passwd = "Leyou2020"
#         self._db = "vpn1"
#         self._port = 3306
#         self._charset = 'utf8'
#         self._conn = None
#         self._cursor = None
#         try:
#             self._conn = pymysql.connect(
#                 host=self._ip,
#                 user=self._user,
#                 password=self._passwd,
#                 database=self._db,
#                 charset=self._charset,
#                 port=self._port,
#                 autocommit=True
#             )
#         except Exception as err:
#             format_err = f"ERROR - {self._ip} session init failed: {err}" + "\n"
#             raise Exception(format_err)
#
#     def query(self, sql):
#         """
#         :param sql: 查询语句
#         :return: result-查询结果;
#         """
#         cursor = self._conn.cursor(pymysql.cursors.DictCursor)
#         try:
#             result = []
#             rows = cursor.execute(sql)
#             if rows > 0:
#                 sql_result = cursor.fetchall()
#                 # result = [list(i) for i in sql_result]
#                 result = sql_result
#             cursor.close()
#             return result
#         except Exception as err:
#             format_err = f"ERROR - {self._ip} query failed: {err} - {sql}" + "\n"
#             raise Exception(format_err)
#         finally:
#             cursor.close()