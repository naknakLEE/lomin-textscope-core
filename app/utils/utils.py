import pdf2image
import sys
import json
import base64
import re
import tifffile
import cv2
import numpy as np

from typing import Dict, List, Optional, Any, Union, Tuple
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pathlib import Path
from pdf2image import convert_from_path
from io import BytesIO
from PIL import Image
from rich.progress import track
from datetime import datetime

from app.common.const import get_settings
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
) -> str:
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


def substitute_spchar_to_alpha(decoded_texts: List[str]) -> List[str]:
    removed_texts: List[str] = list()
    regex = r"[\[\]\|]"
    for decoded_text in decoded_texts:
        if len(decoded_text) > 1:
            regex = r"\|"
        removed_text: List[str] = list()
        for text in decoded_text:
            found_spchar = re.findall(regex, text)
            if found_spchar:
                logger.info(f"find special charaters {found_spchar}")
            removed_text.append(re.sub(regex, "I", text))
        removed_texts.append("".join(removed_text))
    return removed_texts


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


def get_pp_api_name(doc_type: str, customer: str = settings.CUSTOMER) -> Optional[str]:
    if not isinstance(pp_mapping_table, dict):
        raise ResourceDataError(detail="pp mapping table is not a dict")
    
    route_name = None
    if not doc_type: return route_name

    route_name = [k for k, v in pp_mapping_table.items() if doc_type in v][-1]           
    return route_name


def cal_time_elapsed_seconds(
    start: datetime, end: datetime, rounding_digits: int = 3
) -> str:
    elapsed = end - start
    elapsed_string = str(round(elapsed.total_seconds(), rounding_digits))
    return elapsed_string


def basic_time_formatter(target_time: str) -> str:
    return target_time.replace(".", "-", 2).replace(".", "", 1)[:-3]


def read_all_tiff_pages_with_tifffile(
    img_path: Union[Path, str], target_page: int = -1
) -> List[Image.Image]:
    if isinstance(img_path, str):
        img_path = Path(img_path)
    images: List[Image.Image] = []
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
        except FileNotFoundError:
            raise ResourceDataError(f"{img_path} is not exist")
        except:
            # @FIXME: 범용적인 message로 변경
            # @TODO: traceback을 추가해서 에러 파악이 쉽도록 구성
            raise ResourceDataError(f"{img_path} is broken")
    return images


def read_tiff_page(img_path: Union[Path, str], target_page: int = 0) -> Image.Image:
    if isinstance(img_path, str):
        img_path = Path(img_path)
    try:
        tiff_images = Image.open(img_path)
        tiff_images.seek(target_page)
        np_image = np.array(tiff_images.convert("RGB"))
        np_image = np_image.astype(np.uint8)
        tiff_images.close()
    except FileNotFoundError as exc:
        raise ResourceDataError(f"{img_path} is not exist", exc=exc)
    except Exception as exc:
        raise ResourceDataError(f"{img_path} is broken", exc=exc)
    return Image.fromarray(np_image)


def read_basic_image(image_path: Union[Path, str]) -> Image.Image:
    if isinstance(image_path, str):
        image_path = Path(image_path)
    try:
        cv2_img = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
        pil_image = Image.fromarray(cv2_img[:, :, ::-1])
    except FileNotFoundError as exc:
        raise ResourceDataError(f"{image_path} is not exist", exc=exc)
    except Exception as exc:
        raise ResourceDataError(f"{image_path} is broken", exc=exc)
    return pil_image


def read_pdf_image(image_path: Union[Path, str], page: int = 1) -> Image.Image:
    if isinstance(image_path, str):
        image_path = Path(image_path)
    try:
        pages = convert_from_path(image_path)
        pil_image = pages[page - 1]
    except FileNotFoundError as exc:
        raise ResourceDataError(f"{image_path} is not exist", exc=exc)
    except Exception as exc:
        raise ResourceDataError(f"{image_path} is broken", exc=exc)
    return pil_image


def read_image(
    image_path: Union[Path, str],
    page: int = 1,
    ext_allows: List[str] = settings.IMAGE_VALIDATION,
) -> Image.Image:
    if isinstance(image_path, str):
        image_path = Path(image_path)
    ext = image_path.suffix.lower()
    if ext not in ext_allows:
        raise ValueError(f"{ext} is not supported")
    if ext in [".jpg", ".jpeg", ".jp2", ".png", ".bmp"]:
        pil_image = read_basic_image(image_path)
    elif ext in [".pdf"]:
        pil_image = read_pdf_image(image_path, page)
    else:  # ext in [".tiff", "tif"]
        try:
            if isinstance(image_path, Path):
                image_path = image_path.as_posix()
            all_pages = read_all_tiff_pages_with_tifffile(image_path, page)
            pil_image = all_pages[page - 1]
        except:
            pil_image = read_tiff_page(image_path, page - 1)
    pil_image = pil_image.convert("RGB")
    return pil_image


def load_image2base64(img_path: Union[Path, str]) -> Optional[str]:
    image = read_image(img_path)
    if image is None:
        return None
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue())
    return img_str.decode()


def dir_structure_validation(
    path: Path, ext_allows: List[str] = settings.IMAGE_VALIDATION
) -> bool:
    for folder_name in track(["train","val","test"], description="Folder structure validation"):
        folder_path = path / folder_name
        files_under_root = list(folder_path.glob("*.*"))
        category_dirs = list(folder_path.iterdir())
        for file_under_root in files_under_root:
            if file_under_root.suffix.lower() in ext_allows:
                raise ValueError("exist file under the root dir")
        if not category_dirs:
            raise ValueError("directory is empty")
        for category_dir in category_dirs:
            if category_dir.is_dir():
                is_exist_sub_dir = list(
                    sub_dir for sub_dir in category_dir.iterdir() if sub_dir.is_dir()
                )
                if is_exist_sub_dir:
                    raise ValueError(f"{category_dir} include sub dir")
            else:
                raise ValueError(f"{category_dir} is not dir")
            files = list(category_dir.rglob("*.*"))
            if not files:
                raise ValueError(f"{category_dir} is empty")
            for file in files:
                extension = file.suffix
                if extension.lower() not in ext_allows:
                    raise ValueError(f"{extension} is not supported")
    return True


def image_file_validation(file: Path) -> bool:
    white_list = settings.IMAGE_VALIDATION

    file_format = file.suffix.lower()
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


def set_predictions(
    detection_result: Dict[str, List],
    recognition_result: Dict[str, List],
) -> List[Dict[str, Any]]:
    classes = detection_result.get("classes", [])
    scores = detection_result.get("scores", [])
    boxes = detection_result.get("boxes", [])
    texts = (
        detection_result.get("texts", [])
        if "texts" in detection_result
        else recognition_result.get("texts", [])
    )
    predictions: List[Dict[str, Any]] = list()
    for class_, score_, box_, text_ in zip(classes, scores, boxes, texts):
        prediction = {
            "class": class_,
            "score": score_,
            "box": box_,
            "text": text_,
        }
        predictions.append(prediction)
    return predictions


def set_ocr_response(
    inputs: Dict, sequence_list: List[str], result_set: Dict[str, Dict]
) -> Dict[str, Any]:
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
