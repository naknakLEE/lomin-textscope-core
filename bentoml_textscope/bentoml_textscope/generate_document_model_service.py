import os
import cv2
import torch
import shutil
import torchvision

from os import path
from lovit.crypto.solver import pth_solver

from bentoml_textscope.document_model_service import DocumentModelService
from bentoml_textscope.utils.debugging import profiling
from bentoml_textscope.common.const import get_settings
from bentoml_textscope.utils.utils import load_json, get_encrypted_model_path


settings = get_settings()
service_cfg = load_json(settings.SERVICE_CFG_PATH)["document"]["resources"]
model_path = {}
for cfg in service_cfg:
    model_path[cfg["name"]] = path.join(
        settings.BASE_PATH, settings.INFERENCE_SERVER_APP_NAME, cfg["model_path"]
    )

document_model_service = DocumentModelService()

detection_model = torch.jit.load(f"{model_path['detection_model']}")
recognition_model = torch.jit.load(f"{model_path['recognition_model']}")
document_model_service.pack("detection", detection_model)
document_model_service.pack("recognition", recognition_model)
document_model_service.set_version("v1")

service_path = f"{settings.BASE_PATH}/{settings.INFERENCE_SERVER_APP_NAME}/DocumentModelService"
# shutil.rmtree(service_path)
os.makedirs(service_path, exist_ok=True)
document_model_service.save_to_dir(service_path, version="v1")


if settings.DECIPHER:
    model_path = get_encrypted_model_path(model_path["detection_model"])
    saved_file = pth_solver(model_path, settings.CRYPTO_KEY)
    detection_model = torch.jit.load(saved_file)
    model_path = get_encrypted_model_path(model_path["recognition_model"])
    saved_file = pth_solver(model_path, settings.CRYPTO_KEY)
    recognition_model = torch.jit.load(saved_file)

image_path = "../others/assets/basic_cert_update/IMG_5073.jpg"
if settings.OCR_DEBUGGING is not None:
    path = f"{settings.BASE_PATH}/{image_path}"
    # img = PIL.Image.open(image_dir)
    img = cv2.imread(path)

if settings.OCR_DEBUGGING == "base":
    document_model_service.document_ocr(img)
elif settings.OCR_DEBUGGING == "profiling":
    profiling(
        model_service=document_model_service,
        img=img,
        profiling_tool="pyinstrument",
        inference_function_name="document_ocr",
    )
