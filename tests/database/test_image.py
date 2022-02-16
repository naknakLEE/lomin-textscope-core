import pytest
import uuid
from typing import Dict
from app.database.schema import Image


@pytest.mark.unit
@pytest.mark.usefixtures("get_db")
class TestImage:
    fake_image_data: Dict

    def setup_method(self, method):
        self.fake_image_data = {
            "image_id": str(uuid.uuid4()),
            "image_path": "test image path",
            "image_description": f"{method.__name__}",
        }

    def test_create_image(self, get_db):
        image = Image.create(get_db, **self.fake_image_data)
        if image:
            for key, value in self.fake_image_data.items():
                assert value == getattr(image, key)
        else:
            assert False

    def test_get_image_by_id(self, get_db):
        dummy_image = Image.create(get_db, **self.fake_image_data)
        image_id = self.fake_image_data.get("image_id")
        image = Image.get(get_db, image_id=image_id)
        if not image:
            assert False
        assert dummy_image == image

    # @TODO: 중복 이미지 path에 대한 처리
    # @TODO: image bytes 저장 유무
