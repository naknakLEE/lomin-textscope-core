import sys
sys.path.append("pp_server")
import copy

from pp_server.pp.postprocess.el_pp import PrescriptionPP



def test_MD_MIB_add_healthcare_facility_text():
    """
        요양기관기호 (MD-MIB)테스트
        
        "의료기관 요양기관기호" 가 들어가 있는 경우 추출하는 테스트 코드 작성
        원래는 "요양기관기호"로만 구성되어있는데 특이케이스로 "의료기관 요양기관기호"로 구성되어있는 경우가 있음
    """
    pp = PrescriptionPP(relations = {}, doc_type = "MD-PRS", list_of_string = [])
    input =  [[('의료기관요양기관기호', '12376205', [[0, 0, 0, 0]], [0])]]
    predict = {'MD-MIB': [{'type': 'word', 'value': '12376205', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-MIB', 'text': '12376205'}]}
    assert pp._search_header_keyword(input) == predict
