import onnx
import sys
from os import path

sys.path.append("/workspace")
from app.serving.multiple_model_service import MultiModelService
from app.common.const import get_settings
from app.serving.utils.utils import load_json


settings = get_settings()
service_cfg = load_json(settings.SERVICE_CFG_PATH)["idcard"]["resources"]
model_path = {}
for cfg in service_cfg:
    model_path[cfg["name"]] = path.join(settings.BASE_PATH, cfg["model_path"])


# Create a pytorch model service instance
multi_model_service = MultiModelService()

# Pack the newly trained model artifact
boundary_detection_model = onnx.load(f"{model_path['boundary_model']}")
kv_detection_model = onnx.load(f"{model_path['kv_model']}")
recognition_model = onnx.load(f"{model_path['recognition_model']}")
multi_model_service.pack("boundary_detection", boundary_detection_model)
multi_model_service.pack("kv_detection", kv_detection_model)
multi_model_service.pack("recognition", recognition_model)
# multi_model_service.set_version("2021-06.textscope")

# Save the prediction service to disk for model serving
multi_model_service.save()
# multi_model_service.save_to_dir('/root/bentoml/repository/MultiModelService')


# import numpy as np
# import cv2
# img = np.expand_dims(cv2.imread("/workspace/others/assets/000000000000000IMG_4831.jpg"), axis=0)
# multi_model_service.inference(img)
