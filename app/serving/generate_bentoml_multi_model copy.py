import torch
from multi_model_service import MultiModelService
import onnx


# Create a iris classifier service instance
multi_model_service = MultiModelService()

# Pack the newly trained model artifact
# traced_net = torch.jit.load("/workspace/app/serving/mask_rcnn.pt")
boundary_detection_model = onnx.load("boundary_detection_model.onnx")
kv_detection_model = onnx.load("kv_detection_model.onnx")
recognition_model = onnx.load("recognition_model.onnx")
multi_model_service.pack('boundary_detection', boundary_detection_model)
multi_model_service.pack('kv_detection', kv_detection_model)
multi_model_service.pack('recognition', recognition_model)

# Save the prediction service to disk for model serving
saved_path = multi_model_service.save()