import pytest
import string
import random
from app.utils.utils import get_pp_api_name
from app.errors.exceptions import ResourceDataError
from unittest.mock import patch


def random_string():
    characters = string.ascii_letters
    word_lenght = random.randint(0, 10)
    random_word_list = random.sample(characters, word_lenght)
    return "".join(random_word_list)


@pytest.mark.unit
class TestGetPPApiName:
    def test_doc_type_included_idcard(self):
        idcard_doc_type_list = [
            "ID-ARB",
            "ID-ARC",
            "ID-DLC",
            "ID-OKC",
            "ID-ONC",
            "ID-PRC",
            "ID-RRC",
            "Z3",
            "J1",
            "L3",
            "R6",
            "W2",
            "Z3",
            "J5",
            "신분증",
            "idcard",
        ]

        for idcard_doc_type in idcard_doc_type_list:
            output = get_pp_api_name(idcard_doc_type)
            assert output == "idcard"

    def test_doc_type_included_general_pp(self):
        general_doc_type_list = [
            "Z2",
            "사업자등록증",
            "HKL01-DT-IB",
            "HKL01-DT-MC",
            "HKL01-DT-CAD",
            "HKL01-DT-CS",
            "HKL01-DT-CHT",
            "HKL01-DT-PRS",
        ]

        for general_doc_type in general_doc_type_list:
            output = get_pp_api_name(general_doc_type)
            assert output == "kv"

    def test_doc_type_included_bankbook(self):
        bankbook_doc_type_list = [
            "A2",
            "AC",
            "Z1",
            "RF",
            "Z1",
            "통장사본",
            "bankbook",
            "FN-BB",
        ]

        for bankbook_doc_type in bankbook_doc_type_list:
            output = get_pp_api_name(bankbook_doc_type)
            assert output == "bankbook"

    def test_doc_type_included_seal_imp_cert(self):
        seal_imp_cert_doc_type_list = ["J8_인감증명서", "N2_법인인감증명서"]

        for seal_imp_cert_doc_type in seal_imp_cert_doc_type_list:
            output = get_pp_api_name(seal_imp_cert_doc_type)
            assert output == "seal_imp_cert"

    def test_doc_type_included_ccr(self):
        ccr_doc_type_list = ["N1_법인등기부 등본(등기사항 전부증명서)"]

        for ccr_doc_type in ccr_doc_type_list:
            output = get_pp_api_name(ccr_doc_type)
            assert output == "ccr"

    def test_doc_type_included_busan_bank(self):
        busan_bank_doc_type_list = ["법인등기부등본"]

        for busan_bank_doc_type in busan_bank_doc_type_list:
            output = get_pp_api_name(busan_bank_doc_type)
            assert output == "busan_bank"

    def test_doc_type_included_document_type_set_and_customer_is_kakaobank(self):
        document_type_set = {
            "D01": "rrtable",
            "D02": "family_cert",
            "D53": "basic_cert",
            "D54": "regi_cert",
        }

        for doc_type, pp_name in document_type_set.items():
            output = get_pp_api_name(doc_type, customer="kakaobank")
            assert output == pp_name

    def test_doc_type_included_document_type_set_and_customer_is_not_kakaobank(self):
        document_type_set = {
            "D01": "rrtable",
            "D02": "family_cert",
            "D53": "basic_cert",
            "D54": "regi_cert",
        }

        for doc_type, pp_name in document_type_set.items():
            output = get_pp_api_name(doc_type)
            assert output is None

    def test_doc_type_excluded_document_type_set_and_customer_is_kakaobank(self):
        excluded_doc_type = random_string()

        output = get_pp_api_name(excluded_doc_type, customer="kakaobank")
        assert output is None

    def test_doc_type_excluded_document_type_set_and_customer_is_not_kakaobank(self):
        excluded_doc_type = random_string()

        output = get_pp_api_name(excluded_doc_type)
        assert output is None

    @patch("app.utils.utils.pp_mapping_table")
    def test_pp_mapping_table_is_not_dict(self, mock_pp_mapping_table):
        mock_pp_mapping_table.get.return_value = list()
        random_doc_type = random_string()

        with pytest.raises(ResourceDataError):
            get_pp_api_name(random_doc_type)
