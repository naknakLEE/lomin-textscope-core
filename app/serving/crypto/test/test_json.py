from cryptography.fernet import Fernet
import os
import json

BASE_DIR = "crypto/test/sample"
SAMPLE_FILE = "sample"
EXTENSION = "json"

PATH = os.path.join(BASE_DIR, f"{SAMPLE_FILE}.{EXTENSION}")

if __name__ == "__main__":
    key = Fernet.generate_key()

    with open(PATH, "rb") as f:
        sample = f.read()

    with open(PATH, "rb") as f:
        sample_json = json.load(f)

    fernet = Fernet(key)

    encrypted = fernet.encrypt(sample)

    with open(f"{PATH}.enc", "wb") as f:
        f.write(encrypted)
    with open(f"{PATH}.enc", "rb") as f:
        encrypted = f.read()

    decrypted = fernet.decrypt(encrypted)

    assert json.loads(decrypted.decode("utf-8")) == json.loads(sample.decode("utf-8"))
    print("Done")
