import sys
import base64
import tempfile

from typing import Dict, Union, List
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
    if doc_type.split("_")[0] in pp_mapping_table.get("general_pp", []):
        return "kv"
    elif doc_type.split("_")[0] in pp_mapping_table.get("bankbook", []):
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
            file_format == 'tiff' or\
            file_format == 'jpeg':
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


import os
import numpy as np

from datetime import datetime
from pathlib import Path
from typing import List, Optional, Union, Dict
from PIL import ImageDraw, ImageFont, Image

from app.utils.logging import logger
import cv2
import tifffile
from functools import lru_cache, reduce
import base64
import pdf2image


class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"

def revert_size(boxes, current_size, original_size):
    if current_size == original_size:
        return boxes
    x_ratio = original_size[0] / current_size[0]
    y_ratio = original_size[1] / current_size[1]
    boxes[:, 0::2] = boxes[:, 0::2] * x_ratio
    boxes[:, 1::2] = boxes[:, 1::2] * y_ratio
    return boxes


def load_image(data: Dict) -> np.array:
    if "image_path" in data:
        tiff_page = read_pillow(data["image_path"], int(data["page"]))
        image = np.asarray(tiff_page)
        del tiff_page
    else:
        try:
            image_bytes = base64.b64decode(data["image_bytes"])
            nparr = np.fromstring(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR) # cv2.IMREAD_COLOR in OpenCV 3.1
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        except Exception as exception:
            raise ValueError("Could not load image from b64 {}: {}".format(data["image_bytes"], exception)) from exception
    return image


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
        except:  # Out of index
            break
    return images


def read_all_tiff_pages_with_pillow(img_path, target_page=-1):
    images = []
    page_count = 0
    tiff_images = Image.open(img_path)
    for i in range(tiff_images.n_frames):
        tiff_images.seek(i)
        np_image = np.array(tiff_images.convert("RGB"))
        np_image = np_image.astype(np.uint8)
        images.append(Image.fromarray(np_image))
        del np_image
        page_count += 1
        if page_count == target_page:
            break
    tiff_images.close()
    return images


def read_tiff_page(img_path, target_page=0):
    tiff_images = Image.open(img_path)
    tiff_images.seek(target_page)
    np_image = np.array(tiff_images.convert("RGB"))
    np_image = np_image.astype(np.uint8)
    tiff_images.close()
    return Image.fromarray(np_image)




@lru_cache(maxsize=10)
def read_pillow(image_path, page=1):
    ext = os.path.splitext(image_path)[-1].lower()
    if ext in [".jpg", ".jpeg", ".jp2", ".png", ".bmp"]:
        cv2_img = cv2.imread(image_path, cv2.IMREAD_COLOR)
        pil_image = Image.fromarray(cv2_img[:, :, ::-1])
    elif ext in [".tif", ".tiff"]:
        try:
            all_pages = read_all_tiff_pages_with_tifffile(image_path, page)
            pil_image = all_pages[page - 1]
        except:
            try:
                pil_image = read_tiff_page(image_path, page-1)
            except:
                logger.exception("read pillow")
                logger.error(f"Cannot read {image_path}")
                return None
    elif ext in [".pdf"]:
        pages = pdf2image.convert_from_path(image_path)
        pil_image = pages[page - 1]
    else:
        logger.error(f"{image_path} is not supported!")
        return None
    pil_image = pil_image.convert("RGB")
    return pil_image

import torch
from lovit.structures.instances import Instances
from lovit.utils.visualizer import Visualizer
from pathlib import Path, PurePath

def save_debug_img(
    img_arr, 
    boxes, 
    classes, 
    scores, 
    texts, 
    savepath, 
    inference_type: Optional[str] = None, 
):
    _img_arr = img_arr[:, :, ::-1].copy()
    if inference_type == "split_screen":
        img = _img_arr

        instances_inputs = dict(
            image_size=(img_arr.shape[1], img_arr.shape[0]),
            boxes=torch.tensor(boxes),
            classes=np.array(classes),
        )
        if scores is not None and len(scores) > 0:
            instances_inputs["scores"] = np.array(scores)
        instances = Instances(**instances_inputs)
        instances.set("texts", texts)

        h, w, c = img.shape
        img_d = np.zeros([h, w, 3], dtype=np.uint8)
        img_d.fill(255)

        for instance in instances:
            bbox = instance.boxes.cpu().detach().numpy()[0]

            # JSON  BB format [x,y,w,h]
            x = bbox[0]
            y = bbox[1]
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]

            text = instance.texts[0]

            # Filter text  symbols
            text = text.replace("[UNK]", "")
            text = text.replace("/'", "")
            text = text.replace("/?", "")

            # Vertical text
            if h > w:
                vtext = ""
                for c in text:
                    vtext = vtext + c + "\n"
                text = vtext

            if text != "":
                fontpath = PurePath(
                    "/workspace/inference_server", 
                    "assets", 
                    "./malgun.ttf"
                ).as_posix()  # Korean font
                font_size = max(20, int((w + h) / 10))
                font = ImageFont.truetype(fontpath, font_size)
                img_pil = Image.fromarray(img_d)
                draw = ImageDraw.Draw(img_pil)
                draw.text((x, y), text, font=font, fill=(0, 0, 0, 1))
                img_d = np.array(img_pil)

        display_img = cv2.hconcat([img, img_d])

        watermark_img_path = PurePath(
                                "/workspace/inference_server"
                                "assets",
                                "watermark.png"
                            ).as_posix()
      
        _img_arr = display_img
    elif inference_type == "overlay":
        pil_image = _img_arr
        # TODO: label_class 데이터 깔끔하게 넣을 수 있도록 구성
        visualizer = Visualizer(img_rgb=pil_image)
        instances_inputs = dict(
            image_size=(img_arr.shape[1], img_arr.shape[0]),
            boxes=torch.tensor(boxes),
            classes=np.array(classes),
        )
        if scores is not None and len(scores) > 0:
            instances_inputs["scores"] = np.array(scores)
        instances = Instances(**instances_inputs)
        instances.set("texts", texts)
        vis_image = visualizer.draw_instance_predictions(instances).get_image()
        watermark_img_path = PurePath(
                                "/workspace/inference_server"
                                "assets",
                                "watermark.png"
                            ).as_posix()
        _img_arr = vis_image
    else:
        font_size = max(reduce(lambda x, y: x+y, _img_arr.shape)//10, 10)
        font = ImageFont.truetype(
            os.path.join(
                "/workspace/inference_server"
                "assets",
                "gulim.ttc",
            ),
            font_size,
        )
        white_image = Image.new("RGB", (img_arr.shape[1], img_arr.shape[0]), (255, 255, 255))
        logger.info(f"_img_arr: {_img_arr.shape}")
        drawing_paper = Image.fromarray(_img_arr)
        drawing_paper = Image.blend(drawing_paper, white_image, alpha=.3)
        draw = ImageDraw.Draw(drawing_paper)
        for _box, _class, _score, _text in zip(boxes, classes, scores, texts):
            min_x, min_y, max_x, max_y = _box.tolist()
            draw.rectangle([min_x, min_y, max_x, max_y], outline=(0,0,255), width=min(font_size//10, 3))
            draw = ImageDraw.Draw(drawing_paper)
            # if cfg.debug.WITH_CLASS:
            #     draw.text((min_x, abs(min_y-cfg.debug.REPOSITION_VALUE)), f"{_class}: {_text}", cfg.debug.TEXT_BGR, font=font)
            # elif cfg.debug.WITH_SCORE:
            #     draw.text((min_x, abs(min_y-cfg.debug.REPOSITION_VALUE)), f"{round(float(_score), 3)} {_text}", cfg.debug.TEXT_BGR, font=font)
            # else:
            #     draw.text((min_x, abs(min_y-cfg.debug.REPOSITION_VALUE)), f"{_text}", cfg.debug.TEXT_BGR, font=font)
            draw.text((min_x, abs(min_y-30)), f"{_text}", (0,0,255), font=font)
        _img_arr = np.concatenate((_img_arr, np.array(drawing_paper)), axis=1)
        del draw, font

    cv2.imwrite(savepath, _img_arr)
    return savepath