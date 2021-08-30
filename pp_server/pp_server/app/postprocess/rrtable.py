import re
import numpy as np
from PIL import Image
from collections import OrderedDict
import torch
from collections import defaultdict
import re
from soynlp.hangle import jamo_levenshtein, decompose
from loguru import logger

from pp_server.app.structures.keyvalue_dict import KVDict
from pp_server.app.postprocess.family_cert import obj_to_kvdict

# from .document_keywords import *
from pp_server.app.postprocess.commons import BoxlistPostprocessor as PP

# [등본]
# (a) 서류발급일자
# (b) 세대주와의 관계
# (c) 성명
# (d) 주민등록번호

# [초본]
# (a) 서류발급일자
# (b) 성명
# (c) 주민등록번호
# (d) 병역사항처분일자
# (e) 병역사항처분사항

# 등본(copy)
# 초본(abstract)
def get_doc_type(pred):
    return "copy", {}
    texts = pred.get_field("texts")
    indices = [
        i
        for i, text in enumerate(texts)
        if any(
            np.array(
                [jamo_levenshtein(key, text) for key in ["병역사항", "병역", "병사역항", "처분일자", "처분사항"]]
            )
            < 0.5
        )
    ]
    if len(indices) == 0:
        return "copy", {}

    else:
        return "abstract", {"doc_type": pred[np.array(indices)]}


# (b) 성명
# (c) 주민등록번호
def get_abstract_user_info(pred):
    kv_dict = dict()
    debug_dict = OrderedDict()
    kv_dict["regnum"] = ""
    kv_dict["name"] = ""

    texts = pred.get_field("texts")
    key_pred = pred[
        np.array([True if re.search("성명|주민등록번호|한자", text) else False for text in texts])
    ]
    debug_dict.update({"regnum_name_key": key_pred})
    if len(key_pred) > 0:
        filter_pred = (
            abs(pred.bbox[:, 1] - key_pred.bbox[np.argmin(key_pred.bbox[:, 1])][1])
            < (
                key_pred.bbox[np.argmin(key_pred.bbox[:, 1])][3]
                - key_pred.bbox[np.argmin(key_pred.bbox[:, 1])][1]
            )
            / 2
        )
        user_info_pred = pred[torch.tensor(filter_pred, dtype=torch.bool)]
        debug_dict.update({"user_info_candidate": user_info_pred})
        for idx, text in enumerate(user_info_pred.get_field("texts")):
            if re.search("\d{6}", text):
                kv_dict["regnum"] = text
                debug_dict.update({"regnum": user_info_pred[np.array([idx])]})
            elif (
                any(k in text for k in ["(", ")", "한자"])
                and len(kv_dict["name"]) == 0
                and len(user_info_pred) > idx + 1
            ):
                kv_dict["name"] = user_info_pred.get_field("texts")[idx + 1]
                debug_dict.update({"name": user_info_pred[np.array([idx + 1])]})

    return kv_dict, debug_dict


# (b) 세대주와의 관계
# (c) 성명
# (d) 주민등록번호
def get_copy_user_info(pred):
    kv_dict = dict()
    debug_dict = OrderedDict()
    kv_dict["repetition"] = list()
    texts = pred.get_field("texts")
    key_pred = pred[np.array([True if re.search("주민등록번호", text) else False for text in texts])]
    names = list()
    categories = list()

    if len(key_pred) > 0:
        filter_pred = np.array([False] * len(key_pred))
        filter_pred[np.argmin(key_pred.bbox[:, 1])] = True
        key_pred = key_pred[torch.tensor(filter_pred, dtype=torch.bool)]
        debug_dict.update({"repeat_key": key_pred})

        filtered_pred = pred[
            pred.bbox[:, 0]
            - (key_pred.bbox[0][0] - (key_pred.bbox[0][2] - key_pred.bbox[0][0]) / 2)
            > 0
        ]
        filtered_pred = filtered_pred[
            filtered_pred.bbox[:, 2]
            - (key_pred.bbox[0][2] + (key_pred.bbox[0][2] - key_pred.bbox[0][0]) / 2)
            < 0
        ]

        texts = filtered_pred.get_field("texts")
        regnum_pred = filtered_pred[
            np.array([True if re.search("\d{6}", text) else False for text in texts])
        ]
        index_from_up_to_bottom = np.argsort(regnum_pred.bbox[:, 1])
        regnum_pred = regnum_pred[index_from_up_to_bottom]

        if len(regnum_pred) > 1:
            distance_list = list()
            for idx in range(len(regnum_pred) - 1):
                distance_list.append(regnum_pred.bbox[idx + 1][1] - regnum_pred.bbox[idx][3])

            filter_pred = np.array([False] * len(regnum_pred))
            filter_pred[0] = True
            for idx, distance in enumerate(distance_list):
                if abs(distance) < (regnum_pred.bbox[0][3] - regnum_pred.bbox[0][1]) * 4:
                    filter_pred[idx + 1] = True
            regnum_pred = regnum_pred[torch.tensor(filter_pred, dtype=torch.bool)]

        debug_dict.update({"regnums": regnum_pred})

        for regnum_bbox, regnum_text in zip(regnum_pred.bbox, regnum_pred.get_field("texts")):
            repetition_dict = dict()
            filtered_regnum_text = "".join(re.findall("[0-9\*\-]", regnum_text))
            repetition_dict["regnum"] = filtered_regnum_text
            repetition_dict["category"] = ""
            repetition_dict["name"] = ""

            regnum_width = regnum_bbox[2] - regnum_bbox[0]
            regnum_height = regnum_bbox[3] - regnum_bbox[1]

            name_mask = (
                (pred.bbox[:, 3] < regnum_bbox[1] + regnum_height / 2)
                & (pred.bbox[:, 2] > regnum_bbox[0] - regnum_width / 2)
                & (pred.bbox[:, 0] < regnum_bbox[2] + regnum_width / 2)
            )

            name_candidates = pred[name_mask]
            repetition_dict["name"] = ""
            repetition_dict["category"] = ""

            if len(name_candidates) > 0:
                name_filter = np.array([False] * len(name_candidates))
                name_filter[
                    np.argmin(
                        abs(name_candidates.bbox[:, 3] - regnum_bbox[1])
                        + abs(name_candidates.bbox[:, 0] - regnum_bbox[0])
                    )
                ] = True

                name_pred = name_candidates[torch.tensor(name_filter, dtype=torch.bool)]
                repetition_dict["name"] = name_pred.get_field("texts")[0]
                names.append(name_pred[np.array([0])])

                name_bbox = name_pred.bbox[0]
                name_width = name_bbox[2] - name_bbox[0]
                name_height = name_bbox[3] - name_bbox[1]

            category_mask = (
                (pred.bbox[:, 0] < name_bbox[0])
                & (pred.bbox[:, 0] < regnum_bbox[0])
                & (pred.bbox[:, 1] > name_bbox[1] - name_height / 2)
                & (pred.bbox[:, 3] < regnum_bbox[3] + regnum_height / 2)
                if len(name_candidates) > 0
                else np.array([False] * len(category_mask))
            )

            category_candidates = pred[category_mask]
            if len(category_candidates) > 0:
                category_filter = np.array([False] * len(category_candidates))
                category_filter[
                    np.argmin(abs(category_candidates.bbox[:, 2] - name_bbox[0]))
                ] = True
                category_pred = category_candidates[category_filter]

                repetition_dict["category"] = category_pred.get_field("texts")[0]
                categories.append(category_pred[np.array([0])])

            kv_dict["repetition"].append(repetition_dict)

    for name in names[1:]:
        names[0] = names[0].merge_other_boxlist(name)

    for category in categories[1:]:
        categories[0] = categories[0].merge_other_boxlist(category)

    if len(names) > 0:
        debug_dict.update({"names": names[0]})
    if len(categories) > 0:
        debug_dict.update({"categories": categories[0]})

    return kv_dict, debug_dict


def get_left_boundary(text, bbox):
    width = bbox[2] - bbox[0]
    width_per_text = width / len(text)
    if "년" in text:
        _idx = text.index("년")
        year_x = bbox[0] + (width * _idx / len(text))
        boundary = year_x - width_per_text * 7

    elif "월" in text:
        _idx = text.index("월")
        month_x = bbox[0] + (width * _idx / len(text))
        boundary = month_x - width_per_text * 11

    elif "일" in text:
        _idx = text.index("일")
        day_x = bbox[0] + (width * _idx / len(text))
        boundary = day_x - width_per_text * 15

    return boundary


# (a) 서류발급일자
def get_issue_date(pred):
    kv_dict = dict()
    debug_dict = OrderedDict()
    kv_dict["issuedate"] = ""

    texts = pred.get_field("texts")
    key_pred = pred[np.array([True if re.search("년|월|일", text) else False for text in texts])]
    key_pred = PP.sort_tblr(key_pred)
    key_pred_text = key_pred.get_field("texts")
    debug_dict.update({"issuedate_key": key_pred})

    if len(key_pred) > 0:
        find_date = False
        for idx in range(len(key_pred)):
            left_boundary = get_left_boundary(key_pred_text[idx], key_pred.bbox[idx])
            filter_pred = (
                abs(pred.bbox[:, 1] - key_pred.bbox[idx][1])
                < (key_pred.bbox[idx][3] - key_pred.bbox[idx][1]) / 2
            ) & (pred.bbox[:, 0] > left_boundary)
            date_pred = pred[torch.tensor(filter_pred, dtype=torch.bool)]
            if all(
                any([key in text for text in date_pred.get_field("texts")])
                for key in ["년", "월", "일"]
            ):
                find_date = True
                break
        if find_date:
            if len(date_pred) > 1:
                kv_dict["issuedate"] = "".join(date_pred.get_field("texts"))
            elif len(date_pred) == 1:
                kv_dict["issuedate"] = date_pred.get_field("texts")[-1]
        kv_dict["issuedate"] = kv_dict["issuedate"][: kv_dict["issuedate"].find("일") + 1]
        debug_dict.update({"issue_date": date_pred})

    return kv_dict, debug_dict


# (d) 병역사항처분일자
# (e) 병역사항처분사항
def get_army_info(pred):
    kv_dict = OrderedDict()
    debug_dict = OrderedDict()
    kv_dict["mil_date"] = ""
    kv_dict["mil_matter"] = ""
    texts = pred.get_field("texts")

    for condition in ["처분일자$", "처분사항$", "\d{4}-\d{2}-\d{2}"]:
        key_pred = pred[np.array([True if re.search(condition, text) else False for text in texts])]
        if len(key_pred) > 0:
            break

    if len(key_pred) == 0:
        return kv_dict, {"army_info_key": key_pred}

    if len(key_pred) > 1:
        filter_pred = np.array([False] * len(key_pred))
        filter_pred[np.argmax(key_pred.bbox[:, 1])] = True
        key_pred = key_pred[torch.tensor(filter_pred, dtype=torch.bool)]

    debug_dict.update({"army_info_key": key_pred})

    filter_pred = (
        abs(pred.bbox[:, 1] - key_pred.bbox[-1][1])
        < (key_pred.bbox[-1][3] - key_pred.bbox[-1][1]) / 2
    )
    army_info_pred = pred[torch.tensor(filter_pred, dtype=torch.bool)]
    mil_date_indices = list()
    for _i, text in enumerate(army_info_pred.get_field("texts")):
        if re.search("\d{4}-\d{2}-\d{2}", text):
            kv_dict["mil_date"] = text.replace("[", "").replace("]", "")
            mil_date_indices.append(_i)
    kv_dict["mil_matter"] = army_info_pred.get_field("texts")[-1]

    if len(mil_date_indices) > 0:
        debug_dict.update({"army_mil_date": army_info_pred[np.array(mil_date_indices)]})
    debug_dict.update({"army_mil_matter": army_info_pred[np.array([len(army_info_pred) - 1])]})
    return kv_dict, debug_dict


def word_formatter(kv_dict, doc_type):
    if doc_type == "abstract":
        if "mil_matter" in kv_dict and "[" in kv_dict["mil_matter"]:
            mil_matter = kv_dict["mil_matter"]
            filter_idx = mil_matter.index("[")
            kv_dict["mil_matter"] = mil_matter[filter_idx + 1 :].replace("]", "")

    elif doc_type == "copy":

        for repeat in kv_dict["repetition"]:
            try:
                repeat["category"] = re.sub("[0-9]+", "", repeat["category"])
                if len(repeat["category"]) > 1:
                    for word in ["본인", "남편", "배우자", "자녀", "외손"]:
                        if jamo_levenshtein(repeat["category"], word) < 0.5:
                            repeat["category"] = word
                            break
                else:
                    for word in ["처", "자", "손", "부", "모"]:
                        cnt = 0
                        for ch1, ch2 in zip(decompose(word), decompose(repeat["category"])):
                            if ch1 == ch2:
                                cnt += 1
                        if cnt >= 2:
                            repeat["category"] = word
                            break
                regnum = re.sub("[^0-9*]+", "", repeat["regnum"])
                repeat["regnum"] = "".join([regnum[:6], regnum[6:13]])
            except:
                logger.exception("rrtable")

    return kv_dict


def postprocess_rrtable(pred, score_threshold, model_classes):
    from loguru import logger

    pred = PP.filter_score(pred, score_threshold=score_threshold)
    pred = PP.remove_overlapped_box(pred)
    pred = PP.sort_from_left(pred)

    kv_dict = dict()
    debug_dict = OrderedDict()
    doc_type, doc_type_pred = get_doc_type(pred)
    debug_dict.update(doc_type_pred)
    if doc_type == "abstract":
        army_dict, army_debug = get_army_info(pred)
        abstract_user_dict, abstract_user_debug = get_abstract_user_info(pred)
        kv_dict.update(army_dict)
        kv_dict.update(abstract_user_dict)
        debug_dict.update(army_debug)
        debug_dict.update(abstract_user_debug)

    elif doc_type == "copy":
        copy_user_dict, copy_user_debug = get_copy_user_info(pred)

        kv_dict.update(copy_user_dict)
        debug_dict.update(copy_user_debug)
        from loguru import logger

        logger.debug(f"kv_dict: {kv_dict}")

    else:
        pass

    issuedate_dict, issuedate_debug = get_issue_date(pred)
    kv_dict.update(issuedate_dict)
    debug_dict.update(issuedate_debug)

    kv_dict = word_formatter(kv_dict, doc_type)

    result_all_classes = dict()

    for k, v in kv_dict.items():
        result_all_classes[k + "_value"] = v

    # result = obj_to_kvdict(result_all_classes)
    # return result, debug_dict
    return KVDict(result_all_classes, str), debug_dict
