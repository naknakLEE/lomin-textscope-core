from typing import Dict, Tuple

class Error():
    error_code: int
    error_message: str
    
    def __init__(
        self,
        error_code: int = 9500,
        error_message: str = "확인되지 않은 오류가 발생했습니다"
    ):
        self.error_code = error_code
        self.error_message = error_message


ErrorCode: Dict[int, Tuple[int, Error]] = {
    # wrapper
    1501: (500, Error(1501, "코어 서버와 요청, 응답 과정에서 에러가 발생했습니다")),
    
    #core
    2101: (404, Error(2101, "document_id에 해당하는 문서가 존재하지 않습니다")),
    2102: (409, Error(2102, "document_id에 해당하는 문서가 이미 존재합니다")),
    2103: (500, Error(2103, "이미지 정보 변환중 에러가 발생했습니다")),
    2104: (404, Error(2104, "해당 좌표는 이미지에서 벗어났거나, 잘못된 좌표 형식입니다")),
    2105: (404, Error(2105, "지원하지 않는 파일 형식입니다")),
    2106: (404, Error(2106, "model 정보가 존재하지 않습니다")),
    2107: (404, Error(2107, "문서 종류(소분류) 정보가 존재하지 않습니다")),
    2108: (404, Error(2108, "문서 종류(대분류) 정보가 존재하지 않습니다")),
    2109: (404, Error(2109, "요청한 문서 종류와 모델정보는 존재하지 않습니다")),
    2110: (404, Error(2110, "class 정보가 존재하지 않습니다")),
    2201: (404, Error(2201, "task_id에 해당하는 task가 존재하지 않습니다")),
    2202: (409, Error(2202, "task_id에 해당하는 task가 이미 존재합니다")),
    2401: (403, Error(2401, "email 또는 password가 정확하지 않습니다")),
    2402: (403, Error(2402, "OAuth 2.0 인증 상태가 아니거나 만료된 엑세스 토큰입니다")),
    2403: (403, Error(2403, "OAuth 2.0 인증 상태가 아니거나 잘못된 엑세스 토큰입니다")),
    2504: (403, Error(2504, "알 수 없는 사용자 정보입니다")),
    2505: (403, Error(2505, "document_id에 해당하는 문서에 대한 권한이 없습니다")),
    2506: (404, Error(2506, "요청한 페이지는 존재하지 않는 페이지 입니다")),
    2507: (404, Error(2507, "document_id에 해당하는 문서에 대한 추론 정보가 없습니다")),
    2508: (404, Error(2508, "document_path에 문서가 존재하지 않습니다")),
    2509: (404, Error(2509, "사용자에게 부여된 권한이 없습니다")),
    2510: (404, Error(2510, "user_team에 해당하는 그룹에 대한 권한이 없습니다")),
    2511: (409, Error(2511, "document_id에 해당하는 문서는 다른 사용자가 이미 검수 중입니다")),
    2512: (405, Error(2512, "해당 사용자는 비활성화된 사용자입니다")),
    2513: (409, Error(2513, "document_id에 해당하는 문서는 아직 검수 할 수 없습니다")),
    2524: (403, Error("C01.004.4019", "알 수 없는 사원 정보입니다")),
    
    #serving
    3501: (500, Error(3501, "모델 서버 에러가 발생했습니다")),
    3502: (500, Error(3502, "pp 과정에서 에러가 발생했습니다")),
    3503: (500, Error(3503, "텍스트 변환 과정에서 에러가 발생했습니다")),
    
    #database
    4101: (500, Error(4101, "{0} 정보를 가져오는 중 에러가 발생했습니다")),
    4102: (500, Error(4102, "{0} 정보를 저장하는 중 에러가 발생했습니다")),
    
    #unkown
    9500: (500, Error(9500, "확인되지 않은 오류가 발생했습니다"))
}