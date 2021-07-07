from typing import Optional, List
from pydantic.main import BaseModel


class StatusResponse(BaseModel):
    response: str = f"Textscope API (is_database_working: True, is_serving_server_working: True)"


class OcrResult(BaseModel):
    page: str
    status_code: str
    doc_type: str
    kv: Optional[dict] = None


class ReponseHandlerParameter(BaseModel):
    status: int
    description: str = ""
    docuType: str = ""
    ocrResult: dict = {}
    msg: str = ""
    detail: str = ""
    status_code: str = ""
    exc: Exception = None
    request_id: str
    request_at: str
    response_id: str
    response_time: str


class GeneralOcrResponse(BaseModel):
    image_height: int
    image_width: int
    num_instances: int
    page: int
    result: List[dict]


class SuccessfulResponse(BaseModel):
    code: str
    request_id: str
    request_at: str
    response_at: str
    response_time: str
    ocr_result: List[OcrResult]


class ParameterError(BaseModel):
    code: str
    error_message: str


class BusinessRegistration(BaseModel):
    cbr_regnum_business: str
    cbr_regnum_corp: str
    cbr_name: str
    cbr_address_business: str
    cbr_address_headquarter: str
    cbr_work_type: str
    cbr_work_cond: str


class UniqueNumber(BaseModel):
    cun_regnum_business: str
    cun_name: str
    cun_address_business: str


class CopyOfPassbook(BaseModel):
    bb_account_num: str
    bb_account_holder: str
    bb_bank: str


class ResidentRegistrationCardAndOverseasNationalRegistrationCard(BaseModel):
    rrc_title: str
    rrc_name: str
    rrc_regnum: str
    rrc_issue_date: str


class DriverLicense(BaseModel):
    dlc_title: str
    dlc_name: str
    dlc_regnum: str
    dlc_issue_date: str
    dlc_license_num: str
    dlc_exp_date: str


class AlienRegistrationCardAndForeignNationalityResidenceReportAndPermanentResidenceCard(BaseModel):
    arc_title: str
    arc_name: str
    arc_regnum: str
    arc_issue_date: str


class Passport(BaseModel):
    pp_title: str
    pp_name: str
    pp_regnum: str
    pp_issue_date: str


class CertificateOfAllCorporateRegistrationDetails(BaseModel):
    ccr_title: str
    ccr_issue_date: str
    ccr_num_pages: str
    ccr_issued_stock: str


class SealCertificate(BaseModel):
    crs_issue_date: str
