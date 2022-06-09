import requests
import json
import base64
from requests.auth import HTTPBasicAuth

paypal_url = "https://api-m.sandbox.paypal.com"
live_url = "https://api-m.paypal.com"


def create_token():
    """
    paypal 令牌接口
    :return:
    """
    paypal_url = "https://api-m.sandbox.paypal.com"
    live_url = "https://api-m.paypal.com"
    client_id = "AS4dlqmgLF_Yk33iVZL72QrrlBpeurlcNplyZV7pf54Y8ES3_BmSCKmoo2aLVbdQ3D7N0X9gisl8lYUF"
    client_secret = "EALB2ij_TSng82vmWMAA8PDA9XtTiZImTrx9lfBGnK_DAB5FwN47ubf4RNanMFO4y_kHHl9Ds6MmU54H"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    data = {
        "grant_type": "client_credentials"
    }

    url = f"{paypal_url}/v1/oauth2/token"

    reponse = requests.post(url, headers=headers, data=data, auth=HTTPBasicAuth(client_id, client_secret))

    if reponse.status_code == 200:
        return json.loads(reponse.text)
    # print(reponse.status_code)
    # print(reponse.text)
    return None


def create_products(access_token):
    """
        创建商品
    """

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + access_token
        # "PayPal-Request-Id":"PRODUCT-18062020-004"
    }

    data = {
        "name": "vpn shop",
        "description": "vpn shop",
        "type": "SERVICE",
        "category": "SOFTWARE",
        "image_url": "https://example.com/streaming.jpg",
        "home_url": "https://example.com/home"
    }

    # url = f"{paypal_url}/v1/catalogs/products"
    url = "https://api-m.sandbox.paypal.com/v1/catalogs/products"
    reponse = requests.post(url, headers=headers, data=json.dumps(data))
    if reponse.status_code == 200:
        return json.loads(reponse.text)
    print(reponse.status_code)
    print(reponse.text)
    return None


def create_plans(product_id,access_token):
    """
    创建计划
    :param product_id:
    :param access_token:
    :return:
    """

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + access_token,
        'Accept': 'application/json'
        # "PayPal-Request-Id":"PRODUCT-18062020-004"
    }

    data = {
      "product_id": product_id,         # 产品ID
      "name": "Basic Plan",             # 计划名
      "description": "Basic plan",      # 描述
      "billing_cycles": [               # 用于试用计费和常规计费的计费周期数组。 一个计划最多只能有两个试验周期和一个常规周期。
        {
          "frequency": {                 # 此计费周期的频率详细信息
            "interval_unit": "MONTH",    # 订阅收费或计费的时间间隔。  1.DAY 365 2.WEEK  52  3.MONTH  12 4.YEAR 1
            "interval_count": 1          # 对订阅者计费的间隔数。 例如，如果interval_unit为DAY，且interval_count为2，则订阅将每两天计费一次。 下表列出了每个interval_unit允许的interval_count的最大值
          },
          "tenure_type": "TRIAL",         # 计费周期的保留期类型。 如果计划有试验周期，每个计划只允许2个试验周期。  1.REGULAR 定期计费周期 2. TRIAL 试用计费周期
          "sequence": 1,                  # 此周期在其他计费周期中运行的顺序。 例如，试用计费周期的序列为   1.而常规计费周期的序列为 2.因此试用周期在常规周期之前运行
          "total_cycles": 1               # 执行此计费周期的次数。 试用计费周期只能执行有限次(total_cycles的值在1到999之间)。 常规计费周期可以执行无限次(total_cycles的值为0)或有限次(total_cycles的值在1到999之间)
        },
        {
          "frequency": {                 # 此计费周期的频率详细信息
            "interval_unit": "MONTH",    # 订阅收费或计费的时间间隔。  1.DAY 365 2.WEEK  52  3.MONTH  12 4.YEAR 1
            "interval_count": 1
          },
          "tenure_type": "REGULAR",      # 计费周期的保留期类型。 如果计划有试验周期，每个计划只允许2个试验周期。  1.REGULAR 定期计费周期 2. TRIAL 试用计费周期
          "sequence": 2,                 #  此周期在其他计费周期中运行的顺序。 例如，试用计费周期的序列为   1.而常规计费周期的序列为 2.因此试用周期在常规周期之前运行
          "total_cycles": 12,            # 执行此计费周期的次数。 试用计费周期只能执行有限次(total_cycles的值在1到999之间)。 常规计费周期可以执行无限次(total_cycles的值为0)或有限次(total_cycles的值在1到999之间)
          "pricing_scheme": {            # 定价方案
            "fixed_price": {             # 为认购而收取的固定金额。 对固定金额的更改适用于现有和未来的订阅。 对于现有的订阅，在价格变动后10天内付款不受影响。
              "value": "10",                          # 价格
              "currency_code": "USD"                  # 货币单元
            }
          }
        }
      ],
      "payment_preferences": {                         # 订阅的支付首选项
        "auto_bill_outstanding": True,                 # 是否在下一个计费周期自动对未结算的金额进行计费。
        "setup_fee": {                                 # 服务的初始设置费用
          "value": "10",                               # 价格
          "currency_code": "USD"                       # 货币单元
        },
        "setup_fee_failure_action": "CONTINUE",         #  如果初始设置付款失败，则执行订阅的操作
        "payment_failure_threshold": 3                  # 订阅暂停前的最大付款失败数。 例如，如果payment_failure_threshold为2，则如果连续两次支付失败，订阅将自动更新到SUSPEND状态
      },
      "taxes": {                                        # 税费
        "percentage": "10",                             # 开票金额的税率。
        "inclusive": False                              # 指示税费是否已包含在计费金额中。
      }
    }

    url = "https://api-m.sandbox.paypal.com/v1/billing/plans"
    reponse = requests.post(url, headers=headers, data=json.dumps(data),verify=False)
    if reponse.status_code == 200:
        return json.loads(reponse.text)
    print(reponse.status_code)
    print(reponse.text)
    return None


def activate_products(access_token):
    """
        创建商品
    """

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + access_token
        # "PayPal-Request-Id":"PRODUCT-18062020-004"
    }

    data = {
        "name": "Video Streaming Service",
        "description": "A video streaming service",
        "type": "SERVICE",
        "category": "SOFTWARE",
        "image_url": "https://example.com/streaming.jpg",
        "home_url": "https://example.com/home"
    }

    # url = f"{paypal_url}/v1/catalogs/products"
    url = "https://api-m.sandbox.paypal.com/v1/catalogs/products"
    print(headers)
    reponse = requests.post(url, headers=headers, data=json.dumps(data))
    if reponse.status_code == 200:
        return json.loads(reponse.text)
    print(reponse.status_code)
    print(reponse.text)
    return None


def create_agreements(plan_id,access_token):
    """
        创建协议
    """

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + access_token
    }

    data = {
          "name": "Magazine Subscription",
          "description": "Monthly agreement with a regular monthly payment definition and two-month trial payment definition.",
          "start_date": "2017-12-22T09:13:49Z",
          "plan":
          {
            "id": plan_id
          },
          "payer":
          {
            "payment_method": "paypal"
          },
          "shipping_address":
          {
            "line1": "751235 Stout Drive",
            "line2": "0976249 Elizabeth Court",
            "city": "Quimby",
            "state": "IA",
            "postal_code": "51049",
            "country_code": "US"
          }
        }

    # url = f"{paypal_url}/v1/catalogs/products"
    url = "https://api-m.sandbox.paypal.com/v1/payments/billing-agreements/"
    print(headers)
    reponse = requests.post(url, headers=headers, data=json.dumps(data))
    if reponse.status_code == 200:
        return json.loads(reponse.text)
    print(reponse.status_code)
    print(reponse.text)
    return None


def query_sub(user_id,access_token):
    """
        查询订单
    """

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + access_token
    }

    # url = f"{paypal_url}/v1/catalogs/products"
    url = f"https://api-m.sandbox.paypal.com/v1/billing/subscriptions/{user_id}"
    # print(headers)
    reponse = requests.get(url, headers=headers)
    print(reponse.status_code)
    print(reponse.text)

    if reponse.status_code == 200:
        return json.loads(reponse.text)
    return None


def query_pay(user_id,access_token):
    """
        查询订单
    """

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + access_token
    }

    # url = f"{paypal_url}/v1/catalogs/products"
    url = f"https://api-m.sandbox.paypal.com/v1/billing/subscriptions/{user_id}/capture"
    # print(headers)
    data = {
      "note": "Charging as the balance reached the limit",
      "capture_type": "OUTSTANDING_BALANCE",
      "amount": {
        "currency_code": "USD",
        "value": "11"
      }
    }


    reponse = requests.post(url, headers=headers,data=json.dumps(data))
    print(reponse.status_code)
    print(reponse.text)

    if reponse.status_code == 200:
        return json.loads(reponse.text)
    return None






if __name__ == '__main__':
    # result = create_token()
    # print(result)
    access_token = "A21AAJ8OBvyqXh7A3s0CydRhIWOAJ9wqZBXAGLpH3ScQ-MaoUrkIqQ-MalU6aPRn4l-G98kTcVt_C1fSKlLf0mN8fCWAhUzDQ"
    # create_products(access_token)

    # product_id= "PROD-2KK23503G0166470C"
    # create_plans(product_id,access_token)
    plan_id = "P-1P170782V2312534HMG5OR6I"
    # create_agreements(plan_id,access_token)
    uid = "I-PX82YGUM9NSA"
    user_token = "4TV42809TR454482T"
    # query_sub(uid, access_token)
    # shop_id = "PROD-62H63828SX974921L"

    query_pay(uid, access_token)

    #
    # # access_token = result.get("access_token")
    # create_plans(shop_id,access_token)
