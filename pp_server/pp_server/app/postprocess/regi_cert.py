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
PERSONAL_INFO_KEYWORDS = ("권리자", "(주민)등록번호")
BOTTOM_KEYWORDS = ("주소", "부동산고유번호", "부동산소재", "접수일자", "등기목적", "등기원인및일자")
PADDING_FACTOR = (0.2, 2.5, 0.5, 0.5)


def get_keyword_index(preds, KEYWORD, priority="upper"):
    """
    priority : upper / bottom / right / left
    """
    texts = preds.get_field("texts")
    edit_distances = [jamo_levenshtein(text, KEYWORD) for text in texts]
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
            text_filter = np.array(
                [True if re.search("\d{4}-", text) else False for text in texts]
            )
            filter_mask = (y_iou_score > 0) * (text_filter)

        if np.sum(filter_mask) == 0:
            filter_mask = np.array(
                [
                    True if re.search("\d{4}-\d{4}-\d{6}", text) else False
                    for text in texts
                ]
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

    return estate_num


def get_serial_num(preds):
    try:
        texts = np.array(preds.get_field("texts"))
        text_filter = np.array(
            [
                True if re.search("[A-Z]{4}-[A-Z]{4}-[A-Z]{4}", text) else False
                for text in texts
            ]
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
                [
                    True if re.search("[A-Z]{4}-[A-Z]{4}-[A-Z]{4}", text) else False
                    for text in texts
                ]
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
            [
                True if re.search("[A-Z]{4}-[A-Z]{4}-[A-Z]{4}", text) else False
                for text in texts
            ]
        )
        candidates = preds[torch.tensor(text_filter, dtype=torch.bool)]

        if len(candidates) > 0:
            candidates_text = candidates.get_field("texts")
            serial_num = candidates_text[0]

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
        get_keyword_index(preds, KEYWORD, priority="upper")
        for KEYWORD in UPPER_BOUNDARY_KEYWORDS
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
    pwd_candidates = preds.copy_with_fields(
        list(preds.extra_fields.keys()), skip_missing=False
    )
    texts = pwd_candidates.get_field("texts")
    text_filter = np.array(
        [True if re.match("[0-9]{6}-", text) else False for text in texts]
    )
    pwd_candidates = pwd_candidates[torch.tensor(text_filter, dtype=torch.bool)]
    try:
        pwd_numbers = min(50, np.sum(text_filter))
        upper_boundaries = get_upper_boundary(texts, preds)

        for upper_boundary in upper_boundaries:
            _pwd_candidates = pwd_candidates[
                torch.tensor(
                    pwd_candidates.bbox[:, 3] > upper_boundary, dtype=torch.bool
                )
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



def get_rightful_person(preds):
    try:
        texts = np.array(preds.get_field("texts"))
        text_filter = np.array(
            [
                True if re.findall("[가-힇]{3}", text) else False
                for text in texts
            ]
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
                [
                    True if re.search("[A-Z]{4}-[A-Z]{4}-[A-Z]{4}", text) else False
                    for text in texts
                ]
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
            [
                True if re.search("[A-Z]{4}-[A-Z]{4}-[A-Z]{4}", text) else False
                for text in texts
            ]
        )
        candidates = preds[torch.tensor(text_filter, dtype=torch.bool)]

        if len(candidates) > 0:
            candidates_text = candidates.get_field("texts")
            serial_num = candidates_text[0]


def get_passwords(preds):
    pwd_candidates = preds.copy_with_fields(
        list(preds.extra_fields.keys()), skip_missing=False
    )
    texts = pwd_candidates.get_field("texts")
    text_filter = np.array(
        [True if re.match("\d{2}-\d{4}", text) else False for text in texts]
    )
    pwd_candidates = pwd_candidates[torch.tensor(text_filter, dtype=torch.bool)]
    try:
        pwd_numbers = min(50, np.sum(text_filter))
        upper_boundaries = get_upper_boundary(texts, preds)

        for upper_boundary in upper_boundaries:
            _pwd_candidates = pwd_candidates[
                torch.tensor(
                    pwd_candidates.bbox[:, 3] > upper_boundary, dtype=torch.bool
                )
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

def find_values(
    boundary_bbox,
    pred,
    debug_dic,
    keyword,
    idx,
    max_y=None,
    x_iou_thres=0.25,
    is_name=False,
):
    bboxes = pred.bbox

    keyword_index = get_keyword_index(pred, keyword, priority="upper")
    x_iou_scores = _get_iou_y(pred.bbox[np.array([keyword_index])], pred.bbox)[0]
    x_iou_mask = x_iou_scores > x_iou_thres
    x_iou_mask = torch.squeeze(x_iou_mask, dim=0)

    t_mask = bboxes[:, 0] > boundary_bbox[2]
    b_mask = (
        bboxes[:, 3] < max_y
        if max_y is not None
        else torch.ones((bboxes.size(0),), dtype=torch.bool)
    )
    target_mask = t_mask & x_iou_mask & b_mask

    if target_mask.sum() > 0:
        target_boxlist = pred[target_mask]
        closest_bbox_idx = None
        for i, bbox in enumerate(target_boxlist.bbox):
            if (
                closest_bbox_idx is None
                or bbox[1] < target_boxlist.bbox[closest_bbox_idx][1]
            ):
                closest_bbox_idx = i

        bbox = target_boxlist.bbox[closest_bbox_idx]
        _, (bbox, value) = find_line_and_merge(bbox, target_boxlist)

    return value
    # else:
    #     max_y = None

    # if len(values) > 0:
    #     debug_dic.update(
    #         {
    #             "%s_%d_%d"
    #             % (keyword, idx[0], idx[1]): [
    #                 {"bbox": value[0], "text": value[1]} for value in values
    #             ]
    #         }
    #     )

    # if max_y is None:
    #     return values

    # if is_name:
    #     boundary_bbox = np.array([boundary_bbox[0], bbox[1], boundary_bbox[2], bbox[3]])
    # else:
    #     boundary_bbox = np.array(bbox)
    # return values + find_values(
    #     boundary_bbox,
    #     pred,
    #     debug_dic,
    #     keyword,
    #     (idx[0], idx[1] + 1),
    #     max_y,
    #     x_iou_thres,
    #     is_name,
    # )


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
    for keyword, padding in zip(PERSONAL_INFO_KEYWORDS, PADDING_FACTOR):
        if keyword not in keyword_map:
            continue

        kbv_dict[keyword] = []
        for i in range(len(keyword_map[keyword])):
            target = keyword_map[keyword][i]["bbox"]
            max_y = None if i == 0 else bb["bbox"][1]
            width = target[2] - target[0]
            height = target[2] - target[0]
            # boundary_bbox = np.array(
            #     [
            #         target[0] - width / 2 * padding,
            #         target[1],
            #         target[2] + width / 2 * padding,
            #         target[3],
            #     ]
            # )
            boundary_bbox = target
            bvs = find_values(
                boundary_bbox,
                pred,
                debug_dic=debug_dic,
                keyword=keyword,
                idx=(i, 0),
                max_y=max_y,
            )
            kbv_dict[keyword] = bvs

    return kbv_dict



def postprocess_regi_cert(predictions, score_thresh=0.1, *args):
    predictions = PP.sort_tblr(predictions)
    if isinstance(predictions.bbox, torch.Tensor):
        predictions.bbox = copy.deepcopy(predictions.bbox.numpy())

    estate_num = get_estate_num(predictions)
    serial_num = get_serial_num(predictions)
    pwd_texts = get_passwords(predictions)
    # rightful_person = get_rightful_person(predictions)
    # resident_registration_number = get_resident_registration_number(predictions)

    pred = predictions[predictions.get_field("scores") > score_thresh]
    keyword_map = {}
    for keyword in PERSONAL_INFO_KEYWORDS:
        keyword_map[keyword] = []

    texts = pred.get_field("texts")

    for i, text in enumerate(texts):
        for keyword in PERSONAL_INFO_KEYWORDS:
            if keyword in text or (len(text) > 5 and levenshtein(keyword, text) < 2):
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
        personal_info = get_personal_info(
            pred, keyword_map, BOTTOM_KEYWORDS
        )
    except:
        personal_info = []
        personal_info_debug = {}


    for k, v in personal_info.items():
        if k == "권리자":
            personal_info[k] = "".join(re.findall("[가-힇]", v))
        elif k == "(주민)등록번호":
            personal_info[k] = "".join(re.findall("[\d-]", v))

    result = {}
    result.update({"estate_num": estate_num})
    result.update({"serial_num": serial_num})
    result.update({"passwords": pwd_texts})
    result.update({"rightful_person": personal_info["권리자"]})
    result.update({"resident_registration_number": personal_info["(주민)등록번호"]})

    result_all_classes = {}

    for k, v in result.items():
        result_all_classes[k + "_value"] = v

    return KVDict(result_all_classes, str), {}
