import pytest
from app.utils.utils import substitute_spchar_to_alpha


@pytest.mark.unit
class TestSubstituteSpcharToAlpha:
    @pytest.mark.parametrize("word", ["[", "]", "|"])
    def test_one_char_composed_bracket_or_vertical_bar(self, word):
        output = substitute_spchar_to_alpha(word)
        assert output == "I"

    @pytest.mark.parametrize("word", ["*", "1", "J", "%"])
    def test_one_char_not_composed_bracket_or_vertical_bar(self, word):
        output = substitute_spchar_to_alpha(word)
        assert word == output

    @pytest.mark.parametrize("word", ["|1", "i|", "*|", "[|]"])
    def test_chars_included_vertical_bar(self, word):
        output = substitute_spchar_to_alpha(word)
        expected_word = word.replace("|", "I")
        assert output == expected_word

    def test_blank_char(self):
        output = substitute_spchar_to_alpha("")
        assert output == ""

    @pytest.mark.parametrize("word", ["1*", "I892", "@3zd"])
    def test_chars_excluded_vertical_bar(self, word):
        output = substitute_spchar_to_alpha(word)
        assert output == word
