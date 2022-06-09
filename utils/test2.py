import requests

url = "https://cp.pushwoosh.com/json/1.3/getMsgStats"

json_data = {
     "request":{
       "auth": "vcsFgPOX2grNZoWAQpvOJEJI1ANkymDhfwThSRa9YSr5rgJ1KwXx5GBZ5ZKg21tbRkGXdPahfqETeMIDtxKS",
       "application" : "C231C-8A73D"
     }
}

response = requests.post(url=url,json=json_data)


print(response.status_code)
print(response.text)