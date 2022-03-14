import pytest
from typing import List
from app.utils.utils import substitute_spchar_to_alpha


@pytest.mark.unit
class TestSubstituteSpcharToAlpha:
    @pytest.mark.parametrize(
        "word, expected",
        (
            (["["], ["I"]),
            (["]"], ["I"]),
            (["|"], ["I"]),
        ),
    )
    def test_one_char_composed_bracket_or_vertical_bar(
        self, word: List[str], expected: List[str]
    ) -> None:
        output = substitute_spchar_to_alpha(word)
        assert output == expected

    @pytest.mark.parametrize(
        "word, expected",
        (
            (["*"], ["*"]),
            (["1"], ["1"]),
            (["J"], ["J"]),
            (["%"], ["%"]),
        ),
    )
    def test_one_char_not_composed_bracket_or_vertical_bar(
        self, word: List[str], expected: List[str]
    ) -> None:
        output = substitute_spchar_to_alpha(word)
        assert output == expected

    @pytest.mark.parametrize(
        "word, expected",
        (
            (["|1"], ["I1"]),
            (["i|"], ["iI"]),
            (["*|"], ["*I"]),
            (["[|]"], ["[I]"]),
        ),
    )
    def test_chars_included_vertical_bar(
        self, word: List[str], expected: List[str]
    ) -> None:
        output = substitute_spchar_to_alpha(word)
        assert output == expected

    def test_blank_char(self) -> None:
        output = substitute_spchar_to_alpha([""])
        assert output == [""]

    @pytest.mark.parametrize(
        "word, expected",
        (
            (["1*"], ["1*"]),
            (["I892"], ["I892"]),
            (["@3zd"], ["@3zd"]),
        ),
    )
    def test_chars_excluded_vertical_bar(
        self, word: List[str], expected: List[str]
    ) -> None:
        output = substitute_spchar_to_alpha(word)
        assert output == expected
