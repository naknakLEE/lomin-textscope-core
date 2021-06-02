import onnx
import sys

sys.path.append("/workspace")
from app.serving.multiple_model_service import MultiModelService
from app.common.const import get_settings


settings = get_settings()

# Create a pytorch model service instance
multi_model_service = MultiModelService()

# Pack the newly trained model artifact
boundary_detection_model = onnx.load(f"{settings.BASE_PATH}/assets/id_boundary/1/kb_201027_skkang_002_id_outline_mask_0195000_b1.onnx")
kv_detection_model = onnx.load(f"{settings.BASE_PATH}/assets/id_kv/1/kb_201016_skkang_001_id_kv_0069000_b1.onnx")
recognition_model = onnx.load(f"{settings.BASE_PATH}/assets/recognizer/1/kb_201109_skkang_001_id_rec_0020000_b9.onnx")
multi_model_service.pack('boundary_detection', boundary_detection_model)
multi_model_service.pack('kv_detection', kv_detection_model)
multi_model_service.pack('recognition', recognition_model)

# Save the prediction service to disk for model serving
saved_path = multi_model_service.save()
print(saved_path)
