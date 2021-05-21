import torch
import torchvision
import numpy as np
import cv2
import time
import json
import os
import numpy as np

from bentoml import env, artifacts, api, BentoService
from bentoml.adapters import ImageInput
from bentoml.frameworks.onnx import OnnxModelArtifact


from lovit.utils.converter import CharacterMaskGenerator, build_converter
from lovit.structures.catalogs import LabelCatalog, DocumentCatalog



class ELabelCatalog(LabelCatalog):
    @staticmethod
    def get(label_files, data_dir=None, decipher=None):
        if data_dir is None:
            data_dir = LabelCatalog.LABEL_DIR
        characters = ''
        for label_file in label_files:
            if decipher:
                label_path = os.path.join(data_dir, decipher.prefix + LabelCatalog.LABELS[label_file])
                assert os.path.exists(label_path), label_path
                label = decipher(label_path)
                characters += ''.join(label).replace('\n','').replace('\r','')
            else:
                label_path = os.path.join(data_dir, LabelCatalog.LABELS[label_file])
                assert os.path.exists(label_path)
                label = open(label_path, encoding='utf-8').readlines()
                characters += ''.join(label).replace('\n','')
        return characters


class EDocumentCatalog(DocumentCatalog):
    @classmethod
    def get_template(cls, doc_name, decipher=None):
        if decipher:
            path = os.path.join(cls.BASE_DIR, decipher.prefix + cls.MAP[doc_name]['template'])
            return decipher(path)
        
        with open(cls.get_template_path(doc_name)) as f:
            return json.load(f)


characters = ELabelCatalog.get(("num", "eng_cap", "eng_low", "kor_2350", "symbols"), decipher=False)
converter = build_converter(characters, True)
mask_generator = CharacterMaskGenerator(converter)
mask_generator.class_mask_map.update(EDocumentCatalog.ID_CARD)


def _get_class_masks(leaf_kv_classes):
    class_masks = None
    for leaf_kv_class in leaf_kv_classes:
        mask = mask_generator("id")
        mask = np.expand_dims(mask, axis=0)
        class_masks = np.concatenate([class_masks, mask]) if class_masks is not None else mask
    return class_masks

def get_cropped_images(image, boxes):
    cropped_images = list()
    for box in boxes:
        box = box.astype(np.int)
        cropped_images.append(image[
            :
            box[1]:box[3],
            box[0]:box[2],
        ])
    return cropped_images

def _get_fixed_batch(batch_size, *inputs):
        start_t = time.time()
        batch_inputs = []     
        for i in inputs:
            if len(i) < batch_size:
                pad = np.zeros((batch_size - len(i), *i.shape[1:]), dtype=i.dtype)
                batch_inputs.append(np.concatenate([i, pad]))
            else:
                batch_inputs.append(i[:batch_size])

        return batch_inputs


# multiple model inference
# https://docs.bentoml.org/en/latest/concepts.html#packaging-model-artifacts
@env(pip_packages=['torchvision'])
@env(infer_pip_packages=True)
@artifacts([
    OnnxModelArtifact('boundary_detection'),
    OnnxModelArtifact('kv_detection'),
    OnnxModelArtifact('recognition'),
])
class MultiModelService(BentoService):
    """
    A minimum prediction service exposing a Scikit-learn model
    """
    @api(input=ImageInput(), batch=True)
    def inference(self, imgs):
        """
        An inference APId `predict` with Dataframe input adapter, which codifies
        how HTTP requests or CSV files are converted to a pandas Dataframe object as the
        inference API function input
        """
        start = previous_time = time.time()
        input_data = cv2.resize(np.array(imgs[0], dtype=np.float32), dsize=(320, 288), interpolation=cv2.INTER_CUBIC)
        # input_data = np.transpose(np.expand_dims(input_data, axis=0), (0,3,1,2))
        input_data = np.transpose(input_data, (2,0,1))

        preprocessed_time = time.time() - previous_time
        previous_time = time.time()
        inputs1 = self.artifacts.boundary_detection.get_inputs()[0]
        outputs = self.artifacts.boundary_detection.get_outputs()
        print_data(color=94, **{
            "shape": input_data.shape, 
            "input1": inputs1,
            "output1": outputs[0],
            "output2": outputs[1],
            "output3": outputs[2],
        })
        boundary_detection_output = self.artifacts.boundary_detection.run([outputs[0].name, outputs[1].name, outputs[2].name], {inputs1.name: input_data})
        model1_inference_time = time.time() - previous_time
        previous_time = time.time()


        input_data2 = np.expand_dims(input_data, axis=0)
        inputs2 = self.artifacts.kv_detection.get_inputs()[0]
        outputs2 = self.artifacts.kv_detection.get_outputs()
        print_data(color=95, **{
            "shape": input_data2.shape, 
            "input1": inputs2,
            "output1": outputs2[0],
            "output2": outputs2[1],
            "output3": outputs2[2],
        })
        kv_detection_output = self.artifacts.kv_detection.run([outputs2[0].name,outputs2[1].name], {inputs2.name: input_data2})
        model2_inference_time = time.time() - previous_time
        previous_time = time.time()


        input_data2 = cv2.resize(np.array(imgs[0], dtype=np.float32), dsize=(32, 128), interpolation=cv2.INTER_CUBIC)
        input_data2 = np.expand_dims(np.transpose(input_data2, (2,0,1)), axis=0)
        input_data3 = np.concatenate((input_data2,input_data2,input_data2,input_data2,input_data2,input_data2,input_data2,input_data2,input_data2), axis=0)
        class_masks = _get_class_masks(kv_detection_output[0])
        inputs3 = self.artifacts.recognition.get_inputs()
        outputs3 = self.artifacts.recognition.get_outputs()
        print_data(color=96, **{
            # "shape": input_data3.shape, 
            "input1": inputs3[0],
            "input2": inputs3[1],
            "output1": outputs3[0],
            "output2": outputs3[1],
        })

    
        inputs = _get_fixed_batch(9, input_data3, class_masks)
        inputs = dict((self.artifacts.recognition.get_inputs()[i].name, inpt) for i, inpt in enumerate(inputs))
        print(input_data3.shape)
        recognition_output = self.artifacts.recognition.run([outputs3[0].name,outputs3[1].name], inputs)
        model3_inference_time = time.time() - previous_time
        previous_time = time.time()

        print_data(color=35, **{
            "outputs1": boundary_detection_output, 
            "outputs2": kv_detection_output,
            "outputs3": recognition_output,
        })
        print_data(color=36, **{
            "time[preprocess]": preprocessed_time, 
            "time[boundary]": model1_inference_time,
            "time[kv_detection]": model2_inference_time,
            "time[recognition]": model3_inference_time,
            "time[total]": time.time() - start,
        })
        
        return [recognition_output]
        
def print_data(color=35, **kwargs):
    for key, val in kwargs.items():
        print(f'\033[{color}m' + f"{key}: {val}" + '\033[0m')
    print("")