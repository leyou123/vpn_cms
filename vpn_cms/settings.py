"""
Django settings for vpn_cms project.


For more information on this file, see

For the full list of settings and their values, see
"""

from pathlib import Path
import sys
import os
from pymongo import MongoClient


# Build paths inside the project like this: BASE_DIR / 'subdir'.
# BASE_DIR = Path(__file__).resolve().parent.parent
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, os.path.join(BASE_DIR, 'apps'))

# Quick-start development settings - unsuitable for production

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '9lr#)=@(9zxs@8sl&@*74_xy@0ow#304kh1hny#t8a_j$nl5ky'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'apps.manage.apps.ManageConfig',
    'apps.users.apps.UsersConfig',
    'apps.nodes.apps.NodesConfig',
    'apps.orders.apps.OrderConfig',
    'apps.report.apps.ReportConfig',
    'apps.timersched.apps.TimerschedConfig',
    'crispy_forms',
    'xadmin',
    'django_apscheduler',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    # 'utils.frequency_intercept.RequestBlockingMiddleware',
    # 'utils.frequency_intercept.OauthProcessMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'vpn_cms.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'vpn_cms.wsgi.application'


AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization

LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = False

# Static files (CSS, JavaScript, Images)

STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(BASE_DIR,'/static/')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static')
]


MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

HOST = "54.183.220.55"

MASTER_HOST = HOST
MYSQL_PASSWORD = "Leyou2020"

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'vpn',
        'HOST': MASTER_HOST,
        'PORT': 3306,
        'USER': 'root',
        'PASSWORD': MYSQL_PASSWORD,
        'TEST': {
            'CHARSET': 'utf8',
            'COLLATION': 'utf8_general_ci',
        }

    }
}

HOME_URL = "https://9527.click"
URL = "http://13.56.18.206"


# 节点Redis
NODE_REDIS_HOST = "13.52.248.95"
NODE_REDIS_PASSWORD = "redis_!@node2021"
NODE_REDIS_PORT = 6379


# mongodb配置
MONGODB_HOST = "13.52.97.173"
MONGODB_PORT = '27017'
MONGODB_PASSWORD = "leyou2021"

mongodb = MongoClient(f'mongodb://root:{MONGODB_PASSWORD}@{MONGODB_HOST}:{MONGODB_PORT}/').vpn_cms

# 节点配置
NODE_HOST = 'https://nodes.9527.click'

# #  ios支付回调参数信息
# IOS_BJ_PASSWORD = '108c6f6660464f9ebd9d1889e2241c34'
# IOS_QD_PASSWORD = 'b3d2a412d8a845218c3ef9192f060c9a'
# IOS_CS_PASSWORD = '108c6f6660464f9ebd9d1889e2241c34'


# IOS_URL_BUY = 'https://buy.itunes.apple.com/verifyReceipt'  # # 正式环境
# IOS_URL_SANDBOX = 'https://sandbox.itunes.apple.com/verifyReceipt'
NODE_MAX = 30

# redis配置
REDIS_HOST = "3.101.19.69"
REDIS_PORT = '6379'
REDIS_PASSWORD = "leyou2020"
# redis过期时间
EX_TIME = 60 * 60

# 二维码配置
QR_CODE_PATH = f'{BASE_DIR}/media/qrcode/'
HTML_PATH = f'{BASE_DIR}/media/html/'

# google配置
GOOGLE_API_URL = "https://androidpublisher.googleapis.com/androidpublisher/v3/applications"

# google 刷新token配置
TOKEN_URL = "https://accounts.google.com/o/oauth2/token"
GRANT_TYPE = "refresh_token"
CLIENT_ID = "191408343277-mak6ta61q50d58usdro5ml8gfas3n64h.apps.googleusercontent.com"
CLIENT_SECRET = "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"
REFRESH_TOKEN = "1//0dhgIrfCghpMKCgYIARAAGA0SNwF-L9IrYOT76O7uHdJpy_0Svdik0wpA8yyft37S8HG_H3FuJV2m8ugXguWz8jEZcfrd2wsz2Fg"

# 邮件发送设置
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_USE_SSL = True
EMAIL_PORT = 465

# google邮箱配置
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'vpnletgo@gmail.com'
EMAIL_HOST_PASSWORD = 'ergnkkqktsifrzfw'
EMAIL_FROM = EMAIL_HOST_USER

# palpay 支付秘钥
# 测试
# paypal_url = "https://api-m.sandbox.paypal.com"
# 正式
paypal_url = "https://api-m.paypal.com"
# paypal沙盒账户
# client_id = "AS4dlqmgLF_Yk33iVZL72QrrlBpeurlcNplyZV7pf54Y8ES3_BmSCKmoo2aLVbdQ3D7N0X9gisl8lYUF"
# client_secret = "EALB2ij_TSng82vmWMAA8PDA9XtTiZImTrx9lfBGnK_DAB5FwN47ubf4RNanMFO4y_kHHl9Ds6MmU54H"
# paypal正式账户
client_id = "AeFpA8QSci9rroXvB15tAKdyZ4JkuY2Oed54pPgtwMOYUVllI99-hpe9bwiqPpUo8j3fG4ynTr2lQl-N"
client_secret = "ELS2XlAMoL74DSFTtrS8IPY7giOVqvLBx1uEn5p3gVswJQXGPCx3n7zh073pjhiX_8nAGPXeN2-Wc3mI"

USER_KEY = "leyou2021"
# redis缓存
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        # 有密码
        'LOCATION': f'redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0',
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    },
    'DB1': {
        #
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/1',
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    },
    'DB2': {
        # 节点列表
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/2',
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    },

    'DB3': {
        # 节点列表
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/3',
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    },

    'DB4': {
        # 配置缓存
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/4',
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    },

    'DB5': {
        # 登录缓存
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/5',
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    },

    'DB6': {
        # 设备缓存
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/6',
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    },

    'DB10': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/10',
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    },
    'DB11': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/11',
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    },
    'DB12': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/12',
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    },
    'DB13': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/13',
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    },
}
