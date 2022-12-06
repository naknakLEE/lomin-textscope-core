import sys
sys.path.append("pp_server")
import copy

from pp_server.pp.postprocess.el_pp import PrescriptionPP

default_table = {
    "shape": [1, 5],
    "corner": {},
    "row-header": {},
    "column-header": {
        "position": [0, 0, 0, 0],
        "content": [["1회투여량"]], # 테스트 대상
        "bbox": [[[0, 0, 0, 0]]],
        "span": [],
        "score": [[0, 0, 0, 0]]
    },
    "body": {
        "position": [0, 1, 0, 4],
        "content": [["0"], ["1"], ["2"], ["3"]], # 테스트 대상
        "bbox": [
            [[0, 0, 0, 0]],
            [[0, 0, 0, 0]],
            [[0, 0, 0, 0]],
            [[0, 0, 0, 0]],
        ],
        "span": [],
        "score": [
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0]
        ]
    },
    "is_big_table": True
}



def test_el_tables_column_header_MD_PRS_1():
    """
        1회 투약량 테스트
        1회 투약량 값을 각각 0, 1, 2, 3 넣어 테스트
    """
    input_table = copy.deepcopy(default_table)
    input_table['column-header']['content'] = [["1회 투약량"]]
    input_table['body']['content'] = [["0"], ["1"], ["2"], ["3"]]
    
    EL = PrescriptionPP({}, "MD-PRS", [])
    res = EL.get_templatized_big_table(input_table)
    
    assert res['column-header']['content'] == [['처방 의약품의 명칭'], ['1회 투약량'], ['1회 투여횟수'], ['총 투약일수']], "처방전 1회 투약량 헤더의 output이 잘못되었습니다."
    assert res['body']['content'] == [['', 0.0, 0, 0], ['', 1.0, 0, 0], ['', 2.0, 0, 0], ['', 3.0, 0, 0]], "처방전 1회 투약량 헤더의 output이 잘못되었습니다."



def test_el_tables_column_header_MD_PRS_2():
    """
        1회 투여량 테스트
        1회 투여량 값을 각각 0, 1, 2, 3 넣어 테스트
    """
    input_table = copy.deepcopy(default_table)
    input_table['column-header']['content'] = [["1회 투여량"]]
    input_table['body']['content'] = [["0"], ["1"], ["2"], ["3"]]
    
    EL = PrescriptionPP({}, "MD-PRS", [])
    res = EL.get_templatized_big_table(input_table)
    
    assert res['column-header']['content'] == [['처방 의약품의 명칭'], ['1회 투약량'], ['1회 투여횟수'], ['총 투약일수']], "처방전 1회 투여량 헤더의 output이 잘못되었습니다."
    assert res['body']['content'] == [['', 0.0, 0, 0], ['', 1.0, 0, 0], ['', 2.0, 0, 0], ['', 3.0, 0, 0]], "처방전 1회 투여량 헤더의 output이 잘못되었습니다."
