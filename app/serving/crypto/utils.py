import os

from cryptography.fernet import Fernet
from app.serving.crypto.crypto import Crypto

FILE_REGEXP_BASE = r"[A-Za-z0-9_-]+\."


def encrypt_file(path, key=None, prefix="enc", save_key=False, remove=False):
    dir_path, filename = os.path.split(path)
    if len(filename) > len(prefix) and filename[: len(prefix)] == prefix:
        return

    if key == None:
        key = Fernet.generate_key()
        print(f"Generated Key : {key}")

    c = Crypto()
    with open(path, "rb") as f:
        data = f.read()
    encrypted, key = c.encrypt(data, key)

    out_path = os.path.join(dir_path, prefix + filename)
    with open(out_path, "wb") as f:
        f.write(encrypted)

    # Save key only when it is not provided
    if save_key:
        with open(out_path + ".key", "wb") as f:
            f.write(key)

    if remove:
        os.remove(path)


def encrypt_dir(path, key=None, prefix="enc_", filter=None, remove=False):
    filenames = os.listdir(path)
    for filename in filenames:
        file_path = os.path.join(path, filename)
        # print("\033[95m" + f"{file_path}" + "\033[m")
        if os.path.isdir(file_path):
            encrypt_dir(file_path, key=key, prefix=prefix, filter=filter, remove=remove)
        elif filter == None or filter.search(filename) != None:
            encrypt_file(file_path, key, prefix=prefix, remove=remove)


def check_target(name, targets):
    for target in targets:
        if target in name:
            return True

    return False
