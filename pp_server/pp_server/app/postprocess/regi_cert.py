import re
import copy
import torch
import numpy as np

from collections import OrderedDict
from functools import cmp_to_key
from soynlp.hangle import jamo_levenshtein
from soynlp.hangle import levenshtein
from pp_server.app.structures.keyvalue_dict import KVDict
from pp_server.app.postprocess.commons import _get_iou_y, _get_iou_x, BoxlistPostprocessor as PP

ESTATE_NUM_KEYWORD = "부동산고유번호"
SERIAL_NUM_KEYWORD = "일련번호"
UPPER_BOUNDARY_KEYWORDS = ["비밀번호", "일련번호", "등기원인및일자"]
PERSONAL_INFO_KEYWORDS = ("등록번호", "혥횷횷혥")
BOTTOM_KEYWORDS = ("주소", "부동산고유번호", "부동산소재", "접수일자", "등기목적", "등기원인및일자")
PADDING_FACTOR = (0.2, 2.5, 0.5, 0.5)
TARGET_KEYWORDS = PERSONAL_INFO_KEYWORDS + BOTTOM_KEYWORDS


def get_keyword_index(preds, KEYWORD, priority="upper"):
    """
    priority : upper / bottom / right / left
    """
    texts = preds.get_field("texts")
    edit_distances = [jamo_levenshtein(text.split(")")[-1], KEYWORD) for text in texts]
    min_indices = np.where(edit_distances == np.min(edit_distances))[0]
    if len(min_indices) == 1:
        return min_indices[0]

    keyword_bboxes = preds.bbox[min_indices]
    if priority == "upper":
        index = min_indices[np.argmin(keyword_bboxes[:, 1])]

    elif priority == "bottom":
        index = min_indices[np.argmax(keyword_bboxes[:, 3])]

    elif priority == "left":
        index = min_indices[np.argmin(keyword_bboxes[:, 0])]

    elif priority == "right":
        index = min_indices[np.argmax(keyword_bboxes[:, 2])]

    return index


def get_regex_index(preds, exp, priority="bottom"):
    """
    priority : upper / bottom / right / left
    If there is no text satisfied expression,
    Return None
    """
    texts = preds.get_field("texts")
    regex_mask = np.array([True if re.search(exp, text) else False for text in texts])

    mask_indices = np.where(regex_mask == True)[0]
    if len(mask_indices) == 0:
        return None

    mask_bboxes = preds.bbox[mask_indices]
    if priority == "upper":
        index = mask_indices[np.argmin(mask_bboxes[:, 1])]

    elif priority == "bottom":
        index = mask_indices[np.argmax(mask_bboxes[:, 3])]

    elif priority == "left":
        index = mask_indices[np.argmin(mask_bboxes[:, 0])]

    elif priority == "right":
        index = mask_indices[np.argmax(mask_bboxes[:, 2])]

    else:
        raise

    return index


def fix_password(pwd_preds):
    return None


def get_estate_num(preds):
    try:
        texts = np.array(preds.get_field("texts"))
        text_filter = np.array(
            [True if re.search("\d{4}-\d{4}-\d{6}", text) else False for text in texts]
        )

        estate_num = ""
        keyword_index = get_keyword_index(preds, ESTATE_NUM_KEYWORD, priority="upper")
        y_iou_score = _get_iou_y(preds.bbox[np.array([keyword_index])], preds.bbox)[0]

        y_iou_score[keyword_index] = 0
        filter_mask = (y_iou_score > 0) * (text_filter)

        if np.sum(filter_mask) == 0:
            text_filter = np.array([True if re.search("\d{4}-", text) else False for text in texts])
            filter_mask = (y_iou_score > 0) * (text_filter)

        if np.sum(filter_mask) == 0:
            filter_mask = np.array(
                [True if re.search("\d{4}-\d{4}-\d{6}", text) else False for text in texts]
            )

        if np.sum(filter_mask) == 0:
            filter_mask = np.array(
                [True if re.search("\d{4}-\d{1}", text) else False for text in texts]
            )

        candidates = preds[torch.tensor(filter_mask, dtype=torch.bool)]

        if len(candidates) > 0:
            candidates_text = candidates.get_field("texts")
            max_idx = np.argmax(y_iou_score[filter_mask])
            estate_num = candidates_text[max_idx]

    except:
        estate_num = ""
        texts = np.array(preds.get_field("texts"))
        text_filter = np.array(
            [True if re.search("\d{4}-\d{4}-\d{6}", text) else False for text in texts]
        )
        candidates = preds[torch.tensor(text_filter, dtype=torch.bool)]

        if len(candidates) > 0:
            candidates_text = candidates.get_field("texts")
            estate_num = candidates_text[0]

    estate_num = "".join(re.findall("[\d]", estate_num))
    return estate_num


def get_serial_num(preds):
    try:
        texts = np.array(preds.get_field("texts"))
        text_filter = np.array(
            [True if re.search("[A-Z]{4}-[A-Z]{4}-[A-Z]{4}", text) else False for text in texts]
        )

        serial_num = ""
        keyword_index = get_keyword_index(preds, SERIAL_NUM_KEYWORD, priority="upper")
        y_iou_score = _get_iou_y(preds.bbox[np.array([keyword_index])], preds.bbox)[0]

        y_iou_score[keyword_index] = 0
        filter_mask = (y_iou_score > 0) * (text_filter)

        if np.sum(filter_mask) == 0:
            text_filter = np.array(
                [True if re.search("[A-Z]{4}", text) else False for text in texts]
            )
            filter_mask = (y_iou_score > 0) * (text_filter)

        if np.sum(filter_mask) == 0:
            filter_mask = np.array(
                [True if re.search("[A-Z]{4}-[A-Z]{4}-[A-Z]{4}", text) else False for text in texts]
            )

        if np.sum(filter_mask) == 0:
            filter_mask = np.array(
                [True if re.search("[A-Z]{4}", text) else False for text in texts]
            )

        candidates = preds[torch.tensor(filter_mask, dtype=torch.bool)]

        if len(candidates) > 0:
            candidates_text = candidates.get_field("texts")
            max_idx = np.argmax(y_iou_score[filter_mask])
            serial_num = candidates_text[max_idx]

    except:
        serial_num = ""
        texts = np.array(preds.get_field("texts"))
        text_filter = np.array(
            [True if re.search("[A-Z]{4}-[A-Z]{4}-[A-Z]{4}", text) else False for text in texts]
        )
        candidates = preds[torch.tensor(text_filter, dtype=torch.bool)]

        if len(candidates) > 0:
            candidates_text = candidates.get_field("texts")
            serial_num = candidates_text[0]

    serial_num = "".join(re.findall("[A-Z]", serial_num))
    return serial_num


def get_indices(texts, KEYWORDS):
    indices = list()
    for keyword in KEYWORDS:
        edit_distances = [jamo_levenshtein(text, keyword) for text in texts]
        min_idx = np.argmin(edit_distances)
        indices.append(min_idx)

    return indices


def get_upper_boundary(texts, preds):
    upper_indices = [
        get_keyword_index(preds, KEYWORD, priority="upper") for KEYWORD in UPPER_BOUNDARY_KEYWORDS
    ]
    upper_boundary = [preds.bbox[index, 1] for index in upper_indices]
    upper_boundary = sorted(upper_boundary, reverse=True)

    return upper_boundary


def get_person_info_bottom_boundary(keyword_map, bottom_keywords):
    bb = None
    for keyword in bottom_keywords:
        if keyword in keyword_map and len(keyword_map[keyword]) > 0:
            bb = keyword_map[keyword][0]
            break
    return bb


def get_bottom_boundary(preds):
    year_idx = get_regex_index(preds, "\d{4}년", priority="bottom")
    month_idx = get_regex_index(preds, "\d{1, 2}월", priority="bottom")
    day_idx = get_regex_index(preds, "\d{1, 2}일", priority="bottom")

    year = preds.bbox[year_idx, 3] if year_idx is not None else 0
    month = preds.bbox[month_idx, 3] if month_idx is not None else 0
    day = preds.bbox[day_idx, 3] if day_idx is not None else 0

    date_boundary = max([year, month, day])

    less_tighter_index = get_keyword_index(preds, "등기관", priority="bottom")
    less_tighter_boundary = preds.bbox[less_tighter_index, 3]
    lower_boundary = sorted([date_boundary, less_tighter_boundary])

    return lower_boundary


def get_resident_registration_number(preds):
    pwd_candidates = preds.copy_with_fields(list(preds.extra_fields.keys()), skip_missing=False)
    texts = pwd_candidates.get_field("texts")
    text_filter = np.array([True if re.match("[0-9]{6}-", text) else False for text in texts])
    pwd_candidates = pwd_candidates[torch.tensor(text_filter, dtype=torch.bool)]
    try:
        pwd_numbers = min(50, np.sum(text_filter))
        upper_boundaries = get_upper_boundary(texts, preds)

        for upper_boundary in upper_boundaries:
            _pwd_candidates = pwd_candidates[
                torch.tensor(pwd_candidates.bbox[:, 3] > upper_boundary, dtype=torch.bool)
            ]
            # ==가 아니라 >= 사용해야하는거 아닌가?
            if len(_pwd_candidates) == pwd_numbers:
                continue

        """
        if len(_pwd_candidates) > 50 :
            filtered_pwd_candidates = _pwd_candidates
            bottom_boundaries = get_bottom_boundary(preds)

            for bottom_boundary in bottom_boundaries:
                _filtered_pwd_candidates = filtered_pwd_candidates[torch.tensor(filtered_pwd_candidates.bbox[:, 1] < bottom_boundary, dtype = torch.bool)]
                if len(_filtered_pwd_candidates) == pwd_numbers:
                    continue
        
            _pwd_candidates = _filtered_pwd_candidates
        """
        pwd_mask = (preds.bbox[:, 1] > int(min(_pwd_candidates.bbox[:, 1] - 1))) * (
            preds.bbox[:, 3] < int(max(_pwd_candidates.bbox[:, 3] + 1))
        )
        passwords = preds[torch.tensor(pwd_mask, dtype=torch.bool)]
        password_texts = passwords.get_field("texts")
        # passwords = fix_password(passwords)

    except:
        pwd_candidates = pwd_candidates[torch.tensor(text_filter, dtype=torch.bool)]
        password_texts = pwd_candidates.get_field("texts")

    return password_texts


def get_passwords(preds):
    pwd_candidates = preds.copy_with_fields(list(preds.extra_fields.keys()), skip_missing=False)
    texts = pwd_candidates.get_field("texts")
    text_filter = np.array([True if re.match("\d{2}-\d{4}", text) else False for text in texts])
    pwd_candidates = pwd_candidates[torch.tensor(text_filter, dtype=torch.bool)]
    try:
        pwd_numbers = min(50, np.sum(text_filter))
        upper_boundaries = get_upper_boundary(texts, preds)

        for upper_boundary in upper_boundaries:
            _pwd_candidates = pwd_candidates[
                torch.tensor(pwd_candidates.bbox[:, 3] > upper_boundary, dtype=torch.bool)
            ]
            # ==가 아니라 >= 사용해야하는거 아닌가?
            if len(_pwd_candidates) == pwd_numbers:
                continue

        """
        if len(_pwd_candidates) > 50 :
            filtered_pwd_candidates = _pwd_candidates
            bottom_boundaries = get_bottom_boundary(preds)

            for bottom_boundary in bottom_boundaries:
                _filtered_pwd_candidates = filtered_pwd_candidates[torch.tensor(filtered_pwd_candidates.bbox[:, 1] < bottom_boundary, dtype = torch.bool)]
                if len(_filtered_pwd_candidates) == pwd_numbers:
                    continue
        
            _pwd_candidates = _filtered_pwd_candidates
        """
        pwd_mask = (preds.bbox[:, 1] > int(min(_pwd_candidates.bbox[:, 1] - 1))) * (
            preds.bbox[:, 3] < int(max(_pwd_candidates.bbox[:, 3] + 1))
        )
        passwords = preds[torch.tensor(pwd_mask, dtype=torch.bool)]
        password_texts = passwords.get_field("texts")
        # passwords = fix_password(passwords)

    except:
        pwd_candidates = pwd_candidates[torch.tensor(text_filter, dtype=torch.bool)]
        password_texts = pwd_candidates.get_field("texts")

    return password_texts


def bbox_vcmp(b0, b1):
    return b0["bbox"][1] - b1["bbox"][1]


def bbox_hcmp(b0, b1):
    return b0["bbox"][0] - b1["bbox"][0]


def merge_line(boxlist):
    bboxes = boxlist.bbox
    texts = boxlist.get_field("texts")

    def _cmp(l, r):
        lbb, _ = l
        rbb, _ = r
        return lbb[0] - rbb[0]

    sorted_line = sorted(zip(bboxes, texts), key=cmp_to_key(_cmp))
    bboxes, texts = list(zip(*sorted_line))

    line_bbox = [1000000, 1000000, 0, 0]
    for bbox in bboxes:
        line_bbox[0] = min(bbox[0], line_bbox[0])
        line_bbox[1] = min(bbox[1], line_bbox[1])
        line_bbox[2] = max(bbox[2], line_bbox[2])
        line_bbox[3] = max(bbox[3], line_bbox[3])
    text = "".join(texts)
    return (line_bbox, text)


def find_line_and_merge(bbox, target_boxlist):
    if isinstance(bbox, torch.Tensor):
        bbox = bbox.numpy()
    bbox = np.expand_dims(bbox, axis=0)
    y_iou_score = _get_iou_y(bbox, target_boxlist.bbox, divide_by_area2=True)
    y_iou_mask = y_iou_score > 0.5
    y_iou_mask = torch.squeeze(y_iou_mask, dim=0)
    line_boxlist = target_boxlist[y_iou_mask]
    return line_boxlist, merge_line(line_boxlist)


"""
min_y = pred.bbox[keyword_index][1].tolist()
for bottom in pred.bbox[:,1].tolist():
    if bottom < min_y:
        min_y = bottom
pred.bbox[keyword_index][1] > 
"""


def get_target_mask(boundary_bbox, pred, max_y, x_iou_thres, bbox):
    bboxes = pred.bbox
    x_iou_scores = _get_iou_y(bbox, pred.bbox)[0]
    x_iou_mask = x_iou_scores > x_iou_thres
    x_iou_mask = torch.squeeze(x_iou_mask, dim=0)

    t_mask = bboxes[:, 0] > boundary_bbox[2]
    b_mask = (
        bboxes[:, 1] < max_y
        if max_y is not None
        else torch.ones((bboxes.size(0),), dtype=torch.bool)
    )
    target_mask = t_mask & x_iou_mask & b_mask

    target_boxlist = pred[target_mask]
    if target_mask.sum() == 0:
        return None

    return target_mask, target_boxlist


def cal_find_value(keyword, target_boxlist):
    if keyword == "등록번호":
        closest_bbox_idx = None
        texts = target_boxlist.get_field("texts")
        for i, bbox in enumerate(target_boxlist.bbox):
            if closest_bbox_idx is None or "".join(
                re.findall("[\d-]{6}", target_boxlist.extra_fields.get("texts")[closest_bbox_idx])
            ):
                closest_bbox_idx = i

        bbox = target_boxlist.bbox[closest_bbox_idx]
        line_boxlist, (bbox, value) = find_line_and_merge(bbox, target_boxlist)
        boxlist_texts = target_boxlist.extra_fields.get("texts")
        pasted_text = "".join(boxlist_texts)
        resident_registration_number = "".join(re.findall("[\d]", pasted_text))
        if len(resident_registration_number) == 0:
            resident_registration_number = ""
        return resident_registration_number
    elif keyword == "권리자":
        closest_bbox_idx = None
        texts = target_boxlist.get_field("texts")
        for i, bbox in enumerate(target_boxlist.bbox):
            if closest_bbox_idx is None or bbox[0] < target_boxlist.bbox[closest_bbox_idx][0]:
                closest_bbox_idx = i

        bbox = target_boxlist.bbox[closest_bbox_idx]
        line_boxlist, (bbox, value) = find_line_and_merge(bbox, target_boxlist)
        boxlist_texts = target_boxlist.extra_fields.get("texts")
        pasted_text = "".join(boxlist_texts)
        right_holder = "".join(re.findall("[가-힇]", pasted_text))
        return right_holder


def find_values(
    boundary_bbox,
    pred,
    keyword,
    max_y=None,
    x_iou_thres=0.25,
):
    resident_registration_number = ""
    right_holder = ""

    keyword_index = get_keyword_index(pred, keyword, priority="upper")
    resident_registration_number_bbox = pred.bbox[np.array([keyword_index])]
    target_mask, target_boxlist = get_target_mask(
        boundary_bbox, pred, max_y, x_iou_thres, resident_registration_number_bbox
    )
    if target_mask.sum() > 0:
        resident_registration_number = cal_find_value("등록번호", target_boxlist)

    bbox = pred.bbox[keyword_index]
    margin_y = (bbox[3] - bbox[1]) * 0.7
    right_holder_bbox = torch.tensor(
        [np.array([bbox[0], bbox[1] - margin_y, bbox[2], bbox[3] - margin_y])]
    )
    target_mask, target_boxlist = get_target_mask(
        boundary_bbox, pred, max_y, x_iou_thres, right_holder_bbox
    )
    if target_mask.sum() > 0:
        right_holder = cal_find_value("권리자", target_boxlist)

    return {
        "resident_registration_number": resident_registration_number,
        "right_holder": right_holder,
    }


def get_longest_bvs(kbv_dict):
    longest_bvs = []
    for bvs in kbv_dict.values():
        if len(longest_bvs) < len(bvs):
            longest_bvs = bvs
    return longest_bvs


def get_personal_info(pred, keyword_map, bottom_keywords):
    debug_dic = OrderedDict()
    bb = get_person_info_bottom_boundary(keyword_map, bottom_keywords)

    kbv_dict = {}
    for keyword in PERSONAL_INFO_KEYWORDS:
        if keyword not in keyword_map:
            continue

        kbv_dict[keyword] = []
        for i in range(len(keyword_map[keyword])):
            target = keyword_map[keyword][i]["bbox"]
            max_y = None if bb is None else bb["bbox"][1]
            boundary_bbox = target
            bvs = find_values(
                boundary_bbox,
                pred,
                keyword=keyword,
                max_y=max_y,
            )
            kbv_dict.update(bvs)

    return kbv_dict


def to_numpy(tensor):
    if tensor.requires_grad:
        return tensor.detach().cpu().numpy()
    else:
        return tensor.cpu().numpy()


def save_debug_img(kv_boxes, savepath):
    kv_boxes = to_numpy(kv_boxes).astype(int)
    import cv2

    img_arr = cv2.imread("/workspace/bentoml_textscope/1626769155.7656195.jpg")
    _img_arr = img_arr[:, :, ::-1].copy()
    for _box in kv_boxes:
        min_x, min_y, max_x, max_y = _box.tolist()
        width = max_x - min_x
        height = max_y - min_y
        cv2.rectangle(_img_arr, (min_x, min_y, width, height), (255, 0, 0), 1)
    _img_arr = cv2.cvtColor(_img_arr, cv2.COLOR_BGR2RGB)
    cv2.imwrite(savepath, _img_arr)


def postprocess_regi_cert(predictions, score_thresh=0.1, *args):
    predictions = PP.remove_overlapped_box(predictions)
    predictions = predictions[predictions.get_field("scores") > score_thresh]
    predictions = PP.sort_tblr(predictions)
    # save_debug_img(predictions.bbox, "./test.jpg")
    if isinstance(predictions.bbox, torch.Tensor):
        predictions.bbox = copy.deepcopy(predictions.bbox.numpy())

    estate_num = get_estate_num(predictions)
    serial_num = get_serial_num(predictions)
    pwd_texts = get_passwords(predictions)
    # rightful_person = get_rightful_person(predictions)
    # resident_registration_number = get_resident_registration_number(predictions)

    pred = predictions[predictions.get_field("scores") > score_thresh]
    keyword_map = {}
    for keyword in TARGET_KEYWORDS:
        keyword_map[keyword] = []

    texts = pred.get_field("texts")

    for i, text in enumerate(texts):
        for keyword in BOTTOM_KEYWORDS:
            if keyword in text:
                bbox = pred.bbox[i]
                keyword_map[keyword].append({"bbox": bbox, "text": text})

    for i, text in enumerate(texts):
        for keyword in PERSONAL_INFO_KEYWORDS:
            if keyword in text or (len(text) > 5 and levenshtein(keyword, text) < 3):
                bbox = pred.bbox[i]
                # keyword_map[keyword].append(bbox)
                keyword_map[keyword].append({"bbox": bbox, "text": text})

    for keyword, box_dic in keyword_map.items():
        box_dic.sort(key=cmp_to_key(bbox_vcmp))
        if len(box_dic) > 2:  # find more smart way
            box_dic.sort(key=cmp_to_key(bbox_hcmp))
            box_dic = box_dic[:2]
            box_dic.sort(key=cmp_to_key(bbox_vcmp))
            keyword_map[keyword] = box_dic

    try:
        personal_info = get_personal_info(pred, keyword_map, BOTTOM_KEYWORDS)
    except:
        personal_info = []

    result = {}
    result.update({"estate_num": estate_num})
    result.update({"serial_num": serial_num})
    result.update({"passwords": pwd_texts})
    result.update({"rightful_person": personal_info["right_holder"]})
    result.update({"resident_registration_number": personal_info["resident_registration_number"]})

    result_all_classes = {}

    for k, v in result.items():
        result_all_classes[k + "_value"] = v

    return KVDict(result_all_classes, str), {}
