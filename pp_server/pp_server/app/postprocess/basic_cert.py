import enum
import copy
from functools import cmp_to_key
import torch
import numpy as np
import re
from collections import OrderedDict
from soynlp.hangle import jamo_levenshtein, levenshtein
from pp_server.app.postprocess.commons import (
    _get_iou_x,
    _get_iou_y,
    BoxlistPostprocessor as PP,
)
from pp_server.app.postprocess.commons import (
    _remove_invalid_characters,
    _remove_others_in_text,
)
from pp_server.app.postprocess.family_cert import (
    get_personal_info,
    get_issue_date,
    obj_to_kvdict,
    bbox_hcmp,
    bbox_vcmp,
)



PERSONAL_INFO_KEYWORDS = ("구분", "성명", "출생연월일", "주민등록번호")
PERSONAL_INFO_KEYWORDS = ("구분", "성명", "출생연월일", "주민등록번호")
DATE_WILDCARD_KEYWORDS = (
    "출생년월일",
    "중생연월일",
    "충생연월일",
    "충생년월일",
    "출상년월일",
    "중앙연월일",
    "순생연월일",
    "중상연월일",
)

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





def get_multiple_right_value(pred, texts, keyword, value_num=2, threshold=0.5):
    value = list()
    try:
        bboxes = pred.bbox
        if isinstance(bboxes, torch.Tensor):
            bboxes = bboxes.numpy()

        edit_distances = [
            jamo_levenshtein(keyword, text) / len(keyword) for text in texts
        ]

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
        valid_value = y_iou_score[0]>threshold
        valid_index = [i for i, value in enumerate(valid_value) if value]
        # value_num = len(valid_index) if value_num > len(valid_index) else value_num
        # valid_index = valid_index[:value_num]
        
        for index in valid_index:
            value.append({"text": right_pred.get_field("texts")[index], "bbox":right_pred.bbox[np.array([index])]})
            
        # value_idx = np.argsort(y_iou_score[0])[-2:]
    except:
        pass

    return value

def get_right_value(pred, texts, keyword):
    try:
        bboxes = pred.bbox
        if isinstance(bboxes, torch.Tensor):
            bboxes = bboxes.numpy()

        edit_distances = [
            jamo_levenshtein(keyword, text) / len(keyword) for text in texts
        ]

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
        value = (
            right_pred.get_field("texts")[value_idx]
            if y_iou_score[0][value_idx] > 0.5
            else ""
        )

    except:
        value = ""

    return value

def split_parental_authority_value(parent_relation, parental_authority):
    # 이름과 관계 분리
    assert len(parent_relation) >= 2
    copy_parent_relation = copy.deepcopy(parent_relation)
    for i, value in enumerate(copy_parent_relation):
        if len(value["text"]) == 1:
            relation = parent_relation.pop(i)
            parental_authority["relation"] = relation["text"]
            relation_x = relation["bbox"][0][2]
            break
    for value in parent_relation:
        if value["bbox"][0][0] > relation_x:
            parental_authority["authName"] = value["text"]
    return parental_authority



def get_target_mask(pred, x_iou_thres, bbox):
    # bboxes = pred.bbox
    x_iou_scores = _get_iou_y(bbox, pred.bbox)[0]
    x_iou_mask = x_iou_scores > x_iou_thres
    x_iou_mask = torch.squeeze(x_iou_mask, dim=0)

    # t_mask = bboxes[:, 0] > boundary_bbox[2]

    # b_mask = (
    #     bboxes[:, 1] < max_y
    #     if max_y is not None
    #     else torch.ones((bboxes.size(0),), dtype=torch.bool)
    # )
    # target_mask = t_mask & x_iou_mask & b_mask
    target_mask = x_iou_mask

    target_boxlist = pred[target_mask]
    if target_mask.sum() == 0:
        return None

    return target_mask, target_boxlist


def get_parental_authority(pred):
    texts = pred.get_field("texts")
    texts = _remove_invalid_characters(_remove_others_in_text(texts))

    parental_authority = {
        "authName": "",
        "relation": "",
    }
    # box_index_list = list()
    # for i, bbox in enumerate(pred.bbox):
    #     if bbox[1] > 1908 - 50 and bbox[3] < 1958 + 50:
    #         box_index_list.append(i)

    parent_relation = get_multiple_right_value(pred, texts, "친권자")
    if len(parent_relation) == 0:
        parent_relation = get_multiple_right_value(pred, texts, "친권행사자")
    if len(parent_relation) == 1:
        parental_authority["authName"] = parent_relation[0]["text"]
        target_mask, target_boxlist = get_target_mask(
            pred, x_iou_thres=0.1, bbox=parent_relation[0]["bbox"]
        )
    elif len(parent_relation) >= 2:
        parental_authority = split_parental_authority_value(parent_relation, parental_authority) 
    return parental_authority


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




def to_numpy(tensor):
    if tensor.requires_grad:
        return tensor.detach().cpu().numpy()
    else:
        return tensor.cpu().numpy()


def save_debug_img(kv_boxes, savepath):
    kv_boxes = to_numpy(kv_boxes).astype(int)
    import cv2

    img_arr = cv2.imread("/workspace/bentoml_textscope/rotated_img.jpg")
    _img_arr = img_arr[:, :, ::-1].copy()
    for _box in kv_boxes:
        min_x, min_y, max_x, max_y = _box.tolist()
        width = max_x - min_x
        height = max_y - min_y
        cv2.rectangle(_img_arr, (min_x, min_y, width, height), (255, 0, 0), 3)
    _img_arr = cv2.cvtColor(_img_arr, cv2.COLOR_BGR2RGB)
    cv2.imwrite(savepath, _img_arr)


def postprocess_basic_cert(pred, score_thresh=0.3, *args):
    debug_dic = OrderedDict()
    pred = PP.remove_overlapped_box(pred, iou_thresh=0.85)
    pred = pred[pred.get_field("scores") > score_thresh]

    # filtered_pred = filter_pred(pred)
    filtered_pred = pred
    save_debug_img(filtered_pred.bbox, "./test.jpg")

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
                    if (
                        len(text) > 4
                        and wildcard in text
                        or levenshtein(wildcard, text) < 3
                    ):
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

    parental_authority = get_parental_authority(pred)

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
    result.update({"authStatus": "Y" if len(parental_authority["relation"]) else "N"})
    result.update({"relation": parental_authority["relation"]})
    result.update({"authName": parental_authority["authName"]})

    result = obj_to_kvdict(result)
    return result, debug_dic
