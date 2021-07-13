from typing import List, Optional, Any
from pydantic import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # DOCKER SERVER ADDRESS
    KAKAO_WRAPPER_IP_ADDR: str
    POSTGRES_IP_ADDR: str
    MYSQL_IP_ADDR: str
    WEB_IP_ADDR: str
    SERVING_IP_ADDR: str
    REDIS_IP_ADDR: str
    PP_IP_ADDR: str

    # POSTGRESQL CONFIG
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    # MYSQL CONFIG
    MYSQL_ROOT_USER: str
    MYSQL_DB: str
    MYSQL_PASSWORD: str

    # SERVING CONFIG
    KAKAO_WRAPPER_IP_PORT: int
    SERVING_IP_PORT: int
    REDIS_IP_PORT: int
    WEB_IP_PORT: int
    PP_IP_PORT: int

    # BASE CONFIG
    DEVELOP: bool = True
    API_ENV: str = "production"
    BASE_PATH: str = "."

    # KB_WRAPPER_DOCUMENT_TYPE_SET
    PARAMETER_ERROR_SET = {
        2000: "Request ID와 Image path 파라미터가 누락됨",
        2100: "이미지 파일이 경로에 존재하지 않음",
        3000: "알 수 없는 서버 내부 에러 발생",
    }

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

    KV_TYPE_SET = {
        "BusinessRegistration": [
            "cbr_regnum_business",
            "cbr_regnum_corp",
            "cbr_name",
            "cbr_address_business",
            "cbr_address_headquarter",
            "cbr_work_type",
            "cbr_work_cond",
        ],
        "UniqueNumber": [
            "cun_regnum_business",
            "cun_name",
            "cun_address_business",
        ],
        "CopyOfPassbook": [
            "bb_account_num",
            "bb_account_holder",
            "bb_bank",
        ],
        "ResidentRegistrationCardAndOverseasNationalRegistrationCard": [
            "rrc_title",
            "rrc_name",
            "rrc_regnum",
            "rrc_issue_date",
        ],
        "DriverLicense": [
            "dlc_title",
            "dlc_name",
            "dlc_regnum",
            "dlc_issue_date",
            "dlc_license_num",
            "dlc_exp_date",
        ],
        "외국인등록증 (전면)": [
            "arc_title",
            "arc_name",
            "arc_regnum",
            "arc_issue_date",
            "arc_exp_date",
        ],
        "여권": [
            "pp_title",
            "pp_name",
            "pp_regnum",
            "pp_issue_date",
        ],
        "법인등기사항전부증명서": [
            "ccr_title",
            "ccr_issue_date",
            "ccr_num_pages",
            "ccr_issued_stock",
            "crs_issue_date",
        ],
    }

    DOC_CODE_SET = {
        # 운전면허증 + 주민등록증, 우선 랜덤으로 추출할까?
        "REGISTRATION_SET_KEY": [
            "L1",
            "L3",
            "R6",
            "W2",
        ],
        # 외국인등록증 + 외국국적동포거소신고증 +영주증
        "FOREIGNER_SET_KEY": ["J6"],
        # 여권
        "PASSPORT_KEY": ["J5"],
    }

    DOC_KEY_SET = {
        "REGISTRATION_SET_KEY": [
            "rrc_title",
            "rrc_name",
            "rrc_regnum",
            "rrc_issue_date",
        ],
        "DRIVER_LICENSE_KEY": [
            "dlc_title",
            "dlc_name",
            "dlc_regnum",
            "dlc_issue_date",
            "dlc_license_num",
            "dlc_exp_date",
        ],
        "FOREIGNER_SET_KEY": [
            "arc_title",
            "arc_name",
            "arc_regnum",
            "arc_issue_date",
        ],
        "PASSPORT_KEY": [
            "pp_title",
            "pp_name",
            "pp_regnum",
            "pp_issue_date",
        ],
        "BusinessRegistration": [
            "cbr_regnum_business"
            "cbr_regnum_corp"
            "cbr_name"
            "cbr_address_business"
            "cbr_address_headquarter"
            "cbr_work_type"
            "cbr_work_cond"
        ],
        "UniqueNumber": ["cun_regnum_business" "cun_name" "cun_address_business"],
        "CopyOfPassbook": ["bb_account_num" "bb_account_holder" "bb_bank"],
        "ResidentRegistrationCardAndOverseasNationalRegistrationCard": [
            "rrc_title" "rrc_name" "rrc_regnum" "rrc_issue_date"
        ],
        "DriverLicense": [
            "dlc_title" "dlc_name" "dlc_regnum" "dlc_issue_date" "dlc_license_num" "dlc_exp_date"
        ],
        "AlienRegistrationCardAndForeignNationalityResidenceReportAndPermanentResidenceCard": [
            "arc_title" "arc_name" "arc_regnum" "arc_issue_date"
        ],
        "Passport": ["pp_title" "pp_name" "pp_regnum" "pp_issue_date"],
        "CertificateOfAllCorporateRegistrationDetails": [
            "ccr_title" "ccr_issue_date" "ccr_num_pages" "ccr_issued_stock"
        ],
        "SealCertificate": ["crs_issue_date"],
    }

    # LOGGER CONFIG
    LOG_DIR_PATH: str = f"{BASE_PATH}/logs/kb_wrapper"
    LOG_ROTATION: str = "1MB"
    LOG_RETENTION: str = "30 days"
    LOG_LEVEL: str = "DEBUG"
    FILE_MAX_BYTE: int = 1024 * 1024
    BACKUP_COUNT: int = 100000000
    LOG_LEVEL: str = "DEBUG"
    BACKTRACE: str = "True"
    DIAGNOSE: str = "True"
    ENQUEUE: str = "True"
    COLORIZE: str = "True"
    SERIALIZE = "serialize"
    ENCODING: str = "utf-8"
    FORMAT: str = "{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Any:
    return Settings()
