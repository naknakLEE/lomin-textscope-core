import cv2
import math
import numpy as np
import json
import os
import sys
import onnxruntime as rt
import time

from collections import defaultdict

# from service_streamer import ThreadedStreamer
from shapely.geometry import Polygon
from lovit.utils.converter import CharacterMaskGenerator, build_converter

from app.serving.utils.envs import logger, settings
from app.serving.utils.catalogs import ELabelCatalog, EDocumentCatalog
from app.errors.exceptions import InferenceException


characters = ELabelCatalog.get(
    ("num", "eng_cap", "eng_low", "kor_2350", "symbols"), decipher=settings.DECIPHER
)
converter = build_converter(characters, True)
mask_generator = CharacterMaskGenerator(converter)
mask_generator.class_mask_map.update(EDocumentCatalog.ID_CARD)

boundary_score_threshold = float(settings.ID_BOUNDARY_SCORE_TH)
kv_score_threshold = float(settings.ID_KV_SCORE_TH)
kv_box_expansion = float(settings.ID_BOX_EXPANSION)
target_width = int(settings.ID_TRANSFORM_TARGET_WIDTH)
target_height = int(settings.ID_TRANSFORM_TARGET_HEIGHT)
min_size = int(settings.ID_IMG_MIN_SIZE)
deidentify_classes = ["id", "dlc_license_num"]
valid_type = {
    "RRC": ["id", "issue_date", "name"],
    "DLC": [
        "id",
        "issue_date",
        "name",
        "dlc_license_region",
        "dlc_license_num",
        "dlc_serial_num",
    ],
    "ARC_FRONT": ["id", "issue_date", "name", "arc_nationality", "arc_visa"],
    "ARC_BACK": ["expiration_date"],
}


def load_json(path):
    with open(path, mode="r", encoding="utf-8") as f:
        data = f.read()
    return json.loads(data)


def pad_with_stride(img_arr, stride=32):
    max_size = list(img_arr.shape)
    max_size[1] = int(math.ceil(img_arr.shape[1] / stride) * stride)
    max_size[2] = int(math.ceil(img_arr.shape[2] / stride) * stride)
    pad_img = np.zeros(max_size)
    pad_img[: img_arr.shape[0], : img_arr.shape[1], : img_arr.shape[2]] = img_arr
    return pad_img


def revert_size(boxes, current_size, original_size):
    if current_size == original_size:
        return boxes
    x_ratio = original_size[0] / current_size[0]
    y_ratio = original_size[1] / current_size[1]
    boxes[:, 0::2] *= x_ratio
    boxes[:, 1::2] *= y_ratio
    return boxes


def get_cropped_images(image, boxes):
    cropped_images = list()
    for box in boxes:
        cropped_images.append(image[box[1] : box[3], box[0] : box[2], :])
    return cropped_images


infinite_defaultdict = lambda: defaultdict(infinite_defaultdict)
default_to_regular = (
    lambda d: {k: default_to_regular(v) for k, v in d.items()}
    if isinstance(d, defaultdict)
    else d
)


def build_resize(resize_cfg):
    """
    Based on resize transform in detection repo
    """
    resize_mode = resize_cfg["resize_mode"]
    if resize_mode == "fixed":
        target_width = resize_cfg["width"]
        target_height = resize_cfg["height"]

        def resize_func(img_arr, extra_info=None):
            return (
                cv2.resize(
                    img_arr,
                    (target_width, target_height),
                    interpolation=cv2.INTER_LINEAR,
                ),
                extra_info,
            )

    elif resize_mode == "keep_ratio":
        min_size = resize_cfg["min_size"]
        max_size = resize_cfg["max_size"]

        def resize_func(img_arr, min_size=min_size, max_size=max_size, extra_info=None):
            h, w = img_arr.shape[0:2]
            oh, ow = -1, -1
            min_original_size = float(min((w, h)))
            max_original_size = float(max((w, h)))

            _max_size = max_original_size / min_original_size * min_size
            max_size = min(_max_size, max_size)
            min_size = round(max_size * min_original_size / max_original_size)

            ow = int(min_size if w < h else max_size)
            oh = int(max_size if w < h else min_size)
            return (
                cv2.resize(img_arr, (ow, oh), interpolation=cv2.INTER_LINEAR),
                extra_info,
            )

    elif resize_mode == "keep_ratio+0.5":
        target_width = resize_cfg["width"]
        target_height = resize_cfg["height"]

        def resize_func(
            img_arr,
            target_width=target_width,
            target_height=target_height,
            extra_info=None,
        ):
            h, w = img_arr.shape[0:2]
            ow, oh = target_width, target_height
            img_aspect_ratio = w / h
            tgt_aspect_ratio = ow / oh
            if img_aspect_ratio > tgt_aspect_ratio:
                img_target_size = (ow, max(int(h * (ow / w)), oh // 2))
            else:
                img_target_size = (max(int(w * (oh / h)), ow // 2), oh)
            ow, oh = img_target_size
            resized_arr = cv2.resize(img_arr, (ow, oh), interpolation=cv2.INTER_LINEAR)
            _h, _w = resized_arr.shape[:2]
            blank = np.zeros((target_height, target_width, 3), dtype=np.uint8)
            blank[:_h, :_w, :] = resized_arr
            return blank, extra_info

    elif resize_mode == "horizontal_padding":
        target_width = resize_cfg["width"]
        target_height = resize_cfg["height"]

        def resize_func(
            img_arr,
            target_width=target_width,
            target_height=target_height,
            extra_info=None,
        ):
            h, w = img_arr.shape[0:2]
            ow, oh = target_width, target_height
            _ow = int(w * (oh / h))
            if _ow < oh:  # min aspect ratio 1
                _ow = oh
            if _ow > ow:  # limit max width
                _ow = ow
            ow = _ow
            resized_arr = cv2.resize(img_arr, (ow, oh), interpolation=cv2.INTER_LINEAR)
            _h, _w = resized_arr.shape[:2]
            blank = np.zeros((target_height, target_width, 3), dtype=np.uint8)
            blank[:_h, :_w, :] = resized_arr
            return blank, extra_info

    elif resize_mode == "cut_n_stack":  # From detection repository
        ow = resize_cfg["width"]
        oh = resize_cfg["height"]

        def ceildiv(a, b):
            return -(-a // b)

        def resize_func(img_arr, extra_info=None, ow=ow, oh=oh):
            no_lines = 1
            h, w = img_arr.shape[0:2]
            img_aspect_ratio = w / h
            tgt_aspect_ratio = ow / oh
            cut_ratio_th = 2.5

            if (1.0 / cut_ratio_th < img_aspect_ratio) and (
                cut_ratio_th > img_aspect_ratio
            ):
                #'keep_ratio+min0.5'
                if img_aspect_ratio > tgt_aspect_ratio:
                    img_target_size = (ow, max(int((h * (ow / w))), oh // 2))
                else:
                    img_target_size = (max(int(w * (oh / h)), ow // 2), oh)
                extra_info["no_lines"] = no_lines
                blank = np.zeros((oh, ow, 3), dtype=np.uint8)
                blank[: img_target_size[1], : img_target_size[0], :] = cv2.resize(
                    img_arr, img_target_size, interpolation=cv2.INTER_LINEAR
                )
                return blank, extra_info

            if img_aspect_ratio < 1.0:
                cut_ratio_list = [
                    1 / (cut_ratio_th * 4),
                    1 / (cut_ratio_th * 3),
                    1 / (cut_ratio_th * 2),
                    1 / cut_ratio_th,
                ]
                cut_size_list = [5, 4, 3, 2]
                cut_size = 2
                for idx, ratio_th in enumerate(cut_ratio_list):
                    if img_aspect_ratio < ratio_th:
                        cut_size = cut_size_list[idx]
                        break
                cut_length = ceildiv(h, cut_size)
                blank = np.zeros((cut_length, cut_size * w, 3), dtype=np.uint8)
                crop_y0 = 0
                paste_x0 = 0
                for idx in range(cut_size):
                    _cut_h = min(crop_y0 + cut_length, h)
                    min_x = 0
                    max_x = w
                    min_y = crop_y0
                    max_y = _cut_h
                    cropped_img = img_arr[min_y:max_y, min_x:max_x, :]

                    min_x = paste_x0
                    max_x = paste_x0 + cropped_img.shape[1]
                    min_y = 0
                    max_y = cropped_img.shape[0]
                    blank[min_y:max_y, min_x:max_x, :] = cropped_img

                    crop_y0 += cut_length
                    paste_x0 += w
                img_arr = blank
            else:
                cut_ratio_list = [
                    cut_ratio_th * 4,
                    cut_ratio_th * 3,
                    cut_ratio_th * 2,
                    cut_ratio_th,
                ]
                cut_size_list = [5, 4, 3, 2]
                cut_size = 2
                for idx, ratio_th in enumerate(cut_ratio_list):
                    if img_aspect_ratio > ratio_th:
                        cut_size = cut_size_list[idx]
                        break

                cut_length = ceildiv(w, cut_size)
                blank = np.zeros((cut_size * h, cut_length, 3), dtype=np.uint8)

                crop_x0 = 0
                paste_y0 = 0
                for idx in range(cut_size):
                    min_x = crop_x0
                    max_x = min(crop_x0 + cut_length, w)
                    min_y = 0
                    max_y = h
                    cropped_img = img_arr[min_y:max_y, min_x:max_x, :]

                    min_x = 0
                    max_x = cropped_img.shape[1]
                    min_y = paste_y0
                    max_y = paste_y0 + cropped_img.shape[0]
                    blank[min_y:max_y, min_x:max_x, :] = cropped_img
                    crop_x0 += cut_length
                    paste_y0 += h
                img_arr = blank

            extra_info["no_lines"] = no_lines
            return (
                cv2.resize(img_arr, (ow, oh), interpolation=cv2.INTER_LINEAR),
                extra_info,
            )

    else:
        raise ValueError
    return resize_func


def build_norm_std(norm_std_cfg):
    """
    Based on torchvision.transforms.Normalize
    https://pytorch.org/docs/stable/torchvision/transforms.html#torchvision.transforms.Normalize
    output[channel] = (input[channel] - mean[channel]) / std[channel]

    """

    norm_mode = norm_std_cfg["mode"] if "mode" in norm_std_cfg else None
    mean = np.array(norm_std_cfg["mean"], dtype=np.float32)
    std = np.array(norm_std_cfg["std"], dtype=np.float32)

    if norm_mode is None:

        def norm_std(img_arr, mean=mean, std=std, extra_info=None):
            img_arr = cv2.cvtColor(np.array(img_arr), cv2.COLOR_BGR2RGB)
            img_arr = ((img_arr - mean) / std).transpose(2, 0, 1)

            return img_arr, extra_info

    elif norm_mode == "n1p1":

        def norm_std(img_arr, mean=mean, std=std, extra_info=None):
            img_arr = cv2.cvtColor(np.array(img_arr), cv2.COLOR_BGR2RGB)
            img_arr = img_arr / 255  # to 0-1 as totensor in pytorch
            img_arr = ((img_arr - mean) / std).transpose(2, 0, 1)
            return img_arr, extra_info

    return norm_std


def build_pad_with_stride(pad_with_stride_cfg):
    stride = pad_with_stride_cfg["stride"]

    def pad_with_stride(img_arr, stride=stride, extra_info=None):
        max_size = list(img_arr.shape)
        max_size[1] = int(math.ceil(img_arr.shape[1] / stride) * stride)
        max_size[2] = int(math.ceil(img_arr.shape[2] / stride) * stride)
        if max_size[1] > max_size[2]:
            max_size[2] = max_size[1]
        else:
            max_size[1] = max_size[2]
        pad_img = np.zeros(max_size)
        pad_img[: img_arr.shape[0], : img_arr.shape[1], : img_arr.shape[2]] = img_arr
        extra_info = {
            "size_after_resize_before_pad": (img_arr.shape[1], img_arr.shape[2])
        }
        return pad_img, extra_info

    return pad_with_stride


PRE_PROCESS_BUILD_MAP = {
    "resize": build_resize,
    "norm_std": build_norm_std,
    "pad_with_stride": build_pad_with_stride,
}


def build_preprocess(preprocess_cfg):
    preprocs_funcs = list()

    for _cfg in preprocess_cfg:
        _type = _cfg["type"]
        assert _type in PRE_PROCESS_BUILD_MAP
        func = PRE_PROCESS_BUILD_MAP[_type](_cfg)
        preprocs_funcs.append(func)
    return preprocs_funcs


def mask_to_quad(mask, box, mask_threshold=0.5, force_rect=False, resize_ratio=5.0):
    min_x = box[0]
    min_y = box[1]
    width = box[2] - min_x
    height = box[3] - min_y

    mask_pred = (mask > mask_threshold).astype(np.uint8)[0]
    mask_width, mask_height = mask_pred.shape

    if resize_ratio > 1.0:
        mask_pred = cv2.resize(
            mask_pred,
            fx=resize_ratio,
            fy=resize_ratio,
            dsize=None,
            interpolation=cv2.INTER_CUBIC,
        )
    contours, _ = cv2.findContours(
        mask_pred, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    contour = np.concatenate(contours, 0)
    contour = cv2.convexHull(contour, False)

    if resize_ratio > 1.0:
        contour = np.rint(contour / resize_ratio).astype(np.int32)

    if force_rect:
        marect = cv2.minAreaRect(contour)
        quad = cv2.boxPoints(marect)
    else:
        epsilon = 0.02 * cv2.arcLength(contour, True)
        eps_min = 0.0
        eps_max = epsilon
        eps = (eps_max + eps_min) / 2

        # find upperbound
        approx = cv2.approxPolyDP(contour, eps, True)
        cnt = 0

        while len(approx) < 4 and cnt < 10:
            eps_max = (eps_max - eps_min) * 2 + eps_max
            eps_min = eps
            eps = (eps_max + eps_min) / 2
            approx = cv2.approxPolyDP(contour, eps, True)
            cnt += 1

        # find possible quadrangle approximation
        if len(approx) != 4:
            for j in range(10):
                approx = cv2.approxPolyDP(contour, eps, True)
                if len(approx) == 4:
                    break
                if len(approx) < 4:  # reduce eps
                    eps_max = eps
                else:  # increase eps
                    eps_min = eps
                eps = (eps_max + eps_min) / 2

        # get rotatedRect
        marect = cv2.minAreaRect(contour)
        marect = cv2.boxPoints(marect)

        approx = np.squeeze(approx)
        contour = np.squeeze(contour)

        if len(approx) != 4:
            quad = marect
        else:
            poly_marect = Polygon([(x, y) for x, y in zip(marect[:, 0], marect[:, 1])])
            poly_approx = Polygon([(x, y) for x, y in zip(approx[:, 0], approx[:, 1])])
            poly_contour = Polygon(
                [(x, y) for x, y in zip(contour[:, 0], contour[:, 1])]
            )

            if (
                not poly_marect.is_valid
                or not poly_approx.is_valid
                or not poly_contour.is_valid
            ):
                quad = marect
            else:
                inter_marect = poly_marect.intersection(poly_contour).area
                inter_approx = poly_approx.intersection(poly_contour).area
                union_marect = poly_marect.union(poly_contour).area
                union_approx = poly_approx.union(poly_contour).area

                iou_marect = inter_marect / union_marect
                iou_approx = inter_approx / union_approx
                if iou_marect > iou_approx:
                    quad = marect
                else:
                    quad = np.squeeze(approx)

    quad[:, 0] = quad[:, 0] * width / mask_width
    quad[:, 1] = quad[:, 1] * height / mask_height

    return np.int32(quad)


def order_points(quad):
    """Order corner points of quadrangle clockwise.
    Args:
        quad (np.ndarray): 4x2 dimension array
    Returns:
        quad (np.ndarray): ordered array
    """
    quad_norm = quad - quad.sum(0) / 4
    atan_angle = np.arctan2(quad_norm[:, 1], quad_norm[:, 0])
    return quad[np.argsort(atan_angle)]


def get_fixed_batch(batch_size, *inputs):
    batch_inputs = []
    for i in inputs:
        if len(i) < batch_size:
            pad = np.zeros((batch_size - len(i), *i.shape[1:]), dtype=i.dtype)
            batch_inputs.append(np.concatenate([i, pad]))
        else:
            batch_inputs.append(i[:batch_size])

    return batch_inputs


def load_models(infer_sess_map: dict, service_cfg: dict, orb_matcher: dict = dict()):
    resources = service_cfg["resources"]
    for resource in resources:
        _type = resource["type"]
        _name = resource["name"]
        _use_streamer = (
            resource["use_streamer"] if "use_streamer" in resource else False
        )
        # _model_path = os.path.join(settings.BASE_PATH, resource['model_path']) if 'model_path' in resource else ''
        _batch_size = resource["batch_size"] if "batch_size" in resource else 1
        _max_latency = resource["max_latency"] if "max_latency" in resource else 0.1
        _preprocess_cfg = resource["preprocess"] if "preprocess" in resource else []
        _extra_config = resource["config"] if "config" in resource else {}
        if _name in infer_sess_map:
            continue

        if _type == "onnx_model":
            # _model_name = os.path.basename(_model_path)
            # if decipher:
            #     dir_path, basename = os.path.split(_model_path)
            #     _model_path = os.path.join(dir_path, decipher.prefix + basename)
            #     _onnx_io = decipher(_model_path)
            #     _sess = rt.InferenceSession(_onnx_io.getvalue())
            # else:
            #     _sess = rt.InferenceSession(_model_path)
            # _sess = rt.InferenceSession(_model_path)

            # output_names = [_.name for _ in _sess.get_outputs()]

            # def batch_prediction(inputs):
            #     images = np.stack(inputs)
            #     outputs = _sess.run(output_names, {'images': images})
            #     batch_size = len(images)
            #     output_list = list()
            #     for i in range(batch_size):
            #         _output = list()
            #         for j in range(len(output_names)):
            #             _output.append(outputs[j][i])
            #         output_list.append(_output)
            #     return output_list

            _pre_process = build_preprocess(_preprocess_cfg)

            if "label_classes" in _extra_config:
                lookup_table = np.asarray(_extra_config["label_classes"])
                _extra_config["label_classes"] = lookup_table
            # if _use_streamer:
            #     streamer = ThreadedStreamer(
            #         batch_prediction,
            #         batch_size=_batch_size,
            #         max_latency=_max_latency
            #     )
            else:
                streamer = None
            infer_sess_map[_name] = {
                "streamer": streamer,
                # 'sess': _sess,
                # 'output_names': output_names,
                "preprocess": _pre_process,
                "config": _extra_config,
                "batch_size": _batch_size,
            }
        elif _type == "orb_matcher":
            assert "config" in resource
            assert (
                "image_path" in resource["config"]
                and len(resource["config"]["image_path"]) > 0
            )
            _image_path = resource["config"]["image_path"]
            orb_matcher["image_path"] = _image_path
        else:
            raise ValueError


def print_data(self, color=35, **kwargs):
    for key, val in kwargs.items():
        logger.info(f"\033[{color}m" + f"{key}: {val}" + "\033[0m")


def check_angle_label(boundary_quad):
    first_w_index = np.where(np.argsort(boundary_quad[:, 0]) == 0)[0][0]
    first_h_index = np.where(np.argsort(boundary_quad[:, 1]) == 0)[0][0]
    if first_w_index < 2 and first_h_index < 2:
        angle_label = 1  # pass
    elif first_w_index >= 2 and first_h_index >= 2:
        angle_label = 6  # cv2.ROTATE_180
    elif first_h_index >= 2:
        angle_label = 5  # cv2.ROTATE_90_CLOCKWISE
    else:
        angle_label = 7  # cv2.ROTATE_90_COUNTERCLOCKWISE
    return angle_label


def save_debug_img(img_arr, kv_boxes, kv_classes, texts, savepath):
    _img_arr = img_arr[:, :, ::-1].copy()
    for _box, _class, _text in zip(kv_boxes, kv_classes, texts):
        min_x, min_y, max_x, max_y = _box.tolist()
        width = max_x - min_x
        height = max_y - min_y
        cv2.rectangle(_img_arr, (min_x, min_y, width, height), (255, 0, 0), 1)
        cv2.putText(
            _img_arr,
            f"{_class}: {_text}",
            (min_x, min_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 0, 0),
            2,
        )
    _img_arr = cv2.cvtColor(_img_arr, cv2.COLOR_BGR2RGB)
    pre_ext, ext = os.path.splitext(savepath)
    savepath_debug = f"{pre_ext}_debug{ext}"
    cv2.imwrite(savepath_debug, _img_arr)


def deidentify_img(img_arr, kv_boxes, kv_classes, savepath):
    start_t = time.time()
    _img_arr = img_arr[:, :, ::-1].copy()
    for _target_cls in deidentify_classes:
        if not _target_cls in kv_classes:
            continue
        indicies = np.where(kv_classes == _target_cls)[0]
        if _target_cls == "dlc_license_num" and len(indicies) == 4:
            index = 2
        else:
            index = 1
        if len(indicies) == 1:
            index = 0
        _box = kv_boxes[indicies[index]]
        _img_arr[_box[1] : _box[3], _box[0] : _box[2], :] = 0

    if settings.DEVELOP:
        for _box, _class in zip(kv_boxes, kv_classes):
            min_x, min_y, max_x, max_y = _box.tolist()
            width = max_x - min_x
            height = max_y - min_y
            _img_arr = cv2.rectangle(
                _img_arr, (min_x, min_y, width, height), (255, 0, 0), 3
            )

    _img_arr = cv2.cvtColor(_img_arr, cv2.COLOR_BGR2RGB)
    if settings.DE_ID_LIMIT_SIZE:
        limit_size = settings.DE_ID_MAX_SIZE
        image_max = max(_img_arr.shape)
        resize_ratio = limit_size / float(image_max)
        if resize_ratio < 1.0:
            _img_arr = cv2.resize(_img_arr, None, fx=resize_ratio, fy=resize_ratio)
    pwd = os.path.dirname(savepath)
    os.makedirs(pwd, exist_ok=True)
    cv2.imwrite(savepath, _img_arr)
    if sys.platform == "linux":
        os.chown(pwd, int(settings.SAVE_UID), int(settings.SAVE_GID))
        os.chown(savepath, int(settings.SAVE_UID), int(settings.SAVE_GID))
    logger.info(f"Deidentify time: \t{(time.time()-start_t) * 1000:.2f}ms")
    return 0


def filter_class(kv_boxes, kv_scores, kv_classes, id_type):
    # remove redundant boxes by checking classes in id_type
    valid_classes = valid_type[id_type] if id_type in valid_type else None
    inval_flags = np.zeros(kv_scores.shape, dtype=np.bool)
    for i, _class in enumerate(kv_classes):
        if _class not in valid_classes:
            inval_flags[i] = True
    return kv_boxes[~inval_flags], kv_scores[~inval_flags], kv_classes[~inval_flags]


def get_class_masks(kv_classes):
    class_masks = None
    for kv_class in kv_classes:
        mask = mask_generator(kv_class)
        mask = np.expand_dims(mask, axis=0)
        class_masks = (
            np.concatenate([class_masks, mask]) if class_masks is not None else mask
        )
    return class_masks


def get_fixed_batch(batch_size, *inputs):
    start_t = time.time()
    batch_inputs = []
    for i in inputs:
        if len(i) < batch_size:
            pad = np.zeros((batch_size - len(i), *i.shape[1:]), dtype=i.dtype)
            batch_inputs.append(np.concatenate([i, pad]))
        else:
            batch_inputs.append(i[:batch_size])

    return batch_inputs


def to_wide(img_arr):
    height, width = img_arr.shape[:2]
    img_aspect_ratio = width / height
    if img_aspect_ratio < 1:
        return cv2.rotate(img_arr, cv2.ROTATE_90_COUNTERCLOCKWISE)
    return img_arr


def expand_size(img_arr):
    height, width = img_arr.shape[:2]
    height_ratio = min_size / height
    width_ratio = min_size / width
    expand_ratio = max(height_ratio, width_ratio)
    if expand_ratio <= 1:
        return img_arr
    target_size = (int(width * expand_ratio), int(height * expand_ratio))
    return cv2.resize(img_arr, target_size)


def add_backup_boxes(kv_boxes, kv_scores, kv_classes, id_type, id_size):
    if id_type == "DLC":
        min_ln_count = 4
        if "dlc_license_region" in kv_classes:
            min_ln_count = 3

        # target_index = 3 #TODO REMOVE THIS LINE
        # dlc_license_num_indicies = np.where(kv_classes=='dlc_license_num') #TODO REMOVE THIS LINE
        # kv_boxes = np.delete(kv_boxes,dlc_license_num_indicies[0][target_index],0) #TODO REMOVE THIS LINE
        # kv_scores = np.delete(kv_scores,dlc_license_num_indicies[0][target_index],0) #TODO REMOVE THIS LINE
        # kv_classes = np.delete(kv_classes,dlc_license_num_indicies[0][target_index],0) #TODO REMOVE THIS LINE

        dlc_license_num_flag = kv_classes == "dlc_license_num"
        ln_indicies = np.where(dlc_license_num_flag)[0]
        ln_boxes = kv_boxes[dlc_license_num_flag]
        ln_box_count = len(ln_boxes)
        if len(ln_boxes) >= min_ln_count or ln_box_count <= 1:
            return kv_boxes, kv_scores, kv_classes
        ln_centers = (
            np.stack(
                [ln_boxes[:, 2] + ln_boxes[:, 0], ln_boxes[:, 3] + ln_boxes[:, 1]],
                axis=1,
            )
            / 2
        )

        ln_ar = (ln_boxes[:, 2] - ln_boxes[:, 0]) / (
            ln_boxes[:, 3] - ln_boxes[:, 1]
        )  # w/h
        long_ln_index = ln_ar.argmax()
        long_ln_ar = ln_ar[long_ln_index]
        if long_ln_ar <= 2:
            return kv_boxes, kv_scores, kv_classes
        ln_distances = np.delete(
            ln_centers - ln_centers[long_ln_index], long_ln_index, 0
        )
        unit_distance = np.abs(ln_distances).mean(axis=0) / 2

        new_box_class = "dlc_license_num"
        new_box_score = 0.5
        if long_ln_index == 1:  # Missing first licenes_num
            new_box = ln_boxes[0].astype(np.float)
            new_box[:2] -= unit_distance * 1.1
            new_box[2:] -= unit_distance * 1.1
            target_index = ln_indicies[0] - 1
        elif long_ln_index == 2:  # Missing last licenes_num:
            new_box = ln_boxes[1].astype(np.float)
            new_box[:2] += unit_distance * 3.1
            new_box[2:] += unit_distance * 3.1
            target_index = ln_indicies[-1] + 1
        new_box = np.expand_dims(new_box, axis=0).astype(np.int)
        new_box_score = np.expand_dims(new_box_score, axis=0)
        new_box_class = np.expand_dims(new_box_class, axis=0)
        kv_boxes = np.concatenate(
            [kv_boxes[:target_index], new_box, kv_boxes[target_index:]]
        )
        kv_scores = np.concatenate(
            [kv_scores[:target_index], new_box_score, kv_scores[target_index:]]
        )
        kv_classes = np.concatenate(
            [kv_classes[:target_index], new_box_class, kv_classes[target_index:]]
        )

        if (
            long_ln_index == 1 and ln_box_count == 2
        ):  # Missing first and last licenes_num
            new_box_class = "dlc_license_num"
            new_box_score = 0.5
            new_box = ln_boxes[0].astype(np.float)
            new_box[:2] += unit_distance * 4.1
            new_box[2:] += unit_distance * 4.1
            target_index = ln_indicies[-1] + 2
            new_box = np.expand_dims(new_box, axis=0).astype(np.int)
            new_box_score = np.expand_dims(new_box_score, axis=0)
            new_box_class = np.expand_dims(new_box_class, axis=0)
            kv_boxes = np.concatenate(
                [kv_boxes[:target_index], new_box, kv_boxes[target_index:]]
            )
            kv_scores = np.concatenate(
                [kv_scores[:target_index], new_box_score, kv_scores[target_index:]]
            )
            kv_classes = np.concatenate(
                [kv_classes[:target_index], new_box_class, kv_classes[target_index:]]
            )
    elif id_type == "RRC":
        name_flag = kv_classes == "name"
        id_flag = kv_classes == "id"
        name_boxes = kv_boxes[name_flag]
        id_boxes = kv_boxes[id_flag]

        if len(name_boxes) == 0 or len(id_boxes) != 1:
            return kv_boxes, kv_scores, kv_classes
        id_index = np.where(id_flag)[0]
        name_x_end = name_boxes[:, 2].mean()
        id_x_center = id_boxes[:, 0::2].mean()
        min_y = id_boxes[0][1]
        max_y = id_boxes[0][3]

        if id_x_center <= name_x_end:
            id_unit_length = abs((id_boxes[0][0] - id_boxes[0][2]) / 6)
            min_x = id_boxes[0][2] + id_unit_length
            max_x = min_x + id_unit_length * 7
            target_index = id_index[0] + 1
        else:
            id_unit_length = abs((id_boxes[0][0] - id_boxes[0][2]) / 7)
            max_x = id_boxes[0][0] - id_unit_length
            min_x = max_x - id_unit_length * 6
            target_index = max(id_index[0] - 1, 0)

        new_box_class = "id"
        new_box_score = 0.5
        new_box = np.array([min_x, min_y, max_x, max_y])
        new_box = np.expand_dims(new_box, axis=0).astype(np.int)
        new_box_score = np.expand_dims(new_box_score, axis=0)
        new_box_class = np.expand_dims(new_box_class, axis=0)
        kv_boxes = np.concatenate(
            [kv_boxes[:target_index], new_box, kv_boxes[target_index:]]
        )
        kv_scores = np.concatenate(
            [kv_scores[:target_index], new_box_score, kv_scores[target_index:]]
        )
        kv_classes = np.concatenate(
            [kv_classes[:target_index], new_box_class, kv_classes[target_index:]]
        )
    return kv_boxes, kv_scores, kv_classes


def rectify_img(img_arr, H, angle_label, is_portrait=False):
    if angle_label in [2, 4] or is_portrait:
        target_size = (target_height, target_width)
    else:
        target_size = (target_width, target_height)
    img_arr = cv2.warpPerspective(img_arr, H, target_size)
    return img_arr


def if_use_keypoint(valid_keypoints, current_size, original_size):
    boundary_quad = valid_keypoints[0, :, :2]
    boundary_quad = revert_size(boundary_quad, current_size, original_size).astype(
        np.int32
    )
    length_top_edge = np.linalg.norm(boundary_quad[0] - boundary_quad[1])
    length_right_edge = np.linalg.norm(boundary_quad[1] - boundary_quad[2])
    angle_label = check_angle_label(boundary_quad)

    boundary_quad[:, 0] = np.clip(boundary_quad[:, 0], 0, original_size[0])
    boundary_quad[:, 1] = np.clip(boundary_quad[:, 1], 0, original_size[1])

    if length_top_edge < length_right_edge:
        target_quad = np.array(
            [
                [0, 0],
                [target_height, 0],
                [target_height, target_width],
                [0, target_width],
            ]
        )
        is_portrait = True
    else:
        target_quad = np.array(
            [
                [0, 0],
                [target_width, 0],
                [target_width, target_height],
                [0, target_height],
            ]
        )
    boundary_quad[:, 0] -= boundary_quad[:, 0].min()
    boundary_quad[:, 1] -= boundary_quad[:, 1].min()
    H, mask = cv2.findHomography(boundary_quad, target_quad, method=0)
    return H, mask


def if_use_mask(valid_mask, argmax_score, boundary_box, angle_label):
    boundary_mask = valid_mask[argmax_score]
    boundary_quad = mask_to_quad(
        boundary_mask,
        boundary_box,
        mask_threshold=settings.ID_BOUNDARY_MASK_THRESH,
        force_rect=settings.ID_BOUNDARY_MASK_FORCE_RECT,
    )
    boundary_quad = order_points(boundary_quad)

    if angle_label in [2, 4]:
        target_quad = np.array(
            [
                [0, 0],
                [target_height - 1, 0],
                [target_height - 1, target_width - 1],
                [0, target_width - 1],
            ]
        )
    else:
        target_quad = np.array(
            [
                [0, 0],
                [target_width - 1, 0],
                [target_width - 1, target_height - 1],
                [0, target_height - 1],
            ]
        )
    src_points = boundary_quad.copy()
    src_points[:, 0] += boundary_box[0]
    src_points[:, 1] += boundary_box[1]
    H, _ = cv2.findHomography(src_points, target_quad, method=0)
    return H


def boundary_postprocess(
    scores,
    boxes,
    labels,
    use_mask,
    use_keypoint,
    masks,
    keypoints,
    extra_info,
    original_size,
):
    valid_mask = None
    valid_keypoints = None
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
    current_size = (
        extra_info["size_after_resize_before_pad"][1],
        extra_info["size_after_resize_before_pad"][0],
    )
    valid_boxes = revert_size(valid_boxes, current_size, original_size).astype(np.int32)
    argmax_score = np.argmax(valid_scores)
    boundary_box = valid_boxes[argmax_score]
    boundary_score = valid_scores[argmax_score]
    angle_label = valid_labels[argmax_score]

    boundary_box[0::2] = np.clip(boundary_box[0::2], 0, original_size[0] - 1)
    boundary_box[1::2] = np.clip(boundary_box[1::2], 0, original_size[1] - 1)

    return (
        valid_mask,
        valid_keypoints,
        current_size,
        argmax_score,
        boundary_box,
        boundary_score,
        angle_label,
    )


def kv_postprocess(scores, boxes, labels, extra_info, infer_sess_map, original_size):
    valid_indicies = scores > kv_score_threshold
    valid_scores = scores[valid_indicies]
    valid_boxes = boxes[valid_indicies]
    valid_labels = labels[valid_indicies]
    if len(valid_boxes) < 1:
        return None, None, None
    ind = np.lexsort((valid_boxes[:, 1], valid_boxes[:, 0]))
    valid_boxes = valid_boxes[ind]
    valid_scores = valid_scores[ind]
    valid_labels = valid_labels[ind]
    current_size = (
        extra_info["size_after_resize_before_pad"][1],
        extra_info["size_after_resize_before_pad"][0],
    )
    zvalid_boxes = revert_size(valid_boxes, current_size, original_size).astype(
        np.int32
    )
    lookup_table = infer_sess_map["kv_model"]["config"]["label_classes"]
    kv_classes = lookup_table[valid_labels]

    return valid_scores, valid_boxes, kv_classes


def update_valid_kv_boxes(valid_boxes, original_size):
    try:
        valid_boxes_w = valid_boxes[:, 2] - valid_boxes[:, 0]
        valid_boxes_h = valid_boxes[:, 3] - valid_boxes[:, 1]
        valid_boxes_ar = valid_boxes_w / valid_boxes_h
        w_expand = valid_boxes_w * kv_box_expansion
        h_expand = valid_boxes_h * kv_box_expansion
        _expand = np.minimum(w_expand, h_expand).astype(np.int32)
        # _expand = (np.minimum(w_expand, h_expand)*np.abs(np.log(valid_boxes_ar))).astype(np.int32)
        valid_boxes[:, 0] -= _expand
        valid_boxes[:, 1] -= _expand
        valid_boxes[:, 2] += _expand
        valid_boxes[:, 3] += _expand
        valid_boxes[:, 0::2] = np.clip(valid_boxes[:, 0::2], 0, original_size[0])
        valid_boxes[:, 1::2] = np.clip(valid_boxes[:, 1::2], 0, original_size[1])
    except Exception:
        raise InferenceException(
            {
                "code": "T4001",
                "message": "Invalid image file",
            },
            400,
        )

    return valid_boxes


def convert_recognition_to_text(rec_preds):
    texts = converter.decode(rec_preds, [rec_preds.shape[0]] * len(rec_preds))
    texts = [_t[: _t.find("[s]")] for _t in texts]
    return texts


def roate_image(boundary_angle, id_image_arr):
    if boundary_angle == 1:
        pass
    elif boundary_angle == 2:
        id_image_arr = cv2.rotate(id_image_arr, cv2.ROTATE_90_CLOCKWISE)
    elif boundary_angle == 3:
        id_image_arr = cv2.rotate(id_image_arr, cv2.ROTATE_180)
    elif boundary_angle == 4:
        id_image_arr = cv2.rotate(id_image_arr, cv2.ROTATE_90_COUNTERCLOCKWISE)
    elif boundary_angle == 5:
        id_image_arr = cv2.rotate(id_image_arr, cv2.ROTATE_90_CLOCKWISE)
    elif boundary_angle == 6:
        id_image_arr = cv2.rotate(id_image_arr, cv2.ROTATE_180)
    elif boundary_angle == 7:
        id_image_arr = cv2.rotate(id_image_arr, cv2.ROTATE_90_COUNTERCLOCKWISE)

    return id_image_arr


def kv_postprocess_with_edge(kv_boxes, kv_scores, kv_classes):
    edges_length = kv_boxes[:, 2:] - kv_boxes[:, :2]
    short_edges = (edges_length <= 5).any(axis=1)

    kv_boxes = kv_boxes[~short_edges]
    kv_scores = kv_scores[~short_edges]
    kv_classes = kv_classes[~short_edges]

    return kv_boxes, kv_scores, kv_classes
