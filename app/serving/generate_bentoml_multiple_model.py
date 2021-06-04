import onnx
import sys

sys.path.append("/workspace")
from app.serving.multiple_model_service import MultiModelService
from app.common.const import get_settings
from app.serving.utils.utils import load_json


settings = get_settings()
service_cfg = load_json(settings.SERVICE_CFG_PATH)['idcard']['resources']
model_path = {}
for cfg in service_cfg:
    model_path[cfg['name']] = cfg['model_path']

# Create a pytorch model service instance
multi_model_service = MultiModelService()

# Pack the newly trained model artifact
boundary_detection_model = onnx.load(f"{model_path['boundary_model']}")
kv_detection_model = onnx.load(f"{model_path['kv_model']}")
recognition_model = onnx.load(f"{model_path['recognition_model']}")
multi_model_service.pack('boundary_detection', boundary_detection_model)
multi_model_service.pack('kv_detection', kv_detection_model)
multi_model_service.pack('recognition', recognition_model)

# Save the prediction service to disk for model serving
saved_path = multi_model_service.save()
print(saved_path)
