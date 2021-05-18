# iris_classifier.py
import torch
import torchvision

from bentoml import env, artifacts, api, BentoService
from bentoml.adapters import ImageInput
from bentoml.frameworks.pytorch import PytorchModelArtifact


@env(infer_pip_packages=True)
@env(pip_packages=['torchvision'])
@artifacts([PytorchModelArtifact('net')])
class PytorchModelService(BentoService):
    """
    A minimum prediction service exposing a Scikit-learn model
    """

    @api(input=ImageInput(), batch=True)
    def inference(self, imgs):
        """
        An inference API named `predict` with Dataframe input adapter, which codifies
        how HTTP requests or CSV files are converted to a pandas Dataframe object as the
        inference API function input
        """
        
        results = self.artifacts.net(torch.as_tensor(imgs).permute(0,3,1,2)[0])
        result_shape = []
        for result in results:
            print(result.shape)
        return [{ "pred_boxes": results[0], "pred_classes": results[1], "pred_masks": results[2], "scores": results[3], "size": results[4] }]
        # return [{ "pred_boxes": results[0]["unknown_obj"], "pred_classes": results[1]["unknown_obj"], "pred_masks": results[2]["unknown_obj"], "scores": results[3]["unknown_obj"], "size": results[4]["unknown_obj"] }]