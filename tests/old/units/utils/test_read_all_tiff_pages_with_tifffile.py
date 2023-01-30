import pytest
import numpy as np
from pathlib import Path
from PIL import Image
from app.utils.utils import read_all_tiff_pages_with_tifffile
from app.errors.exceptions import ResourceDataError
from unittest.mock import patch, MagicMock

RESOURCE_PATH = Path(__file__, "../../../resources").resolve()


@pytest.mark.unit
class TestReadAllTiffPagesWithTifffile:
    @patch("app.utils.utils.tifffile.imread")
    def test_noraml_image_using_mocking(self, mock_imread: MagicMock) -> None:
        fake_image = np.full((480, 640, 3), 255, dtype=np.uint8)
        fake_image_path = "/fake/image_path.jpg"
        mock_imread.return_value = fake_image
        expected = [Image.fromarray(fake_image)]
        output = read_all_tiff_pages_with_tifffile(fake_image_path, target_page=1)
        assert expected == output

    def test_not_exist_image_path(self) -> None:
        dummy_image_path = "/not/exist/image_path.tif"
        with pytest.raises(ResourceDataError):
            read_all_tiff_pages_with_tifffile(dummy_image_path)

    def test_broken_image_path(self) -> None:
        image_path = Path(
            RESOURCE_PATH, "supported_image/broken_image/broken_image.tif"
        )
        with pytest.raises(ResourceDataError):
            read_all_tiff_pages_with_tifffile(image_path)

    def test_normal_image_multi_page(self) -> None:
        image_path = Path(
            RESOURCE_PATH, "supported_image/normal_image/Merged_document.tiff"
        )
        output = read_all_tiff_pages_with_tifffile(image_path)
        assert isinstance(output, list)
        assert len(output) == 2
        for _output in output:
            assert isinstance(_output, Image.Image)

    def test_normal_image_single_page(self) -> None:
        image_path = Path(
            RESOURCE_PATH, "supported_image/normal_image/cat-g736138cac_1920.tif"
        )
        output = read_all_tiff_pages_with_tifffile(image_path)
        assert isinstance(output, list)
        assert len(output) == 1
        for _output in output:
            assert isinstance(_output, Image.Image)
