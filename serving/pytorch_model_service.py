# iris_classifier.py
import torch
import torchvision
import json
import base64
import io

from bentoml import env, artifacts, api, BentoService
from bentoml.adapters import ImageInput, JsonInput
from bentoml.frameworks.pytorch import PytorchModelArtifact
from torchvision import transforms
from PIL import Image

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
        # imgs = torch.from_numpy(imgs).permute(2,0,1)
        # print(imgs)
        # print(imgs.shape, type(imgs), imgs.dtype)
        # print(torch.as_tensor(imgs).permute(0,3,1,2).shape)
        results = self.artifacts.net(torch.as_tensor(imgs).permute(0,3,1,2)[0])
        result_shape = []
        for result in results:
            print(result.shape)
        
        return results

    @api(input=JsonInput(), batch=True)
    def predict_json(self, json_arr):
        # print(json_arr)
        # image = self.transform_image(json_arr)
        # image = json_arr.decode('utf-8')
        
        image = base64.b64decode(json_arr[0]['image'])
        print(image)
        data = self.artifacts.net(image)
        # data = {}
        # data['img'] = base64.encodebytes(result).decode('utf-8')

        return json.dumps({ "data": data })

    # def transform_image(self, image_bytes):
    #         transform = transforms.Compose([
    #             # transforms.Resize((self.img_size, self.img_size)),
    #             transforms.ToTensor(),
    #             # transforms.Normalize(mean=(0.5, 0.5, 0.5), std=(0.5, 0.5, 0.5))
    #         ])
    #         print(type(image_bytes))
    #         byteio = io.BytesIO(image_bytes)
    #         image = Image.open(byteio).convert('RGB')
    #         return transform(image)



