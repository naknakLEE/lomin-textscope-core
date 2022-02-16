import pytest
from PIL import Image
from pathlib import Path
from app.utils.utils import read_tiff_page
from app.errors.exceptions import ResourceDataError

RESOURCE_PATH = Path(__file__, "../../../resources").resolve()


@pytest.mark.unit
class TestReadTiffPage:
    def test_not_exist_image_path(self):
        fake_image_path = "/not/exist/image_path.tif"
        with pytest.raises(ResourceDataError):
            read_tiff_page(fake_image_path)

    def test_broken_image_path(self):
        image_path = Path(
            RESOURCE_PATH, "supported_image/broken_image/broken_image.tif"
        )
        with pytest.raises(ResourceDataError):
            read_tiff_page(image_path)

    def test_normal_image_multi_page(self):
        image_path = Path(
            RESOURCE_PATH, "supported_image/normal_image/Merged_document.tiff"
        )
        output = read_tiff_page(image_path, target_page=1)
        assert isinstance(output, Image.Image)

    def test_normal_image_single_page(self):
        image_path = Path(
            RESOURCE_PATH, "supported_image/normal_image/cat-g736138cac_1920.tif"
        )
        output = read_tiff_page(image_path)
        assert isinstance(output, Image.Image)
