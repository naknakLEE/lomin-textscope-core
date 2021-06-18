import torch
import numpy as np
import cv2
import sys

sys.path.append("/workspace")
from app.serving.pytorch_model_service import PytorchModelService
from app.common.const import get_settings


settings = get_settings()


# Create a pytorch model service instance
pytorch_model_service = PytorchModelService()

# Pack the newly trained model artifact
print(f"{settings.BASE_PATH}/assets/models/gocr_chshin_efficientdet_d4_210607_model.ts")
traced_net = torch.jit.load(f"{settings.BASE_PATH}/assets/models/mask_rcnn.pt")
# traced_net = torch.jit.load(f"{settings}/assets/models/mask_rcnn.pt").to(torch.device("cuda"))
pytorch_model_service.pack('net', traced_net)

# Save the prediction service to disk for model serving
saved_path = pytorch_model_service.save()
