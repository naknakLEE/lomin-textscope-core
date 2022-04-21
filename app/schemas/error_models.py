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
    

ErrorCode = {
    # wrapper
    1501: (500, Error(1501, "코어 서버와 요청, 응답 과정에서 에러가 발생했습니다")),
    
    #core
    2101: (404, Error(2101, "image_id에 해당하는 이미지가 존재하지 않습니다")),
    2102: (409, Error(2102, "image_id에 해당하는 이미지가 이미 존재합니다")),
    2201: (404, Error(2201, "task_id에 해당하는 task가 존재하지 않습니다")),
    2202: (409, Error(2202, "task_id에 해당하는 task가 이미 존재합니다")),
    2401: (403, Error(2401, "email 또는 password가 정확하지 않습니다")),
    2402: (403, Error(2402, "OAuth 2.0 인증 상태가 아니거나 만료된 엑세스 토큰입니다")),
    2403: (403, Error(2403, "OAuth 2.0 인증 상태가 아니거나 잘못된 엑세스 토큰입니다")),
    
    #serving
    3501: (500, Error(3501, "모델 서버 에러가 발생했습니다")),
    3502: (500, Error(3502, "pp 과정에서 에러가 발생했습니다")),
    3503: (500, Error(3503, "텍스트 변환 과정에서 에러가 발생했습니다")),
    
    #database
    4101: (500, Error(4101, "이미지 정보를 가져오는 중 에러가 발생했습니다")),
    4102: (500, Error(4102, "이미지 정보를 저장하는 중 에러가 발생했습니다")),
    4201: (500, Error(4201, "task 정보를 가져오는 중 에러가 발생했습니다")),
    4202: (500, Error(4202, "task 정보를 저장하는 중 에러가 발생했습니다")),
    
    #unkown
    9500: (500, Error(9500, "확인되지 않은 오류가 발생했습니다"))
}