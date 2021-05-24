import numpy as np
import cv2
import time
import numpy as np
import os
import sys

sys.path.append("/workspace/app")

import re
import cv2
import time
import numpy as np
import onnxruntime as rt
import imutils

from bentoml import env, artifacts, api, BentoService
from bentoml.adapters import ImageInput
from bentoml.frameworks.onnx import OnnxModelArtifact

from datetime import datetime
from service_streamer import ThreadedStreamer
from onnxruntime.capi.onnxruntime_pybind11_state import Fail

from lovit.utils.converter import CharacterMaskGenerator, build_converter
from serving.idcard_utils.utils import revert_size, get_cropped_images, build_preprocess, _load_models
from serving.idcard_utils.catalogs import ELabelCatalog, EDocumentCatalog
from serving.idcard_utils.utils import (
    mask_to_quad, 
    order_points, 
    load_json,
    check_angle_label,
    save_debug_img,
    deidentify_img,
    _filter_class,
    _get_class_masks,
    _get_fixed_batch,
    _to_wide,
    _expand_size,
    _add_backup_boxes,
    _rectify_img,

)
from serving.idcard_utils.envs import cfgs, logger
from serving.idcard_utils.errors import InferenceError


characters = ELabelCatalog.get(("num","eng_cap","eng_low","kor_2350","symbols"), decipher=cfgs.DECIPHER)
converter = build_converter(characters, True)
mask_generator = CharacterMaskGenerator(converter)
mask_generator.class_mask_map.update(EDocumentCatalog.ID_CARD)

boundary_score_threshold = float(cfgs.ID_BOUNDARY_SCORE_TH)
boundary_crop_expansion = int(cfgs.ID_BOUNDARY_CROP_EXPANSION)
kv_score_threshold = float(cfgs.ID_KV_SCORE_TH)
kv_box_expansion = float(cfgs.ID_BOX_EXPANSION)
remove_region_code = bool(cfgs.ID_DLC_REMOVE_REGION_CODE)
min_size = int(cfgs.ID_IMG_MIN_SIZE)


service_cfg = load_json("/workspace/app/serving/idcard_utils/textscope_id.json")["idcard"]
batch_size = service_cfg['batch_size'] if 'batch_size' in service_cfg else 256
with_async = service_cfg['with_async'] if 'with_async' in service_cfg else False
valid_type = {
    'RRC': ['id', 'issue_date', 'name'],
    'DLC': ['id', 'issue_date', 'name', 'dlc_license_region', 'dlc_license_num', 'dlc_serial_num'],
    'ARC_FRONT': ['id', 'issue_date', 'name', 'arc_nationality', 'arc_visa'],
    'ARC_BACK': ['expiration_date']
}
essential_keys = {
    'RRC': ['id', 'name', 'issue_date'],
    'DLC': ['id', 'issue_date', 'name', 'dlc_license_num'],
    'ARC_FRONT': ['id', 'issue_date', 'name', 'arc_nationality'],
    'ARC_BACK': ['expiration_date']
}
deidentify_classes = ['id', 'dlc_license_num']
save_output_img = cfgs.OUTPUT_IMG_SAVE

target_width = int(cfgs.ID_TRANSFORM_TARGET_WIDTH)
target_height = int(cfgs.ID_TRANSFORM_TARGET_HEIGHT)
date_reg = re.compile(r'[^0-9]+')

infer_sess_map = dict()
_load_models(infer_sess_map, service_cfg)
orb_matcher = dict()

savepath = "/workspace/app/outputs/idcard/test.png"
id_type = None



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

        response_log = dict()

        start_t = time.time()
        tic_request = time.time()
        time_request = datetime.now().strftime('%Y.%m.%d. %H:%M:%S.%f')
        response_log.update({"time_textscope_request": time_request})

        img_arr = _expand_size(_to_wide(imgs[0]))
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
                img_arr = img_arr[erosion_y:height-erosion_y, erosion_x:width-erosion_x, :]
                boundary_box, boundary_score, boundary_angle, H, is_portrait = self._boundary_infer(img_arr)
                if boundary_box is not None:
                    break

        if boundary_box is None:
            logger.debug("Unable to find id card (3)")
                
        if boundary_box is None:
            use_full_img = True
        else:
            short_width = boundary_box[2]-boundary_box[0] < img_arr.shape[1]*0.1
            short_height = boundary_box[3]-boundary_box[1] < img_arr.shape[0]*0.1
            if short_width or short_height:
                use_full_img = True

        if use_full_img:
            id_image_arr = img_arr.copy()
        else:
            id_image_arr = img_arr[boundary_box[1]:boundary_box[3],boundary_box[0]:boundary_box[2],:]

        if H is not None and cfgs.ID_USE_TRANSFORM_BOUNDARY and not use_full_img:
            # id_image_arr = _rectify_img(id_image_arr, H, boundary_angle, is_portrait)
            id_image_arr = _rectify_img(img_arr, H, boundary_angle, is_portrait)

        if boundary_angle == 1:
            pass
        elif boundary_angle == 2:
            id_image_arr = cv2.rotate(id_image_arr, cv2.ROTATE_90_CLOCKWISE)
        elif boundary_angle == 3:
            id_image_arr = cv2.rotate(id_image_arr, cv2.ROTATE_180)
        elif boundary_angle == 4:
            id_image_arr = cv2.rotate(id_image_arr, cv2.ROTATE_90_COUNTERCLOCKWISE)

        kv_boxes, kv_scores, kv_classes = self._kv_infer(id_image_arr)
        if kv_boxes is None:
            if boundary_angle == 5:
                id_image_arr = cv2.rotate(id_image_arr, cv2.ROTATE_90_CLOCKWISE)
            elif boundary_angle == 6:
                id_image_arr = cv2.rotate(id_image_arr, cv2.ROTATE_180)
            elif boundary_angle == 7:
                id_image_arr = cv2.rotate(id_image_arr, cv2.ROTATE_90_COUNTERCLOCKWISE)

            logger.info("Unable to detect kv_boxes")
            raise InferenceError({
                'code': 'T5001',
                'message': 'Unable to extract information from id card'
            }, 500)
        if cfgs.ID_FORCE_TYPE:
            kv_boxes, kv_scores, kv_classes = _filter_class(kv_boxes, kv_scores, kv_classes, id_type)
        edges_length = kv_boxes[:,2:] - kv_boxes[:,:2]
        short_edges = (edges_length <= 5).any(axis=1)

        kv_boxes = kv_boxes[~short_edges]
        kv_scores = kv_scores[~short_edges]
        kv_classes = kv_classes[~short_edges]
        id_height, id_width = id_image_arr.shape[:2]

        if cfgs.ID_ADD_BACKUP_BOXES:
            inputs = (
                kv_boxes, kv_scores, kv_classes, id_type, (id_width, id_height)
            )
            kv_boxes, kv_scores, kv_classes = _add_backup_boxes(*inputs)

        cropped_images = get_cropped_images(id_image_arr, kv_boxes)
        if save_output_img and savepath is not None:
            deidentify_img(id_image_arr, kv_boxes, kv_classes, savepath)
        
        if cfgs.SAVE_ID_DEBUG_INFO and cfgs.ID_DEBUG_INFO_PATH is not None:
            info_save_dir = os.path.join(cfgs.ID_DEBUG_INFO_PATH, time.strftime('%Y%m%d'))
            os.makedirs(info_save_dir, exist_ok=True)
            info_save_path = os.path.join(info_save_dir, os.path.basename(savepath))
            deidentify_img(id_image_arr, kv_boxes, kv_classes, info_save_path)

        class_masks = _get_class_masks(kv_classes)
        texts = self._rec_infer(cropped_images, class_masks)
        
        # TO DEBUG OUTPUT OF INFERENCE
        if save_output_img and savepath is not None and cfgs.DEVELOP and cfgs.ID_DRAW_BBOX_IMG:
            save_debug_img(id_image_arr, kv_boxes, kv_classes, texts, savepath)

        # if boundary_box is not None:
        #     kv_boxes[:,0::2] += boundary_box[0] - boundary_crop_expansion
        #     kv_boxes[:,1::2] += boundary_box[1] - boundary_crop_expansion

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
        for _proc in infer_sess_map['boundary_model']['preprocess']:
            img_arr, extra_info = _proc(img_arr, extra_info=extra_info)

        inputs = {
            'images': np.expand_dims(img_arr.astype(np.float32), axis=0)
        }
        output_names = infer_sess_map['boundary_model']['output_names']
        use_mask = 'mask' in output_names
        use_keypoint = 'keypoints' in output_names
        if use_mask:
            try:
                boxes, labels, scores, masks = self.artifacts.boundary_detection.run(output_names,inputs)
                # boxes, labels, scores, masks = MultiModelService.artifacts.boundary_detection.run(output_names,inputs)
            except Fail:
                boxes, labels, scores, masks = None, None, None, None
            except Exception as e:
                raise
        elif use_keypoint:
            try:
                boxes, labels, scores, keypoints = self.artifacts.boundary_detection.run(output_names,inputs)
            except Exception as e:
                boxes, labels, scores, keypoints = None, None, None, None
        else:
            boxes, labels, scores = self.artifacts.boundary_detection.run(output_names,inputs)
        if boxes is None:
            return None, None, None, None, False

        valid_indicies = scores > boundary_score_threshold
        valid_scores = scores[valid_indicies]
        valid_boxes = boxes[valid_indicies]
        valid_labels = labels[valid_indicies]
        if use_mask:
            valid_mask = masks[valid_indicies]
        if use_keypoint:
            valid_keypoints = keypoints[valid_indicies]
        if len(valid_boxes) < 1:
            return None, None, None, None, False
        current_size = (extra_info['size_after_resize_before_pad'][1], extra_info['size_after_resize_before_pad'][0])
        valid_boxes = revert_size(valid_boxes, current_size, original_size).astype(np.int32)
        argmax_score = np.argmax(valid_scores)
        boundary_box = valid_boxes[argmax_score]
        boundary_score = valid_scores[argmax_score]
        angle_label = valid_labels[argmax_score]
        H = None
        is_portrait = False
        
        # boundary_box[:2] -= boundary_crop_expansion
        # boundary_box[2:] += boundary_crop_expansion
        boundary_box[0::2] = np.clip(boundary_box[0::2], 0, original_size[0] - 1)
        boundary_box[1::2] = np.clip(boundary_box[1::2], 0, original_size[1] - 1)

        if use_mask and cfgs.ID_USE_BOUNDARY_MASK_TRANSFORM:
            boundary_mask = valid_mask[argmax_score]
            boundary_quad = mask_to_quad(
                boundary_mask, 
                boundary_box,
                mask_threshold=cfgs.ID_BOUNDARY_MASK_THRESH,
                force_rect=cfgs.ID_BOUNDARY_MASK_FORCE_RECT
            )
            boundary_quad = order_points(boundary_quad)

            if angle_label in [2, 4]:
                target_quad = np.array([
                    [0, 0],
                    [target_height - 1, 0],
                    [target_height - 1, target_width - 1],
                    [0, target_width - 1]
                ])
            else:
                target_quad = np.array([
                    [0, 0],
                    [target_width - 1, 0],
                    [target_width - 1, target_height - 1],
                    [0, target_height - 1]
                ])
            src_points = boundary_quad.copy()
            src_points[:, 0] += boundary_box[0]
            src_points[:, 1] += boundary_box[1]
            H, _ = cv2.findHomography(src_points, target_quad, method=0)

        if use_keypoint:
            boundary_quad = valid_keypoints[0,:,:2]
            boundary_quad = revert_size(boundary_quad, current_size, original_size).astype(np.int32)
            length_top_edge = np.linalg.norm(boundary_quad[0]-boundary_quad[1])
            length_right_edge = np.linalg.norm(boundary_quad[1]-boundary_quad[2])
            angle_label = check_angle_label(boundary_quad)

            # w_index = np.argsort(boundary_quad[:,0])
            # h_index = np.argsort(boundary_quad[:,1])
            # boundary_quad[:,0][w_index[:2]]-=boundary_crop_expansion
            # boundary_quad[:,0][w_index[2:]]+=boundary_crop_expansion
            # boundary_quad[:,1][h_index[:2]]-=boundary_crop_expansion
            # boundary_quad[:,1][h_index[2:]]+=boundary_crop_expansion
            boundary_quad[:,0] = np.clip(boundary_quad[:,0], 0, original_size[0])
            boundary_quad[:,1] = np.clip(boundary_quad[:,1], 0, original_size[1])

            if length_top_edge < length_right_edge:
                target_quad = np.array([
                    [0, 0],
                    [target_height, 0],
                    [target_height, target_width],
                    [0, target_width]
                ])
                is_portrait = True
            else:
                target_quad = np.array([
                    [0, 0],
                    [target_width, 0],
                    [target_width, target_height],
                    [0, target_height]
                ])
            boundary_quad[:,0]-=boundary_quad[:,0].min()
            boundary_quad[:,1]-=boundary_quad[:,1].min()
            H, mask = cv2.findHomography(boundary_quad, target_quad, method=0)

        logger.info(f"Bound inference time: \t{(time.time()-start_t) * 1000:.2f}ms")
        return boundary_box,  boundary_score, angle_label, H, is_portrait
    
    def _kv_infer(self, img_arr):
        start_t = time.time()
        original_size = (img_arr.shape[1], img_arr.shape[0])
        extra_info = dict()
        for _proc in infer_sess_map['kv_model']['preprocess']:
            img_arr, extra_info = _proc(img_arr, extra_info=extra_info)
        inputs = {
            'images': np.expand_dims(img_arr.astype(np.float32), axis=0)
        }

        output_names = infer_sess_map['kv_model']['output_names']
        boxes, labels, scores = self.artifacts.kv_detection.run(output_names, inputs)
        valid_indicies = scores > kv_score_threshold
        valid_scores = scores[valid_indicies]
        valid_boxes = boxes[valid_indicies]
        valid_labels = labels[valid_indicies]
        if len(valid_boxes) < 1:
            return None, None, None
        ind = np.lexsort((valid_boxes[:,1], valid_boxes[:, 0]))
        valid_boxes = valid_boxes[ind]
        valid_scores = valid_scores[ind]
        valid_labels = valid_labels[ind]
        current_size = (extra_info['size_after_resize_before_pad'][1], extra_info['size_after_resize_before_pad'][0])
        valid_boxes = revert_size(valid_boxes, current_size, original_size).astype(np.int32)
        lookup_table = infer_sess_map['kv_model']['config']['label_classes']
        kv_classes = lookup_table[valid_labels]
        logger.info(f"KV inference time: \t{(time.time()-start_t) * 1000:.2f}ms")


        valid_boxes_w = valid_boxes[:,2] - valid_boxes[:,0]
        valid_boxes_h = valid_boxes[:,3] - valid_boxes[:,1]
        valid_boxes_ar = valid_boxes_w/valid_boxes_h
        w_expand  = valid_boxes_w*kv_box_expansion
        h_expand  = valid_boxes_h*kv_box_expansion
        _expand = np.minimum(w_expand, h_expand).astype(np.int32)
        # _expand = (np.minimum(w_expand, h_expand)*np.abs(np.log(valid_boxes_ar))).astype(np.int32)
        valid_boxes[:, 0] -= _expand
        valid_boxes[:, 1] -= _expand
        valid_boxes[:, 2] += _expand
        valid_boxes[:, 3] += _expand
        valid_boxes[:, 0::2] = np.clip(valid_boxes[:, 0::2], 0, original_size[0])
        valid_boxes[:, 1::2] = np.clip(valid_boxes[:, 1::2], 0, original_size[1])
        return valid_boxes, valid_scores, kv_classes

    def _rec_infer(self, cropped_images, class_masks):
        start_t = time.time()
        rec_sess = self.artifacts.recognition
        info_list = list()
        for i in range(len(cropped_images)):
            extra_info = dict()
            for _proc in infer_sess_map['recognition_model']['preprocess']:
                cropped_images[i], extra_info = _proc(cropped_images[i], extra_info=extra_info)
            info_list.append(extra_info)

        cropped_images = np.stack(cropped_images)
        cropped_images = cropped_images.astype(np.float32)

        output_names = [_.name for _ in rec_sess.get_outputs()]
        rec_preds = []
        fixed_batch_size = infer_sess_map['recognition_model']['batch_size']
        for i in range(0, len(cropped_images), fixed_batch_size):
            if (i + fixed_batch_size) < len(cropped_images):
                end = i +  fixed_batch_size
            else:
                end = len(cropped_images)
            _cropped_images = cropped_images[i:end]
            _class_masks = class_masks[i:end]
            inputs = _get_fixed_batch(fixed_batch_size, _cropped_images, _class_masks)
            inputs = dict((rec_sess.get_inputs()[i].name, inpt) for i, inpt in enumerate(inputs))
            results = rec_sess.run(output_names, inputs)

            preds = results[0][:(end - i)]
            rec_preds = np.concatenate([rec_preds, preds]) if len(rec_preds) > 0 else preds

        texts = converter.decode(rec_preds, [rec_preds.shape[0]]*len(rec_preds))
        texts = [_t[:_t.find('[s]')] for _t in texts]
        logger.info(f"Rec inference time: \t{(time.time()-start_t) * 1000:.2f}ms")
        return texts