import sys
import json
import base64
import re
import tifffile
import cv2
import numpy as np

from typing import Dict, List, Optional, Union
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pathlib import Path
from pdf2image import convert_from_path
from io import BytesIO
from PIL import Image
from app.common.const import get_settings
from datetime import datetime
from app.errors.exceptions import ResourceDataError

from app.utils.logging import logger


settings = get_settings()
pp_mapping_table = settings.PP_MAPPING_TABLE
document_type_set = settings.DOCUMENT_TYPE_SET


# @FIXME: 이름과 기능이 맞지 않음
def pretty_dict(
    data: Dict,
    indent: int = 4,
    sort_keys: bool = True,
    ensure_ascii: bool = False,
):
    if isinstance(data, dict):
        data = jsonable_encoder(data)
        return json.dumps(
            data, indent=indent, sort_keys=sort_keys, ensure_ascii=ensure_ascii
        )
    elif isinstance(data, list):
        data = jsonable_encoder(dict(data=data))
        return json.dumps(
            dict(data=data),
            indent=indent,
            sort_keys=sort_keys,
            ensure_ascii=ensure_ascii,
        )
    else:
        data = jsonable_encoder(data.dict())
        return json.dumps(
            data, indent=indent, sort_keys=sort_keys, ensure_ascii=ensure_ascii
        )


def substitute_spchar_to_alpha(decoded_texts):
    removed_texts = list()
    regex = r"[\[\]\|]"
    if len(decoded_texts) > 1:
        regex = r"\|"
    for text in decoded_texts:
        found_spchar = re.findall(regex, text)
        if found_spchar:
            logger.info(f"find special charaters {found_spchar}")
        removed_texts.append(re.sub(regex, "I", text))
    return "".join(removed_texts)


# @TODO: delete
def set_json_response(
    code: str, ocr_result: Dict = {}, message: str = ""
) -> JSONResponse:
    return JSONResponse(
        content=jsonable_encoder(
            dict(
                code=code,
                ocr_result=ocr_result,
                message=message,
            )
        )
    )


def get_pp_api_name(
    doc_type: str, customer: str = settings.CUSTOMER
) -> Union[None, str]:
    if not isinstance(pp_mapping_table, dict):
        raise ResourceDataError(detail="pp mapping table is not a dict")
    if doc_type in pp_mapping_table.get("idcard", []):
        return "idcard"
    if doc_type in pp_mapping_table.get("general_pp", []):
        return "kv"
    elif doc_type in pp_mapping_table.get("bankbook", []):
        return "bankbook"
    elif doc_type in pp_mapping_table.get("seal_imp_cert", []):
        return "seal_imp_cert"
    elif doc_type in pp_mapping_table.get("ccr", []):
        return "ccr"
    elif doc_type in pp_mapping_table.get("busan_bank", []):
        return "busan_bank"
    elif customer == "kakaobank" and doc_type in document_type_set:
        return document_type_set.get(doc_type)
    return None


def cal_time_elapsed_seconds(
    start: datetime, end: datetime, rounding_digits: int = 3
) -> str:
    elapsed = end - start
    elapsed_string = str(round(elapsed.total_seconds(), rounding_digits))
    return elapsed_string


def basic_time_formatter(target_time: str):
    return target_time.replace(".", "-", 2).replace(".", "", 1)[:-3]


def read_all_tiff_pages_with_tifffile(img_path, target_page=-1):
    images = []
    page_count = 0
    while True:  # we don't know how many page in tif file
        try:
            image = tifffile.imread(img_path, key=page_count)
            if image.dtype == np.bool:
                image = (image * 255).astype(np.uint8)
            else:
                image = image.astype(np.uint8)
            images.append(Image.fromarray(image))
            del image
            page_count += 1
            if page_count == target_page:
                break
        except IndexError:  # Out of index
            break
        except:
            return None
    return images


def read_tiff_page(img_path, target_page=0):
    try:
        tiff_images = Image.open(img_path)
        tiff_images.seek(target_page)
        np_image = np.array(tiff_images.convert("RGB"))
        np_image = np_image.astype(np.uint8)
        tiff_images.close()
    except:
        logger.exception("read tiff page")
        return None
    return Image.fromarray(np_image)


def read_basic_image(image_path):
    try:
        cv2_img = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
        pil_image = Image.fromarray(cv2_img[:, :, ::-1])
    except:
        logger.exception("read basic image")
        return None
    return pil_image


def read_pdf_image(image_path, page=1):
    try:
        pages = convert_from_path(image_path)
        pil_image = pages[page - 1]
    except:
        logger.exception("read pdf image")
        return None
    return pil_image


def read_image(image_path: Path, page=1):
    # @FIXME: return None -> raise exception of each case
    ext = image_path.suffix.lower()
    if ext in [".jpg", ".jpeg", ".jp2", ".png", ".bmp"]:
        pil_image = read_basic_image(image_path)
        if pil_image is None:
            return None
    elif ext in [".tif", ".tiff"]:
        all_pages = read_all_tiff_pages_with_tifffile(image_path, page)
        if all_pages is None:
            pil_image = read_tiff_page(image_path, page - 1)
            if pil_image is None:
                return None
        else:
            pil_image = all_pages[page - 1]
    elif ext in [".pdf"]:
        pil_image = read_pdf_image(image_path, page)
        if pil_image is None:
            return None
    else:
        logger.error(f"{image_path.suffix.lower()} is not supported!")
        return None
    pil_image = pil_image.convert("RGB")
    return pil_image


def load_image2base64(img_path: Path) -> Optional[str]:
    image = read_image(img_path)
    if image is None:
        return None
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue())
    return img_str.decode()


def dir_structure_validation(path: Path) -> int:
    if list(path.glob("*.*")):
        return False
    categories = list(path.iterdir())
    whole_files = list(set(path.rglob("*")) - set(categories))
    is_exist_sub_dir = set(len(file.parts) for file in whole_files if file.is_file())
    is_only_file = [file.is_file() for file in whole_files]
    is_not_empty_dir = [len(list(category.iterdir())) > 0 for category in categories]
    result = len(is_exist_sub_dir) == 1 and all(is_only_file) and all(is_not_empty_dir)
    return result


def image_file_validation(file: Path) -> bool:
    white_list = settings.IMAGE_VALIDATION

    file_format = file.suffix[1:].lower()
    if file_format not in white_list:
        return False

    image = read_image(file)
    if image is None:
        return False
    return True


def print_error_log() -> None:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    if exc_type is not None and exc_value is not None and exc_traceback is not None:
        error_log = {
            "filename": exc_traceback.tb_frame.f_code.co_filename,
            "lineno": exc_traceback.tb_lineno,
            "name": exc_traceback.tb_frame.f_code.co_name,
            "type": exc_type.__name__,
            "message": str(exc_value),
        }
        logger.info("error log detail: {}", error_log)
        del (exc_type, exc_value, exc_traceback, error_log)
    else:
        return None


def set_predictions(
    detection_result: Dict,
    recognition_result: Dict,
) -> List:
    classes = detection_result.get("classes", [])
    scores = detection_result.get("scores", [])
    boxes = detection_result.get("boxes", [])
    texts = (
        detection_result.get("texts", [])
        if "texts" in detection_result
        else recognition_result.get("texts", [])
    )
    predictions = list()
    for class_, score_, box_, text_ in zip(classes, scores, boxes, texts):
        prediction = {
            "class": class_,
            "score": score_,
            "box": box_,
            "text": text_,
        }
        predictions.append(prediction)
    return predictions


def set_ocr_response(inputs: Dict, sequence_list: List, result_set: Dict) -> Dict:
    detection_method = "general_detection"
    if "kv_detection" in sequence_list:
        detection_method = "kv_detection"
    classification_result = result_set.get("classification", {})
    detection_result = result_set.get(detection_method, {})
    recognition_result = result_set.get("recognition", {})
    predicsions = set_predictions(
        detection_result=detection_result,
        recognition_result=recognition_result,
    )
    return dict(
        predicsions=predicsions,
        class_score=classification_result.get("score", 0.0),
        image_height=detection_result.get("image_height"),
        image_width=detection_result.get("image_width"),
        id_type=detection_result["id_type"],
        rec_preds=recognition_result.get("rec_preds", []),
        doc_type=classification_result.get("doc_type", "None"),
    )
