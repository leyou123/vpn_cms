from pymongo import MongoClient

mongodb_link = MongoClient('mongodb://root:leyou2021@mongodb.9527.click:27017/').vpn_cms


if __name__ == '__main__':


    datas = mongodb_link.orders_request.find()
    user_id = "310000886306185"
    for data in datas:
        # print(data)
        unified_receipt = data.get("unified_receipt","")


        if unified_receipt:
            orders = unified_receipt["latest_receipt_info"]
            for order in orders:
                order_id = order["transaction_id"]

                if order_id == user_id:
                    print(data)
