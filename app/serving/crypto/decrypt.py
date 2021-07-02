import os
from app.serving.crypto.decipher import Decipher

CRYPTO_KEY = b"s7smOzlG-OWQiMA3RIysQGa9OOgNTqbVvSghCp2svBQ="
CRYPTO_PREFIX = ""


def decrypt_file(self, file_path):
    decipher = Decipher(CRYPTO_KEY, CRYPTO_PREFIX)
    base, name = os.path.split(file_path)
    en_file_path = os.path.join(base, CRYPTO_PREFIX + name)
    decrypted = decipher(en_file_path)
    return decrypted
