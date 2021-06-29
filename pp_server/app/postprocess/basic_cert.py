from functools import cmp_to_key
import torch
import numpy as np
import re
from collections import OrderedDict
from soynlp.hangle import jamo_levenshtein, levenshtein
from pp_server.app.postprocess.commons import _get_iou_x, _get_iou_y, BoxlistPostprocessor as PP
from pp_server.app.postprocess.commons import _remove_invalid_characters, _remove_others_in_text
from pp_server.app.postprocess.family_cert import (
    get_personal_info,
    get_issue_date,
    obj_to_kvdict,
    bbox_hcmp,
    bbox_vcmp,
)


PERSONAL_INFO_KEYWORDS = ("구분", "성명", "출생연월일", "주민등록번호")
DATE_WILDCARD_KEYWORDS = ("출생년월일", "중생연월일", "충생연월일", "충생년월일", "출상년월일", "중앙연월일", "순생연월일", "중상연월일")

PADDING_FACTOR = (0.2, 2.5, 0.5, 0.5)

BOTTOM_KEYWORDS = ("기록사항", "틀림없음", "증명합니다")

TARGET_KEYWORDS = PERSONAL_INFO_KEYWORDS + BOTTOM_KEYWORDS


def get_between_pred(pred, keyword, texts):
    mask = torch.tensor((texts == keyword), dtype=torch.bool)
    boundary_pred = pred[mask]
    min_y = min(boundary_pred.bbox[:, 3]) + 1
    max_y = max(boundary_pred.bbox[:, 1]) - 1

    filter_mask = (pred.bbox[:, 1] < max_y) & (pred.bbox[:, 1] > min_y)
    filter_pred = pred[torch.tensor(filter_mask, dtype=torch.bool)]

    return filter_pred


def filter_pred(pred):
    texts = np.array(pred.get_field("texts"))

    if np.sum(texts == "구분") == 3:
        filter_pred = get_between_pred(pred, "구분", texts)

    elif np.sum(texts == "상세내용") == 2:
        filter_pred = get_between_pred(pred, "상세내용", texts)

    elif np.sum(texts == "출생연월일") == 1 and np.sum(texts == "일반등록사항") == 1:
        upper_idx = np.where(texts == "출생연월일")[0][0]
        height = pred.bbox[upper_idx, 3] - pred.bbox[upper_idx, 1]
        min_y = pred.bbox[upper_idx, 1] - height * 1.5

        lower_idx = np.where(texts == "일반등록사항")[0][0]
        max_y = pred.bbox[lower_idx, 3]

        filter_mask = (pred.bbox[:, 1] < max_y) & (pred.bbox[:, 1] > min_y)
        filter_pred = pred[torch.tensor(filter_mask, dtype=torch.bool)]

    else:
        edit_distances = [jamo_levenshtein("출생연월일", text) for text in texts]
        key_idx = np.argmin(edit_distances)
        key_bbox = pred.bbox[key_idx]
        height = key_bbox[3] - key_bbox[1]
        min_y = key_bbox[1] - height * 1.5
        max_y = key_bbox[3] + height * 5.0

        filter_mask = (pred.bbox[:, 1] < max_y) & (pred.bbox[:, 1] > min_y)
        filter_pred = pred[torch.tensor(filter_mask, dtype=torch.bool)]

    return filter_pred


def get_right_value(pred, texts, keyword):
    try:
        bboxes = pred.bbox
        if isinstance(bboxes, torch.Tensor):
            bboxes = bboxes.numpy()

        edit_distances = [jamo_levenshtein(keyword, text) / len(keyword) for text in texts]

        key_index = np.argmin(edit_distances)

        ## There is no similar word with keyword!
        if edit_distances[key_index] > 0.2:
            return ""
        key_bbox = bboxes[key_index]
        x0, y0, x1, y1 = key_bbox

        right_mask = torch.tensor(pred.bbox[:, 0] > ((x0 + x1) / 2), dtype=torch.bool)
        right_pred = pred[right_mask]
        right_bboxes = bboxes[right_mask.numpy()]

        y_iou_score = _get_iou_y(np.expand_dims(key_bbox, 0), right_bboxes)

        value_idx = np.argmax(y_iou_score[0])
        value = right_pred.get_field("texts")[value_idx] if y_iou_score[0][value_idx] > 0.5 else ""

    except:
        value = ""

    return value


def get_parental_authority(pred):
    texts = pred.get_field("texts")
    texts = _remove_invalid_characters(_remove_others_in_text(texts))

    parent_relation = get_right_value(pred, texts, "친권자")
    parent_regnum_key = get_right_value(pred, texts, "친권자의주민등록번호")

    return parent_relation, parent_regnum_key


def parse_personal_info(personal_info):
    name = ""
    regnum = ""

    if len(personal_info) == 0:
        return name, regnum

    categories = np.array([_info["구분"] for _info in personal_info]) == "본인"
    indices = np.where(categories == True)[0]
    idx = 0 if len(indices) == 0 else indices[0]
    name = personal_info[idx]["성명"]
    regnum = personal_info[idx]["주민등록번호"]

    return name, regnum


def postprocess_basic_cert(pred, score_thresh=0.5, *args):
    debug_dic = OrderedDict()
    pred = PP.remove_overlapped_box(pred)
    pred = pred[pred.get_field("scores") > score_thresh]

    filtered_pred = filter_pred(pred)

    keyword_map = {}
    for keyword in TARGET_KEYWORDS:
        keyword_map[keyword] = []

    texts = pred.get_field("texts")
    filtered_texts = filtered_pred.get_field("texts")

    for i, text in enumerate(texts):
        for keyword in BOTTOM_KEYWORDS:
            if keyword in text:
                bbox = pred.bbox[i]
                keyword_map[keyword].append({"bbox": bbox, "text": text})

    for i, text in enumerate(filtered_texts):
        for keyword in PERSONAL_INFO_KEYWORDS:
            if keyword in text:
                bbox = filtered_pred.bbox[i]
                keyword_map[keyword].append({"bbox": bbox, "text": text})
            elif keyword == PERSONAL_INFO_KEYWORDS[2]:  # dirty code
                for wildcard in DATE_WILDCARD_KEYWORDS + (keyword,):
                    if len(text) > 4 and wildcard in text or levenshtein(wildcard, text) < 3:
                        bbox = filtered_pred.bbox[i]
                        keyword_map[keyword].append({"bbox": bbox, "text": text})
                        break

    for keyword, box_dic in keyword_map.items():
        box_dic.sort(key=cmp_to_key(bbox_vcmp))
        if len(box_dic) > 2:  # find more smart way
            box_dic.sort(key=cmp_to_key(bbox_hcmp))
            box_dic = box_dic[:2]
            box_dic.sort(key=cmp_to_key(bbox_vcmp))
            keyword_map[keyword] = box_dic

    try:
        personal_info, personal_info_debug = get_personal_info(
            filtered_pred, keyword_map, BOTTOM_KEYWORDS
        )
    except:
        personal_info = []
        personal_info_debug = {}

    try:
        issue_date, issuedate_debug = get_issue_date(pred, keyword_map, BOTTOM_KEYWORDS)
    except:
        issue_date = ""
        issuedate_debug = {}

    parent_relation, parent_regnum = get_parental_authority(pred)

    debug_dic.update(personal_info_debug)
    debug_dic.update(issuedate_debug)

    for pi in personal_info:
        for k, v in pi.items():
            if k == "성명":
                pi[k] = "".join(re.findall("[가-힇]", v))
            elif k == "주민등록번호":
                pi[k] = "".join(re.findall("[\d-]", v))

    result = {}
    name, regnum = parse_personal_info(personal_info)

    result.update({"name": name})
    result.update({"regnum": regnum})
    result.update({"issue_date": issue_date})
    result.update({"relation": parent_relation})
    result.update({"is_parent": parent_regnum})

    result = obj_to_kvdict(result)
    return result, debug_dic
