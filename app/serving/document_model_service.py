import numpy as np
import time
import torch
import torchvision
import onnx
import onnxruntime
import PIL
import cv2
import os

from PIL import Image, ImageOps
from torchvision import transforms
from bentoml import env, artifacts, api, BentoService
from bentoml.adapters import ImageInput
from bentoml.frameworks.onnx import OnnxModelArtifact
from bentoml.frameworks.pytorch import PytorchModelArtifact

from app.errors.exceptions import InferenceException
from app.serving.utils.envs import settings, logger
from app.serving.utils.utils import (
    load_json,
    convert_recognition_to_text,
    get_cropped_images,
    load_models,
    deidentify_img,
)


class ResizeKeepRatioPad(object):
    def __init__(self, height, width, interpolation=Image.BICUBIC):
        self.height = height
        self.width = width
        self.interpolation = interpolation

    def __call__(self, img: Image):
        width, height = img.size
        target_height = self.height
        target_width = int(width * target_height / height)
        x_padding = 0
        if target_width > self.width:
            target_width = self.width
        else:
            x_padding = self.width - target_width
        if target_width == 0:
            target_width += 1
        img = img.resize((target_width, target_height), self.interpolation)
        return ImageOps.expand(img, border=(0, 0, x_padding, 0), fill=(0, 0, 0))


def build_preprocess():
    transform_list = [ResizeKeepRatioPad(height=32, width=100)]
    # TODO:Manage normalize params with cfg
    transform_list += [transforms.ToTensor(), transforms.Normalize((0, 0, 0), (1, 1, 1))]
    return transforms.Compose(transform_list) if len(transform_list) > 0 else None


recognition_preprocess = build_preprocess()

# def recognition_preprocessing(self, cropped_images):
#         info_list = list()
#         for i in range(len(cropped_images)):
#             extra_info = dict()
#             for _proc in self.infer_sess_map["recognition_model"]["preprocess"]:
#                 cropped_images[i], extra_info = _proc(
#                     cropped_images[i], extra_info=extra_info)
#             info_list.append(extra_info)

#         cropped_images = np.stack(cropped_images)
#         cropped_images = cropped_images.astype(np.float32)
#         cropped_images = torch.from_numpy(cropped_images).to("cuda")

#         array = [recognition_preprocess(transforms.ToPILImage()(image))
#                  for image in cropped_images]

#         return torch.stack(array)


@env(pip_packages=["torchvision"])
@env(infer_pip_packages=True)
@artifacts(
    [
        PytorchModelArtifact("detection"),
        OnnxModelArtifact("recognition"),
    ]
)
class DocumentModelService(BentoService):
    def __init__(self):
        super().__init__()
        self.infer_sess_map = dict()
        self.service_cfg = load_json(f"/workspace/assets/textscope_id.json")["idcard"]
        load_models(self.infer_sess_map, self.service_cfg)
        self.detection_threshold = float(settings.DOCUMENT_DETECTION_SCORE_THRETHOLD)
        label_classes = self.service_cfg["resources"][1]["config"]["label_classes"]
        self.lookup_table = np.asarray(label_classes)

    def detection_preprocessing(self, img_arr):
        img_arr = np.transpose(img_arr, (2, 0, 1))
        return torch.from_numpy(img_arr)

    # def recognition_preprocessing(self, cropped_images):
    #     info_list = list()
    #     for i in range(len(cropped_images)):
    #         extra_info = dict()
    #         for _proc in self.infer_sess_map["recognition_model"]["preprocess"]:
    #             cropped_images[i], extra_info = _proc(cropped_images[i], extra_info=extra_info)
    #         info_list.append(extra_info)

    #     cropped_images = np.stack(cropped_images)
    #     cropped_images = cropped_images.astype(np.float32)

    #     return cropped_images
    def recognition_preprocessing(self, cropped_images):
        info_list = list()
        for i in range(len(cropped_images)):
            extra_info = dict()
            for _proc in self.infer_sess_map["recognition_model"]["preprocess"]:
                cropped_images[i], extra_info = _proc(cropped_images[i], extra_info=extra_info)
            info_list.append(extra_info)

        cropped_images = np.stack(cropped_images)
        cropped_images = cropped_images.astype(np.float32)
        cropped_images = torch.from_numpy(cropped_images).to("cuda")

        array = [recognition_preprocess(transforms.ToPILImage()(image)) for image in cropped_images]

        return torch.stack(array)

    def detection_postprocessing(self, img, boxes, scores, labels):
        boxes = boxes.cpu().detach().numpy()
        scores = scores.cpu().detach().numpy()
        labels = labels.cpu().detach().numpy()

        valid_indicies = scores > self.detection_threshold
        valid_scores = scores[valid_indicies]
        valid_boxes = boxes[valid_indicies]
        valid_labels = labels[valid_indicies]
        if len(valid_boxes) < 1:
            return None, None
        ind = np.lexsort((valid_boxes[:, 1], valid_boxes[:, 0]))
        valid_boxes = valid_boxes[ind].astype(int)
        valid_scores = valid_scores[ind]
        valid_labels = valid_labels[ind]

        kv_classes = self.lookup_table[valid_labels]
        cropped_images = get_cropped_images(img, valid_boxes)

        return {
            "cropped_images": cropped_images,
            "detection_boxes": valid_boxes,
            "detection_scores": valid_scores,
            "detection_classes": kv_classes,
        }

    def recognition_postprocessing(self, rec_preds, start_t):
        texts = convert_recognition_to_text(rec_preds)
        logger.info(f"Rec inference time: \t{(time.time()-start_t) * 1000:.2f}ms")
        return texts

    def to_numpy(self, tensor):
        if tensor.requires_grad:
            return tensor.detach().cpu().numpy()
        else:
            return tensor.cpu().numpy()

    def recognition(self, cropped_images):
        # inputs = torch.from_numpy(cropped_images).to("cuda")
        inputs = cropped_images
        ort_inputs = {
            self.artifacts.recognition.get_inputs()[0].name: self.to_numpy(inputs),
        }
        ort_outs = self.artifacts.recognition.run(None, ort_inputs)[0]
        return ort_outs

    def detection_result_visualization(self, img, detection_boxes, detection_classes):
        self.savepath = (
            f"{settings.BASE_PATH}/others/assets/deidentify_img_sg_{self.detection_threshold}.jpg"
        )
        info_save_dir = os.path.join(settings.ID_DEBUG_INFO_PATH, time.strftime("%Y%m%d"))
        os.makedirs(info_save_dir, exist_ok=True)
        info_save_path = os.path.join(info_save_dir, os.path.basename(self.savepath))
        deidentify_img(img, detection_boxes, detection_classes, info_save_path)
        # cv2.imwrite("/workspace/others/assets/bytes_to_document.png", img)

    @api(input=ImageInput(), batch=False)
    def document_ocr(self, img):
        if settings.DEVELOP:
            img = cv2.resize(img, dsize=(2052, 2736), interpolation=cv2.INTER_AREA)

        detection_start_time = time.time()
        img_tensor = self.detection_preprocessing(img)
        with torch.no_grad():
            boxes, labels, scores, img_size = self.artifacts.detection(img_tensor)
        detection_result = self.detection_postprocessing(img, boxes, scores, labels)
        logger.info(
            f"Detection processing time: \t{(time.time()-detection_start_time) * 1000:.2f}ms"
        )

        if settings.SAVE_DOCUMENT_VISULAIZATION_IMG:
            self.detection_result_visualization(
                img,
                detection_result["detection_boxes"],
                detection_result["detection_classes"],
            )

        recognition_start_time = time.time()
        cropped_images = self.recognition_preprocessing(detection_result["cropped_images"])
        recognition_result = self.recognition(cropped_images)
        # from scipy.special import softmax
        # rec_probs = softmax(rec_logits, axis=-1)
        rec_preds = np.argmax(recognition_result, axis=-1)
        logger.info(
            f"Recognition processing time: \t{(time.time()-recognition_start_time) * 1000:.2f}ms"
        )
        return {
            "rec_preds": rec_preds,
            "scores": detection_result["detection_scores"],
            "boxes": detection_result["detection_boxes"],
            "img_size": np.array(img_size),
        }


# import numpy as np
# import time
# import torch
# import torchvision
# import onnx
# import onnxruntime
# import PIL
# import cv2
# import os

# from bentoml import env, artifacts, api, BentoService
# from bentoml.adapters import ImageInput
# from bentoml.frameworks.onnx import OnnxModelArtifact
# from bentoml.frameworks.pytorch import PytorchModelArtifact

# from app.errors.exceptions import InferenceException
# from app.serving.utils.envs import settings, logger
# from app.serving.utils.utils import (
#     load_json,
#     convert_recognition_to_text,
#     get_class_masks,
#     get_cropped_images,
#     load_models,
#     deidentify_img,
#     get_fixed_batch,
# )


# @env(pip_packages=["torchvision"])
# @env(infer_pip_packages=True)
# @artifacts(
#     [
#         PytorchModelArtifact("detection"),
#         OnnxModelArtifact("recognition"),
#     ]
# )
# class MultiModelService(BentoService):
#     def __init__(self):
#         super().__init__()
#         self.infer_sess_map = dict()
#         self.service_cfg = load_json(f"/workspace/assets/textscope_id.json")["idcard"]
#         load_models(self.infer_sess_map, self.service_cfg)
#         self.detection_threshold = float(settings.DOCUMENT_DETECTION_SCORE_THRETHOLD)
#         label_classes = self.service_cfg["resources"][1]["config"]["label_classes"]
#         self.lookup_table = np.asarray(label_classes)

#     def detection_preprocessing(self, img_arr):
#         img_arr = np.transpose(img_arr, (2, 0, 1))
#         return torch.from_numpy(img_arr)

#     def recognition_preprocessing(self, cropped_images):
#         # info_list = list()
#         # for i in range(len(cropped_images)):
#         #     extra_info = dict()
#         #     for _proc in self.infer_sess_map["recognition_model"]["preprocess"]:
#         #         cropped_images[i], extra_info = _proc(cropped_images[i], extra_info=extra_info)
#         #     info_list.append(extra_info)

#         # cropped_images = np.stack(cropped_images)
#         # cropped_images = cropped_images.astype(np.float32)

#         # return cropped_images
#         rec_sess = self.artifacts.recognition
#         info_list = list()
#         for i in range(len(cropped_images)):
#             extra_info = dict()
#             for _proc in self.infer_sess_map["recognition_model"]["preprocess"]:
#                 cropped_images[i], extra_info = _proc(cropped_images[i], extra_info=extra_info)
#             info_list.append(extra_info)

#         cropped_images = np.stack(cropped_images)
#         cropped_images = cropped_images.astype(np.float32)

#         output_names = [_.name for _ in rec_sess.get_outputs()]
#         fixed_batch_size = self.infer_sess_map["recognition_model"]["batch_size"]

#         return cropped_images, fixed_batch_size, rec_sess, output_names

#     def detection_postprocessing(self, img, boxes, scores, labels):
#         boxes = boxes.cpu().detach().numpy()
#         scores = scores.cpu().detach().numpy()
#         labels = labels.cpu().detach().numpy()

#         valid_indicies = scores > self.detection_threshold
#         valid_scores = scores[valid_indicies]
#         valid_boxes = boxes[valid_indicies]
#         valid_labels = labels[valid_indicies]
#         if len(valid_boxes) < 1:
#             return None, None
#         ind = np.lexsort((valid_boxes[:, 1], valid_boxes[:, 0]))
#         valid_boxes = valid_boxes[ind].astype(int)
#         valid_scores = valid_scores[ind]
#         valid_labels = valid_labels[ind]

#         kv_classes = self.lookup_table[valid_labels]
#         cropped_images = get_cropped_images(img, valid_boxes)
#         class_masks = get_class_masks(kv_classes)

#         return {
#             "cropped_images": cropped_images,
#             "class_masks": class_masks,
#             "detection_boxes": valid_boxes,
#             "detection_scores": valid_scores,
#             "detection_classes": kv_classes,
#         }

#     def recognition_postprocessing(self, rec_preds, start_t):
#         texts = convert_recognition_to_text(rec_preds)
#         logger.info(f"Rec inference time: \t{(time.time()-start_t) * 1000:.2f}ms")
#         return texts

#     def to_numpy(self, tensor):
#         if tensor.requires_grad:
#             return tensor.detach().cpu().numpy()
#         else:
#             return tensor.cpu().numpy()

#     def recognition(self, cropped_images):
#         inputs = torch.from_numpy(cropped_images).to("cuda")
#         ort_inputs = {
#             self.artifacts.recognition.get_inputs()[0].name: self.to_numpy(inputs),
#         }
#         ort_outs = self.artifacts.recognition.run(None, ort_inputs)[0]
#         return ort_outs

#     def detection_result_visualization(self, img, detection_boxes, detection_classes):
#         self.savepath = (
#             f"{settings.BASE_PATH}/others/assets/deidentify_img_sg_{self.detection_threshold}.jpg"
#         )
#         info_save_dir = os.path.join(settings.ID_DEBUG_INFO_PATH, time.strftime("%Y%m%d"))
#         os.makedirs(info_save_dir, exist_ok=True)
#         info_save_path = os.path.join(info_save_dir, os.path.basename(self.savepath))
#         deidentify_img(img, detection_boxes, detection_classes, info_save_path)
#         # cv2.imwrite("/workspace/others/assets/bytes_to_document.png", img)

#     @api(input=ImageInput(), batch=False)
#     def document_ocr(self, img):
#         if settings.DEVELOP:
#             img = cv2.resize(img, dsize=(2052, 2736), interpolation=cv2.INTER_AREA)

#         detection_start_time = time.time()
#         img_tensor = self.detection_preprocessing(img)
#         with torch.no_grad():
#             boxes, labels, scores, img_size = self.artifacts.detection(img_tensor)
#         detection_result = self.detection_postprocessing(img, boxes, scores, labels)
#         logger.info(
#             f"Detection processing time: \t{(time.time()-detection_start_time) * 1000:.2f}ms"
#         )

#         if settings.SAVE_DOCUMENT_VISULAIZATION_IMG:
#             self.detection_result_visualization(
#                 img,
#                 detection_result["detection_boxes"],
#                 detection_result["detection_classes"],
#             )

#         recognition_start_time = time.time()
#         # cropped_images = self.recognition_preprocessing(detection_result["cropped_images"])
#         # recognition_result = self.recognition(cropped_images)
#         # rec_preds = np.argmax(recognition_result, axis=-1)
#         (
#             cropped_images,
#             fixed_batch_size,
#             rec_sess,
#             output_names,
#         ) = self.recognition_preprocessing(detection_result["cropped_images"])

#         # rec_preds = self.recognition(
#         #     cropped_images,
#         #     fixed_batch_size,
#         #     rec_sess,
#         #     detection_result["class_masks"],
#         #     output_names,
#         # )

#         ###################################################################
#         rec_sess = self.artifacts.recognition
#         # info_list = list()
#         # for i in range(len(cropped_images)):
#         #     extra_info = dict()
#         #     for _proc in self.infer_sess_map["recognition_model"]["preprocess"]:
#         #         cropped_images[i], extra_info = _proc(cropped_images[i], extra_info=extra_info)
#         #     info_list.append(extra_info)

#         cropped_images = np.stack(cropped_images)
#         cropped_images = cropped_images.astype(np.float32)

#         output_names = [_.name for _ in rec_sess.get_outputs()]
#         rec_preds = []
#         fixed_batch_size = self.infer_sess_map["recognition_model"]["batch_size"]
#         for i in range(0, len(cropped_images), fixed_batch_size):
#             if (i + fixed_batch_size) < len(cropped_images):
#                 end = i + fixed_batch_size
#             else:
#                 end = len(cropped_images)
#             _cropped_images = cropped_images[i:end]
#             _class_masks = detection_result["class_masks"][i:end]
#             inputs = get_fixed_batch(fixed_batch_size, _cropped_images, _class_masks)
#             inputs = dict((rec_sess.get_inputs()[i].name, inpt) for i, inpt in enumerate(inputs))
#             results = rec_sess.run(output_names, inputs)

#             preds = results[0][: (end - i)]
#             rec_preds = np.concatenate([rec_preds, preds]) if len(rec_preds) > 0 else preds

#         texts = convert_recognition_to_text(rec_preds)
#         ###################################################################
#         # return texts

#         logger.info(
#             f"Recognition processing time: \t{(time.time()-recognition_start_time) * 1000:.2f}ms"
#         )

#         return {
#             "rec_preds": rec_preds,
#             "scores": detection_result["detection_scores"],
#             "boxes": detection_result["detection_boxes"],
#             "img_size": np.array(img_size),
#         }
