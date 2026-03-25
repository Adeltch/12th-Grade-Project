__author__ = "Adel Tchernitsky"


from hashlib import md5
from base64 import b64decode, b64encode

from Cryptodome.Cipher import AES
from Cryptodome.Random import get_random_bytes
from Cryptodome.Util.Padding import pad, unpad


KEY = "Hello there! General Kenobi"


class AESCipher:
    def __init__(self):
        self.key = md5(KEY.encode('utf8')).digest()

    def encrypt(self, data):
        """
        return encrypted data
        """
        iv = get_random_bytes(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        if type(data) is str:
            return b64encode(iv + cipher.encrypt(pad(data.encode('utf-8'), AES.block_size)))
        return b64encode(iv + cipher.encrypt(pad(data, AES.block_size)))

    def decrypt(self, data):
        """
        return decrypted data
        """
        raw = b64decode(data)
        cipher = AES.new(self.key, AES.MODE_CBC, raw[:AES.block_size])
        return unpad(cipher.decrypt(raw[AES.block_size:]), AES.block_size)
