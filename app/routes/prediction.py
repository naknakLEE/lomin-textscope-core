from fastapi import APIRouter, Depends
from starlette.responses import JSONResponse

from sqlalchemy.orm import Session

from app import models
from app.database.connection import db
from app.common.const import get_settings
from app.utils.auth import get_current_active_user

from app.service.prediction import (
    get_all_prediction as get_all_prediction_service,
    get_cls_kv_prediction as get_cls_kv_prediction_service,
    get_gocr_prediction as get_gocr_prediction_service,
    get_document_info_inference_pdf as get_document_info_inference_pdf_service
)

settings = get_settings()
router = APIRouter()

@router.get("/")
def get_all_prediction(
    session: Session = Depends(db.session)
) -> JSONResponse:
    return get_all_prediction_service(session = session)
    


@router.get("/cls-kv")
def get_cls_kv_prediction(
    task_id: str, visualize: bool, session: Session = Depends(db.session)
) -> JSONResponse:
    return get_cls_kv_prediction_service(
        task_id = task_id,
        visualize = visualize,
        session = session
    )


@router.get("/gocr")
def get_gocr_prediction(
    task_id: str, visualize: bool, session: Session = Depends(db.session)
) -> JSONResponse:
    return get_gocr_prediction_service(
        task_id = task_id,
        visualize = visualize,
        session = session
    )

@router.get("/download/documents/pdf")
def get_document_info_inference_pdf(
    document_id:   str,
    pdf_file_name:      str,
    text_type:     str,
    apply_inspect: bool,
    session: Session = Depends(db.session),
    current_user: models.UserInfo = Depends(get_current_active_user)
):
    """
    특정 문서의 gocr 또는 kv 인식 결과를 searchablePDF로 저장합니다.
    """
    return get_document_info_inference_pdf_service(
        document_id=document_id,
        pdf_file_name=pdf_file_name,
        text_type=text_type,
        apply_inspect=apply_inspect,
        session=session,
        current_user=current_user
    )