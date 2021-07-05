import torch
import torchvision
import numpy as np
import PIL

from os import path

from inference_server.common.const import get_settings
from inference_server.utils.utils import load_json
from inference_server.crypto.utils import encrypt_dir
from inference_server.crypto.crypto import Crypto

settings = get_settings()
service_cfg = load_json(settings.SERVICE_CFG_PATH)["document"]["resources"]
model_path = {}
for cfg in service_cfg:
    model_path[cfg["name"]] = path.join(settings.BASE_PATH, cfg["model_path"])

import os
from inference_server.crypto.decipher import Decipher
from inference_server.crypto.solver import pth_solver

encrypt_path = (
    "/root/bentoml/repository/DocumentModelService/2021-07.textscope/DocumentModelService/artifacts"
)
CRYPTO_KEY = b"s7smOzlG-OWQiMA3RIysQGa9OOgNTqbVvSghCp2svBQ="
CRYPTO_PREFIX = "enc_"


# def decrypt_file(file_path):
#     decipher = Decipher(CRYPTO_KEY, CRYPTO_PREFIX)
#     base, name = os.path.split(file_path)
#     en_file_path = os.path.join(base, name)
#     decrypted = decipher(en_file_path)
#     return decrypted


# # result = decrypt_file(encrypt_path)
# result = pth_solver(f"{encrypt_path}/lo_general_200702_skjung_001_rec.ts", CRYPTO_KEY)
# print("\033[95m" + f"{result}" + "\033[m")

# detection_model = torch.jit.load(f"{model_path['detection_model']}")


# image_dir = f"{settings.BASE_PATH}/others/assets/basic_cert2.jpg"
# img = PIL.Image.open(image_dir)
# img = np.array(img)
# img = np.transpose(img, (2, 0, 1))
# img = torch.from_numpy(img.copy())
# with torch.no_grad():
#     reuslt = detection_model(img)
# print("\033[95m" + f"{reuslt[0].shape}" + "\033[m")

# exit()


crypto = Crypto()
# key = crypto.generate_key()
key = CRYPTO_KEY
print("\033[95m" + f"{key}" + "\033[m")
encrypt_dir(encrypt_path, key=key, prefix=CRYPTO_PREFIX, filter=None, remove=True)
exit()

detection_model = torch.jit.load(f"{model_path['detection_model']}")


image_dir = f"{settings.BASE_PATH}/others/assets/basic_cert2.jpg"
img = PIL.Image.open(image_dir)
img = np.array(img)
img = np.transpose(img, (2, 0, 1))
img = torch.from_numpy(img.copy())
with torch.no_grad():
    reuslt = detection_model(img)
print("\033[95m" + f"{reuslt[0].shape}" + "\033[m")
