import numpy as np
import time
import torch
import torchvision
import lovit.preprocess.augmentation_impl as T
import PIL
import cv2
import os

from PIL import Image, ImageOps
from torchvision import transforms
from bentoml import env, artifacts, api, BentoService
from bentoml.adapters import ImageInput

from bentoml.frameworks.pytorch import PytorchModelArtifact
from lovit.preprocess import recognition
from lovit.preprocess import aggamoto

from app.errors.exceptions import InferenceException
from app.serving.utils.envs import settings, logger
from app.serving.utils.utils import (
    load_json,
    convert_recognition_to_text,
    get_cropped_images,
    load_models,
    deidentify_img,
)


@env(pip_packages=["torchvision"])
@env(infer_pip_packages=True)
@artifacts(
    [
        PytorchModelArtifact("detection"),
        PytorchModelArtifact("recognition"),
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
        self.recognition_preprocess = recognition.build_preprocess()

    def detection_preprocessing(self, img_arr):
        img_arr = np.transpose(img_arr, (2, 0, 1))
        return torch.from_numpy(img_arr.copy())

    def recognition_preprocessing(self, cropped_images):
        cropped_images = [
            self.recognition_preprocess(Image.fromarray(cropped_image))
            for cropped_image in cropped_images
        ]

        cropped_images = np.stack(cropped_images)
        cropped_images = cropped_images.astype(np.float32)
        cropped_images = torch.from_numpy(cropped_images).to("cuda")

        array = [
            self.recognition_preprocess(transforms.ToPILImage()(image)) for image in cropped_images
        ]

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
        inputs = cropped_images
        with torch.no_grad():
            ort_outs = self.artifacts.recognition(inputs.half().to("cuda"))
        return self.to_numpy(ort_outs)

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
        # settings.INPUT.MIN_SIZE_TEST, settings.INPUT.MIN_SIZE_TEST], settings.INPUT.MAX_SIZE_TEST
        transforms = [T.ResizeShortestEdge([3000, 3000], 3200)]
        img = aggamoto.preprocess_image(img, transforms)

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
