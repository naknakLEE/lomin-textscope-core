import sys
import pytest
from app.utils.utils import print_error_log
from unittest.mock import patch, MagicMock


@pytest.mark.unit
class TestPrintErrorLog:
    @patch("app.utils.utils.sys.exc_info")
    def test_raise_exception(self, mock_exc_info: MagicMock) -> None:
        try:
            raise ValueError("test")
        except:
            mock_exc_info.return_value = sys.exc_info()
            with pytest.raises(ValueError):
                print_error_log()

    def test_not_raise_exception(self) -> None:
        try:
            print_error_log()
            assert True
        except:
            assert False
