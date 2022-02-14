import os
import uuid
import pytest
import random
import base64
import tempfile
import tifffile
import numpy as np
import cv2
from io import BytesIO
from pathlib import Path
from typing import List
from PIL import Image
from pdf2image import convert_from_path
from datetime import datetime, timedelta
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from tests.utils.utils import Assert
from app.utils.utils import (
    get_pp_api_name,
    set_json_response,
    cal_time_elapsed_seconds,
    basic_time_formatter,
    load_image2base64,
    dir_structure_validation,
    image_file_validation,
    print_error_log,
    substitute_spchar_to_alpha,
)


@pytest.mark.unit
def test_get_pp_api_name():
    test_datas = [
        {"input": {"doc_type": "HKL01-DT-CAD"}, "expected": "kv"},
        {"input": {"doc_type": "HKL01-DT-CD"}, "expected": None},
        {"input": {"doc_type": "HKL01-DT-PRS"}, "expected": "kv"},
    ]
    for test_data in test_datas:
        Assert(get_pp_api_name, test_data).equal()


@pytest.mark.unit
def test_set_json_response():
    test_datas = [
        {
            "input": {"code": "3000", "ocr_result": {}, "message": "test_message"},
            "expected": JSONResponse(
                content=jsonable_encoder(
                    dict(code="3000", ocr_result={}, message="test_message")
                )
            ),
        },
        {
            "input": {"code": "3000", "ocr_result": {}},
            "expected": JSONResponse(
                content=jsonable_encoder(dict(code="3000", ocr_result={}, message=""))
            ),
        },
        {
            "input": {"code": "5000"},
            "expected": JSONResponse(
                content=jsonable_encoder(dict(code="5000", ocr_result={}, message=""))
            ),
        },
    ]
    for test_data in test_datas:
        test = Assert(set_json_response, test_data)
        test.is_instance(JSONResponse)
        test.equal_response()


@pytest.mark.unit
def test_cal_time_elapsed_seconds():
    test_datas: List = []
    for _ in range(5):
        std_start_time = datetime.now()
        std_end_time = datetime.now() + timedelta(
            milliseconds=random.uniform(1.0, 100.0)
        )
        rounding_digits = random.randint(1, 5)
        elapsed = std_end_time - std_start_time
        elapsed_string = str(round(elapsed.total_seconds(), rounding_digits))
        test_data = {
            "input": {
                "start": std_start_time,
                "end": std_end_time,
                "rounding_digits": rounding_digits,
            },
            "expected": elapsed_string,
        }
        test_datas.append(test_data)

    for test_data in test_datas:
        Assert(cal_time_elapsed_seconds, test_data).equal()


@pytest.mark.unit
def test_basic_time_formatter():
    test_datas: List = []
    for _ in range(5):
        std_time = str(datetime.now())
        test_data = {
            "input": {"target_time": std_time},
            "expected": std_time.replace(".", "-", 2).replace(".", "", 1)[:-3],
        }
        test_datas.append(test_data)

        for test_data in test_datas:
            Assert(basic_time_formatter, test_data).equal()


@pytest.mark.usefixtures("base_path")
@pytest.mark.unit
class TestLoadImageToBase64:
    test_image_list: List

    def generate_test_data(self, base_path, image_dir, is_valid=True):
        test_image_root_path = Path(f"{base_path}/resources/{image_dir}").resolve()
        self.test_image_list = [
            test_image
            for test_image in test_image_root_path.glob("**/*")
            if test_image.is_file()
        ]

    def encode(self, image_path):
        image = self.read(image_path)
        buffer = BytesIO()
        image.save(buffer, format="JPEG")
        return base64.b64encode(buffer.getvalue()).decode()

    def read(self, image_path):
        ext = image_path.suffix.lower()
        if ext in [".jpg", ".jpeg", ".jp2", ".png", ".bmp"]:
            pil_image = self.read_pillow_image(image_path)
        elif ext in [".tiff", ".tif"]:
            pil_image = self.read_tiff_image(image_path)
        elif ext in [".pdf"]:
            pil_image = self.read_pdf_image(image_path)
        return pil_image.convert("RGB")

    def read_pillow_image(self, image_path):
        cv2_img = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
        return Image.fromarray(cv2_img[:, :, ::-1])

    def read_pdf_image(self, image_path, page=1):
        pdf_images = convert_from_path(image_path)
        return pdf_images[page - 1]

    def read_tiff_image(self, image_path, page=1):
        try:
            all_pages = self.read_all_tiff_pages_with_tifffile(image_path, page)
            pil_image = all_pages[page - 1]
        except:
            pil_image = self.read_tiff_page(image_path, page - 1)
        finally:
            return pil_image

    def read_tiff_page(img_path, target_page=0):
        tiff_images = Image.open(img_path)
        tiff_images.seek(target_page)
        np_image = np.array(tiff_images.convert("RGB"))
        np_image = np_image.astype(np.uint8)
        tiff_images.close()
        return Image.fromarray(np_image)

    def read_all_tiff_pages_with_tifffile(self, img_path, target_page=-1):
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

    def test_supported_extension_normal_image(self, base_path):
        image_dir = "supported_image/normal_image"
        self.generate_test_data(base_path, image_dir, is_valid=True)
        test_datas: List = []
        for test_image in self.test_image_list:
            img_str = self.encode(test_image)
            test_data = {
                "input": {"img_path": test_image},
                "expected": img_str,
            }
            test_datas.append(test_data)

        for test_data in test_datas:
            Assert(load_image2base64, test_data).equal()

    def test_supported_extension_broken_image(self, base_path):
        image_dir = "supported_image/broken_image"
        self.generate_test_data(base_path, image_dir, is_valid=False)
        test_datas: List = []
        for test_image in self.test_image_list:
            test_data = {
                "input": {"img_path": test_image},
            }
            test_datas.append(test_data)

        for test_data in test_datas:
            Assert(load_image2base64, test_data).is_none()

    def test_unsupported_extension_normal_image(self, base_path):
        image_dir = "unsupported_image/normal_image"
        self.generate_test_data(base_path, image_dir, is_valid=False)
        test_datas: List = []
        for test_image in self.test_image_list:
            test_data = {"input": {"img_path": test_image}}
            test_datas.append(test_data)

        for test_data in test_datas:
            Assert(load_image2base64, test_data).is_none()

    def test_unsupported_extension_broken_image(self, base_path):
        image_dir = "unsupported_image/broken_image"
        self.generate_test_data(base_path, image_dir, is_valid=False)
        test_datas: List = []
        for test_image in self.test_image_list:
            test_data = {
                "input": {"img_path": test_image},
            }
            test_datas.append(test_data)

        for test_data in test_datas:
            Assert(load_image2base64, test_data).is_none()


@pytest.mark.unit
class TestDirStructureValidation:
    root_path: Path
    generate_dir_count: int
    make_subdir_flags: List
    make_file_flags: List
    make_file_under_root_path_flag: bool = False

    @classmethod
    def setup_class(cls):
        cls.generate_dir_count = random.randint(1, 10)

    def setup_method(self, method):
        self.root_path = tempfile.TemporaryDirectory()

    def teardown_method(self, method):
        self.root_path.cleanup()

    def gen_name(self):
        return str(uuid.uuid4())

    def generate_test_data(self, is_valid=True):
        if is_valid:
            self.make_subdir_flags = [False for _ in range(self.generate_dir_count)]
            self.make_file_flags = [True for _ in range(self.generate_dir_count)]
        else:
            self.make_subdir_flags = [
                True for _ in range(self.generate_dir_count - 1)
            ] + [False]
            random.shuffle(self.make_subdir_flags)
            self.make_file_flags = [
                True for _ in range(self.generate_dir_count - 1)
            ] + [False]
            random.shuffle(self.make_file_flags)
        if self.make_file_under_root_path_flag:
            temp_file_name = self.gen_name() + ".txt"
            temp_file_path = Path(self.root_path.name).joinpath(temp_file_name)
            with open(temp_file_path, "w") as file_io:
                file_io.write("test")
        for make_subdir_flag, make_file_flag in zip(
            self.make_subdir_flags, self.make_file_flags
        ):
            temp_dir_name = self.gen_name()
            temp_dir_path = Path(self.root_path.name).joinpath(temp_dir_name)
            os.makedirs(temp_dir_path, exist_ok=True)
            if make_subdir_flag:
                sub_temp_dir_name = self.gen_name()
                sub_temp_dir_path = temp_dir_path.joinpath(sub_temp_dir_name)
                os.mkdir(sub_temp_dir_path)
            if make_file_flag:
                temp_file_name = self.gen_name() + ".txt"
                temp_file_path = temp_dir_path.joinpath(temp_file_name)
                with open(temp_file_path, "w") as file_io:
                    file_io.write("test")

        return {
            "input": {"path": Path(self.root_path.name)},
            "expected": is_valid,
        }

    def test_correct_directory_structure(self):
        test_datas: List = [self.generate_test_data(is_valid=True)]
        for test_data in test_datas:
            Assert(dir_structure_validation, test_data).equal()

    def test_exist_sub_dir_or_not_exist_file(self):
        test_datas: List = [self.generate_test_data(is_valid=False)]
        for test_data in test_datas:
            Assert(dir_structure_validation, test_data).equal()

    def test_exist_file_under_root_path(self):
        self.make_file_under_root_path_flag = True
        test_datas: List = [self.generate_test_data(is_valid=False)]
        for test_data in test_datas:
            Assert(dir_structure_validation, test_data).equal()


@pytest.mark.unit
@pytest.mark.usefixtures("base_path")
class TestImageFileValidation:
    def generate_test_data(self, base_path, img_dir_name, is_valid=True):
        test_datas: List = []
        imgs_path = Path(base_path).joinpath("resources").joinpath(img_dir_name)
        imgs = list(imgs_path.rglob("*.*"))
        for img in imgs:
            test_data = {
                "input": {"file": img},
                "expected": is_valid,
            }
            test_datas.append(test_data)
        return test_datas

    def test_supported_extension_normal_image(self, base_path):
        is_valid = True
        img_dir_name = "supported_image/normal_image"
        test_datas = self.generate_test_data(base_path, img_dir_name, is_valid)
        for test_data in test_datas:
            Assert(image_file_validation, test_data).equal()

    def test_supported_extension_broken_image(self, base_path):
        is_valid = False
        img_dir_name = "supported_image/broken_image"
        test_datas = self.generate_test_data(base_path, img_dir_name, is_valid)
        for test_data in test_datas:
            Assert(image_file_validation, test_data).equal()

    def test_unsupported_extension_normal_image(self, base_path):
        is_valid = False
        img_dir_name = "unsupported_image/normal_image"
        test_datas = self.generate_test_data(base_path, img_dir_name, is_valid)
        for test_data in test_datas:
            Assert(image_file_validation, test_data).equal()

    def test_unsupported_extension_broken_image(self, base_path):
        is_valid = False
        img_dir_name = "unsupported_image/broken_image"
        test_datas = self.generate_test_data(base_path, img_dir_name, is_valid)
        for test_data in test_datas:
            Assert(image_file_validation, test_data).equal()


@pytest.mark.unit
class TestPrintErrorLog:
    def test_occur_exception(self):
        try:
            raise ValueError("test print error log")
        except Exception:
            print_error_log()
            assert True

    def test_not_occur_exception(self):
        Assert(print_error_log).is_none()


@pytest.mark.unit
class TestSubstituteSpcharToAlpha:
    def test_include_one_spchar(self):
        test_datas = [
            {"input": {"decoded_texts": "["}, "expected": "I"},
            {"input": {"decoded_texts": "]"}, "expected": "I"},
            {"input": {"decoded_texts": "|"}, "expected": "I"},
            {"input": {"decoded_texts": "*"}, "expected": "*"},
        ]
        for test_data in test_datas:
            Assert(substitute_spchar_to_alpha, test_data).equal()

    def test_include_many_spchar(self):
        test_datas = [
            {"input": {"decoded_texts": "[]"}, "expected": "[]"},
            {"input": {"decoded_texts": "]A"}, "expected": "]A"},
            {"input": {"decoded_texts": "123|"}, "expected": "123I"},
            {"input": {"decoded_texts": "1*]"}, "expected": "1*]"},
        ]
        for test_data in test_datas:
            Assert(substitute_spchar_to_alpha, test_data).equal()
