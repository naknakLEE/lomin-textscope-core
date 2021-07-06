import os
import numpy as np
import PIL
import cv2
import torch
import torchvision

from os import path

from inference_server.document_model_service import DocumentModelService
from inference_server.common.const import get_settings
from inference_server.utils.utils import load_json


settings = get_settings()
service_cfg = load_json(settings.SERVICE_CFG_PATH)["document"]["resources"]
model_path = {}
for cfg in service_cfg:
    model_path[cfg["name"]] = path.join(settings.BASE_PATH, cfg["model_path"])

document_model_service = DocumentModelService()

detection_model = torch.jit.load(f"{model_path['detection_model']}")
recognition_model = torch.jit.load(f"{model_path['recognition_model']}")
document_model_service.pack("detection", detection_model)
document_model_service.pack("recognition", recognition_model)
document_model_service.set_version("2021-07.textscope")

document_model_service.save()


############################ for debugging ############################

# image_dir = f"{settings.BASE_PATH}/others/assets/basic_cert2.jpg"
# img = PIL.Image.open(image_dir)
# img = np.array(img)
# document_model_service.document_ocr(img)


############################ for encrypted model ############################

# def get_encrypted_model_path(path):
#     split_path = path.split("/")
#     model_path = os.path.join("/", *split_path[:-1], f"{settings.CRYPTO_PREFIX}{split_path[-1]}")
#     return model_path

# if settings.DECIPHER:
#     from lovit.crypto.solver import pth_solver

#     model_path = get_encrypted_model_path(model_path["detection_model"])
#     saved_file = pth_solver(model_path, settings.CRYPTO_KEY)
#     detection_model = torch.jit.load(saved_file)
#     model_path = get_encrypted_model_path(model_path["recognition_model"])
#     saved_file = pth_solver(model_path, settings.CRYPTO_KEY)
#     recognition_model = torch.jit.load(saved_file)
