import pytest
import random
from typing import Callable
from tests.utils.utils import Assert
from app.utils.hint import apply_cls_hint
from app.common.const import get_settings

settings = get_settings()


@pytest.mark.unit
class TestApplyClsHint:
    reliable_score: Callable
    unreliable_score: Callable

    def setup_method(self, method):
        hint_threshold = settings.CLS_HINT_SCORE_THRESHOLD
        self.reliable_score = lambda: random.uniform(hint_threshold, 1.0)
        self.unreliable_score = lambda: random.uniform(0.0, hint_threshold)

    def test_trusted_hint_and_reliable_score(self):
        test_datas = [
            {
                "input": {
                    "doc_type_hint": {
                        "doc_type": "hint_doc_type",
                        "use": True,
                        "trust": True,
                    },
                    "cls_result": {
                        "score": self.reliable_score(),
                        "doc_type": "original_doc_type",
                    },
                },
                "expected": {
                    "doc_type": "hint_doc_type",
                    "is_hint_used": True,
                    "is_hint_trusted": True,
                },
            },
            {
                "input": {
                    "doc_type_hint": {
                        "doc_type": "hint_doc_type",
                        "use": True,
                        "trust": True,
                    },
                    "cls_result": {
                        "score": self.reliable_score(),
                        "doc_type": "original_doc_type",
                    },
                },
                "expected": {
                    "doc_type": "hint_doc_type",
                    "is_hint_used": True,
                    "is_hint_trusted": True,
                },
            },
        ]
        for test_data in test_datas:
            Assert(apply_cls_hint, test_data).equal()

    def test_trusted_hint_and_unreliable_score(self):
        test_datas = [
            {
                "input": {
                    "doc_type_hint": {
                        "doc_type": "hint_doc_type",
                        "use": True,
                        "trust": True,
                    },
                    "cls_result": {
                        "score": self.unreliable_score(),
                        "doc_type": "original_doc_type",
                    },
                },
                "expected": {
                    "doc_type": "hint_doc_type",
                    "is_hint_used": True,
                    "is_hint_trusted": True,
                },
            },
            {
                "input": {
                    "doc_type_hint": {
                        "doc_type": "hint_doc_type",
                        "use": True,
                        "trust": True,
                    },
                    "cls_result": {
                        "score": self.unreliable_score(),
                        "doc_type": "original_doc_type",
                    },
                },
                "expected": {
                    "doc_type": "hint_doc_type",
                    "is_hint_used": True,
                    "is_hint_trusted": True,
                },
            },
        ]
        for test_data in test_datas:
            Assert(apply_cls_hint, test_data).equal()

    def test_not_trusted_hint_and_reliable_score(self):
        test_datas = [
            {
                "input": {
                    "doc_type_hint": {
                        "doc_type": "hint_doc_type",
                        "use": True,
                        "trust": False,
                    },
                    "cls_result": {
                        "score": self.reliable_score(),
                        "doc_type": "original_doc_type",
                    },
                },
                "expected": {
                    "doc_type": "original_doc_type",
                    "is_hint_used": False,
                    "is_hint_trusted": False,
                },
            },
            {
                "input": {
                    "doc_type_hint": {
                        "doc_type": "hint_doc_type",
                        "use": True,
                        "trust": False,
                    },
                    "cls_result": {
                        "score": self.reliable_score(),
                        "doc_type": "original_doc_type",
                    },
                },
                "expected": {
                    "doc_type": "original_doc_type",
                    "is_hint_used": False,
                    "is_hint_trusted": False,
                },
            },
        ]
        for test_data in test_datas:
            Assert(apply_cls_hint, test_data).equal()

    def test_not_trusted_hint_and_unreliable_score(self):
        test_datas = [
            {
                "input": {
                    "doc_type_hint": {
                        "doc_type": "hint_doc_type",
                        "use": True,
                        "trust": False,
                    },
                    "cls_result": {
                        "score": self.unreliable_score(),
                        "doc_type": "original_doc_type",
                    },
                },
                "expected": {
                    "doc_type": "hint_doc_type",
                    "is_hint_used": True,
                    "is_hint_trusted": False,
                },
            },
            {
                "input": {
                    "doc_type_hint": {
                        "doc_type": "hint_doc_type",
                        "use": True,
                        "trust": False,
                    },
                    "cls_result": {
                        "score": self.unreliable_score(),
                        "doc_type": "original_doc_type",
                    },
                },
                "expected": {
                    "doc_type": "hint_doc_type",
                    "is_hint_used": True,
                    "is_hint_trusted": False,
                },
            },
        ]
        for test_data in test_datas:
            Assert(apply_cls_hint, test_data).equal()
