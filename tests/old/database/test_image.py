import pytest
import uuid
from typing import Dict, Callable
from app.database.schema import Image
from sqlalchemy.orm import Session


@pytest.mark.unit
@pytest.mark.usefixtures("get_db")
class TestImage:
    fake_image_data: Dict

    def setup_method(self, method: Callable) -> None:
        self.fake_image_data = {
            "image_id": str(uuid.uuid4()),
            "image_path": "test image path",
            "image_description": f"{method.__name__}",
            "image_type": "INFERENCE"
        }

    def test_create_image(self, get_db: Session) -> None:
        image = Image.create(get_db, **self.fake_image_data)
        if image:
            for key, value in self.fake_image_data.items():
                assert value == getattr(image, key)
        else:
            assert False

    def test_get_image_by_id(self, get_db: Session) -> None:
        dummy_image = Image.create(get_db, **self.fake_image_data)
        image_id = self.fake_image_data.get("image_id", "")
        image = Image.get(get_db, **dict(image_id=image_id))
        if not image:
            assert False
        assert dummy_image == image

    # @TODO: 중복 이미지 path에 대한 처리
    # @TODO: image bytes 저장 유무
