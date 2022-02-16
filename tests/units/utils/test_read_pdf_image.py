import pytest
import numpy as np
from PIL import Image
from pathlib import Path
from app.utils.utils import read_pdf_image
from app.errors.exceptions import ResourceDataError
from unittest.mock import patch

RESOURCE_PATH = Path(__file__, "../../../resources").resolve()


@pytest.mark.unit
class TestReadPDFImage:
    @patch("app.utils.utils.convert_from_path")
    def test_noraml_image_using_mocking(self, mock_convert_from_path):
        fake_image_path = "/fake/image_path.pdf"
        fake_pdf_image_data = np.full((480, 640, 3), 255, dtype=np.uint8)
        mock_convert_from_path.return_value = [Image.fromarray(fake_pdf_image_data)]
        output = read_pdf_image(fake_image_path)
        mock_convert_from_path.assert_called_once_with(fake_image_path)
        return isinstance(output, Image.Image)

    def test_not_exist_image_path(self):
        fake_image_path = "/not/exist/image_path.jpg"
        with pytest.raises(ResourceDataError):
            read_pdf_image(fake_image_path)

    def test_broken_image_path(self):
        image_path = Path(
            RESOURCE_PATH, "supported_image/broken_image/broken_image.pdf"
        )
        with pytest.raises(ResourceDataError):
            read_pdf_image(image_path)

    def test_normal_image_multi_page(self):
        image_path = Path(
            RESOURCE_PATH, "supported_image/normal_image/Merged_document.pdf"
        )
        output = read_pdf_image(image_path)
        assert isinstance(output, Image.Image)
        output = read_pdf_image(image_path, page=2)
        assert isinstance(output, Image.Image)
        with pytest.raises(ResourceDataError):
            read_pdf_image(image_path, page=3)

    def test_normal_image_single_page(self):
        image_path = Path(
            RESOURCE_PATH, "supported_image/normal_image/cat-g736138cac_1920.pdf"
        )
        output = read_pdf_image(image_path)
        assert isinstance(output, Image.Image)
        with pytest.raises(ResourceDataError):
            read_pdf_image(image_path, page=2)
