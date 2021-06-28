import torch
import torchvision
import onnx
from os import path

# from app.serving.multiple_model_service import MultiModelService
from app.serving.document import MultiModelService
from app.common.const import get_settings
from app.serving.utils.utils import load_json


settings = get_settings()
print("\033[95m" + f"{load_json(settings.SERVICE_CFG_PATH)}" + "\033[m")
service_cfg = load_json(settings.SERVICE_CFG_PATH)["document"]["resources"]
model_path = {}
for cfg in service_cfg:
    model_path[cfg["name"]] = path.join(settings.BASE_PATH, cfg["model_path"])


multi_model_service = MultiModelService()

detection_model = torch.jit.load(f"{model_path['detection_model']}")
recognition_model = onnx.load(f"{model_path['recognition_model']}")
multi_model_service.pack("detection", detection_model)
multi_model_service.pack("recognition", recognition_model)

multi_model_service.save()
