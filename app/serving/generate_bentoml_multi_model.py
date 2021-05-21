import torch
import onnx
from multi_model_service import MultiModelService


# Create a iris classifier service instance
multi_model_service = MultiModelService()

# Pack the newly trained model artifact
# traced_net = torch.jit.load("/workspace/app/serving/mask_rcnn.pt")
# boundary_detection_model = onnx.load("/workspace/app/serving/mobilenetv2-7.onnx")
boundary_detection_model = onnx.load("/workspace/app/serving/boundary.onnx")
kv_detection_model = onnx.load("/workspace/app/serving/kv_detection_model.onnx")
recognition_model = onnx.load("/workspace/app/serving/recognition_model.onnx")
multi_model_service.pack('boundary_detection', boundary_detection_model)
multi_model_service.pack('kv_detection', kv_detection_model)
multi_model_service.pack('recognition', recognition_model)

# Save the prediction service to disk for model serving
saved_path = multi_model_service.save()