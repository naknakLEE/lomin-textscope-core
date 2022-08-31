import cv2
import numpy as np
import tifffile
import pdf2image
import base64

from io import BytesIO
from PIL import Image
from typing import Dict, Optional, Tuple, List, Union
from pathlib import Path
from functools import lru_cache
from app.models import ImageCropBbox

from app.utils.logging import logger
from app.common.const import get_settings
from app.utils.minio import MinioService


settings = get_settings()
minio_client = MinioService()

jpegopt={
    "quality": 100,
    "progressive": False,
    "optimize": False
}


def read_tiff_multi_page_from_bytes(image_bytes):
    pil_images = list()
    try:
        tif_images = list()
        with tifffile.TiffFile(BytesIO(image_bytes)) as tif:
            tif_images = [ x.asarray() for x in tif.pages ]
        
        for tif_image in tif_images:
            if tif_image.dtype == np.bool:
                np_image = (tif_image * 255).astype(np.uint8)
            else: # tif_images.dtype == np.unit8:
                np_image = tif_image.astype(np.uint8)
            
            pil_images.append(Image.fromarray(np_image))
        
    except:
        try:
            pil_images = read_tiff_multi_page_from_bytes_(image_bytes)
        except:
            pil_images = None
        
    finally:
        return pil_images


def read_tiff_multi_page_from_bytes_(image_bytes):
    pil_images = list()
    
    page = 0
    tiff_images = Image.open(BytesIO(image_bytes))
    try:
        while True:
            tiff_images.seek(page)
            np_image = np.array(tiff_images.convert("RGB"))
            np_image = np_image.astype(np.uint8)
            
            pil_images.append(Image.fromarray(np_image))
            page += 1
        
    except EOFError:
        pass
    
    tiff_images.close()
    
    return pil_images


def read_tiff_one_page_from_bytes(image_bytes, page=1):
    pil_image = None
    try:
        try:
            tif_image = tifffile.imread(BytesIO(image_bytes), key=page - 1)
        except IndexError:
            tif_image = tifffile.imread(BytesIO(image_bytes), key=0)
        
        if tif_image.dtype == np.bool:
            np_image = (tif_image * 255).astype(np.uint8)
        else: # tif_images.dtype == np.unit8:
            np_image = tif_image.astype(np.uint8)
        
        pil_image = Image.fromarray(np_image)
        
    except:
        try:
            pil_image = read_tiff_one_page_from_bytes_(image_bytes, page)
        except:
            pil_image = None
        
    finally:
        return pil_image


def read_tiff_one_page_from_bytes_(image_bytes: str, page: int):
    tiff_images = Image.open(BytesIO(image_bytes))
    tiff_images.seek(page - 1)
    np_image = np.array(tiff_images.convert("RGB"))
    np_image = np_image.astype(np.uint8)
    tiff_images.close()
    
    return Image.fromarray(np_image)


@lru_cache(maxsize=15)
def read_pillow_from_bytes(image_bytes, image_filename, page: int = 1, separate: bool = False):
    pil_images = list()
    file_extension = Path(image_filename).suffix.lower()
    if file_extension in [".jpg", ".jpeg", ".jp2", ".png", ".bmp"]:
        try:
            nparr = np.fromstring(image_bytes, np.uint8)
            cv2_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            pil_images.append(Image.fromarray(cv2_img[:, :, ::-1]))
        except:
            pil_images = None
        
    elif file_extension in [".tif", ".tiff"]:
        if separate == False:
            pil_images.append(read_tiff_one_page_from_bytes(image_bytes, page))
        else:
            pil_images = read_tiff_multi_page_from_bytes(image_bytes)
            
    elif file_extension == ".pdf":
        if separate == False:
            pil_images = pdf2image.convert_from_bytes(image_bytes, fmt="jpeg", first_page=page, last_page=page, jpegopt=jpegopt)
            
            if len(pil_images) == 0:
                pil_images = pdf2image.convert_from_bytes(image_bytes, fmt="jpeg", first_page=1, last_page=1, jpegopt=jpegopt)
        else:
            pil_images = pdf2image.convert_from_bytes(image_bytes, fmt="jpeg", jpegopt=jpegopt)
        
    else:
        logger.error(f"{image_filename} is not supported!")
        pil_images = None
    
    if pil_images is None:
        logger.exception("read pillow")
        logger.error(f"Cannot read page:{page} in {image_filename}")
        pil_images = None
    
    pil_images_ = list()
    for pil_image in pil_images:
        if pil_image.mode == "RGB":
            pil_images_.append(pil_image)
        else:
            pil_images_.append(pil_image.convert("RGB"))
    
    return pil_images_


# @lru_cache(maxsize=15)
def read_image_from_bytes(
    image_bytes: str, image_filename: str, angle: Optional[float], page: int, /, separate: bool = False
) -> Union[List[Image.Image], Image.Image]:
    """
    Get pillow images or image from image_bytes
    separate: true will return list of images, false will return one image
    """
    images = read_pillow_from_bytes(image_bytes, image_filename, page, separate=separate)
    
    if images and angle != 0.0:
        images = [ x.rotate(angle, expand=True) for x in images ]
    
    if separate == False:
        return images[0]
    
    return images


@lru_cache(maxsize=15)
def get_image_info_from_bytes(
    image_bytes: str, image_filename: str, page: int
) -> Tuple[str, int, int, str]:
    
    image = read_pillow_from_bytes(image_bytes, image_filename, page)[0]
    
    if image is None:
        return (None, 0, 0, "")
    
    image_base64 = image_to_base64(image, "jpeg")
    
    return (image_base64.decode(), image.size[0], image.size[1], "jpeg")


def image_to_base64(image: Image, file_format: str = "jpeg") -> str:
    buffered = BytesIO()
    image.save(buffered, file_format)
    
    return base64.b64encode(buffered.getvalue())


def load_image(data: dict):
    image_id:    str = data.get("image_id")
    image_path:  str = data.get("image_path")
    image_bytes: str = data.get("image_bytes")
    
    if image_path is None:
        logger.warning(f"Request must have image_path to load image (image_id: {image_id})")
        return None
    
    image_path = Path(image_path)
    image_filename = image_path.name
    if image_bytes is None:
        image_bytes = get_image_bytes(image_id, image_path)
    
    image = read_image_from_bytes(
        image_bytes, image_filename, float(data.get("angle", 0.0)), int(data.get("page", 1))
    )
    
    if image is None:
        logger.warning(f"{image_filename} is not support image or file")
        return None
    
    logger.debug(f"Loaded image shape: {image.size}")
    
    return image


def save_upload_image(
    image_id: str, image_name: str, image_base64: str
) -> Tuple[bool, str]:
    
    decoded_image_data = base64.b64decode(image_base64)
    success = False
    save_path = ""
    if settings.USE_MINIO:
        success = minio_client.put(
            bucket_name=settings.MINIO_IMAGE_BUCKET,
            object_name=image_id + '/' + image_name,
            data=decoded_image_data,
        )
        save_path = "minio/" + image_name
        
    else:
        root_path = Path(settings.IMG_PATH)
        base_path = root_path.joinpath(image_id)
        base_path.mkdir(parents=True, exist_ok=True)
        save_path = base_path.joinpath(image_name)
        
        with save_path.open("wb") as file:
            file.write(decoded_image_data)
        
        success = True
    
    return success, save_path


def get_image_bytes(image_id: str, image_path: Path) -> str:
    image_bytes = None
    
    if settings.USE_MINIO:
        image_minio_path = "/".join([image_id, image_path.name])
        image_bytes = minio_client.get(image_minio_path, settings.MINIO_IMAGE_BUCKET)
    else:
        with image_path.open("rb") as f:
            image_bytes = f.read()
    
    return image_bytes


def get_crop_image(image: Image, format: str, crop: List[ImageCropBbox]) -> List[Dict[int, str]]:
    crop_images = list()
    image_size = image.size
    
    if format not in ["jpeg", "png"]:
        format = "jpeg"
    
    for cropBbox in crop:
        bbox = cropBbox.bbox
        crop_area = (bbox.x, bbox.y, bbox.x + bbox.w, bbox.y + bbox.h)
        
        if is_cropBbox_in_range(image_size, crop_area) is False:
            break
        
        crop_image = image.crop(crop_area)
        
        crop_images.append(dict(
            index=cropBbox.index,
            label=cropBbox.label,
            image=image_to_base64(crop_image, format)
        ))
    
    return crop_images


def is_cropBbox_in_range(image_size: tuple, crop_area: tuple) -> bool:
    
    # w, h was zero or minus
    if crop_area[0] >= crop_area[2] or crop_area[1] >= crop_area[3]:
        return False
    
    # start coordinate was out of range
    if crop_area[0] < 0 or image_size[0] < crop_area[0] \
        or crop_area[1] < 0 or image_size[1] < crop_area[1]:
        return False
    
    # end coordinate was out of range
    if crop_area[2] < 0 or image_size[0] < crop_area[2] \
        or crop_area[3] < 0 or image_size[1] < crop_area[3]:
        return False
    
    return True