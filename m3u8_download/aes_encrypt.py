# -*- coding:utf-8 -*-
import base64
import hashlib
from Crypto import Random
from Crypto.Cipher import AES
# change  ...\Python37\Lib\site-packages\crypto to  ...\Python37\Lib\site-packages\Crypto

class AESCipher(object):

    def __init__(self, key): 
        self.bs = 16
        self.key = hashlib.sha256(key.encode()).digest()

    def encrypt(self, raw):
        raw = self._pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw))

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')

    def _pad(self, s):
        return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)

    @staticmethod
    def _unpad(s):
        return s[:-ord(s[len(s)-1:])]


def encrypt(data, key, iv=None):
    """
    data : type bytes
    key:   type bytes
    return type: bytes
    """
    bs = AES.block_size
    pad = lambda s: s + ((bs - len(s) % bs) * chr(bs - len(s) % bs)).encode()
    if (not iv):
        iv = Random.new().read(bs)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    data = cipher.encrypt(pad(data))
    data = iv + data
    return (data)

def decrypt(data, key, iv=None):
    bs = AES.block_size
    if len(data) <= bs:
        return (data)
    #unpad = lambda s : s[0:-ord(s[-1])]
    unpad = lambda s : s[0:-(s[-1])]
    if (not iv):
        iv = data[:bs]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    data  = unpad(cipher.decrypt(data[bs:]))
    return (data)

def ts_dec():
    ts_file = open("v.f30.ts", "rb")
    data = ts_file.read()
    ts_file.close()
    key = b'\xEF\x46\xC9\xB4\x80\x62\x41\x2E\x72\xF7\xA0\x8E\x15\x2D\x90\x58'
    iv = b'\x00'*16
    
    decrypt_data = decrypt(data, key, iv)
    ts_out = "ts_out.ts"
    out_file = open(ts_out, "wb")
    out_file.write(decrypt_data)
    out_file.close()
    
if __name__ == "__main__":
    '''
    key = 
    aes = AESCipher("12230000000000000000000000000000")
    text = b'abcdefg'
    print (aes.encrypt(text))
    '''
    data = 'd437814d9185a290af20514d9341b710'
    password = '78f40f2c57eee727a4be179049cecf89' #16,24,32位长的密码
    password = password.encode('utf-8')
    data = data.encode('utf-8')
    encrypt_data = encrypt(data, password)
    encrypt_data = base64.b64encode(encrypt_data)
    print ('encrypt_data:', encrypt_data)
    print ('encrypt_data len:', len(encrypt_data))
 
 
    encrypt_data = base64.b64decode(encrypt_data)
    decrypt_data = decrypt(encrypt_data, password)
    print ('decrypt_data:', decrypt_data)    