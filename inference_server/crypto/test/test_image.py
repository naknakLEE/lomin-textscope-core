from cryptography.fernet import Fernet
import os
import json
from PIL import Image, ImageChops
import io

BASE_DIR = "crypto/test/sample"
SAMPLE_FILE = "sample"
EXTENSION = "png"

PATH = os.path.join(BASE_DIR, f"{SAMPLE_FILE}.{EXTENSION}")

if __name__ == "__main__":
    key = Fernet.generate_key()

    with open(PATH, "rb") as f:
        sample = f.read()

    fernet = Fernet(key)

    encrypted = fernet.encrypt(sample)

    with open(f"{PATH}.enc", "wb") as f:
        f.write(encrypted)
    with open(f"{PATH}.enc", "rb") as f:
        encrypted = f.read()

    decrypted = fernet.decrypt(encrypted)

    io_1 = io.BytesIO(sample)
    io_2 = io.BytesIO(decrypted)
    
    image_1 = Image.open(io_1)
    image_2 = Image.open(io_2)

    image_2.save(os.path.join(BASE_DIR, f"dec_{SAMPLE_FILE}.{EXTENSION}"))

    diff = ImageChops.difference(image_1, image_2)
    assert not diff.getbbox()
    print("Done")
