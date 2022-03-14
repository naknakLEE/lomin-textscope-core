import uuid
import pytest
import logging
from typing import Callable
from httpx import Client
from unittest.mock import patch, MagicMock
from app.wrapper.pipeline import single
from tests.utils.single_pipeline import FakeInferenceRequestInput, FakeInferenceResponse

logger = logging.getLogger(__name__)


@pytest.mark.mock
class TestSinglePipeline:
    def setup_method(self, method: Callable) -> None:
        task_id = str(uuid.uuid4())
        self.doc_type_hint = {"doc_type": "FN-BB", "trust": False, "use": False}
        self.key_value_hint = {
            "key": "FN-BB-BID",
            "trust": False,
            "use": False,
            "value": "2018.05.01",
        }
        self.hint = {
            "doc_type": self.doc_type_hint,
            "key_value": self.key_value_hint,
            "trust": False,
            "use": False,
        }
        rectify = {"rotation_90n": False, "rotation_fine": False}
        self.fake_input = FakeInferenceRequestInput(
            convert_preds_to_texts=True,
            customer="textscope",
            detection_resize_ratio=1.0,
            detection_score_threshold=0.5,
            doc_type="None",
            hint=self.hint,
            idcard_version="v1",
            image_id="image_id",
            image_path="image_path",
            image_pkey=1,
            page=1,
            rectify=rectify,
            request_id=task_id,
            task_id=task_id,
            use_general_ocr=False,
        )
        self.fake_inference_result = dict(
            scores=[0.683474],
            boxes=[[100, 200, 100, 200]],
            classes=["text"],
            response_log={},
            rec_preds=[[1, 2, 3]],
            doc_type="FN-BB",
            image_height=1080,
            image_width=1920,
            request_id=str(uuid.uuid4()),
            angle=0.0,
            id_type="default",
        )
        self.fake_response = FakeInferenceResponse(status_code=200)
        self.fake_response.response_data = self.fake_inference_result

    @patch("app.wrapper.pipeline.Client.post")
    def test_single_pipeline_not_use_cls_hint(
        self, mock_serving_request: MagicMock
    ) -> None:
        """단일 pipeline으로 구성된 model service에 inference 요청"""
        mock_serving_request.return_value = self.fake_response
        inputs = self.fake_input.__dict__
        status_code, inference_result, response_log = single(
            client=Client(), inputs=inputs, response_log={}, route_name="ocr"
        )
        mock_serving_request.assert_called_once_with(
            f"http://10.251.0.4:5000/ocr",
            json=inputs,
            timeout=30.0,
            headers={"User-Agent": "textscope core"},
        )
        assert status_code == 200
        assert inference_result.get("doc_type") == self.fake_inference_result.get(
            "doc_type"
        )

    @patch("app.wrapper.pipeline.Client.post")
    def test_single_pipeline_use_cls_hint(
        self, mock_serving_request: MagicMock
    ) -> None:
        """trust가 true인 cls hint를 적용"""
        test_doc_type = "changed_doc_type"
        self.doc_type_hint = {"doc_type": test_doc_type, "trust": True, "use": True}
        self.fake_response.response_data.update(doc_type=test_doc_type)
        mock_serving_request.return_value = self.fake_response
        inputs = self.fake_input.__dict__
        status_code, inference_result, response_log = single(
            client=Client(), inputs=inputs, response_log={}, route_name="ocr"
        )
        mock_serving_request.assert_called_once_with(
            f"http://10.251.0.4:5000/ocr",
            json=inputs,
            timeout=30.0,
            headers={"User-Agent": "textscope core"},
        )
        assert status_code == 200
        assert inference_result.get("doc_type") == test_doc_type
