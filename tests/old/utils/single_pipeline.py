from typing import Dict


class FakeInferenceRequestInput:
    def __init__(
        self,
        convert_preds_to_texts: bool,
        customer: str,
        detection_resize_ratio: float,
        detection_score_threshold: float,
        doc_type: str,
        hint: Dict,
        idcard_version: str,
        image_id: str,
        image_path: str,
        image_pkey: int,
        page: int,
        rectify: Dict,
        request_id: str,
        task_id: str,
        use_general_ocr: bool,
    ):
        self.convert_preds_to_texts = convert_preds_to_texts
        self.customer = customer
        self.detection_resize_ratio = detection_resize_ratio
        self.detection_score_threshold = detection_score_threshold
        self.doc_type = doc_type
        self.hint = hint
        self.idcard_version = idcard_version
        self.image_id = image_id
        self.image_path = image_path
        self.image_pkey = image_pkey
        self.page = page
        self.rectify = rectify
        self.request_id = request_id
        self.task_id = task_id
        self.use_general_ocr = use_general_ocr

    @property
    def convert_preds_to_texts(self) -> bool:
        return self.__convert_preds_to_texts

    @convert_preds_to_texts.setter
    def convert_preds_to_texts(self, convert_preds_to_texts: bool) -> None:
        self.__convert_preds_to_texts = convert_preds_to_texts

    @property
    def customer(self) -> str:
        return self.__customer

    @customer.setter
    def customer(self, customer: str) -> None:
        self.__customer = customer

    @property
    def detection_resize_ratio(self) -> float:
        return self.__detection_resize_ratio

    @detection_resize_ratio.setter
    def detection_resize_ratio(self, detection_resize_ratio: float) -> None:
        self.__detection_resize_ratio = detection_resize_ratio

    @property
    def detection_score_threshold(self) -> float:
        return self.__detection_score_threshold

    @detection_score_threshold.setter
    def detection_score_threshold(self, detection_score_threshold: float) -> None:
        self.__detection_score_threshold = detection_score_threshold

    @property
    def doc_type(self) -> str:
        return self.__doc_type

    @doc_type.setter
    def doc_type(self, doc_type: str) -> None:
        self.__doc_type = doc_type

    @property
    def hint(self) -> Dict:
        return self.__hint

    @hint.setter
    def hint(self, hint: Dict) -> None:
        self.__hint = hint

    @property
    def idcard_version(self) -> str:
        return self.__idcard_version

    @idcard_version.setter
    def idcard_version(self, idcard_version: str) -> None:
        self.__idcard_version = idcard_version

    @property
    def image_id(self) -> str:
        return self.__image_id

    @image_id.setter
    def image_id(self, image_id: str) -> None:
        self.__image_id = image_id

    @property
    def image_path(self) -> str:
        return self.__image_path

    @image_path.setter
    def image_path(self, image_path: str) -> None:
        self.__image_path = image_path

    @property
    def image_pkey(self) -> int:
        return self.__image_pkey

    @image_pkey.setter
    def image_pkey(self, image_pkey: int) -> None:
        self.__image_pkey = image_pkey

    @property
    def page(self) -> int:
        return self.__page

    @page.setter
    def page(self, page: int) -> None:
        self.__page = page

    @property
    def rectify(self) -> Dict:
        return self.__rectify

    @rectify.setter
    def rectify(self, rectify: Dict) -> None:
        self.__rectify = rectify

    @property
    def request_id(self) -> str:
        return self.__request_id

    @request_id.setter
    def request_id(self, request_id: str) -> None:
        self.__request_id = request_id

    @property
    def task_id(self) -> str:
        return self.__task_id

    @task_id.setter
    def task_id(self, task_id: str) -> None:
        self.__task_id = task_id

    @property
    def use_general_ocr(self) -> bool:
        return self.__use_general_ocr

    @use_general_ocr.setter
    def use_general_ocr(self, use_general_ocr: bool) -> None:
        self.__use_general_ocr = use_general_ocr


class FakeInferenceResponse:
    def __init__(
        self, status_code: int, response_data: Dict = {}, response_log: Dict = {}
    ):
        self.status_code = status_code
        self.response_data = response_data
        self.response_log = response_log

    @property
    def status_code(self) -> int:
        return self.__status_code

    @status_code.setter
    def status_code(self, status_code: int) -> None:
        self.__status_code = status_code

    @property
    def response_data(self) -> Dict:
        return self.__response_data

    @response_data.setter
    def response_data(self, response_data: Dict) -> None:
        self.__response_data = response_data

    @property
    def response_log(self) -> Dict:
        return self.__response_log

    @response_log.setter
    def response_log(self, response_log: Dict) -> None:
        self.__response_log = response_log

    def json(self) -> Dict:
        return self.response_data
