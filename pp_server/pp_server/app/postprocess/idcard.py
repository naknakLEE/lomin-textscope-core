import re
import datetime
import numpy as np

from lovit.postprocess import postprocess_idcard
from typing import List, Dict

# from pp_server.app.utils.utils import logger
from loguru import logger
from pp_server.app.common.const import get_settings


settings = get_settings()
remove_region_code = bool(settings.ID_DLC_REMOVE_REGION_CODE)
date_reg = re.compile(r"[^0-9]+")
valid_type = settings.VALID_TYPE
essential_keys = settings.ESSENTIAL_KEYS


def parse_results(
    kv_boxes: List,
    kv_scores: List,
    kv_classes: List,
    texts: List,
    id_type: str,
):
    logger.debug(f"kv_boxes: {kv_boxes}")
    logger.debug(f"kv_scores: {kv_scores}")
    logger.debug(f"kv_classes: {kv_classes}")

    result_kv = dict()
    # unique_classes = list(set(kv_classes))
    valid_classes = valid_type[id_type] if id_type in valid_type else None
    for kv_class, text in zip(kv_classes, texts):
        if kv_class not in result_kv:
            result_kv[kv_class] = [text]
        else:
            result_kv[kv_class].append(text)

    result_classes = [_ for _ in kv_classes]
    all_classes = set(result_classes)
    result_scores = dict()
    for classname in all_classes:
        inds = [_ for _, x in enumerate(result_classes) if x == classname]
        result_scores.update({classname: [kv_scores[_] for _ in inds]})

    logger.debug(f"result_scores: {result_scores}")
    logger.debug(f"result_kv: {result_kv}")

    for k, v in result_kv.items():
        scores = result_scores[k]
        if k == "dlc_serial_num":
            result_kv[k] = v[np.argmax(scores)].upper()
        elif k == "id":
            if settings.DEIDENTIFY_JSON:
                result_kv[k] = v[0][:6]
            else:
                result_kv[k] = "-".join([_t[:_l] for _t, _l in zip(v, [6, 7])])
        elif k == "dlc_license_num":
            num_blocks = 3 if remove_region_code else 4
            v = [_.replace("[others]", "") for _ in v]
            v_candidates = [_ for _ in v if _.isnumeric() or _ == "-"]
            inds = np.argsort(scores)[::-1][:num_blocks]
            valid_dlc_license_num = [_ for idx, _ in enumerate(v_candidates) if idx in inds]
            length_limit = [2, 6, 2] if len(scores) == 3 else [2, 2, 6, 2]
            valid_dlc_license_num = [_t[:_l] for _t, _l in zip(valid_dlc_license_num, length_limit)]
            result_kv[k] = "-".join(valid_dlc_license_num)
        elif id_type == "ARC_FRONT" and k in ["name", "arc_nationality"]:
            result_kv[k] = " ".join(v).upper()
        elif k == "name":
            _t = v[np.argmax(scores)]
            if settings.ID_DE_NAME:
                _t_len = len(_t)
                if _t_len == 2:
                    _t = _t[:-1] + "*"
                else:
                    _t = _t[:2] + "*" * (_t_len - 2)
            result_kv[k] = _t  # Pick last one
        elif k in ["issue_date", "expiration_date"]:
            if k == "expiration_date" and id_type == "ARC_BACK":
                bottom_index = np.argmax(kv_boxes[kv_classes == "expiration_date"][1])
                _t = v[bottom_index]  # Pick bottom one
            else:
                _t = v[np.argmax(scores)]  # Pick best one
            _t = date_reg.sub("-", _t)
            if _t[-1] == "-":
                _t = _t[:-1]

            sliced_dates = _t.split("-")
            if len(sliced_dates) == 3:
                sliced_dates[0] = sliced_dates[0][:4]
                month = int(sliced_dates[1][:2])
                if month > 12:
                    month = 12
                if month == 0:
                    month = 9
                day = int(sliced_dates[2][:2])
                if day >= 32:
                    day = 31
                    if sliced_dates[2][0] == sliced_dates[2][1]:
                        day = sliced_dates[2][0]
                if day == 0:
                    day = 9
                sliced_dates[1] = str(month)
                sliced_dates[2] = str(day)
            _t = "-".join(sliced_dates)

            try:
                _t = datetime.strptime(_t, "%Y-%m-%d").strftime("%Y-%m-%d")
            except:
                logger.exception("parse_results")
            result_kv[k] = _t
        else:
            result_kv[k] = "".join(v).rstrip(",")

    for vc in valid_classes:
        if not vc in result_kv:
            result_kv[vc] = ""

    # 신형운전면허증에서 dlc_licenes_region 삭제.
    if "dlc_license_region" in result_kv and result_kv["dlc_license_num"].count("-") >= 3:
        del result_kv["dlc_license_region"]

    logger.debug(f"result_kv(pp): {result_kv}")

    return postprocess_idcard(result_kv)
