# iris_classifier.py
from bentoml.adapters.string_input import StringInput
import torch
import torchvision
import numpy as np
import cv2

from typing import List
from bentoml.types import JsonSerializable
from bentoml import env, artifacts, api, BentoService
from bentoml.adapters import ImageInput, DataframeInput
from bentoml.frameworks.pytorch import PytorchModelArtifact


# multiple model inference
# https://docs.bentoml.org/en/latest/concepts.html#packaging-model-artifacts
@env(infer_pip_packages=True)
@env(pip_packages=["torchvision"])
@artifacts([PytorchModelArtifact("net")])
class PytorchModelService(BentoService):
    """
    A minimum prediction service exposing a Scikit-learn model
    """

    @api(input=ImageInput(), batch=False)
    def detection(self, imgs):
        """
        An inference API named `predict` with Dataframe input adapter, which codifies
        how HTTP requests or CSV files are converted to a pandas Dataframe object as the
        inference API function input
        """

        # inputs = {"images": np.expand_dims(img_arr.astype(np.float32), axis=0)}
        # model_input_names = self.artifacts.net.get_inputs()
        # print("\033[95m" + f"{model_input_names}" + "\033[m")
        # img = torch.unsqueeze(torch.as_tensor(imgs, dtype=torch.float32), 0).permute(0,3,1,2)
        # img = torch.unsqueeze(torch.as_tensor(imgs), 0).permute(0, 3, 1, 2)
        # inputs = {"0": np.expand_dims(img.astype(np.float32), axis=0)}

        # output_names = [_.name for _ in self.artifacts.net.get_outputs()]
        # exit()
        # boxes, labels, scores = self.artifacts.kv_detection.run(output_names, inputs)

        # img = torch.as_tensor(np.expand_dims(imgs, axis=0)).permute(0, 3, 1, 2).float().to(torch.device("cuda"))
        # pred_boxes = results[0]
        # pred_classes = results[1]
        # pred_masks = results[2]
        # scores = results[3]
        # size= results[4]
        # for result in results:
        #     print(result.shape)

        print(type(imgs))
        print(imgs.shape)
        # print(imgs.astype(np.float32))
        # imgs = np.array(imgs)
        img = imgs.astype(np.float32)
        tensor = torch.as_tensor(img).to(torch.device("cuda"))
        batch = torch.unsqueeze(tensor, 0).permute(0, 3, 1, 2)
        # batch = tensor.permute(2,0,1)

        with torch.no_grad():
            results = self.artifacts.net(batch)
        # tensor = torch.as_tensor(imgs.astype(np.float32))
        # batch = torch.unsqueeze(tensor, 0).permute(0,3,1,2)
        # results = self.artifacts.net(batch)
        # print("\033[96m" + f"{results}" + "\033[m")
        return {"result": results.cpu().detach().numpy()}

        # return [{"pred_boxes": results[0], "pred_classes": results[1], "pred_masks": results[2], "scores": results[3], "size": results[4]}]

    @api(input=DataframeInput(), batch=True)
    def recognition(self, parsed_json_list):
        """
        An inference API named `predict` with Dataframe input adapter, which codifies
        how HTTP requests or CSV files are converted to a pandas Dataframe object as the
        inference API function input
        """
        # img = torch.as_tensor(imgs).float().permute(2, 0, 1)
        parsed_json_list
        # img = torch.as_tensor(np.expand_dims(imgs, axis=0)).permute(0, 3, 1, 2).float().to(torch.device("cuda"))

        print("\033[96m" + f"parsed_json_list: {parsed_json_list}" + "\033[m")
        img = cv2.imread("/workspace/others/assets/000000000000000IMG_4831.jpg")
        # encoded_img = np.frombuffer(img, dtype=np.uint8)
        # image = cv2.imdecode(encoded_img, cv2.IMREAD_COLOR)
        img = img.astype(np.float32)
        tensor = torch.as_tensor(img).to(torch.device("cuda"))
        batch = torch.unsqueeze(tensor, 0).permute(0, 3, 1, 2)
        # batch = tensor.permute(2,0,1)
        results = self.artifacts.net(batch)
        # pred_boxes = results[0]
        # pred_classes = results[1]
        # pred_masks = results[2]
        # scores = results[3]
        # size= results[4]
        # for result in results:
        #     print(result.shape)
        # print("\033[96m" + f"{results}" + "\033[m")
        return {"result": results.cpu().detach().numpy()}
        # return [{"pred_boxes": results[0], "pred_classes": results[1], "pred_masks": results[2], "scores": results[3], "size": results[4]}]
