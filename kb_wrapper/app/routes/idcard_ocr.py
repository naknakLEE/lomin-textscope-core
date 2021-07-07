import httpx

from typing import Any
from fastapi import Request, APIRouter, Form
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from kb_wrapper.app import models
from kb_wrapper.app.errors import exceptions as ex
from kb_wrapper.app.common.const import get_settings
from kb_wrapper.app.utils.request_parser import parse_multi_form
from kb_wrapper.app.utils.ocr_result_parser import parse_kakaobank
from kb_wrapper.app.utils.ocr_response_parser import response_handler


router = APIRouter()
settings = get_settings()
TEXTSCOPE_SERVER_URL = f"http://{settings.WEB_IP_ADDR}:{settings.WEB_IP_PORT}"


DOCUMENT_TYPE_SET = {
    "ZZ": "신청서",
    "A1": "사업자등록증",
    "A2": "거래통장",
    "A3": "매장사진",
    "A5": "등록단말기 미설치 사유서",
    "A6": "고객거래확인서",
    "A7": "실제소유자신분증",
    "A8": "주주명부",
    "A9": "POS 보안프로그램 미설치사유서",
    "AA": "복수가맹점 신청서",
    "AB": "페업사실증명서",
    "AC": "계좌개설확인서류 (가상계좌등록요청문)",
    "AD": "제3자 결제계좌 등록요청 및 동의서",
    "AE": "제3자결제계좌등록요청및동의서(편의점)",
    "AG": "선물카드 미수납 사유서",
    "E1": "석유판매업(주유소) 등록증",
    "E2": "액화석유가스(충전소)등록/접수증",
    "E3": "요식업허가증",
    "E4": "유흥/단란주점 허가증",
    "E5": "의료기관개설신고필증",
    "E6": "의료기관개설허가증",
    "E7": "관광사업등록증",
    "E8": "시장(대형점)개설허가증",
    "E9": "저가지향형점포지정서",
    "EA": "보훈매점승인서",
    "EB": "체육시설 허가증",
    "EC": "학원의설립운영등록증",
    "ED": "농가공업승인서",
    "EE": "미곡상영업허가증",
    "EF": "호텔업등급인정증",
    "EG": "대리점계약서",
    "EH": "가맹체인계약서",
    "EJ": "상품권발행 증빙서류",
    "EK": "인지세 납부 서류",
    "EL": "상품권 위탁판매계약서",
    "EM": "상품권 기본",
    "EN": "공제조합가입증명서",
    "EP": "관광사업등록증",
    "EQ": "어린이집 인가증",
    "ER": "영업신고증",
    "EY": "기타첨부서류2",
    "EZ": "기타첨부서류",
    "J1": "대표자신분증",
    "J2": "대표자 기본증명서",
    "J3": "가존관계증명서",
    "J4": "개인정보 수집이용제공 동의서-대표자",
    "J5": "여권",
    "J6": "외국인등록증 OR 국내거소신고서",
    "J7": "작성자 위임장",
    "J8": "인감명서",
    "J9": "주민등록초본",
    "JA": "대표자 본인 전자서명 확인서",
    "JB": "대표자 본인 전자서명 확인서",
    "L1": "대리인 신분증",
    "L2": "개인정보 수집이용제공동의서",
    "L3": "작성자 신분증",
    "L4": "대리인 고객거래확인서",
    "N1": "법인등기부 등본(등기사항 전부증명서)",
    "N2": "법인인감증명서",
    "N3": "등기사항 전부증명서",
    "N4": "정관 혹은 설립인가서",
    "N5": "사용인감계",
    "N6": "변경요청 공문-법인",
    "N7": "합병 및 분할 관련 서류",
    "N8": "가맹목적공문",
    "R1": "합병 및 분할 관련 서류",
    "R2": "공동대표자 가맹점 가입동의 및 위임장",
    "R3": "개인정보 수집이용제공동의서-공동대표",
    "R4": "공동대표 위임장",
    "R5": "공동대표 결제계좌 동의서",
    "R6": "공동대표자 신분증",
    "R7": "개인정보 수집이용제공동의서-공동대표자",
    "R8": "가맹점정보 조회수수집이용제공 동의서",
    "R9": "결제계좌 변경 동의서",
    "RA": "공동 가맹 동의서",
    "RB": "제3자 결제계좌 동의서",
    "RC": "개인정보 수집이용제공동의서",
    "RD": "공동대표자 계좌동의서",
    "RE": "공동대표 인감증명서",
    "RF": "결제계좌사본",
    "W1": "미성년자업주 법정대리인 동의서",
    "W2": "법정대리인 신분증 사본",
    "W3": "법정대리인 인감증명서",
}


@router.post("/kb", status_code=200)
async def inference(
    image_path: str = Form(...),
    request_id: str = Form(...),
    doc_type: str = Form(...),
) -> Any:
    """
    ### 토큰과 파일을 전달받아 모델 서버에 ocr 처리 요청
    입력 데이터: 토큰, ocr에 사용할 파일 <br/>
    응답 데이터: 상태 코드, 최소 퀄리티 보장 여부, 신뢰도, 문서 타입, ocr결과(문서에 따라 다른 결과 반환)
    """

    data = {
        "image_path": image_path,
        "request_id": request_id,
        "doc_type": doc_type,
    }
    results = list()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{TEXTSCOPE_SERVER_URL}/v1/inference/kb/idcard",
            data=data,
            timeout=300.0,
        )
        result = response.json()
        print("\033[95m" + f"{result}" + "\033[m")
        result["status"] = int(result["code"])
        del result["code"]
        if result["status"] >= 1400:
            result = response_handler(**result)
            results.append(models.SuccessfulResponse(**result))
        else:
            result["ocrResult"] = parse_kakaobank(result["ocrResult"])
            result = response_handler(**result)
            results.append(models.SuccessfulResponse(**result))
    return JSONResponse(status_code=200, content=jsonable_encoder(results))
