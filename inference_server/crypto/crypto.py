from cryptography.fernet import Fernet
from itertools import zip_longest
import argparse
import os

class Crypto():
    def __init__(self):
        super().__init__()

    def generate_key(self):
        return Fernet.generate_key()
        
    def encrypt(self, data, key=None):
        if key == None:
            key = self.generate_key()

        fernet = Fernet(key)
        encrypted = fernet.encrypt(data)

        return (encrypted, key)

    def decrypt(self, data, key):
        fernet = Fernet(key)
        decrypted = fernet.decrypt(data)

        return decrypted

    # Not working for large file currently
    def validate(self, data1, data2):
        for line1, line2 in zip_longest(data, decrypted, fillvalue=None):
            if line1 != line2:
                return False
        
        return True
