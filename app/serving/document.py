import numpy as np
import time
import torch
import torchvision
import onnx
import onnxruntime
import PIL
import cv2
import os

from bentoml import env, artifacts, api, BentoService
from bentoml.adapters import ImageInput
from bentoml.frameworks.onnx import OnnxModelArtifact
from bentoml.frameworks.pytorch import PytorchModelArtifact

from app.errors.exceptions import InferenceException
from app.serving.utils.envs import settings, logger
from app.serving.utils.utils import (
    load_json,
    get_class_masks,
    get_fixed_batch,
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
        OnnxModelArtifact("recognition"),
    ]
)
class MultiModelService(BentoService):
    def __init__(self):
        super().__init__()
        self.infer_sess_map = dict()
        self.service_cfg = load_json(f"/workspace/assets/textscope_id.json")["idcard"]
        load_models(self.infer_sess_map, self.service_cfg)
        self.detection_threshold = 0.5

    def detection_preprocessing(self, img_arr):
        start_t = time.time()
        img_arr = np.transpose(img_arr, (2, 0, 1))
        return torch.from_numpy(img_arr), start_t

    def recognition_preprocessing(self, cropped_images):
        start_t = time.time()
        rec_sess = self.artifacts.recognition
        info_list = list()
        for i in range(len(cropped_images)):
            extra_info = dict()
            for _proc in self.infer_sess_map["recognition_model"]["preprocess"]:
                cropped_images[i], extra_info = _proc(cropped_images[i], extra_info=extra_info)
            info_list.append(extra_info)

        cropped_images = np.stack(cropped_images)
        cropped_images = cropped_images.astype(np.float32)

        output_names = [_.name for _ in rec_sess.get_outputs()]
        fixed_batch_size = self.infer_sess_map["recognition_model"]["batch_size"]

        return cropped_images, fixed_batch_size, rec_sess, output_names

    def detection_postprocessing(self, img, boxes, scores, labels, start_t):
        boxes = boxes.cpu().detach().numpy()
        scores = scores.cpu().detach().numpy()
        labels = labels.cpu().detach().numpy()

        # detection_score_threshold = float(settings.ID_KV_SCORE_TH)
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

        lookup_table = [
            "bg",
            "arc_nationality",
            "arc_visa",
            "dlc_license_num",
            "dlc_license_region",
            "dlc_serial_num",
            "expiration_date",
            "id",
            "issue_date",
            "name",
        ]
        lookup_table = np.asarray(lookup_table)
        kv_classes = lookup_table[valid_labels]

        cropped_images = get_cropped_images(img, valid_boxes)
        class_masks = get_class_masks(kv_classes)

        logger.info(f"KV inference time: \t{(time.time()-start_t) * 1000:.2f}ms")

        return cropped_images, class_masks, valid_boxes, valid_scores, kv_classes

    def recognition_postprocessing(self, rec_preds, start_t):
        texts = convert_recognition_to_text(rec_preds)
        logger.info(f"Rec inference time: \t{(time.time()-start_t) * 1000:.2f}ms")
        return texts

    def to_numpy(self, tensor):
        if tensor.requires_grad:
            return tensor.detach().cpu().numpy()
        else:
            return tensor.cpu().numpy()

    def recognition(self, cropped_images, fixed_batch_size, rec_sess, class_masks, output_names):

        providers = [
            (
                "CUDAExecutionProvider",
                {
                    "device_id": 0,
                },
            ),
            # 'CPUExecutionProvider',
        ]
        inputs = torch.from_numpy(cropped_images).to("cuda")
        # output_path = "/workspace/assets/models/baseline_exp1_-epoch=2_acc=0.onnx"
        # exported_model = onnx.load(output_path)
        # onnx.checker.check_model(exported_model)
        # ort_session = onnxruntime.InferenceSession(output_path, providers=providers)
        # compute ONNX Runtime output prediction
        ort_inputs = {
            self.artifacts.recognition.get_inputs()[0].name: self.to_numpy(inputs),
        }
        ort_outs = self.artifacts.recognition.run(None, ort_inputs)
        # ort_outs = ort_session.run(None, ort_inputs)
        # np.testing.assert_allclose(self.to_numpy(torch_out), ort_outs[0], rtol=1e-03, atol=1e-05)
        return ort_outs

    @api(input=ImageInput(), batch=False)
    def document_ocr(self, img):
        img = cv2.resize(img, dsize=(2052, 2736), interpolation=cv2.INTER_AREA)

        img_tensor, start_t = self.detection_preprocessing(img)
        with torch.no_grad():
            boxes, labels, scores, img_size = self.artifacts.detection(img_tensor)
            # print(boxes)

        (
            cropped_images,
            class_masks,
            detection_boxes,
            detection_scores,
            detection_classes,
        ) = self.detection_postprocessing(img, boxes, scores, labels, start_t)

        print(f"boxes size: {np.array(detection_boxes).shape}")
        self.savepath = f"/workspace/others/assets/deidentify_img_sg_{self.detection_threshold}.jpg"
        info_save_dir = os.path.join(settings.ID_DEBUG_INFO_PATH, time.strftime("%Y%m%d"))
        os.makedirs(info_save_dir, exist_ok=True)
        info_save_path = os.path.join(info_save_dir, os.path.basename(self.savepath))
        deidentify_img(img, detection_boxes, detection_classes, info_save_path)

        # cv2.imwrite("/workspace/others/assets/bytes_to_document.png", img)

        start_t = time.time()

        (
            cropped_images,
            fixed_batch_size,
            rec_sess,
            output_names,
        ) = self.recognition_preprocessing(cropped_images)

        rec_preds = self.recognition(
            cropped_images, fixed_batch_size, rec_sess, class_masks, output_names
        )

        logger.info(f"Recognition inference time: \t{(time.time()-start_t) * 1000:.2f}ms")
        return {
            "rec_preds": np.array(np.argmax(rec_preds[0], axis=-1)),
            "scores": np.array(detection_scores),
            "boxes": np.array(detection_boxes),
            "img_size": np.array(img_size),
        }
