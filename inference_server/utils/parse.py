import os
import re
import sys
import time
import json
import datetime
import numpy as np

from lovit.postprocess import postprocess_idcard

from inference_server.utils.envs import logger, settings
from inference_server.errors import exceptions as ex


remove_region_code = bool(settings.ID_DLC_REMOVE_REGION_CODE)
date_reg = re.compile(r"[^0-9]+")
valid_type = {
    "RRC": ["id", "issue_date", "name"],
    "DLC": ["id", "issue_date", "name", "dlc_license_region", "dlc_license_num", "dlc_serial_num"],
    "ARC_FRONT": ["id", "issue_date", "name", "arc_nationality", "arc_visa"],
    "ARC_BACK": ["expiration_date"],
}
essential_keys = {
    "RRC": ["id", "name", "issue_date"],
    "DLC": ["id", "issue_date", "name", "dlc_license_num"],
    "ARC_FRONT": ["id", "issue_date", "name", "arc_nationality"],
    "ARC_BACK": ["expiration_date"],
}


def parse_results(
    kv_boxes,
    kv_scores,
    kv_classes,
    texts,
    boundary_box,
    boundary_score,
    id_type,
    savepath,
    response_log,
):

    logger.debug(f"kv_boxes: {kv_boxes}")
    logger.debug(f"kv_scores: {kv_scores}")
    logger.debug(f"kv_classes: {kv_classes}")

    result_kv = dict()
    unique_classes = list(set(kv_classes))
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
                pass
            result_kv[k] = _t
        else:
            result_kv[k] = "".join(v).rstrip(",")

    # essential_classes = essential_keys[id_type]
    # # if not all([_ in result_kv.keys() for _ in essential_classes]):
    # if sum([_ in result_kv.keys() for _ in essential_classes]) < 2 and len(essential_classes) > 1:
    #     raise ex.InferenceException(
    #         code="T5001", message="Unable to extract information from id card"
    #     )

    # print("\033[95m" + f"{result_kv.keys()}" + "\033[m")
    # print("\033[95m" + f"{valid_classes}" + "\033[m")
    # 다른 경우 올바른 값을 반환하도록 구성
    # # Parameter로 입력된 신분증 종류와 인식된 결과가 다른 경우 에러 발생
    # if (not settings.ID_FORCE_TYPE) and (
    #     len(set(result_kv.keys()) - set(valid_classes)) > 0
    #     or not all([_ in result_kv.keys() for _ in essential_classes])
    # ):
    #     raise ex.InferenceException(
    #         code="T5002",
    #         message="Type of ID card recognized differently from parameter",
    #     )

    for vc in valid_classes:
        if not vc in result_kv:
            result_kv[vc] = ""

    # 신형운전면허증에서 dlc_licenes_region 삭제.
    if "dlc_license_region" in result_kv and result_kv["dlc_license_num"].count("-") >= 3:
        del result_kv["dlc_license_region"]

    logger.debug(f"result_kv(pp): {result_kv}")
    logger.debug(f"savepath: {savepath}")
    return_savepath = "/" + "/".join(savepath.split("/")[-2:])

    response = {
        "result": postprocess_idcard(result_kv),
        "savepath": return_savepath,
    }
    if settings.RESPONSE_LOG:
        response["log"] = response_log

    if settings.SAVE_ID_DEBUG_INFO and settings.ID_DEBUG_INFO_PATH is not None:
        json_object = json.dumps(response)
        info_save_dir = os.path.join(settings.ID_DEBUG_INFO_PATH, time.strftime("%Y%m%d"))
        os.makedirs(info_save_dir, exist_ok=True)
        info_save_path = os.path.join(
            info_save_dir, os.path.basename(savepath).split(".")[0] + ".json"
        )
        with open(info_save_path, "w") as outfile:
            outfile.write(json_object)
        if sys.platform == "linux":
            os.chown(
                os.path.dirname(info_save_path), int(settings.SAVE_UID), int(settings.SAVE_GID)
            )
            os.chown(info_save_path, int(settings.SAVE_UID), int(settings.SAVE_GID))
    return response
