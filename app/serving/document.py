import numpy as np
import time
import torch
import os
import imutils
import cv2
import torchvision

from datetime import datetime
from bentoml import env, artifacts, api, BentoService
from bentoml.adapters import ImageInput, JsonInput
from bentoml.frameworks.onnx import OnnxModelArtifact
from bentoml.frameworks.pytorch import PytorchModelArtifact
from onnxruntime.capi.onnxruntime_pybind11_state import Fail

from app.errors.exceptions import InferenceException
from app.serving.utils.envs import settings, logger
from app.serving.utils.utils import (
    load_json,
    save_debug_img,
    deidentify_img,
    filter_class,
    get_class_masks,
    get_fixed_batch,
    to_wide,
    expand_size,
    add_backup_boxes,
    rectify_img,
    if_use_keypoint,
    if_use_mask,
    boundary_postprocess,
    kv_postprocess,
    update_valid_kv_boxes,
    convert_recognition_to_text,
    roate_image,
    kv_postprocess_with_edge,
    get_cropped_images,
    load_models,
)


@env(pip_packages=["torchvision"])
@env(infer_pip_packages=True)
@artifacts(
    [
        PytorchModelArtifact("detection"),
        OnnxModelArtifact("recognition"),
    ]
)
class MultiModelService(BentoService):
    def __init__(self):
        super().__init__()
        self.infer_sess_map = dict()
        self.service_cfg = load_json(f"/workspace/assets/textscope_id.json")["idcard"]
        load_models(self.infer_sess_map, self.service_cfg)

        # self.save_output_img = True
        # self.savepath = settings.SAVEPATH


    @api(input=ImageInput(), batch=False)
    def detection(self, img):
        # print("\033[95m" + f"{id_image_arr}" + "\033[m")
        kv_boxes, kv_scores, kv_classes = self._kv_infer(img)

        # print("\033[95m" + f"{kv_boxes}" + "\033[m")
        cropped_images = get_cropped_images(img, kv_boxes)


        class_masks = get_class_masks(kv_classes)
        texts = self._rec_infer(cropped_images, class_masks)

        # logger.debug(f"kv_boxes: {kv_boxes}")
        # logger.debug(f"kv_scores: {kv_scores}")

        # if settings.SAVE_ID_DEBUG_INFO and settings.ID_DEBUG_INFO_PATH is not None:
        self.savepath = './deidentify_img.jpg'
        info_save_dir = os.path.join(
            settings.ID_DEBUG_INFO_PATH, time.strftime("%Y%m%d")
        )
        os.makedirs(info_save_dir, exist_ok=True)
        info_save_path = os.path.join(
            info_save_dir, os.path.basename(self.savepath)
        )
        deidentify_img(img, kv_boxes, kv_classes, info_save_path)

        return [{"texts": texts}]


        # return [
        #     {
        #         "cropped_images": cropped_images,
        #         "id_image_arr": img,
        #         "kv_boxes": kv_boxes,
        #         "kv_scores": kv_scores,
        #     }
        # ]

    @api(input=JsonInput(), batch=False)
    def recognition(self, data):
        data = data[0]
        cropped_images = np.array(data["cropped_images"])
        # id_image_arr = np.array(data["id_image_arr"])
        kv_boxes = data["kv_boxes"]
        kv_scores = data["kv_scores"]
        # kv_classes = data["kv_classes"]

        texts = self._rec_infer(cropped_images)

        # TO DEBUG OUTPUT OF INFERENCE
        # if self.save_output_img and self.savepath is not None:
        #     # if self.save_output_img and self.savepath is not None and settings.DEVELOP and settings.ID_DRAW_BBOX_IMG:
        #     save_debug_img(id_image_arr, kv_boxes, kv_classes, texts, self.savepath)

        logger.debug(f"kv_boxes: {kv_boxes}")
        logger.debug(f"kv_scores: {kv_scores}")
        # logger.debug(f"kv_classes: {kv_classes}")

        return [{"texts": texts}]


    def kv_postprocess(self, scores, boxes, labels):
        # kv_score_threshold = float(settings.ID_KV_SCORE_TH)
        kv_score_threshold = 0.5
        valid_indicies = scores > kv_score_threshold
        valid_scores = scores[valid_indicies]
        valid_boxes = boxes[valid_indicies]
        valid_labels = labels[valid_indicies]
        if len(valid_boxes) < 1:
            return None, None
        ind = np.lexsort((valid_boxes[:, 1], valid_boxes[:, 0]))
        valid_boxes = valid_boxes[ind]
        valid_scores = valid_scores[ind]
        valid_labels = valid_labels[ind]

        lookup_table =  ["bg",
                        "arc_nationality",
                        "arc_visa",
                        "dlc_license_num",
                        "dlc_license_region",
                        "dlc_serial_num",
                        "expiration_date",
                        "id",
                        "issue_date",
                        "name"
                        ]
        lookup_table = np.asarray(lookup_table)
                        


        kv_classes = lookup_table[valid_labels]
        return valid_scores, valid_boxes, kv_classes

    def _kv_infer(self, img_arr):
        start_t = time.time()
        original_size = (img_arr.shape[1], img_arr.shape[0])
        # img_arr = self.preprocess_cropped_images(img_arr)
        img_arr = np.transpose(img_arr, (2,0,1))

        # inputs = {"images": np.expand_dims(img_arr.astype(np.float32), axis=0)}

        # model_input_names = self.artifacts.detection.get_inputs()

        # print('\033[95m' + f"{input_names[0].name}" + '\033[m')
        # output_names = self.infer_sess_map['kv_model']['output_names']
        # output_names = [_.name for _ in self.artifacts.detection.get_outputs()]
        # print("\033[95m" + f"{output_names}" + "\033[m")
        # exit()
        # boxes, labels, scores = self.artifacts.detection(inputs)
        img_tensor = torch.from_numpy(img_arr)

        with torch.no_grad():
            boxes, labels, scores, img_size = self.artifacts.detection(img_tensor)
    
        # print("\033[95m" + f"{scores}" + "\033[m")
        boxes = boxes.cpu().detach().numpy()
        scores = scores.cpu().detach().numpy()
        labels = labels.cpu().detach().numpy()
        valid_scores, valid_boxes, kv_classes = self.kv_postprocess(scores, boxes, labels)
        # valid_scores, valid_boxes = scores, boxes
        logger.info(f"KV inference time: \t{(time.time()-start_t) * 1000:.2f}ms")
        # valid_boxes = update_valid_kv_boxes(valid_boxes, original_size)

        return valid_boxes.astype(int), valid_scores, kv_classes

    def preprocess_cropped_images(self, cropped_image, width=128, height=32):
        image = cv2.resize(cropped_image, (width, height))
        image = np.transpose(image, (2,0,1))
        image[:,:,:] = image[:,:,:] / 127.5 - 1.0
        return image

    def _rec_infer(self, cropped_images, class_masks):
        start_t = time.time()
        rec_sess = self.artifacts.recognition
        info_list = list()
        for i in range(len(cropped_images)):
            extra_info = dict()
            for _proc in self.infer_sess_map["recognition_model"]["preprocess"]:
                cropped_images[i], extra_info = _proc(
                    cropped_images[i], extra_info=extra_info
                )
            info_list.append(extra_info)

        cropped_images = np.stack(cropped_images)
        cropped_images = cropped_images.astype(np.float32)

        output_names = [_.name for _ in rec_sess.get_outputs()]
        rec_preds = []
        fixed_batch_size = self.infer_sess_map["recognition_model"]["batch_size"]
        for i in range(0, len(cropped_images), fixed_batch_size):
            if (i + fixed_batch_size) < len(cropped_images):
                end = i + fixed_batch_size
            else:
                end = len(cropped_images)
            _cropped_images = cropped_images[i:end]
            _class_masks = class_masks[i:end]
            inputs = get_fixed_batch(fixed_batch_size, _cropped_images, _class_masks)
            inputs = dict(
                (rec_sess.get_inputs()[i].name, inpt) for i, inpt in enumerate(inputs)
            )
            results = rec_sess.run(output_names, inputs)

            preds = results[0][: (end - i)]
            rec_preds = (
                np.concatenate([rec_preds, preds]) if len(rec_preds) > 0 else preds
            )

        texts = convert_recognition_to_text(rec_preds)
        logger.info(f"Rec inference time: \t{(time.time()-start_t) * 1000:.2f}ms")

        return texts