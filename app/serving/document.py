import numpy as np
import time
import torch
import torchvision

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
                cropped_images[i], extra_info = _proc(
                    cropped_images[i], extra_info=extra_info
                )
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

        return (
            cropped_images,
            class_masks,
            valid_boxes.astype(int),
            valid_scores,
            kv_classes,
        )

    def recognition_postprocessing(self, rec_preds, start_t):
        texts = convert_recognition_to_text(rec_preds)
        logger.info(f"Rec inference time: \t{(time.time()-start_t) * 1000:.2f}ms")
        return texts

    def recognition(
        self, cropped_images, fixed_batch_size, rec_sess, class_masks, output_names
    ):
        rec_preds = []
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
        return rec_preds

    @api(input=ImageInput(), batch=False)
    def document_ocr(self, img):
        img_tensor, start_t = self.detection_preprocessing(img)
        with torch.no_grad():
            boxes, labels, scores, _ = self.artifacts.detection(img_tensor)
        (
            cropped_images,
            class_masks,
            kv_boxes,
            kv_scores,
            kv_classes,
        ) = self.detection_postprocessing(img, boxes, scores, labels, start_t)

        (
            cropped_images,
            fixed_batch_size,
            rec_sess,
            output_names,
        ) = self.recognition_preprocessing(cropped_images)

        rec_preds = self.recognition(
            cropped_images, fixed_batch_size, rec_sess, class_masks, output_names
        )

        texts = self.recognition_postprocessing(rec_preds, start_t)

        logger.debug(f"kv_boxes: {kv_boxes}")
        logger.debug(f"kv_scores: {kv_scores}")

        return [{"texts": texts}]
