import pytest
from pathlib import Path
from PIL import Image
from app.utils.utils import read_image
from app.errors.exceptions import ResourceDataError

RESOURCE_PATH = Path(__file__, "../../../resources").resolve()


@pytest.mark.unit
class TestReadImage:
    def test_not_supported_extension_image(self):
        image_path = Path("/not/supported/image.ext")
        with pytest.raises(ValueError):
            read_image(image_path, ext_allows=["jpg"])

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
    def test_broken_image(self, image_path):
        with pytest.raises(ResourceDataError):
            read_image(image_path)

    @pytest.mark.parametrize(
        "image_path",
        [
            (image_path)
            for image_path in RESOURCE_PATH.joinpath(
                "supported_image/normal_image"
            ).rglob("*.*")
            if image_path.is_file()
        ],
    )
    def test_normal_image(self, image_path):
        output = read_image(image_path)
        assert isinstance(output, Image.Image)
