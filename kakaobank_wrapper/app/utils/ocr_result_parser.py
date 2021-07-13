import re
import cv2
import os
import tifffile
import pdf2image
from loguru import logger
from PIL import Image
from collections import OrderedDict
import numpy as np
from skimage.color import rgb2gray
from skimage.transform import hough_line, hough_line_peaks
from scipy.stats import mode
from skimage.filters import threshold_otsu, sobel
from copy import deepcopy
from loguru import logger
import json

RRTABLE_TEMPLATE = {
    "tenantName": "",  # 차주한글이름
    "tenantID": "",  # 차주주민등록번호
    "memberNum": 0,  # 세대원 수
    "memberList": [],  # 세대원 정보
    "releaseDate": "",  # 발급일자
}
FAMILY_CERT_TEMPLATE = {
    "tenantName": "",  # 명의자이름
    "tenantID": "",  # 명의자주민등록번호
    "memberNum": 0,  # 세대원 수
    "memberList": [],  # 멤버리스트
    "releaseDate": "",  # 발급일자
}
REGI_CERT_TEMPLATE = {
    "realID": "",  # 부동산 고유번호
    "regID": "",  # 등기필정보 일련번호
    # 등기필정보 비밀번호
    "regPwd": [{"pwdKey": f"{(i + 1):02d}", "pwdValue": ""} for i in range(0, 50)],
}
BASIC_CERT_TEMPLATE = {
    "type": "",  # 기본증명서 문서 타입
    "tenantName": "",  # 차주한글이름
    "tenantID": "",  # 차주주민등록번호
    # "authStatus": "",  # 일반등록사항의 친권여부
    # "relation": "",  # 친권란의 관계
    "releaseDate": "",  # 발급일자
}
SUPPORTED_IMG_FORMATS = [
    ".jpg",
    ".jpeg",
    ".jp2",
    ".png",
    ".bmp",
    ".tif",
    ".tiff",
    ".pdf",
]
# kv result parser for kakaobank poc


async def parse_kakaobank(kv_result, kv_mode):
    result = OrderedDict()
    # 주민등록표
    if kv_mode == "rrtable":
        result.update(deepcopy(RRTABLE_TEMPLATE))
        if kv_result is not None:
            apply_rrtable_result(result, kv_result)
    # 가족관계증명서
    elif kv_mode == "family_cert":
        result.update(deepcopy(FAMILY_CERT_TEMPLATE))
        if kv_result is not None:
            apply_family_cert_result(result, kv_result)
    # 등기필증
    elif kv_mode == "regi_cert":
        result.update(deepcopy(REGI_CERT_TEMPLATE))
        if kv_result is not None:
            apply_regi_cert_result(result, kv_result)
    # 기본증명서
    elif kv_mode == "basic_cert":
        result.update(deepcopy(BASIC_CERT_TEMPLATE))
        if kv_result is not None:
            apply_basic_cert_result(result, kv_result)
    else:
        raise NotImplementedError
    return result


def apply_rrtable_result(rrtable_result, kv_result):
    rrtable_result["releaseDate"] = kv_result["issuedate"] if "issuedate" in kv_result else ""
    repetition = kv_result["repetition"] if "repetition" in kv_result else []
    rrtable_result["memberNum"] = len(repetition)
    for repeat in repetition:
        name = repeat["name"] if "name" in repeat else ""
        regnum = repeat["regnum"] if "regnum" in repeat else ""
        category = repeat["category"] if "category" in repeat else ""
        if category == "본인":
            rrtable_result["tenantName"] = name
            rrtable_result["tenantID"] = regnum
        member_dict = {
            "memberName": name,
            "memberID": regnum,
            "memberRelation": category,
        }
        rrtable_result["memberList"].append(member_dict)


def apply_family_cert_result(fam_cert_result, kv_result):
    fam_cert_result["releaseDate"] = kv_result["발행일"] if "발행일" in kv_result else ""
    repetition = kv_result["인적사항"] if "인적사항" in kv_result else []
    fam_cert_result["memberNum"] = len(repetition)
    for repeat in repetition:
        name = repeat["성명"] if "성명" in repeat else ""
        regnum = repeat["주민등록번호"] if "주민등록번호" in repeat else ""
        category = repeat["구분"] if "구분" in repeat else ""
        if category == "본인":
            fam_cert_result["tenantName"] = name
            fam_cert_result["tenantID"] = regnum
        fam_cert_result["memberList"].append(
            {
                "memberName": name,
                "memberID": regnum,
                "memberRelation": category,
                "status": "사망" if "사망" in repeat else "생존",
            }
        )


def apply_regi_cert_result(regi_cert_result, kv_result):
    regi_cert_result["realID"] = kv_result["estate_num"] if "estate_num" in kv_result else ""
    regi_cert_result["regID"] = kv_result["serial_num"] if "serial_num" in kv_result else ""
    passwords = sorted(kv_result["passwords"]) if "passwords" in kv_result else []
    for pwd in passwords:
        try:
            idx = pwd[:2]
            value = pwd[-4:]
            if int(idx) < 1 or int(idx) > 50:
                continue
            regi_cert_result["regPwd"][int(idx) - 1]["pwdValue"] = value
        except:
            pass


def apply_basic_cert_result(basic_cert_result, kv_result):
    basic_cert_result["tenantName"] = kv_result["name"] if "name" in kv_result else ""
    basic_cert_result["tenantID"] = kv_result["regnum"] if "regnum" in kv_result else ""
    # 보류
    # basic_cert_result['authStatus'] = kv_result['is_parent'] if 'is_parent' in kv_result else ''
    # basic_cert_result['relation'] = kv_result['relation'] if 'relation' in kv_result else ''
    basic_cert_result["releaseDate"] = kv_result["issue_date"] if "issue_date" in kv_result else ""


def find_rotated_angle(original_image):
    image = rgb2gray(np.array(original_image))
    threshold = threshold_otsu(image)
    bina_image = image < threshold
    image_edges = sobel(bina_image)
    h, theta, d = hough_line(image_edges)
    accum, angles, dists = hough_line_peaks(h, theta, d)
    angle = np.rad2deg(mode(angles)[0][0])
    if angle < 0:
        angle = angle + 90
    else:
        angle = angle - 90
    if angle > 45:
        angle = angle - 90
    elif angle < -45:
        angle = angle + 90
    return angle


def read_all_tiff_pages(img_path, target_page=-1):
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
            page_count += 1
            if page_count == target_page:
                break
        except:  # Out of index
            break
    return images


def read_pillow(image_path, page=1):
    ext = os.path.splitext(image_path)[-1].lower()
    if ext in [".jpg", ".jpeg", ".jp2", ".png", ".bmp"]:
        cv2_img = cv2.imread(image_path, cv2.IMREAD_COLOR)
        pil_image = Image.fromarray(cv2_img[:, :, ::-1])
    elif ext in [".tif", ".tiff"]:
        try:
            all_pages = read_all_tiff_pages(image_path, target_page=page)
            if len(all_pages) == 0:
                pil_image = Image.open(image_path).convert("RGB")
            else:
                pil_image = all_pages[page - 1]
        except:
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


def apply_exif_img(image):
    try:
        exif_data = image._getexif()
        if exif_data is None:
            return image
        if 274 in exif_data.keys():
            orientation = exif_data[274]
            if orientation == 0:
                pass
            elif orientation == 1:
                pass
            elif orientation == 2:
                image = image.transpose(Image.FLIP_LEFT_RIGHT)
            elif orientation == 3:
                image = image.transpose(Image.ROTATE_180)
            elif orientation == 4:
                image = image.transpose(Image.FLIP_TOP_BOTTOM)
            elif orientation == 5:
                image = image.transpose(Image.FLIP_TOP_BOTTOM).transpose(Image.ROTATE_90)
            elif orientation == 6:
                image = image.transpose(Image.ROTATE_270)
            elif orientation == 7:
                image = image.transpose(Image.FLIP_TOP_BOTTOM).transpose(Image.ROTATE_270)
            elif orientation == 8:
                image = image.transpose(Image.ROTATE_90)
        return image
    except:
        return image


def dpi_resize_img(image):
    dpi_ratio = 1.0
    if "dpi" in image.info.keys():
        dpi = image.info["dpi"]
        if dpi[0] * dpi[1] != 0:
            dpi_ratio = dpi[0] / dpi[1]
    if dpi_ratio == 1.0:
        resampled_size = (image.size[0], image.size[1])
    elif dpi_ratio > 1.0:
        resampled_size = (image.size[0], int(image.size[1] * dpi_ratio))
    else:
        resampled_size = (int(image.size[0] / dpi_ratio), image.size[1])
    if dpi_ratio != 1.0:
        image = image.resize(resampled_size, Image.ANTIALIAS)
    return image


def export_to_json(results_all, dir_src, dir_dst, imglist):
    via_anns = {}
    results_kv = {}
    for result_all, imgname in zip(results_all, imglist):
        filename = os.path.splitext(os.path.basename(imgname))[0]
        preds = result_all["result"]
        rot_angle = result_all["angle_to_rotate"] if "angle_to_rotate" in result_all else 0
        via_ann = result_to_via(preds, dir_src, imgname, rot_angle)
        via_anns.update(via_ann)
        if "result_kv" in result_all:
            result_kv = result_all["result_kv"]
            result_kv = {_["key"]: _["value"] for _ in result_kv}
            with open(os.path.join(dir_dst, f"{filename}_kv.json"), "w", encoding="utf8") as f:
                json.dump(result_kv, f, ensure_ascii=False, indent=4)
    with open(os.path.join(dir_dst, "demo_result.json"), "w", encoding="utf8") as f:
        json.dump(via_anns, f, ensure_ascii=False, indent=4)


def result_to_via(preds, dir_src, filename, rot_angle):
    via_anns = {}
    regions = list()
    imname = filename
    size = os.path.getsize(os.path.join(dir_src, filename))
    key = imname + str(size)
    w, h = read_pillow(os.path.join(dir_src, filename)).size
    file_attrs = {"width": w, "height": h, "rot_angle": rot_angle}
    for pred in preds:
        region = {}
        shape_attrs = {
            "name": "rect",
            "x": pred["bbox"][0],
            "y": pred["bbox"][1],
            "width": pred["bbox"][2] - pred["bbox"][0],
            "height": pred["bbox"][3] - pred["bbox"][1],
        }
        region_attrs = {"text": pred["texts"]}
        region.update({"shape_attributes": shape_attrs})
        region.update({"region_attributes": region_attrs})
        regions.append(region)
    data_dict = {
        "file_attributes": file_attrs,
        "filename": imname,
        "size": size,
        "regions": regions,
    }
    via_anns.update({key: data_dict})
    return via_anns
