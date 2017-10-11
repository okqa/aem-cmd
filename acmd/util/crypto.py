# coding: utf-8
import base64

from acmd.compat import AES, Random
from acmd.compat import bytestring, stdstring

IV_BLOCK_SIZE = 16


def parse_prop(prop):
    """ Reads property and outputs tuple (encrypted_password, iv) """
    if not (prop.startswith('{') and prop.endswith('}')):
        raise Exception('Unexpected format of prop {}'.format(prop))
    payload_encoded = prop[1:-1]
    payload = base64.b64decode(payload_encoded)

    iv_bytes = payload[0:IV_BLOCK_SIZE]
    ciphertext_bytes = payload[IV_BLOCK_SIZE:]

    assert type(ciphertext_bytes) == bytes
    assert type(iv_bytes) == bytes

    return ciphertext_bytes, iv_bytes


def encode_prop(ciphertext_bytes, iv_bytes):
    assert type(ciphertext_bytes) == bytes
    assert type(iv_bytes) == bytes
    tmp = iv_bytes + ciphertext_bytes

    payload = base64.b64encode(bytestring(tmp))
    return "{" + stdstring(payload) + "}"


def encrypt_str(iv, key, plaintext):
    """ Takes strings in and is expected to give strings out.
        All binary string conversion is internal only.

        iv: 16 character standard string
        key: bytes array
        plaintext: standard string
    """
    assert type(iv) == bytes
    assert type(key) == bytes
    assert type(plaintext) == str

    codec = AES.new(bytestring(key), AES.MODE_CFB, iv)
    bindata = codec.encrypt(bytestring(plaintext))
    return bindata


def decrypt(iv, key, ciphertext_bytes):
    """ Takes strings in and is expected to give strings out.
        All binary string conversion is internal only. """
    assert type(iv) == bytes
    assert type(key) == bytes
    assert type(ciphertext_bytes) == bytes

    codec = AES.new(bytestring(key), AES.MODE_CFB, bytestring(iv))
    return stdstring(codec.decrypt(ciphertext_bytes))


def generate_iv():
    """ Generate initial vector for encryption
        Returns string of base64
     """
    ret = Random.new().read(IV_BLOCK_SIZE)
    assert type(ret) == bytes
    return ret
