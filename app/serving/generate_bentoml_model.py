import torch
from pytorch_model_service import PytorchModelService
from sklearn import svm
from sklearn import datasets



iris = datasets.load_iris()
X, y = iris.data, iris.target

clf = svm.SVC(gamma='scale')
clf.fit(X, y)

# Create a iris classifier service instance
pytorch_model_service = PytorchModelService()

# Pack the newly trained model artifact
traced_net = torch.jit.load("/workspace/app/serving/mask_rcnn.pt")
pytorch_model_service.pack('net', traced_net)

# Save the prediction service to disk for model serving
saved_path = pytorch_model_service.save()