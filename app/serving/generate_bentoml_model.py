import torch
import numpy as np
import cv2

from pytorch_model_service import PytorchModelService



# Create a iris classifier service instance
pytorch_model_service = PytorchModelService()

# Pack the newly trained model artifact
traced_net = torch.jit.load("/workspace/assets/models/mask_rcnn.pt")
# traced_net = torch.jit.load("/workspace/assets/models/mask_rcnn.pt").to(torch.device("cuda"))
pytorch_model_service.pack('net', traced_net)

# Save the prediction service to disk for model serving
saved_path = pytorch_model_service.save()
