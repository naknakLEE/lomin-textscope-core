import pytest
import numpy as np
import cv2
from PIL import Image
from pathlib import Path
from app.utils.utils import read_basic_image
from app.errors.exceptions import ResourceDataError
from unittest.mock import patch, MagicMock

RESOURCE_PATH = Path(__file__, "../../../resources").resolve()


@pytest.mark.unit
class TestReadBasicImage:
    @patch("app.utils.utils.cv2.imread")
    def test_normal_image_using_mocking(self, mock_imread: MagicMock) -> None:
        fake_image_path = "/fake/image/path"
        fake_image = np.full((480, 640, 3), 255, dtype=np.uint8)
        expected = Image.fromarray(fake_image)
        mock_imread.return_value = fake_image
        output = read_basic_image(fake_image_path)
        mock_imread.assert_called_once_with(fake_image_path, cv2.IMREAD_COLOR)
        assert output == expected

    def test_not_exist_image(self) -> None:
        fake_image_path = "/not/exist/image.jpg"
        with pytest.raises(ResourceDataError):
            read_basic_image(fake_image_path)

    @pytest.mark.parametrize(
        "image_path",
        [
            (image_path)
            for image_path in RESOURCE_PATH.joinpath(
                "supported_image/broken_image"
            ).rglob("*.*")
            if image_path.is_file()
        ],
    )
    def test_borken_image(self, image_path: Path) -> None:
        with pytest.raises(ResourceDataError):
            read_basic_image(image_path)

    @pytest.mark.parametrize(
        "image_path",
        [
            (image_path)
            for image_path in RESOURCE_PATH.joinpath(
                "supported_image/normal_image"
            ).rglob("*.*")
            if image_path.is_file()
            and Path(image_path).suffix not in [".pdf", ".tif", ".tiff"]
        ],
    )
    def test_normal_image(self, image_path: Path) -> None:
        output = read_basic_image(image_path)
        assert isinstance(output, Image.Image)
