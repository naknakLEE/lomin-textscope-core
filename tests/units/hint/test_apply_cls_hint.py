import pytest
from typing import Dict, Callable
from app.utils.hint import apply_cls_hint
from app.models import DocTypeHint


@pytest.mark.unit
class TestApplyClsHint:
    expected_form: Dict
    hint_doc_type: str
    cls_doc_type: str
    cls_result: Dict

    @classmethod
    def setup_class(cls) -> None:
        cls.hint_doc_type = "hint doc type"
        cls.cls_doc_type = "cls doc type"
        cls.cls_result = {"doc_type": cls.cls_doc_type, "score": 0.0}

    def setup_method(self, method: Callable) -> None:
        self.expected_form = {
            "doc_type": None,
            "is_hint_used": False,
            "is_hint_trusted": False,
        }

    def test_trust_true_and_exist_cls_result(self) -> None:
        doc_type_hint = DocTypeHint(use=True, trust=True, doc_type=self.hint_doc_type)
        output = apply_cls_hint(doc_type_hint, self.cls_result)
        self.expected_form.update(
            doc_type=self.hint_doc_type, is_hint_used=True, is_hint_trusted=True
        )
        assert output == self.expected_form

    def test_trust_true_and_not_exist_cls_result(self) -> None:
        doc_type_hint = DocTypeHint(use=True, trust=True, doc_type=self.hint_doc_type)
        output = apply_cls_hint(doc_type_hint)
        self.expected_form.update(
            doc_type=self.hint_doc_type, is_hint_used=True, is_hint_trusted=True
        )
        assert output == self.expected_form

    def test_trust_false_and_reliable_cls_result(self) -> None:
        doc_type_hint = DocTypeHint(use=True, trust=False, doc_type=self.hint_doc_type)
        self.cls_result.update(score=0.99)
        threshold = 0.5
        self.expected_form.update(
            doc_type=self.cls_doc_type, is_hint_used=False, is_hint_trusted=False
        )
        output = apply_cls_hint(
            doc_type_hint, self.cls_result, hint_threshold=threshold
        )
        assert output == self.expected_form

    def test_trust_false_and_unreliable_cls_result(self) -> None:
        doc_type_hint = DocTypeHint(use=True, trust=False, doc_type=self.hint_doc_type)
        self.cls_result.update(score=0.1)
        threshold = 0.5
        self.expected_form.update(
            doc_type=self.hint_doc_type, is_hint_used=True, is_hint_trusted=False
        )
        output = apply_cls_hint(
            doc_type_hint, self.cls_result, hint_threshold=threshold
        )
        assert output == self.expected_form

    def test_trust_false_and_not_exist_cls_result(self) -> None:
        doc_type_hint = DocTypeHint(use=True, trust=False, doc_type=self.hint_doc_type)
        output = apply_cls_hint(doc_type_hint)
        assert output == self.expected_form

    def test_use_false(self) -> None:
        doc_type_hint = DocTypeHint(use=True, trust=False, doc_type=self.hint_doc_type)
        output = apply_cls_hint(doc_type_hint)
        assert output == self.expected_form

    def test_doc_type_is_none(self) -> None:
        output = apply_cls_hint(None)
        assert output == self.expected_form
