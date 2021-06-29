from functools import cmp_to_key
import torch
import numpy as np
import re
from collections import OrderedDict
from soynlp.hangle import levenshtein

from pp_server.app.postprocess.commons import _get_iou_x, _get_iou_y, BoxlistPostprocessor as PP
from pp_server.app.structures.keyvalue_dict import KVDict

TITLE_KEYWORDS = (
    "가족관계증명서",
    "가족관계증명서(일반)",
    "가족관계증명서(일",
    "가족관계증명서(일반",
    "가족관계증명서(상세)",
    "가족관계증명서(상",
    "가족관계증명서(상세",
    "가족관계증명서(특정)",
    "가족관계증명서(특",
    "가족관계증명서(특정",
)
PERSONAL_INFO_KEYWORDS = ("구분", "성명", "출생연월일", "주민등록번호")
DATE_WILDCARD_KEYWORDS = ("출생년월일", "중생연월일", "충생연월일", "충생년월일", "출상년월일", "중앙연월일", "순생연월일", "중상연월일")
DATE_KEYWORDS = ("년", "월", "일")
PADDING_FACTOR = (0.2, 2.5, 0.5, 0.5)

BOTTOM_KEYWORDS = ("등록부의", "기록사항", "틀림없음", "증명합니다", "상세내용", "정정일")


TARGET_KEYWORDS = PERSONAL_INFO_KEYWORDS + BOTTOM_KEYWORDS


def bbox_vcmp(b0, b1):
    return b0["bbox"][1] - b1["bbox"][1]


def bbox_hcmp(b0, b1):
    return b0["bbox"][0] - b1["bbox"][0]


def obj_to_kvdict(obj):
    kv_dict = {}
    for k, v in obj.items():
        kv_dict[k + "_key"] = k
        kv_dict[k + "_value"] = v

    kv_dict = KVDict(kv_dict, str)
    return kv_dict


def postprocess_family_cert(pred, score_thresh=0.5, *args):
    debug_dic = OrderedDict()
    pred = PP.remove_overlapped_box(pred)
    pred = pred[pred.get_field("scores") > score_thresh]

    keyword_map = {}
    for keyword in TARGET_KEYWORDS:
        keyword_map[keyword] = []

    texts = pred.get_field("texts")

    for i, text in enumerate(texts):
        for keyword in TARGET_KEYWORDS:
            if keyword in text:
                bbox = pred.bbox[i]
                # keyword_map[keyword].append(bbox)
                keyword_map[keyword].append({"bbox": bbox, "text": text})
            elif keyword == PERSONAL_INFO_KEYWORDS[2]:  # dirty code
                for wildcard in DATE_WILDCARD_KEYWORDS + (keyword,):
                    # print("\033[95m" + f"wildcard: {wildcard}" + "\033[m")
                    # print("\033[95m" + f"text: {text}" + "\033[m")
                    if len(text) > 4 and wildcard in text or levenshtein(wildcard, text) < 3:
                        bbox = pred.bbox[i]
                        # keyword_map[keyword].append(bbox)
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
        personal_info, personal_info_debug = get_personal_info(pred, keyword_map, BOTTOM_KEYWORDS)
    except:
        personal_info = []
        personal_info_debug = {}

    issue_date, issuedate_debug = get_issue_date(pred, keyword_map, BOTTOM_KEYWORDS)
    title = get_title(pred)

    debug_dic.update(personal_info_debug)
    debug_dic.update(issuedate_debug)

    for pi in personal_info:
        for k, v in pi.items():
            if k == "성명":
                pi[k] = "".join(re.findall("[가-힇]", v))
            elif k == "주민등록번호":
                pi[k] = "".join(re.findall("[\d-]", v))

    result = {}
    result.update({"인적사항": personal_info})
    result.update({"발행일": issue_date})
    result.update({"타이틀": title})
    result = obj_to_kvdict(result)
    return result, debug_dic


def find_line_and_merge(bbox, target_boxlist):
    if isinstance(bbox, torch.Tensor):
        bbox = bbox.numpy()
    bbox = np.expand_dims(bbox, axis=0)
    y_iou_score = _get_iou_y(bbox, target_boxlist.bbox, divide_by_area2=True)
    y_iou_mask = y_iou_score > 0.5
    y_iou_mask = torch.squeeze(y_iou_mask, dim=0)
    line_boxlist = target_boxlist[y_iou_mask]
    return line_boxlist, merge_line(line_boxlist)


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


def get_bottom_boundary(keyword_map, bottom_keywords):
    bb = None
    for keyword in bottom_keywords:
        if keyword in keyword_map and len(keyword_map[keyword]) > 0:
            bb = keyword_map[keyword][0]
            break
    return bb


def get_regexp_mask(pred, regexp):
    mask = torch.zeros((len(pred),), dtype=torch.bool)
    texts = pred.get_field("texts")
    for i, text in enumerate(texts):
        if re.match(regexp, text):
            mask[i] = True

    return mask


def get_issue_date(pred, keyword_map, bottom_keywords):
    debug_dic = OrderedDict()
    bb = get_bottom_boundary(keyword_map, bottom_keywords)
    debug_dic.update({"bottom_boundary": [bb]})
    regexp = re.compile("(\d+(년|월|일)|(년월일))")

    bboxes = pred.bbox
    # print("\033[95m" + f"wildcard: {bboxes[:, 1]}" + "\033[m")
    # print("\033[95m" + f"keyword_map: {keyword_map}" + "\033[m")
    # print("\033[95m" + f"bottom_keywords: {bottom_keywords}" + "\033[m")
    t_mask = bboxes[:, 1] > bb["bbox"][3]
    keyword_mask = get_regexp_mask(pred, regexp)
    target_mask = t_mask & keyword_mask
    target_boxlist = pred[target_mask]
    debug_dic.update({"issuedate_candidate": target_boxlist})
    value = ""
    for keyword in DATE_KEYWORDS:
        closest_bbox_idx = None
        texts = target_boxlist.get_field("texts")
        for i, bbox in enumerate(target_boxlist.bbox):
            if closest_bbox_idx is None or bbox[1] < target_boxlist.bbox[closest_bbox_idx][1]:
                closest_bbox_idx = i

        if closest_bbox_idx == None:
            continue

        bbox = target_boxlist.bbox[closest_bbox_idx]
        line_boxlist, (bbox, value) = find_line_and_merge(bbox, target_boxlist)
        debug_dic.update({"issuedate": line_boxlist})
        break

    if value == "년월일":
        value = ""
    return value, debug_dic


def get_title(pred):
    texts = pred.get_field("texts")

    title = ""
    for text in texts:
        if len(text) < len(title):
            continue

        for keyword in TITLE_KEYWORDS:
            if len(text) >= len(keyword) and keyword in text:
                title = keyword

    split_title = title.split("(")
    if len(split_title) < 2:
        return split_title[0]
    else:
        return (
            f"{split_title[0]}(상세)"
            if "상" in split_title[1]
            else f"{split_title[0]}(특정)"
            if "특" in split_title[1]
            else f"{split_title[0]}(일반)"
            if "일" in split_title[1]
            else title
        )


def find_values(
    boundary_bbox, pred, debug_dic, keyword, idx, max_y=None, x_iou_thres=0.25, is_name=False
):
    bboxes = pred.bbox

    x_iou_scores = _get_iou_x(
        np.expand_dims(boundary_bbox, axis=0), pred.bbox, divide_by_area2=True
    )
    x_iou_mask = x_iou_scores > x_iou_thres
    x_iou_mask = torch.squeeze(x_iou_mask, dim=0)

    t_mask = bboxes[:, 1] > boundary_bbox[3]
    b_mask = (
        bboxes[:, 3] < max_y
        if max_y is not None
        else torch.ones((bboxes.size(0),), dtype=torch.bool)
    )
    target_mask = t_mask & x_iou_mask & b_mask

    values = []
    if target_mask.sum() > 0:
        target_boxlist = pred[target_mask]
        closest_bbox_idx = None
        for i, bbox in enumerate(target_boxlist.bbox):
            if closest_bbox_idx is None or bbox[1] < target_boxlist.bbox[closest_bbox_idx][1]:
                closest_bbox_idx = i

        bbox = target_boxlist.bbox[closest_bbox_idx]
        _, (bbox, value) = find_line_and_merge(bbox, target_boxlist)

        if value in ("부모", "무모"):  # side case caused by wrong detection and recognition
            l, t, r, b = bbox
            h = b - t
            bbox_up = [l, t, r, t + h / 2]
            bbox_down = [l, t + h / 2, r, b]
            values += [(bbox_up, "부"), (bbox_down, "모")]
        else:
            values.append((bbox, value))
    else:
        max_y = None

    if len(values) > 0:
        debug_dic.update(
            {
                "%s_%d_%d"
                % (keyword, idx[0], idx[1]): [
                    {"bbox": value[0], "text": value[1]} for value in values
                ]
            }
        )

    if max_y is None:
        return values

    if is_name:
        boundary_bbox = np.array([boundary_bbox[0], bbox[1], boundary_bbox[2], bbox[3]])
    else:
        boundary_bbox = np.array(bbox)
    return values + find_values(
        boundary_bbox, pred, debug_dic, keyword, (idx[0], idx[1] + 1), max_y, x_iou_thres, is_name
    )


def get_personal_info(pred, keyword_map, bottom_keywords):
    debug_dic = OrderedDict()
    bb = get_bottom_boundary(keyword_map, bottom_keywords)

    kbv_dict = {}
    for keyword, padding in zip(PERSONAL_INFO_KEYWORDS, PADDING_FACTOR):
        if keyword not in keyword_map:
            continue

        kbv_dict[keyword] = []
        for i in range(len(keyword_map[keyword])):
            target = keyword_map[keyword][i]["bbox"]
            max_y = None if i == 0 else bb["bbox"][1]
            if keyword == "성명":
                lbbox = keyword_map["구분"][0]["bbox"]
                rbbox = keyword_map["출생연월일"][0]["bbox"]
                boundary_bbox = np.array([lbbox[2], target[1], rbbox[0], target[3]])
                bvs = find_values(
                    boundary_bbox,
                    pred,
                    debug_dic=debug_dic,
                    keyword=keyword,
                    idx=(i, 0),
                    max_y=max_y,
                    x_iou_thres=0.99,
                    is_name=True,
                )
            else:
                width = target[2] - target[0]
                boundary_bbox = np.array(
                    [
                        target[0] - width / 2 * padding,
                        target[1],
                        target[2] + width / 2 * padding,
                        target[3],
                    ]
                )
                bvs = find_values(
                    boundary_bbox,
                    pred,
                    debug_dic=debug_dic,
                    keyword=keyword,
                    idx=(i, 0),
                    max_y=max_y,
                )
            kbv_dict[keyword] += bvs

    groupped_info = find_personal_info_group(kbv_dict)
    return groupped_info, debug_dic


def find_personal_info_group(kbv_dict):
    groups = []
    base_bvs = validate_parent(kbv_dict)

    for idx_base, base_bv in enumerate(base_bvs):
        base_bbox, base_value = base_bv
        base_bbox = np.array(base_bbox)

        group = {"구분": base_value}
        for keyword in PERSONAL_INFO_KEYWORDS[1:]:
            target_bvs = kbv_dict[keyword]
            target_bboxes = [b for b, v in target_bvs]
            target_bboxes = np.array(target_bboxes)
            if keyword == "주민등록번호":
                birth_bboxes = np.array([b for b, v in kbv_dict["출생연월일"]])
                birth_box_idx = np.argmax(_get_iou_y(base_bbox[None, :], birth_bboxes))
                left_bbox = birth_bboxes[birth_box_idx]
            else:
                left_bbox = base_bbox
            y_iou_score = _get_iou_y(left_bbox[None, :], target_bboxes, divide_by_area2=True)
            y_iou_mask = y_iou_score > 0.2
            if isinstance(y_iou_mask, np.ndarray):
                y_iou_mask = torch.tensor(y_iou_mask)
            target_mask = torch.squeeze(y_iou_mask, dim=0)

            if target_mask.sum() > 0:
                idx = torch.nonzero(target_mask)[0][0]
                value = target_bvs[idx][1]
            else:
                if y_iou_score.max() < 0.05:
                    padding_ratio = 0.1
                    ymin_ori, ymax_ori = base_bbox[1::2]
                    max_ymax = ymax_ori + (ymax_ori - ymin_ori)
                    flag = False
                    for i in range(10):
                        ymin, ymax = base_bbox[1::2]
                        h = ymax - ymin
                        ymin = max(0, int(ymin - padding_ratio * h))
                        ymax = max(max_ymax, int(ymax + padding_ratio * h))
                        base_bbox[1] = ymin
                        base_bbox[3] = ymax
                        y_iou_score = _get_iou_y(
                            base_bbox[None, :], target_bboxes, divide_by_area2=True
                        )
                        if y_iou_score.max() > 0.05:
                            flag = True
                            break
                    if flag:
                        idx = np.argmax(y_iou_score.squeeze())
                        value = target_bvs[idx][1]
                    else:
                        value = ""
                else:
                    idx = np.argmax(y_iou_score.squeeze())
                    value = target_bvs[idx][1]

            if keyword == "성명":
                dead_checker = value.split(")")
                is_dead = (len(dead_checker) > 1 and len(dead_checker[-1]) > 1) or (
                    len(value) > 2 and "사망" in value
                )
                value = value.split("(")[0]
                value = value.replace("[others]", "")
                value.rstrip("사망")
                if is_dead:
                    group["사망"] = "사망"
            elif keyword == "주민등록번호":
                if value.find("-") < 0 and len(value) > 7:
                    value = value[:6] + "-" + value[6:]
            group[keyword] = value

        groups.append(group)

    return groups


def validate_parent(kbv_dict):
    gubun_bvs = kbv_dict[PERSONAL_INFO_KEYWORDS[0]]

    if len(set(["부", "모"]) & set([_[1] for _ in gubun_bvs])) > 0:
        # 만약 '구분' 열의 '부', '모' 키워드 중 하나 이상이 인식된 경우
        if len(gubun_bvs) > 2 and (
            (gubun_bvs[1][1] != "부" and gubun_bvs[2][1] == "모")
            or (gubun_bvs[1][1] == "부" and gubun_bvs[2][1] != "모")
        ):
            match_target = get_longest_bvs(kbv_dict)
            match_target_idx = 1 if gubun_bvs[1][1] != "부" else 2

            item = (
                [
                    gubun_bvs[0][0][0],
                    match_target[match_target_idx][0][1],
                    gubun_bvs[0][0][2],
                    match_target[match_target_idx][0][3],
                ],
                "부" if match_target_idx == 1 else "모",
            )

            gubun_bvs = gubun_bvs[:match_target_idx] + [item] + gubun_bvs[match_target_idx:]
        return gubun_bvs
    else:
        all_gubun_keys = [_[1] for _ in gubun_bvs]
        if "본인" in all_gubun_keys and "배우자" in all_gubun_keys:
            # interpolation ratio
            ip_father = 0.62
            ip_mother = 0.78
            interpolate = lambda a, b, ip: ip * b + (1 - ip) * a
            longest_bvs = get_longest_bvs(kbv_dict)
            gubun_self_bbox = [np.array(_[0]) for _ in gubun_bvs if _[1] == "본인"][0]
            gubun_spouse_bbox = [np.array(_[0]) for _ in gubun_bvs if _[1] == "배우자"][0]
            gubun_father_bbox = [
                interpolate(a, b, ip_father) for a, b in zip(gubun_self_bbox, gubun_spouse_bbox)
            ]
            gubun_mother_bbox = [
                interpolate(a, b, ip_mother) for a, b in zip(gubun_self_bbox, gubun_spouse_bbox)
            ]
            item_father = ([torch.tensor(_) for _ in gubun_father_bbox], "부")
            item_mother = ([torch.tensor(_) for _ in gubun_mother_bbox], "모")
            gubun_bvs = [gubun_bvs[0]] + [item_father] + [item_mother] + gubun_bvs[1:]
            return gubun_bvs
        else:
            return gubun_bvs


def get_longest_bvs(kbv_dict):
    longest_bvs = []
    for bvs in kbv_dict.values():
        if len(longest_bvs) < len(bvs):
            longest_bvs = bvs
    return longest_bvs
