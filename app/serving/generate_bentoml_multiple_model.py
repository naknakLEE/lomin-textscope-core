import torch
import onnx

from multiple_model_service import MultiModelService


# Create a iris classifier service instance
multi_model_service = MultiModelService()

# Pack the newly trained model artifact
# traced_net = torch.jit.load("/workspace/app/serving/mask_rcnn.pt")
boundary_detection_model = onnx.load("/workspace/assets/id_boundary/1/kb_201031_skkang_001_id_outline_keypoint_convert_0140000_b1.onnx")
kv_detection_model = onnx.load("/workspace/assets/id_kv/1/kb_201016_skkang_001_id_kv_0069000_b1.onnx")
recognition_model = onnx.load("/workspace/assets/recognizer/1/kb_201109_skkang_001_id_rec_0020000_b9.onnx")
multi_model_service.pack('boundary_detection', boundary_detection_model)
multi_model_service.pack('kv_detection', kv_detection_model)
multi_model_service.pack('recognition', recognition_model)

# Save the prediction service to disk for model serving
saved_path = multi_model_service.save()
