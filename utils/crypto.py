from Crypto.Cipher import AES

import base64


class Aescrypt():
    def __init__(self):
        self.encode_ = "UTF-8"
        self.model = AES.MODE_ECB
        self.key = self.add_16("VXH2THdPBsHEp+TY")
        self.aes = AES.new(self.key, self.model)  # 创建一个aes对象

    def add_16(self, par):
        par = par.encode(self.encode_)
        while len(par) % 16 != 0:
            par += b'\x00'
        return par

    def aesencrypt(self, text):
        text = self.add_16(text)
        self.encrypt_text = self.aes.encrypt(text)
        return base64.encodebytes(self.encrypt_text).decode().strip()

    def aesdecrypt(self, text):
        text = base64.decodebytes(text.encode(self.encode_))
        self.decrypt_text = self.aes.decrypt(text)
        return self.decrypt_text.decode(self.encode_).strip('\0')


if __name__ == '__main__':



    aes = Aescrypt()
    # test = aes.aesencrypt("123123")
    # print(test)
    test1 = "0YQj64k2opV1P2cWWQX9MrxgX3p7rAk1MAoEKN+TquG0ZNTnBBZPOHhc5CbMOiuqj4uL4uOjM5y6z9XjGRd8kI9pNgFRSPZuYP9vFmA3g9wwdVlhvzsWCnnOFs6xDSgWnHU7bDgxKc1ox8K3ekfLOVTbjA6PpXL2kJ0btmamMxE="

    # res1 = aes.aesdecrypt("hfarCXmT/di7kOMWG2znSg==")
    res1 = aes.aesdecrypt(test1)
    print(res1)