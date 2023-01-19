
import copy
import sys
import pytest
sys.path.append("pp_server")

from pp_server.pp.business.kbl1 import separate_MD_DN_MD_DLD
from pp_server.pp.postprocess.general import regex_yyyy_mm_dd


def test_yyyymmdd():
    res = regex_yyyy_mm_dd('2022 년 10 월 29 일 - ')
    assert ('20221029', '2022년10월29') == res, "regex_yyyy_mm_dd 테스트 실패"
    
    res = regex_yyyy_mm_dd('2022 년 12 원 11 일 - 제 01036 호')
    assert ('20221211', '2022년12월11') == res, "regex_yyyy_mm_dd 테스트 실패"
    

@pytest.mark.parametrize(
    "test_input, expected",
    [
        (
            {'MD-DN': {'type': 'word', 'value': '2022 년 10 월 29 일 - 제 01009 호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '2022 년 10 월 29 일 - 제 01009 호'}},
            {
                'MD-DN': {'type': 'word', 'value': '01009', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '01009'},
                'MD-DLD': {'type': 'word', 'value': '20221029', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221029'}
            }
        ),
        (
            {'MD-DLD': {'type': 'word', 'value': '2022년 10월 29일 제 24호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '2022년 10월 29일 제 24호'}},
            {
                'MD-DN': {'type': 'word', 'value': '24', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '24'},
                'MD-DLD': {'type': 'word', 'value': '20221029', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221029'}
            }
        ),
        (
            {'MD-DLD': {'type': 'word', 'value': '2022 년 10 월 30 일 - 제 00005 호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '2022 년 10 월 30 일 - 제 00005 호'}},
            {
                'MD-DN': {'type': 'word', 'value': '00005', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '00005'},
                'MD-DLD': {'type': 'word', 'value': '20221030', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221030'}
            }
        ),
        (
            {'MD-DN': {'type': 'word', 'value': '2022년 10월 30일 제 00072 호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '2022년 10월 30일 제 00072 호'}},
            {
                'MD-DN': {'type': 'word', 'value': '00072', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '00072'},
                'MD-DLD': {'type': 'word', 'value': '20221030', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221030'}
            }
        ),
        (
            {'MD-DLD': {'type': 'word', 'value': '2022-10-29-00014', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '2022-10-29-00014'}},
            {
                'MD-DN': {'type': 'word', 'value': '00014', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '00014'},
                'MD-DLD': {'type': 'word', 'value': '20221029', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221029'}
            }
        ),
        (
            {'MD-DLD': {'type': 'word', 'value': '2022-10-29-00005', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '2022-10-29-00005'}},
            {
                'MD-DN': {'type': 'word', 'value': '00005', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '00005'},
                'MD-DLD': {'type': 'word', 'value': '20221029', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221029'}
            }
        ),
        (
            {'MD-DN': {'type': 'word', 'value': '2022 년 10 월 29 일 - 제 01004 호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '2022 년 10 월 29 일 - 제 01004 호'}},
            {
                'MD-DN': {'type': 'word', 'value': '01004', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '01004'},
                'MD-DLD': {'type': 'word', 'value': '20221029', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221029'}
            }
        ),
        (
            {'MD-DLD': {'type': 'word', 'value': '2022-10-29-00011', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '2022-10-29-00011'}},
            {
                'MD-DN': {'type': 'word', 'value': '00011', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '00011'},
                'MD-DLD': {'type': 'word', 'value': '20221029', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221029'}
            }
        ),
        (
            {'MD-DLD': {'type': 'word', 'value': '2022년 10월 29일 - 제 9145호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '2022년 10월 29일 - 제 9145호'}},
            {
                'MD-DN': {'type': 'word', 'value': '9145', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '9145'},
                'MD-DLD': {'type': 'word', 'value': '20221029', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221029'}
            }
        ),
        (
            {'MD-DN': {'type': 'word', 'value': '2022 년 10 월 29 일 - 제 01010 호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '2022 년 10 월 29 일 - 제 01010 호'}},
            {
                'MD-DN': {'type': 'word', 'value': '01010', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '01010'},
                'MD-DLD': {'type': 'word', 'value': '20221029', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221029'}
            }
        ),
        (
            {'MD-DLD': {'type': 'word', 'value': '2022년 10월 30일 - 제00016호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '2022년 10월 30일 - 제00016호'}},
            {
                'MD-DN': {'type': 'word', 'value': '00016', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '00016'},
                'MD-DLD': {'type': 'word', 'value': '20221030', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221030'}
            }
        ),
        (
            {'MD-DN': {'type': 'word', 'value': '2022 년 10 월 30 임 - 제 03044 호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '2022 년 10 월 30 임 - 제 03044 호'}},
            {
                'MD-DN': {'type': 'word', 'value': '03044', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '03044'},
                'MD-DLD': {'type': 'word', 'value': '20221030', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221030'}
            }
        ),
        (
            {'MD-DN': {'type': 'word', 'value': '2022 년 10 월 29 일 ------ 제 01006 호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '2022 년 10 월 29 일 ------ 제 01006 호'}},
            {
                'MD-DN': {'type': 'word', 'value': '01006', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '01006'},
                'MD-DLD': {'type': 'word', 'value': '20221029', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221029'}
            }
        ),
        (
            {'MD-DN': {'type': 'word', 'value': '2022 년 10 월 29 일 - 제 01007 호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '2022 년 10 월 29 일 - 제 01007 호'}},
            {
                'MD-DN': {'type': 'word', 'value': '01007', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '01007'},
                'MD-DLD': {'type': 'word', 'value': '20221029', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221029'}
            }
        ),
        (
            {'MD-DLD': {'type': 'word', 'value': '2022년 10월 29일 제 28호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '2022년 10월 29일 제 28호'}},
            {
                'MD-DN': {'type': 'word', 'value': '28', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '28'},
                'MD-DLD': {'type': 'word', 'value': '20221029', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221029'}
            }
        ),
        (
            {'MD-DN': {'type': 'word', 'value': '2022 년 10 월 29 일 제 01008 호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '2022 년 10 월 29 일 제 01008 호'}},
            {
                'MD-DN': {'type': 'word', 'value': '01008', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '01008'},
                'MD-DLD': {'type': 'word', 'value': '20221029', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221029'}
            }
        ),
        (
            {'MD-DLD': {'type': 'word', 'value': '2022-10-29-00013', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '2022-10-29-00013'}},
            {
                'MD-DN': {'type': 'word', 'value': '00013', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '00013'},
                'MD-DLD': {'type': 'word', 'value': '20221029', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221029'}
            }
        ),
        (
            {'MD-DLD': {'type': 'word', 'value': '2022년 10월 29일 제 9142호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '2022년 10월 29일 제 9142호'}},
            {
                'MD-DN': {'type': 'word', 'value': '9142', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '9142'},
                'MD-DLD': {'type': 'word', 'value': '20221029', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221029'}
            }
        ),
        (
            {'MD-DN': {'type': 'word', 'value': '2022 년 10 월 30 일 - 제 01024 호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '2022 년 10 월 30 일 - 제 01024 호'}},
            {
                'MD-DN': {'type': 'word', 'value': '01024', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '01024'},
                'MD-DLD': {'type': 'word', 'value': '20221030', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221030'}
            }
        ),
        (
            {'MD-DN': {'type': 'word', 'value': '2022 년 10 월 29 일 - 제 03023 호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '2022 년 10 월 29 일 - 제 03023 호'}},
            {
                'MD-DN': {'type': 'word', 'value': '03023', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '03023'},
                'MD-DLD': {'type': 'word', 'value': '20221029', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221029'}
            }
        ),
        (
            {'MD-DLD': {'type': 'word', 'value': '2022년 10월 30일 제00069호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '2022년 10월 30일 제00069호'}},
            {
                'MD-DN': {'type': 'word', 'value': '00069', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '00069'},
                'MD-DLD': {'type': 'word', 'value': '20221030', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221030'}
            }
        ),
        (
            {'MD-DLD': {'type': 'word', 'value': '2022년 10월 29일 제 46 호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '2022년 10월 29일 제 46 호'}},
            {
                'MD-DN': {'type': 'word', 'value': '46', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '46'},
                'MD-DLD': {'type': 'word', 'value': '20221029', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221029'}
            }
        ),
        (
            {'MD-DN': {'type': 'word', 'value': '2022년 10월 29일-제00002호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '2022년 10월 29일-제00002호'}},
            {
                'MD-DN': {'type': 'word', 'value': '00002', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '00002'},
                'MD-DLD': {'type': 'word', 'value': '20221029', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221029'}
            }
        ),
        (
            {'MD-DN': {'type': 'word', 'value': '2022 년 10 월 29 일 - 제 01011 호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '2022 년 10 월 29 일 - 제 01011 호'}},
            {
                'MD-DN': {'type': 'word', 'value': '01011', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '01011'},
                'MD-DLD': {'type': 'word', 'value': '20221029', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221029'}
            }
        ),
        (
            {'MD-DN': {'type': 'word', 'value': '2022 년 10 월 30 일 제 00037 호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '2022 년 10 월 30 일 제 00037 호'}},
            {
                'MD-DN': {'type': 'word', 'value': '00037', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '00037'},
                'MD-DLD': {'type': 'word', 'value': '20221030', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221030'}
            }
        ),
        (
            {'MD-DN': {'type': 'word', 'value': '2022 년 10 월 29 일 - 제 01015 호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '2022 년 10 월 29 일 - 제 01015 호'}},
            {
                'MD-DN': {'type': 'word', 'value': '01015', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '01015'},
                'MD-DLD': {'type': 'word', 'value': '20221029', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221029'}
            }
        ),
        (
            {'MD-DLD': {'type': 'word', 'value': '2022-10-29-00003', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '2022-10-29-00003'}},
            {
                'MD-DN': {'type': 'word', 'value': '00003', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '00003'},
                'MD-DLD': {'type': 'word', 'value': '20221029', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221029'}
            }
        ),
        (
            {'MD-DN': {'type': 'word', 'value': '2022 년 10 월 29 일 - 제 01010 호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '2022 년 10 월 29 일 - 제 01010 호'}},
            {
                'MD-DN': {'type': 'word', 'value': '01010', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '01010'},
                'MD-DLD': {'type': 'word', 'value': '20221029', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221029'}
            }
        ),
        (
            {'MD-DN': {'type': 'word', 'value': '2022 년 10 월 29 일 - 제 01008 호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '2022 년 10 월 29 일 - 제 01008 호'}},
            {
                'MD-DN': {'type': 'word', 'value': '01008', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '01008'},
                'MD-DLD': {'type': 'word', 'value': '20221029', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221029'}
            }
        ),
        (
            {'MD-DN': {'type': 'word', 'value': '2022년 10월 29일 제 3', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '2022년 10월 29일 제 3'}},
            {
                'MD-DN': {'type': 'word', 'value': '3', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '3'},
                'MD-DLD': {'type': 'word', 'value': '20221029', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221029'}
            }
        ),
        (
            {'MD-DLD': {'type': 'word', 'value': '2022년 10월 29일-제00001호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '2022년 10월 29일-제00001호'}},
            {
                'MD-DN': {'type': 'word', 'value': '00001', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '00001'},
                'MD-DLD': {'type': 'word', 'value': '20221029', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221029'}
            }
        ),
        (
            {'MD-DN': {'type': 'word', 'value': '2022년 10월 29일 제 2 호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '2022년 10월 29일 제 2 호'}},
            {
                'MD-DN': {'type': 'word', 'value': '2', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '2'},
                'MD-DLD': {'type': 'word', 'value': '20221029', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221029'}
            }
        ),
        (
            {'MD-DLD': {'type': 'word', 'value': '2022년 10월 30일 제 00089 호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '2022년 10월 30일 제 00089 호'}},
            {
                'MD-DN': {'type': 'word', 'value': '00089', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '00089'},
                'MD-DLD': {'type': 'word', 'value': '20221030', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221030'}
            }
        ),
        (
            {'MD-DLD': {'type': 'word', 'value': '2022년 10월 30일 99989', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '2022년 10월 30일 99989'}},
            {
                'MD-DN': {'type': 'word', 'value': '99989', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '99989'},
                'MD-DLD': {'type': 'word', 'value': '20221030', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221030'}
            }
        ),
        (
            {'MD-DLD': {'type': 'word', 'value': '의료 기관 20221030 제 32 호 수투약일수 1일 투여횟수 처방 의료인의 성명 1회 투약량 891104-1048210 U071, JOO 이정훈 적지 않습니다. 총', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '의료 기관 20221030 제 32 호 수투약일수 1일 투여횟수 처방 의료인의 성명 1회 투약량 891104-1048210 U071, JOO 이정훈 적지 않습니다. 총'}},
            {
                'MD-DN': {'type': 'word', 'value': '32', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '32'},
                'MD-DLD': {'type': 'word', 'value': '20221030', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221030'}
            }
        ),
        (
            {'MD-DN': {'type': 'word', 'value': '2022 년 10 월 30 일 - 제 01033 호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '2022 년 10 월 30 일 - 제 01033 호'}},
            {
                'MD-DN': {'type': 'word', 'value': '01033', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '01033'},
                'MD-DLD': {'type': 'word', 'value': '20221030', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221030'}
            }
        ),
        (
            {'MD-DLD': {'type': 'word', 'value': '2022년 10월 30일 제00019호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '2022년 10월 30일 제00019호'}},
            {
                'MD-DN': {'type': 'word', 'value': '00019', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '00019'},
                'MD-DLD': {'type': 'word', 'value': '20221030', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221030'}
            }
        ),
        (
            {'MD-DN': {'type': 'word', 'value': '2022 년 10 월 30 일 - 제 04009 호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '2022 년 10 월 30 일 - 제 04009 호'}},
            {
                'MD-DN': {'type': 'word', 'value': '04009', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '04009'},
                'MD-DLD': {'type': 'word', 'value': '20221030', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221030'}
            }
        ),
        (
            {'MD-DN': {'type': 'word', 'value': '2022년 10월 30일-제00009호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '2022년 10월 30일-제00009호'}},
            {
                'MD-DN': {'type': 'word', 'value': '00009', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '00009'},
                'MD-DLD': {'type': 'word', 'value': '20221030', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221030'}
            }
        ),
        (
            {'MD-DN': {'type': 'word', 'value': '2022 년 10 월 29 일 - 제 01032 호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '2022 년 10 월 29 일 - 제 01032 호'}},
            {
                'MD-DN': {'type': 'word', 'value': '01032', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '01032'},
                'MD-DLD': {'type': 'word', 'value': '20221029', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221029'}
            }
        ),
        (
            {'MD-DLD': {'type': 'word', 'value': '2022-10-29-00051', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '2022-10-29-00051'}},
            {
                'MD-DN': {'type': 'word', 'value': '00051', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '00051'},
                'MD-DLD': {'type': 'word', 'value': '20221029', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221029'}
            }
        ),
        (
            {'MD-DN': {'type': 'word', 'value': '2022 년 10 월 29 일 - 제 13011 호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '2022 년 10 월 29 일 - 제 13011 호'}},
            {
                'MD-DN': {'type': 'word', 'value': '13011', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '13011'},
                'MD-DLD': {'type': 'word', 'value': '20221029', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221029'}
            }
        ),
        (
            {'MD-DN': {'type': 'word', 'value': '2022 년 10 월 29 일 - 제 00237 호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '2022 년 10 월 29 일 - 제 00237 호'}},
            {
                'MD-DN': {'type': 'word', 'value': '00237', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '00237'},
                'MD-DLD': {'type': 'word', 'value': '20221029', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221029'}
            }
        ),
        (
            {'MD-DN': {'type': 'word', 'value': '2022년 10월 28일 제 00002 호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '2022년 10월 28일 제 00002 호'}},
            {
                'MD-DN': {'type': 'word', 'value': '00002', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '00002'},
                'MD-DLD': {'type': 'word', 'value': '20221028', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221028'}
            }
        ),
        (
            {'MD-DN': {'type': 'word', 'value': '2022년 10월 28일 제 00002 호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '2022년 10월 28일 제 00002 호'}},
            {
                'MD-DN': {'type': 'word', 'value': '00002', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '00002'},
                'MD-DLD': {'type': 'word', 'value': '20221028', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221028'}
            }
        ),
        (
            {'MD-DN': {'type': 'word', 'value': '2022년 10월 29일 제 00048 호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '2022년 10월 29일 제 00048 호'}},
            {
                'MD-DN': {'type': 'word', 'value': '00048', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '00048'},
                'MD-DLD': {'type': 'word', 'value': '20221029', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221029'}
            }
        ),
        (
            {'MD-DLD': {'type': 'word', 'value': '2022년10월29일 제00013호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '2022년10월29일 제00013호'}},
            {
                'MD-DN': {'type': 'word', 'value': '00013', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '00013'},
                'MD-DLD': {'type': 'word', 'value': '20221029', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221029'}
            }
        ),
        (
            {'MD-DN': {'type': 'word', 'value': '00037', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '00037'}},
            {
                'MD-DN': {'type': 'word', 'value': '00037', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '00037'},
            }
        ),
        (
            {'MD-DN': {'type': 'word', 'value': '2022 년 11 월 02 일 - 제 01039 호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '2022 년 11 월 02 일 - 제 01039 호'}},
            {
                'MD-DN': {'type': 'word', 'value': '01039', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '01039'},
                'MD-DLD': {'type': 'word', 'value': '20221102', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221102'}
            }
        ),
        (
            {'MD-DN': {'type': 'word', 'value': '2022년 11월 02일 제 00104 호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '2022년 11월 02일 제 00104 호'}},
            {
                'MD-DN': {'type': 'word', 'value': '00104', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '00104'},
                'MD-DLD': {'type': 'word', 'value': '20221102', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221102'}
            }
        ),
        (
            {'MD-DN': {'type': 'word', 'value': '2022 년 11 월 02 일 _ 제 03016 호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '2022 년 11 월 02 일 _ 제 03016 호'}},
            {
                'MD-DN': {'type': 'word', 'value': '03016', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '03016'},
                'MD-DLD': {'type': 'word', 'value': '20221102', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221102'}
            }
        ),
        (
            {'MD-DN': {'type': 'word', 'value': '2022년 11월 02일-제00008호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '2022년 11월 02일-제00008호'}},
            {
                'MD-DN': {'type': 'word', 'value': '00008', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '00008'},
                'MD-DLD': {'type': 'word', 'value': '20221102', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221102'}
            }
        ),
        (
            {'MD-DLD': {'type': 'word', 'value': '2022년 11월 02일 - 제00009호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '2022년 11월 02일 - 제00009호'}},
            {
                'MD-DN': {'type': 'word', 'value': '00009', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '00009'},
                'MD-DLD': {'type': 'word', 'value': '20221102', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221102'}
            }
        ),
        (
            {'MD-DN': {'type': 'word', 'value': '2022년 11월 01일-제00037호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '2022년 11월 01일-제00037호'}},
            {
                'MD-DN': {'type': 'word', 'value': '00037', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '00037'},
                'MD-DLD': {'type': 'word', 'value': '20221101', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221101'}
            }
        ),
        (
            {'MD-DN': {'type': 'word', 'value': '2022 년 11 월 01 일 - 제 01128 호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '2022 년 11 월 01 일 - 제 01128 호'}},
            {
                'MD-DN': {'type': 'word', 'value': '01128', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '01128'},
                'MD-DLD': {'type': 'word', 'value': '20221101', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221101'}
            }
        ),
        (
            {'MD-DN': {'type': 'word', 'value': '2022 년 11 월 01 일 - 제 01063 호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '2022 년 11 월 01 일 - 제 01063 호'}},
            {
                'MD-DN': {'type': 'word', 'value': '01063', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '01063'},
                'MD-DLD': {'type': 'word', 'value': '20221101', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221101'}
            }
        ),
        (
            {'MD-DN': {'type': 'word', 'value': '2022년 11월 01일 제 00045 호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '2022년 11월 01일 제 00045 호'}},
            {
                'MD-DN': {'type': 'word', 'value': '00045', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '00045'},
                'MD-DLD': {'type': 'word', 'value': '20221101', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221101'}
            }
        ),
        (
            {'MD-DLD': {'type': 'word', 'value': '2022 년 11 월 01 일 - 제 00004 호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '2022 년 11 월 01 일 - 제 00004 호'}},
            {
                'MD-DN': {'type': 'word', 'value': '00004', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '00004'},
                'MD-DLD': {'type': 'word', 'value': '20221101', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221101'}
            }
        ),
        (
            {'MD-DN': {'type': 'word', 'value': '2022 년 11 월 01 일 - 제 01008 호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '2022 년 11 월 01 일 - 제 01008 호'}},
            {
                'MD-DN': {'type': 'word', 'value': '01008', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '01008'},
                'MD-DLD': {'type': 'word', 'value': '20221101', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221101'}
            }
        ),
        (
            {'MD-DN': {'type': 'word', 'value': '2022 년 11 월 01 일 - 제 02565 호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '2022 년 11 월 01 일 - 제 02565 호'}},
            {
                'MD-DN': {'type': 'word', 'value': '02565', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '02565'},
                'MD-DLD': {'type': 'word', 'value': '20221101', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221101'}
            }
        ),
        (
            {'MD-DLD': {'type': 'word', 'value': '2022년 11월 01일 - 제 00017 호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '2022년 11월 01일 - 제 00017 호'}},
            {
                'MD-DN': {'type': 'word', 'value': '00017', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '00017'},
                'MD-DLD': {'type': 'word', 'value': '20221101', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221101'}
            }
        ),
        (
            {'MD-DN': {'type': 'word', 'value': '2022 년 10 월 31 일 - 제 02742 호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '2022 년 10 월 31 일 - 제 02742 호'}},
            {
                'MD-DN': {'type': 'word', 'value': '02742', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '02742'},
                'MD-DLD': {'type': 'word', 'value': '20221031', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221031'}
            }
        ),
        (
            {'MD-DN': {'type': 'word', 'value': '2022 년 10 월 31 일 - 제 01171 호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '2022 년 10 월 31 일 - 제 01171 호'}},
            {
                'MD-DN': {'type': 'word', 'value': '01171', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '01171'},
                'MD-DLD': {'type': 'word', 'value': '20221031', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221031'}
            }
        ),
        (
            {'MD-DN': {'type': 'word', 'value': '2022년 10월 31일 제 00046 호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '2022년 10월 31일 제 00046 호'}},
            {
                'MD-DN': {'type': 'word', 'value': '00046', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '00046'},
                'MD-DLD': {'type': 'word', 'value': '20221031', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221031'}
            }
        ),
        (
            {'MD-DN': {'type': 'word', 'value': '2022 년 10 월 30 일 - 제 01072 호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '2022 년 10 월 30 일 - 제 01072 호'}},
            {
                'MD-DN': {'type': 'word', 'value': '01072', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '01072'},
                'MD-DLD': {'type': 'word', 'value': '20221030', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221030'}
            }
        ),
        (
            {'MD-DN': {'type': 'word', 'value': '2022 년 10 월 30 일 - 제 03044 호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '2022 년 10 월 30 일 - 제 03044 호'}},
            {
                'MD-DN': {'type': 'word', 'value': '03044', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '03044'},
                'MD-DLD': {'type': 'word', 'value': '20221030', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221030'}
            }
        ),
        (
            {'MD-DN': {'type': 'word', 'value': '2022 년 10 월 30 일 - 제 03039 호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '2022 년 10 월 30 일 - 제 03039 호'}},
            {
                'MD-DN': {'type': 'word', 'value': '03039', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '03039'},
                'MD-DLD': {'type': 'word', 'value': '20221030', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221030'}
            }
        ),
        (
            {'MD-DN': {'type': 'word', 'value': '2022 년 10 월 30 일 - 제 01058 호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '2022 년 10 월 30 일 - 제 01058 호'}},
            {
                'MD-DN': {'type': 'word', 'value': '01058', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '01058'},
                'MD-DLD': {'type': 'word', 'value': '20221030', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221030'}
            }
        ),
        (
            {'MD-DLD': {'type': 'word', 'value': '2022 년 10월 30일 - 제 00019 호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '2022 년 10월 30일 - 제 00019 호'}},
            {
                'MD-DN': {'type': 'word', 'value': '00019', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '00019'},
                'MD-DLD': {'type': 'word', 'value': '20221030', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221030'}
            }
        ),
        (
            {'MD-DN': {'type': 'word', 'value': '2022 년 10 월 30 일 - 제 01031 호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '2022 년 10 월 30 일 - 제 01031 호'}},
            {
                'MD-DN': {'type': 'word', 'value': '01031', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '01031'},
                'MD-DLD': {'type': 'word', 'value': '20221030', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221030'}
            }
        ),
        (
            {'MD-DLD': {'type': 'word', 'value': '2022년10월30일-제 00028호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '2022년10월30일-제 00028호'}},
            {
                'MD-DN': {'type': 'word', 'value': '00028', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '00028'},
                'MD-DLD': {'type': 'word', 'value': '20221030', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221030'}
            }
        ),
        (
            {'MD-DN': {'type': 'word', 'value': '2022 년 10 월 30 일 - 제 01027 호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '2022 년 10 월 30 일 - 제 01027 호'}},
            {
                'MD-DN': {'type': 'word', 'value': '01027', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '01027'},
                'MD-DLD': {'type': 'word', 'value': '20221030', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221030'}
            }
        ),
        (
            {'MD-DLD': {'type': 'word', 'value': '2022년 10월 02일-제00002호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '2022년 10월 02일-제00002호'}},
            {
                'MD-DN': {'type': 'word', 'value': '00002', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '00002'},
                'MD-DLD': {'type': 'word', 'value': '20221002', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221002'}
            }
        ),
        (
            {'MD-DN': {'type': 'word', 'value': '2022 년 10 월 01 일 - 제 56005 호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '2022 년 10 월 01 일 - 제 56005 호'}},
            {
                'MD-DN': {'type': 'word', 'value': '56005', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '56005'},
                'MD-DLD': {'type': 'word', 'value': '20221001', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221001'}
            }
        ),
        (
            {'MD-DLD': {'type': 'word', 'value': '2022년10월01일 00004', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '2022년10월01일 00004'}},
            {
                'MD-DN': {'type': 'word', 'value': '00004', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '00004'},
                'MD-DLD': {'type': 'word', 'value': '20221001', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221001'}
            }
        ),
        (
            {'MD-DLD': {'type': 'word', 'value': '2022년 10월 1일 제00001호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '2022년 10월 1일 제00001호'}},
            {
                'MD-DN': {'type': 'word', 'value': '00001', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '00001'},
                'MD-DLD': {'type': 'word', 'value': '20221001', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221001'}
            }
        ),
        (
            {'MD-DLD': {'type': 'word', 'value': '2022년 10월 01일-제00001호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '2022년 10월 01일-제00001호'}},
            {
                'MD-DN': {'type': 'word', 'value': '00001', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '00001'},
                'MD-DLD': {'type': 'word', 'value': '20221001', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221001'}
            }
        ),
        (
            {'MD-DLD': {'type': 'word', 'value': '2022년09월28일 제81692호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '2022년09월28일 제81692호'}},
            {
                'MD-DN': {'type': 'word', 'value': '81692', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '81692'},
                'MD-DLD': {'type': 'word', 'value': '20220928', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20220928'}
            }
        ),
        (
            {'MD-DN': {'type': 'word', 'value': '2022 년 10 월 01 일 - 제 56002 호', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '2022 년 10 월 01 일 - 제 56002 호'}},
            {
                'MD-DN': {'type': 'word', 'value': '56002', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '56002'},
                'MD-DLD': {'type': 'word', 'value': '20221001', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20221001'}
            }
        ),
        (
            {'MD-DLD': {'type': 'word', 'value': '2022-09-28-00041', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '2022-09-28-00041'}},
            {
                'MD-DN': {'type': 'word', 'value': '00041', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DN', 'text': '00041'},
                'MD-DLD': {'type': 'word', 'value': '20220928', 'box': [0, 0, 0, 0], 'score': 0, 'class': 'MD-DLD', 'text': '20220928'}
            }
        ),
    ]
)
def test_separate_MD_DN_MD_DLD(test_input, expected):
    """
        MD-DN: 교부번호
        MD-DLD: 교부일자
    """
    print(f"{test_input=}")
    res_kv = separate_MD_DN_MD_DLD(test_input)
    
    print(f"{res_kv=}")
    print(f"{expected=}")
    assert res_kv == expected, "separate_MD_DN_MD_DLD 테스트 실패"