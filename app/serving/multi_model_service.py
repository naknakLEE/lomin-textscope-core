# iris_classifier.py
import torch
import torchvision
import numpy

from bentoml import env, artifacts, api, BentoService
from bentoml.adapters import ImageInput
from bentoml.frameworks.pytorch import PytorchModelArtifact
from bentoml.frameworks.onnx import OnnxModelArtifact


# multiple model inference
# https://docs.bentoml.org/en/latest/concepts.html#packaging-model-artifacts
@env(infer_pip_packages=True)
@env(pip_packages=['torchvision'])
@artifacts([
    OnnxModelArtifact('boundary_detection'),
    OnnxModelArtifact('kv_detection'),
    OnnxModelArtifact('recognition'),
])
class PytorchModelService(BentoService):
    """
    A minimum prediction service exposing a Scikit-learn model
    """

    # @api(input=ImageInput(), batch=True)
    # def inference(self, imgs):
    @api(input=DataframeInput(), batch=True)
    def inference(self, df):
        """
        An inference API named `predict` with Dataframe input adapter, which codifies
        how HTTP requests or CSV files are converted to a pandas Dataframe object as the
        inference API function input
        """
        input_data = df.to_numpy().astype(numpy.float32)
        input_name = self.artifacts.model.get_inputs()[0].name
        output_name = self.artifacts.model.get_outputs()[0].name
        outputs = numpy.zeros(input_data.shape[0])
        for i in range(input_data.shape[0]):
            outputs[i] = self.artifacts.model.run([output_nmae], {input_name: input_data[i: i + 1]})[0]
        return outputs
        # imgs = self.artifacts.boundary_detection.predict(imgs)
        # return self.artifacts.kv_detection.predict(imgs)
        # results = self.artifacts.net(torch.as_tensor(imgs).permute(0,3,1,2)[0])
        # result_shape = []
        # for result in results:
        #     print(result.shape)
        # return [{ "pred_boxes": results[0], "pred_classes": results[1], "pred_masks": results[2], "scores": results[3], "size": results[4] }]
        # return [{ "pred_boxes": results[0]["unknown_obj"], "pred_classes": results[1]["unknown_obj"], "pred_masks": results[2]["unknown_obj"], "scores": results[3]["unknown_obj"], "size": results[4]["unknown_obj"] }]