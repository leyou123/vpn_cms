import qrcode
from vpn_cms.settings import URL, QR_CODE_PATH
import json

def create_qrcode(data):
    img_path = f'{QR_CODE_PATH}{data}.png'
    url = f"{URL}/media/qrcode/{data}.png"
    # 实例化QRCode生成qr对象
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4
    )
    # 传入数据
    json_data = {'code':data}
    qr.add_data(json.dumps(json_data))
    qr.make(fit=True)
    # 生成二维码
    img = qr.make_image()
    # 保存二维码
    img.save(img_path)
    # img.show()
    return url
