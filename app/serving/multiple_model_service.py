import numpy as np
import time
import os
import imutils
import sys

from datetime import datetime
from bentoml import env, artifacts, api, BentoService
from bentoml.adapters import ImageInput
from bentoml.frameworks.onnx import OnnxModelArtifact
from onnxruntime.capi.onnxruntime_pybind11_state import Fail

sys.path.append("/workspace")
from app.serving.envs import cfgs, logger
from app.errors.exceptions import InferenceException
from app.serving.utils import (
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
    load_models
)


@env(pip_packages=['torchvision'])
@env(infer_pip_packages=True)
@artifacts([
    OnnxModelArtifact('boundary_detection'),
    OnnxModelArtifact('kv_detection'),
    OnnxModelArtifact('recognition'),
])
class MultiModelService(BentoService):
    def __init__(self):
        super().__init__()
        self.infer_sess_map = dict()
        self.service_cfg = load_json(cfgs.SERVICE_CFG_PATH)['idcard']
        load_models(self.infer_sess_map, self.service_cfg)

        self.save_output_img = True
        self.id_type = None
        self.savepath = cfgs.SAVEPATH

    @api(input=ImageInput(), batch=True)
    def inference(self, imgs):
        """
        An inference APId `predict` with Dataframe input adapter, which codifies
        how HTTP requests or CSV files are converted to a pandas Dataframe object as the
        inference API function input
        """
        response_log = dict()

        start_t = time.time()
        tic_request = time.time()
        time_request = datetime.now().strftime('%Y.%m.%d. %H:%M:%S.%f')
        response_log.update({"time_textscope_request": time_request})

        img_arr = expand_size(to_wide(imgs[0]))
        use_full_img = False

        boundary_box, boundary_score, boundary_angle, H, is_portrait = self._boundary_infer(img_arr)

        if boundary_box is None:
            logger.debug("Unable to find id card")

        if boundary_box is None and cfgs.ID_ROTATE_FIND:
            for rotate_angle in cfgs.ID_ROTATE_ANGLE:
                logger.debug(f"Rotate and find: {rotate_angle}")
                img_arr = imutils.rotate_bound(img_arr, int(rotate_angle))
                boundary_box, boundary_score, boundary_angle, H, is_portrait = self._boundary_infer(img_arr)
                if boundary_box is not None:
                    break

        if boundary_box is None:
            logger.debug("Unable to find id card (2)")

        if boundary_box is None and cfgs.ID_CROP_FIND:
            for i in range(cfgs.ID_CROP_FIND_NUM):
                height, width = img_arr.shape[:2]
                erosion_x = int(width * (1 - cfgs.ID_CROP_FIND_RATIO)) // 2
                erosion_y = int(height * (1 - cfgs.ID_CROP_FIND_RATIO)) // 2
                logger.debug(f"Erode and find: erosion_x={erosion_x}, erosion_y={erosion_y} / width={width}, height={height}")
                img_arr = img_arr[erosion_y:height - erosion_y, erosion_x:width - erosion_x, :]
                boundary_box, boundary_score, boundary_angle, H, is_portrait = self._boundary_infer(img_arr)
                if boundary_box is not None:
                    break

        if boundary_box is None:
            logger.debug("Unable to find id card (3)")

        if boundary_box is None:
            use_full_img = True
        else:
            short_width = boundary_box[2] - boundary_box[0] < img_arr.shape[1] * 0.1
            short_height = boundary_box[3] - boundary_box[1] < img_arr.shape[0] * 0.1
            if short_width or short_height:
                use_full_img = True

        if use_full_img:
            id_image_arr = img_arr.copy()
        else:
            id_image_arr = img_arr[boundary_box[1]:boundary_box[3], boundary_box[0]:boundary_box[2], :]

        if H is not None and cfgs.ID_USE_TRANSFORM_BOUNDARY and not use_full_img:
            id_image_arr = rectify_img(img_arr, H, boundary_angle, is_portrait)

        id_image_arr = roate_image(boundary_angle, id_image_arr)

        kv_boxes, kv_scores, kv_classes = self._kv_infer(id_image_arr)

        if kv_boxes is None:
            # 이 부분은 왜 있는건가? raise 실행되나?
            id_image_arr = roate_image(boundary_angle, id_image_arr)

            logger.info("Unable to detect kv_boxes")
            raise InferenceException({
                'code': 'T4001',
                'message': 'Invalid image file',
            }, 400)
        if cfgs.ID_FORCE_TYPE:
            kv_boxes, kv_scores, kv_classes = filter_class(kv_boxes, kv_scores, kv_classes, self.id_type)

        kv_boxes, kv_scores, kv_classes = kv_postprocess_with_edge(kv_boxes, kv_scores, kv_classes)

        id_height, id_width = id_image_arr.shape[:2]
        if cfgs.ID_ADD_BACKUP_BOXES:
            inputs = (
                kv_boxes, kv_scores, kv_classes, self.id_type, (id_width, id_height)
            )
            kv_boxes, kv_scores, kv_classes = add_backup_boxes(*inputs)

        cropped_images = get_cropped_images(id_image_arr, kv_boxes)
        if self.save_output_img and self.savepath is not None:
            deidentify_img(id_image_arr, kv_boxes, kv_classes, self.savepath)

        if cfgs.SAVE_ID_DEBUG_INFO and cfgs.ID_DEBUG_INFO_PATH is not None:
            info_save_dir = os.path.join(cfgs.ID_DEBUG_INFO_PATH, time.strftime('%Y%m%d'))
            os.makedirs(info_save_dir, exist_ok=True)
            info_save_path = os.path.join(info_save_dir, os.path.basename(self.savepath))
            deidentify_img(id_image_arr, kv_boxes, kv_classes, info_save_path)

        class_masks = get_class_masks(kv_classes)
        texts = self._rec_infer(cropped_images, class_masks)

        # TO DEBUG OUTPUT OF INFERENCE
        if self.save_output_img and self.savepath is not None and cfgs.DEVELOP and cfgs.ID_DRAW_BBOX_IMG:
            save_debug_img(id_image_arr, kv_boxes, kv_classes, texts, self.savepath)

        logger.info(f"Total inference time: \t{(time.time()-start_t) * 1000:.2f}ms")

        tic_response = time.time()
        time_response = datetime.now().strftime('%Y.%m.%d. %H:%M:%S.%f')
        time_elapsed = tic_response - tic_request
        response_log["time_textscope_response"] = time_response
        response_log["time_textscope_total"] = f"{time_elapsed:.3f} seconds"

        return [{"response_log": response_log, "texts": texts}]

    def _boundary_infer(self, img_arr):
        start_t = time.time()
        original_size = (img_arr.shape[1], img_arr.shape[0])
        extra_info = dict()
        for _proc in self.infer_sess_map['boundary_model']['preprocess']:
            img_arr, extra_info = _proc(img_arr, extra_info=extra_info)

        inputs = {
            'images': np.expand_dims(img_arr.astype(np.float32), axis=0)
        }
        output_names = self.infer_sess_map['boundary_model']['output_names']
        use_mask = 'mask' in output_names
        use_keypoint = 'keypoints' in output_names
        masks = None
        H = None
        is_portrait = False

        if use_mask:
            try:
                boxes, labels, scores, masks = self.artifacts.boundary_detection.run(output_names, inputs)
            except Fail:
                boxes, labels, scores, masks = None, None, None, None
            except Exception as e:
                raise
        elif use_keypoint:
            try:
                boxes, labels, scores, keypoints = self.artifacts.boundary_detection.run(output_names, inputs)
            except Exception as e:
                boxes, labels, scores, keypoints = None, None, None, None
        else:
            boxes, labels, scores = self.artifacts.boundary_detection.run(output_names, inputs)
        if boxes is None:
            return None, None, None, None, False

        (valid_mask, valid_keypoints, current_size, argmax_score, boundary_box, boundary_score, angle_label) = \
            boundary_postprocess(scores, boxes, labels, use_mask, use_keypoint, masks, keypoints, extra_info, original_size)

        if use_mask and cfgs.ID_USE_BOUNDARY_MASK_TRANSFORM:
            H = if_use_mask(valid_mask, argmax_score, boundary_box, angle_label)
        elif use_keypoint:
            H, mask = if_use_keypoint(valid_keypoints, current_size, original_size)

        logger.info(f"Bound inference time: \t{(time.time()-start_t) * 1000:.2f}ms")

        return boundary_box, boundary_score, angle_label, H, is_portrait

    def _kv_infer(self, img_arr):
        start_t = time.time()
        original_size = (img_arr.shape[1], img_arr.shape[0])
        extra_info = dict()
        for _proc in self.infer_sess_map['kv_model']['preprocess']:
            img_arr, extra_info = _proc(img_arr, extra_info=extra_info)
        inputs = {
            'images': np.expand_dims(img_arr.astype(np.float32), axis=0)
        }

        output_names = self.infer_sess_map['kv_model']['output_names']
        boxes, labels, scores = self.artifacts.kv_detection.run(output_names, inputs)

        valid_scores, valid_boxes, kv_classes = kv_postprocess(scores, boxes, labels, extra_info, self.infer_sess_map, original_size)
        logger.info(f"KV inference time: \t{(time.time()-start_t) * 1000:.2f}ms")

        valid_boxes = update_valid_kv_boxes(valid_boxes, original_size)

        return valid_boxes, valid_scores, kv_classes

    def _rec_infer(self, cropped_images, class_masks):
        start_t = time.time()
        rec_sess = self.artifacts.recognition
        info_list = list()
        for i in range(len(cropped_images)):
            extra_info = dict()
            for _proc in self.infer_sess_map['recognition_model']['preprocess']:
                cropped_images[i], extra_info = _proc(cropped_images[i], extra_info=extra_info)
            info_list.append(extra_info)

        cropped_images = np.stack(cropped_images)
        cropped_images = cropped_images.astype(np.float32)

        output_names = [_.name for _ in rec_sess.get_outputs()]
        rec_preds = []
        fixed_batch_size = self.infer_sess_map['recognition_model']['batch_size']
        for i in range(0, len(cropped_images), fixed_batch_size):
            if (i + fixed_batch_size) < len(cropped_images):
                end = i + fixed_batch_size
            else:
                end = len(cropped_images)
            _cropped_images = cropped_images[i:end]
            _class_masks = class_masks[i:end]
            inputs = get_fixed_batch(fixed_batch_size, _cropped_images, _class_masks)
            inputs = dict((rec_sess.get_inputs()[i].name, inpt) for i, inpt in enumerate(inputs))
            results = rec_sess.run(output_names, inputs)

            preds = results[0][:(end - i)]
            rec_preds = np.concatenate([rec_preds, preds]) if len(rec_preds) > 0 else preds

        texts = convert_recognition_to_text(rec_preds)
        logger.info(f"Rec inference time: \t{(time.time()-start_t) * 1000:.2f}ms")

        return texts
