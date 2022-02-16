import cv2
import pytest
import numpy as np
from io import BytesIO
from PIL import Image
from pathlib import Path
from base64 import b64encode, b64decode
from app.utils.utils import load_image2base64
from app.errors.exceptions import ResourceDataError
from unittest.mock import patch

RESOURCE_PATH = Path(__file__, "../../../resources").resolve()


def fake_cv_image():
    color_image = np.full((480, 640), 255, dtype=np.uint8)
    pil_image = Image.fromarray(color_image)
    return pil_image


def encoder(pil_image: Image):
    buffer = BytesIO()
    pil_image.save(buffer, format="JPEG")
    img_bytes = b64encode(buffer.getvalue())
    return img_bytes.decode()


@pytest.mark.unit
class TestLoadImageToBase64:
    @patch("app.utils.utils.read_image")
    def test_given_fake_normal_image(self, mock_read_image):
        fake_pil_image = fake_cv_image()
        mock_read_image.return_value = fake_pil_image
        img_path = "/test/mock/data.png"
        expected_encoded_string = encoder(fake_pil_image)
        output = load_image2base64(img_path)

        mock_read_image.assert_called_once_with(img_path)
        assert output == expected_encoded_string

    @patch("app.utils.utils.read_image")
    def test_given_not_exist_image_path(self, mock_read_image):
        not_exist_image_path = "/not/exist/image_path.jpg"
        mock_read_image.side_effect = ResourceDataError

        with pytest.raises(ResourceDataError) as exc:
            load_image2base64(not_exist_image_path)

    @patch("app.utils.utils.read_image")
    def test_given_fake_broken_image_path(self, mock_read_image):
        broken_image_path = "/broken/image_path.jpg"
        mock_read_image.return_value = None
        output = load_image2base64(broken_image_path)
        assert output is None

    @pytest.mark.parametrize(
        "img_path",
        [
            (img_path)
            for img_path in RESOURCE_PATH.joinpath(
                "supported_image/normal_image"
            ).rglob("*.*")
            if img_path.is_file()
        ],
    )
    def test_given_normal_image_supported_extension(self, img_path):
        output = load_image2base64(img_path)
        try:
            decoded_string = output.encode()
            img_bytes = b64decode(decoded_string)
            nparr = np.fromstring(img_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            assert True
        except:
            assert False

    @pytest.mark.parametrize(
        "img_path",
        [
            (img_path)
            for img_path in RESOURCE_PATH.joinpath(
                "supported_image/broken_image"
            ).rglob("*.*")
            if img_path.is_file()
        ],
    )
    def test_given_broken_image_supported_extension(self, img_path):
        with pytest.raises(ResourceDataError):
            load_image2base64(img_path)

    @pytest.mark.parametrize(
        "img_path",
        [
            (img_path)
            for img_path in RESOURCE_PATH.joinpath(
                "unsupported_image/normal_image"
            ).rglob("*.*")
            if img_path.is_file()
        ],
    )
    def test_given_normal_image_unsupported_extension(self, img_path):
        with pytest.raises(ValueError):
            load_image2base64(img_path)

    @pytest.mark.parametrize(
        "img_path",
        [
            (img_path)
            for img_path in RESOURCE_PATH.joinpath(
                "unsupported_image/broken_image"
            ).rglob("*.*")
            if img_path.is_file()
        ],
    )
    def test_given_broken_image_unsupported_extension(self, img_path):
        with pytest.raises(ValueError):
            load_image2base64(img_path)
