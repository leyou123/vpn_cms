import requests
import json
from vpn_cms.settings import REFRESH_TOKEN


#
# def refresh_token():
#     headers = {"Content-Type": "application/x-www-form-urlencoded"}
#     grant_type = "authorization_code"
#     code = "4/0AY0e-g7_LVUm8X79inXPXBIoowSzjM3JfCprSndwP2LZkleZAzL9Y6Vw9Zn2NQ0FMNVrKw"
#     redirect_uri = "https://9527.click"
#     data = {
#
#         "grant_type": grant_type,
#         "code": code,
#         "client_id": CLIENT_ID,
#         "client_secret": CLIENT_SECRET,
#         "redirect_uri": redirect_uri
#     }
#     reponse = requests.post(TOKEN_URL, headers=headers, data=data)
#     print(reponse.status_code)
#     print(reponse.text)
#     if reponse.status_code == 200:
#         datas = json.loads(reponse.text)
#         refresh_token = datas.get("refresh_token", "")
#         return refresh_token
#     return None



def create_token(datas):
    """
    google 刷新令牌接口
    :return:
    """
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": datas.grant_type,
        "client_id": datas.client_id,
        "client_secret": datas.client_secret,
        "refresh_token": datas.refresh_token
    }
    reponse = requests.post(datas.token_url, headers=headers, data=data)
    # print(reponse.status_code)
    # print(reponse.text)

    if reponse.status_code == 200:
        datas = json.loads(reponse.text)
        access_token = datas.get("access_token", "")
        header = {"Authorization": 'Bearer ' + access_token}

        return header

    return None

if __name__ == '__main__':
    create_token()