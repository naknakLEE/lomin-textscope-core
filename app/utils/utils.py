import sys
import json
import base64
import tempfile

from typing import Dict, Union, List, Tuple
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from os import environ
from pathlib import Path
from pdf2image import convert_from_path
from io import BytesIO
from PIL import Image
from app.common.const import get_settings
from datetime import datetime

from app.utils.logging import logger


settings = get_settings()
pp_mapping_table = settings.PP_MAPPING_TABLE
document_type_set = settings.DOCUMENT_TYPE_SET

def pretty_dict(
    data: Dict,
    indent: int = 4,
    sort_keys: bool = True,
    ensure_ascii: bool = False,

):
    if isinstance(data, dict):
        data = jsonable_encoder(data)
        return json.dumps(data, indent=indent, sort_keys=sort_keys, ensure_ascii=ensure_ascii)
    elif isinstance(data, list):
        data = jsonable_encoder(dict(data=data))
        return json.dumps(dict(data=data), indent=indent, sort_keys=sort_keys, ensure_ascii=ensure_ascii)
    else:
        data = jsonable_encoder(data.dict())
        return json.dumps(data, indent=indent, sort_keys=sort_keys, ensure_ascii=ensure_ascii)

def set_json_response(code: str, ocr_result: Dict = {}, message: str = "") -> JSONResponse:
    return JSONResponse(
        content=jsonable_encoder(
            dict(
                code=code,
                ocr_result=ocr_result,
                message=message,
            )
        )
    )


def get_pp_api_name(doc_type: str) -> Union[None, str]:
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
    elif settings.CUSTOMER == "kakaobank" and doc_type in document_type_set:
        return document_type_set.get(doc_type)
    return None

def cal_time_elapsed_seconds(start: datetime, end: datetime) -> str:
    elapsed = end - start
    sec, microsec = elapsed.seconds, round(elapsed.microseconds / 1_000_000, 3)
    return f'{sec + microsec}'

def basic_time_formatter(target_time: str):
    return target_time.replace('.', '-', 2).replace('.', '', 1)[:-3]

def load_image2base64(img_path):
    buffered = BytesIO()
    pil_image = Image.open(img_path)
    image_convert_rgb = pil_image.convert("RGB")
    image_convert_rgb.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()) 
    return img_str

def dir_structure_validation(path: Path) -> int:
    categories = list(path.iterdir())
    whole_files = list(set(path.rglob('*')) - set(categories))
    is_exist_sub_dir = set(len(file.parts) for file in whole_files if file.is_file())
    is_only_file = [file.is_file() for file in whole_files]
    is_not_empty_dir = [len(list(category.iterdir())) > 0 for category in categories]
    result = len(is_exist_sub_dir) == 1 and all(is_only_file) and all(is_not_empty_dir)
    return result

def file_validation(files: Union[Path, List[Path]]) -> List:
    white_list = settings.IMAGE_VALIDATION
    fake_files = list()
    if not isinstance(files, list):
        files = [files]
    
    for file in files:
        file_format = file.suffix[1:].lower()
        if file_format not in white_list:
            fake_files.append((file.name, 'unsupported extension'))

        if file_format == 'pdf':
            try:
                with tempfile.TemporaryDirectory() as temp_path:
                    img = convert_from_path(file, output_folder=temp_path)
            except Exception as e:
                fake_files.append((file.name, str(e)))
                pass
        elif file_format == 'jpg' or\
            file_format == 'png' or\
            file_format == 'tif' or\
            file_format == 'tiff':
            try:
                img = Image.open(file)
            except Exception as e:
                fake_files.append((file.name, str(e)))
                pass
    return fake_files


def print_error_log() -> None:
    error = sys.exc_info()
    exc_type, exc_value, exc_traceback = error
    error_log = {
        'filename': exc_traceback.tb_frame.f_code.co_filename,
        'lineno'  : exc_traceback.tb_lineno,
        'name'    : exc_traceback.tb_frame.f_code.co_name,
        'type'    : exc_type.__name__,
        'message' : str(exc_value),
    }
    logger.info("error log detail: {}", error_log)
    del(exc_type, exc_value, exc_traceback, error_log)


def set_predictions(
    general_detection_result: Dict,
    kv_detection_result: Dict,
    recogniton_result: Dict,
) -> Tuple[Dict, Dict]:
    # kv detection phase
    classes = kv_detection_result.get("classes", [])
    scores = kv_detection_result.get("scores", [])
    boxes = kv_detection_result.get("boxes", [])
    texts = kv_detection_result.get("texts", [])
    merged_count = kv_detection_result.get("merged_count", [])
    kv_predictions = list()
    for class_, score_, box_, text_, merged_count_ in zip(classes, scores, boxes, texts, merged_count):
        prediction = {
            "class": class_,
            "score": score_,
            "box": box_,
            "text": text_,
            "merged_count": merged_count_
        }
        kv_predictions.append(prediction)

    # general detection phase
    classes = general_detection_result.get("classes", [])
    scores = general_detection_result.get("scores", [])
    boxes = general_detection_result.get("boxes", [])
    texts = recogniton_result.get("texts", [])
    general_predictions = list()
    for class_, score_, box_, text_ in zip(classes, scores, boxes, texts):
        prediction = {
            "class": class_,
            "score": score_,
            "box": box_,
            "text": text_,
        }
        general_predictions.append(prediction)
    
    return {
        "kv_predictions": kv_predictions,
        "general_predictions": general_predictions 
    }


def set_ocr_response(
    general_detection_result: Dict,
    kv_detection_result: Dict,
    recognition_result: Dict,
    classification_result: Dict,
) -> Dict:
    predictions = set_predictions(
        kv_detection_result=kv_detection_result,
        general_detection_result=general_detection_result,
        recogniton_result=recognition_result,
    )
    doc_type = classification_result.get("doc_type")
    class_score = classification_result.get("scores").get(doc_type)
    response = dict(
        predictions=predictions,
        class_score=class_score,
        image_height=general_detection_result.get("image_height"),
        image_width=general_detection_result.get("image_width"),
        id_type=kv_detection_result.get("id_type"),
        rec_preds=recognition_result.get("rec_preds", []),
        doc_type=doc_type,
    )
    return response
