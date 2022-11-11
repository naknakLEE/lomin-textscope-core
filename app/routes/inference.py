import uuid
import os

from httpx import Client

from typing import Dict
from fastapi import APIRouter, Body, Depends
from pathlib import Path
from datetime import datetime
from datetime import timedelta
from sqlalchemy.orm import Session

from app import hydra_cfg
from app.wrapper import pp, pipeline, settings
from app.schemas.json_schema import inference_responses
from app.utils.utils import get_pp_api_name, set_json_response, get_ts_uuid
from app.utils.logging import logger
from app.database.connection import db
from app.utils.pdf2txt import get_pdf_text_info
from typing import Dict
from fastapi import APIRouter, BackgroundTasks, Body, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from sqlalchemy.orm import Session

from app.schemas.json_schema import inference_responses
from app.models import UserInfo as UserInfoInModel
from app.utils.utils import set_json_response, get_pp_api_name, pretty_dict
from app.utils.logging import logger
from app.wrapper import pp, pipeline, settings
from app.database import query, schema
from app.database.connection import db
from app.schemas import error_models as ErrorResponse
from app.errors import exceptions as ex
if hydra_cfg.route.use_token:
    from app.utils.auth import get_current_active_user as get_current_active_user
else:
    from app.utils.auth import get_current_active_user_fake as get_current_active_user


router = APIRouter()


# TODO: 토큰을 이용한 유저 체크 부분 활성화
@router.post("/ocr", status_code=200, responses=inference_responses)
def ocr(
    *,
    request: Request,
    inputs: Dict = Body(...),
    current_user: UserInfoInModel = Depends(get_current_active_user),
    session: Session = Depends(db.session),
) -> Dict:
    """
    ### 토큰과 파일을 전달받아 모델 서버에 ocr 처리 요청
    입력 데이터: 토큰, ocr에 사용할 파일 <br/>
    응답 데이터: 상태 코드, 최소 퀄리티 보장 여부, 신뢰도, 문서 타입, ocr결과(문서에 따라 다른 결과 반환)
    """
    start_time = datetime.now()
    response_log: Dict = dict()
    user_email = current_user.email
    log_id = inputs.get("log_id", get_ts_uuid("log"))
    document_id = inputs.get("document_id")
    document_path = inputs.get("document_path")
    target_page = inputs.get("page", 1)
    
    
    # parameter mapping:
    # web -> inference
    #   docx -> image
    # web -> pp
    #   log -> task
    inputs["image_id"] = document_id
    inputs["image_path"] = document_path
    task_id = log_id
    
    logger.info("#0-1 inference start at {}", datetime.now())
    logger.info("#0-2 start document_id: {}", document_id)
    logger.info("#0-3 document_filename: {}", document_path.split("/")[-1])
    
    logger.info ("[{}] #1-1 try select user info from db", datetime.now())
    select_user_result = query.select_user(session, user_email=user_email)
    logger.info ("[{}] #1-2 end select user info from db (result: {})", datetime.now(), select_user_result)
    
    if isinstance(select_user_result, JSONResponse):
        return select_user_result
    select_user_result: schema.UserInfo = select_user_result
    user_team: str = select_user_result.user_team
    
    logger.info ("[{}] #2-1 try select log info from db", datetime.now())
    select_log_result = query.select_log(session, log_id=task_id) 
    if isinstance(select_log_result, schema.LogInfo):
        status_code, error = ErrorResponse.ErrorCode.get(2202)
        return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
    elif isinstance(select_log_result, JSONResponse):
        status_code_no_log, _ = ErrorResponse.ErrorCode.get(2201)
        if select_log_result.status_code != status_code_no_log:
            return select_log_result
    logger.info ("[{}] #2-2 end select log info from db (result: {})", datetime.now(), select_log_result)
    
    # logger.debug(f"{task_id}-api request start:\n{pretty_dict(inputs)}")
    
    logger.info ("[{}] #3-1 try insert log info to db", datetime.now())
    insert_log_result = query.insert_log(
        session=session,
        log_id=task_id,
        user_email=user_email,
        user_team=user_team,
        log_content=dict({"request": inputs})
    )
    logger.info ("[{}] #3-2 end insert log info to db (result: {})", datetime.now(), insert_log_result)
    if isinstance(insert_log_result, JSONResponse):
        return insert_log_result
    
    # task_pkey = insert_task_result.task_pkey
    
    if (
        inputs.get("use_general_ocr")
        and Path(inputs.get("image_path", "")).suffix in [".pdf", ".PDF"]
        and inputs.get("use_text_extraction")
    ):
        parsed_text_info, image_size = get_pdf_text_info(inputs)
        if len(parsed_text_info) > 0:
            return JSONResponse(
                content=jsonable_encoder(
                    {
                        "inference_results": parsed_text_info,
                        "response_log": {"original_image_size": image_size},
                    }
                )
            )
    
    with Client() as client:
        if os.environ.get('WEB_PP_BYPASS', 'False').lower() in ('true', '1', 't'):
            status_code = 200
            inference_results = {'rec_preds': [[164, 1703, 259, 1033, 2358, 2, 2, 2, 1647, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [1587, 1695, 1661, 1661, 160, 1033, 2358, 2, 1627, 803, 2, 112, 399, 27, 33, 32, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [1216, 2358, 2, 1627, 803, 2, 2, 1627, 803, 2, 2, 2128, 1647, 2181, 2, 1347, 2, 1493, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [1204, 1502, 1661, 1033, 2358, 2, 2, 2, 1647, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [1355, 2308, 1878, 1356, 102, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [2148, 2325, 2, 1627, 803, 2, 542, 1577, 1486, 1059, 1597, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [1355, 1878, 80, 1948, 100, 1577, 254, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [1990, 638, 2, 1120, 2, 1120, 2, 1541, 649, 1541, 649, 1541, 649, 1541, 649, 1541, 649, 1541, 649, 1541, 649, 1541, 649, 1541, 2, 2, 2, 1541, 649, 1541, 2, 2, 2], [1355, 1649, 2, 1627, 803, 2, 112, 399, 217, 1912, 1519, 1698, 2, 1627, 803, 2, 1649, 2, 1541, 865, 1783, 427, 2, 1541, 865, 1783, 427, 2, 2, 2, 2, 2, 2], [1530, 1313, 1782, 77, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [1033, 2358, 2, 1647, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [1577, 254, 2, 1627, 803, 2, 112, 399, 217, 870, 2, 1627, 803, 2, 2, 2, 1013, 2, 1647, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [1033, 2358, 2, 2, 1647, 2, 2, 532, 1647, 2, 532, 1647, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [1033, 2358, 2, 2, 1647, 2, 2, 532, 1647, 2, 532, 1647, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [81, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [81, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [81, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [81, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [81, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [81, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [81, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [1695, 2266, 1904, 865, 2, 1120, 1125, 1013, 2, 1120, 1125, 1013, 2, 1120, 1125, 1013, 2, 1120, 1125, 1013, 2, 542, 1017, 532, 865, 2, 1785, 535, 2, 2, 1013, 2, 2], [81, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [81, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [5, 12, 4, 11, 11, 8, 6, 10, 4, 2, 1629, 2, 1632, 1647, 2, 2, 1785, 822, 73, 10, 74, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [81, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [6, 5, 11, 12, 5, 4, 12, 9, 7, 10, 2, 1629, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [1887, 1650, 2108, 1356, 73, 1751, 74, 2, 1627, 803, 2, 542, 1063, 532, 2, 81, 2, 81, 2, 81, 2, 81, 2, 1649, 2, 2, 2, 2, 2, 2, 2, 2, 2], [4, 6, 78, 13, 4, 6, 78, 8, 8, 11, 11, 2, 1627, 803, 2, 5, 4, 4, 1033, 263, 2, 2, 2, 2, 1647, 2, 2, 2, 2, 2, 2, 2, 2], [6, 4, 6, 6, 78, 5, 4, 78, 5, 13, 2, 1627, 803, 2, 542, 1577, 1486, 1059, 1597, 2, 81, 2, 81, 2, 1649, 2, 2, 2, 2, 2, 2, 2, 2], [1647, 1584, 2317, 2, 1627, 803, 2, 112, 399, 27, 33, 32, 2, 18, 2, 33, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [9, 9, 6, 9, 78, 11, 10, 75, 75, 78, 75, 75, 75, 75, 78, 13, 12, 7, 10, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [4, 13, 7, 9, 4, 11, 6, 9, 2, 1642, 2, 1627, 803, 2, 542, 1063, 532, 2, 44, 53, 59, 48, 40, 51, 2, 81, 2, 2, 2, 2, 2, 2, 2], [81, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [81, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [4, 8, 78, 1240, 1588, 78, 4, 8, 13, 9, 11, 2, 1629, 2, 2, 189, 2, 1647, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [5, 77, 4, 4, 4, 1597, 2, 1642, 2, 1647, 2, 2, 1647, 2, 2, 19, 22, 33, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [84, 2, 2, 1647, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [6, 7, 77, 4, 4, 4, 1597, 2, 1642, 2, 1647, 2, 2, 1647, 2, 2, 19, 22, 33, 73, 1751, 74, 2, 1347, 2, 1347, 2, 2, 2, 2, 1647, 2, 2], [1751, 1264, 1240, 2, 2, 1642, 2, 1120, 2, 1120, 2, 1120, 1125, 1013, 2, 1120, 1125, 1013, 2, 2235, 1647, 1347, 2181, 2, 1347, 2097, 1650, 792, 1033, 2358, 2, 2, 2], [2303, 1577, 1503, 509, 2, 2, 2, 1541, 854, 532, 2, 1002, 1647, 1541, 2, 1541, 522, 2, 1541, 522, 2, 1347, 2, 2, 2, 1541, 865, 2, 2, 2, 2, 2, 2], [73, 5, 5, 11, 7, 74, 78, 73, 8, 8, 9, 13, 80, 8, 5, 5, 6, 74, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [5, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 74, 2, 2, 2, 2, 2, 2, 2, 2], [73, 1063, 191, 1584, 74, 2, 2, 2, 2, 19, 22, 33, 73, 1751, 74, 2, 81, 2, 81, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [4, 4, 8, 13, 7, 6, 11, 4, 7, 8, 2, 1629, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [4, 7, 81, 7, 10, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [6, 8, 2, 2, 1647, 2, 2, 2, 1647, 2, 2, 2, 1647, 2, 2, 2, 2, 1647, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [1358, 2310, 1990, 638, 2, 1120, 2, 1541, 649, 1541, 649, 1541, 649, 1541, 649, 1541, 649, 1541, 649, 1541, 649, 1541, 2, 2, 2, 1541, 649, 1541, 2, 2, 2, 2, 2], [5, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 74, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [107, 1204, 2314, 522, 532, 2, 2, 1647, 2, 2, 1647, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [5, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 74, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [1502, 956, 212, 2148, 1120, 2, 1013, 2, 542, 1017, 532, 79, 2, 1647, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [77, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [24, 52, 2, 2, 1647, 2, 1642, 2, 1120, 2, 1120, 2, 1541, 1647, 2, 2, 532, 1647, 2, 2, 2, 2, 2, 1647, 2, 2, 2, 2, 2, 2, 2, 1647, 2], [12, 1597, 2, 1642, 1597, 2, 189, 2, 1647, 532, 79, 2, 532, 79, 2, 1649, 2, 81, 2, 81, 2, 81, 2, 81, 2, 81, 2, 81, 2, 81, 2, 2, 2], [5, 10, 8, 8, 78, 5, 5, 12, 12, 74, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [164, 1703, 1474, 66, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [1695, 2368, 1033, 2358, 2, 2, 2, 2, 1647, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [1878, 771, 1033, 2358, 2, 2, 2, 2, 1647, 2, 2, 1647, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [136, 758, 1650, 1356, 2, 2, 2, 2, 1647, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [164, 1703, 1577, 254, 81, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [2195, 902, 522, 1120, 1775, 2235, 1647, 2, 1120, 2, 1120, 2, 1120, 2, 1541, 865, 2, 1541, 865, 2, 1541, 865, 2, 1541, 865, 2, 1541, 865, 2, 2, 2, 2, 2], [1530, 1313, 1782, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [4, 7, 81, 5, 13, 78, 4, 7, 81, 7, 10, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [1240, 1588, 7, 7, 14, 57, 11, 8, 9, 10, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [73, 41, 48, 65, 55, 40, 64, 79, 59, 53, 54, 53, 44, 64, 79, 42, 54, 79, 50, 57, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [6, 4, 79, 7, 6, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1647, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2], [4, 4, 4, 1597, 2, 1627, 803, 2, 81, 4, 4, 78, 4, 6, 81, 4, 4, 2, 81, 4, 4, 2, 2, 81, 4, 4, 2, 2, 2, 2, 2, 2, 2]], 'scores': [0.8891149759292603, 0.880352258682251, 0.7041519284248352, 0.8196187615394592, 0.8897390961647034, 0.8244819045066833, 0.903386652469635, 0.8299564719200134, 0.8081455230712891, 0.923951268196106, 0.3241223394870758, 0.7558534145355225, 0.7129824161529541, 0.6441364288330078, 0.5485408306121826, 0.4747833013534546, 0.4540792405605316, 0.49780768156051636, 0.4446125328540802, 0.43223217129707336, 0.5539547204971313, 0.9303896427154541, 0.5492526888847351, 0.5797664523124695, 0.8888874053955078, 0.39043018221855164, 0.8307523131370544, 0.788895308971405, 0.8551278710365295, 0.8471376895904541, 0.872670590877533, 0.5494321584701538, 0.6861048340797424, 0.5601540207862854, 0.6012898683547974, 0.8181435465812683, 0.7920676469802856, 0.3589800298213959, 0.7064439058303833, 0.9130068421363831, 0.9415910243988037, 0.7866745591163635, 0.5165955424308777, 0.8529680371284485, 0.8082984089851379, 0.6722063422203064, 0.6126193404197693, 0.8458729386329651, 0.5026041865348816, 0.8692017793655396, 0.4297051727771759, 0.9356495141983032, 0.3058856129646301, 0.6834235787391663, 0.7114976048469543, 0.883945643901825, 0.8666329979896545, 0.5131120085716248, 0.5640947222709656, 0.5408759713172913, 0.523714542388916, 0.588046133518219, 0.4736063778400421, 0.5185397267341614, 0.5774422883987427, 0.5531896352767944, 0.42838045954704285, 0.7504929304122925], 'boxes': [[735, 1303, 1070, 1432], [737, 1420, 1211, 1563], [748, 1568, 1084, 1690], [750, 1687, 1091, 1817], [762, 2198, 1115, 2353], [765, 2489, 915, 2623], [766, 2339, 1221, 2481], [769, 2835, 917, 2961], [782, 2969, 926, 3106], [858, 3386, 1099, 3520], [951, 1865, 1089, 1940], [972, 2479, 1131, 2609], [977, 2823, 1137, 2954], [983, 2961, 1152, 3100], [1101, 1314, 1133, 1397], [1114, 1571, 1145, 1655], [1119, 1704, 1148, 1781], [1122, 1831, 1154, 1912], [1126, 1956, 1156, 2038], [1130, 2087, 1160, 2166], [1135, 2215, 1168, 2307], [1136, 3372, 1425, 3512], [1148, 2490, 1181, 2576], [1158, 2835, 1192, 2924], [1162, 1294, 1470, 1412], [1168, 2973, 1200, 3064], [1173, 1680, 1517, 1802], [1175, 1534, 1576, 1673], [1182, 1920, 1567, 2053], [1185, 2059, 1532, 2178], [1196, 3096, 1416, 3227], [1223, 2781, 1903, 2946], [1228, 2946, 1518, 3083], [1242, 1436, 1272, 1518], [1244, 2349, 1279, 2434], [1282, 1399, 1739, 1533], [1341, 2453, 1592, 2587], [1402, 2229, 1444, 2260], [1405, 2318, 1691, 2446], [1445, 3086, 1662, 3213], [1455, 3362, 1746, 3503], [1501, 1252, 2090, 1399], [1547, 2942, 1587, 3066], [1552, 1140, 1820, 1266], [1556, 1653, 1913, 1775], [1559, 2047, 1741, 2165], [1583, 2581, 1826, 2782], [1611, 2928, 1908, 3069], [1672, 2177, 1711, 2299], [1695, 3064, 2075, 3212], [1718, 2315, 1757, 2429], [1772, 3345, 2139, 3490], [1829, 2709, 1890, 2785], [1938, 2166, 2022, 2292], [2091, 2296, 2207, 2424], [2137, 3477, 2494, 3628], [2163, 3337, 2415, 3477], [746, 1942, 1096, 2082], [747, 1820, 1097, 1947], [751, 2078, 1108, 2203], [766, 2663, 1385, 2835], [790, 3516, 1331, 3695], [1188, 1154, 1527, 1284], [1194, 2178, 1649, 2327], [1216, 1775, 1997, 1935], [1360, 3496, 2073, 3683], [1727, 2168, 1927, 2299], [1880, 2573, 2374, 2787]], 'classes': ['text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text', 'text'], 'response_log': {'recognition_preprocess_start_time': '2022-11-11 23:12:28', 'recognition_preprocess_end_time': '2022-11-11 23:12:28', 'recognition_start_time': '2022-11-11 23:12:28', 'recognition_input_dim': [68, 3, 32, 200], 'recognition_output_dim': [68, 33, 2490], 'recognition_end_time': '2022-11-11 23:12:28', 'recognition_total_time': 0.285833, 'inference_end_time': '2022-11-11 23:12:28.856'}, 'doc_type': 'None', 'image_height': 4032, 'image_width': 3024, 'image_height_origin': 4032, 'image_width_origin': 3024, 'request_id': None, 'angle': 0.0, 'id_type': '', 'texts': ['결제기번호', '운전자자격번호', '상호', '사업자번호', '승하차시간', '통행', '승차/추가요금', '카드', '승인', '영수증,', '번호', '요금', '번호', '번호', ':', ':', ':', ':', ':', ':', ':', '전표처리', ':', ':', '180774260', ':', '2178108536', '창일택시(주)', '02-902-4477', '2022-10-19', '이용해', '5525-76**-****-9836', '09350725', ':', ':', '04-서울-04957', '1,000원', '=', '23,000원', '주셔서', '필요없는', '(1173)-(4459/4112)', '1', '(보관용)', '0049327034', '03:36', '24', '신한카드', '1', '감사합니다', '1', '업무교통비', ',', 'Km', '8원', '1644-1188)', '결제앱!', '전화번호', '차량번호', '거래일시', '결제요금:', '티머니비즈페이', '영수증', '03:19-03:36', '서울33Ar7456', '(bizpay.tnoney.co.kr', '20.32', '000원']}
            response_log = {'inference_start_time': '2022-11-11 23:12:22.671', 'inference_end_time': '2022-11-11 23:12:28.885', 'inference_total_time': 6.214149}
        else:
            # Inference
            logger.info ("[{}] #4-1 try inference pipline({})", datetime.now(), settings.USE_OCR_PIPELINE)
            if settings.USE_OCR_PIPELINE == 'multiple':
                # TODO: sequence_type을 wrapper에서 받도록 수정
                # TODO: python 3.6 버전에서 async profiling 사용에 제한이 있어 sync로 변경했는데 추후 async 사용해 micro bacing 사용하기 위해서는 다시 변경 필요
                status_code, inference_results, response_log = pipeline.multiple(
                    client=client,
                    inputs=inputs,
                    sequence_type="kv",
                    response_log=response_log,
                )
                response_log = dict()
            elif settings.USE_OCR_PIPELINE == 'duriel':
                status_code, inference_results, response_log = pipeline.heungkuk_life(
                    client=client,
                    inputs=inputs,
                    response_log=response_log,
                    route_name=inputs.get("route_name", "ocr"),
                )
            elif settings.USE_OCR_PIPELINE == 'single':
                status_code, inference_results, response_log = pipeline.single(
                    client=client,
                    inputs=inputs,
                    response_log=response_log,
                    route_name=inputs.get("route_name", "ocr"),
                )
        logger.info ("[{}] #4-2 try inference pipline({}) (status code: {})", datetime.now(), settings.USE_OCR_PIPELINE, status_code)
        
        if isinstance(status_code, int) and (status_code < 200 or status_code >= 400):
            status_code, error = ErrorResponse.ErrorCode.get(3501)
            return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
        
        # inference_result: response 생성에 필요한 값, inference_results: response 생성하기 위한 과정에서 생성된 inference 결과 포함한 값
        inference_result = inference_results
        if "kv_result" in inference_results:
            inference_result = inference_results.get("kv_result", {})
        # logger.debug(f"{task_id}-inference results:\n{inference_results}")
        
        
        # convert preds to texts
        if (
            inputs.get("convert_preds_to_texts") is not None
            and "texts" not in inference_results
        ):
            
            logger.info("[{}] #5-1 try convert rec_preds to texts", datetime.now())
            status_code, texts = pp.convert_preds_to_texts(
                client=client,
                rec_preds=inference_results.get("rec_preds", []),
            )
            logger.info("[{}] #5-2 end convert rec_preds to texts (pp response status code: {})", datetime.now(), status_code)
            
            if status_code < 200 or status_code >= 400:
                status_code, error = ErrorResponse.ErrorCode.get(3503)
                return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
            inference_results["texts"] = texts

        # TODO: pp에서 tsbl_sort를 못할경우 얘를 쓰자
        # tsbl_sort_result = sort_text_tblr(inference_result)
        doc_type_code = inference_results.get("doc_type")
        
        # Post processing
        # 미래과학아카데미는 ocr일경우 줄글 pp로 이동
        if inputs.get("route_name", "ocr") == 'ocr':
            
            logger.info("[{}] #6-1 try general_pp for fsa", datetime.now())
            if os.environ.get('WEB_SERVING_BYPASS', 'False').lower() in ('true', '1', 't'):
                status_code = 200
                post_processing_results = {'result': {'text': {'text': '영수증 (보관용) 결제기번호 : 180774260 (1173)-(4459/4112) 운전자자격번호 : 04-서울-04957 상호 : 창일택시(주) 사업자번호 : 2178108536 0049327034 차량번호 번호 : 서울33Ar7456 전화번호 : 02-902-4477 거래일시 : 2022-10-19 03:36 = 승하차시간 : 03:19-03:36 1 20.32 Km 승차/추가요금 : 23,000원 1 8원 통행 요금 : 1,000원 결제요금: 24 000원 , 카드 번호 : 5525-76**-****-9836 승인 번호 : 09350725 1 신한카드 이용해 주셔서 감사합니다 영수증, 전표처리 필요없는 업무교통비 결제앱! 티머니비즈페이 (bizpay.tnoney.co.kr 1644-1188)', 'score': 0.6778206470258096, 'class': 'text', 'box': [735.0, 1140.0, 2494.0, 3695.0], 'merged_count': 68}}, 'texts': ['결제기번호', '운전자자격번호', '상호', '사업자번호', '승하차시간', '통행', '승차/추가요금', '카드', '승인', '영수증,', '번호', '요금', '번호', '번호', ':', ':', ':', ':', ':', ':', ':', '전표처리', ':', ':', '180774260', ':', '2178108536', '창일택시(주)', '02-902-4477', '2022-10-19', '이용해', '5525-76**-****-9836', '09350725', ':', ':', '04-서울-04957', '1,000원', '=', '23,000원', '주셔서', '필요없는', '(1173)-(4459/4112)', '1', '(보관용)', '0049327034', '03:36', '24', '신한카드', '1', '감사합니다', '1', '업무교통비', ',', 'Km', '8원', '1644-1188)', '결제앱!', '전화번호', '차량번호', '거래일시', '결제요금:', '티머니비즈페이', '영수증', '03:19-03:36', '서울33Ar7456', '(bizpay.tnoney.co.kr', '20.32', '000원']}
                response_log = {'inference_start_time': '2022-11-11 23:12:22.671', 'inference_end_time': '2022-11-11 23:12:28.885', 'inference_total_time': 6.214149, 'post_processing_start_time': '2022-11-11 23:16:39', 'post_processing_end_time': '2022-11-do11 23:16:39', 'post_processing_time': timedelta(microseconds=35087)}
            status_code, post_processing_results, response_log = pp.post_processing(
                client=client,
                task_id=task_id,
                response_log=response_log,
                inputs=inference_result,
                post_processing_type="general_pp",
            )            
            logger.info("[{}] #6-2 end general_pp for fs (pp response status code: {})", datetime.now(), status_code)
            
            if status_code < 200 or status_code >= 400:
                status_code, error = ErrorResponse.ErrorCode.get(3502)
                return JSONResponse(status_code=status_code, content=jsonable_encoder({"error":error}))
            
            text_merged = post_processing_results.get('result').get('text').get('text')

            inference_results.update({
                "text_merged": text_merged
            })                

    
    response_log.update(inference_results.get("response_log", {}))
    logger.info(f"OCR api total time: \t{datetime.now() - start_time}")

    inference_id = get_ts_uuid("inference")
    doc_type_code = inference_results.get("doc_type")
    
    # doc_type_code로 doc_type_index 조회
    
    logger.info("[{}] #7-1 try select doc type info from db", datetime.now())
    select_doc_type_result = query.select_doc_type(session, doc_type_code=doc_type_code)
    logger.info("[{}] #7-2 end select doc type info from db (doc_type: {})", datetime.now(), type(select_doc_type_result))
    
    if isinstance(select_doc_type_result, JSONResponse):
        return select_doc_type_result
    select_doc_type_result: schema.DocTypeInfo = select_doc_type_result
    doc_type_idx = select_doc_type_result.doc_type_idx

    inference_results.update(doc_type=select_doc_type_result)

    logger.info("[{}] #8-1 try insert inference_result to db", datetime.now())
    insert_inference_result = query.insert_inference(
        session=session,
        inference_id=inference_id,
        document_id=document_id, 
        user_email=user_email,
        user_team=user_team,
        inference_result=inference_results,
        inference_type=inputs.get("inference_type"),
        page_num=inference_results.get("page", target_page),
        doc_type_idx=doc_type_idx,
        response_log=response_log
    )
    logger.info("[{}] #8-2 end isnert inference_result to db (result: {})", datetime.now(), type(insert_inference_result))
    
    if isinstance(insert_inference_result, JSONResponse):
        return insert_inference_result
    insert_inference_result: schema.InferenceInfo = insert_inference_result
    inference_results.update(doc_type=insert_inference_result.inference_result.get("doc_type", dict()))
    
    
    response = dict(
        response_log=response_log,
        inference_results=inference_results,
        resource_id=dict(
            # log_id=task_id
        )
    )
    
    logger.info("#9-1 inference end at {}", datetime.now())
    logger.info("#9-2 end document_id: {}", document_id)
    
    return JSONResponse(content=jsonable_encoder(response))


# @TODO utils로 이동
def sort_text_tblr(inference_result: dict) -> Dict[str, list]:
    t_list = inference_result.get("texts", [])
    b_list = inference_result.get("boxes", [])
    s_list = inference_result.get("scores", [])
    c_list = inference_result.get("classes", [])
    
    s_list = s_list if len(s_list) > 0 else [ 0.0 for i in range(len(t_list)) ]
    c_list = c_list if len(c_list) > 0 else [ "" for i in range(len(t_list)) ]
    
    tbsc_list = [ (t, b, s, c) for t, b, s, c in zip(t_list, b_list, s_list, c_list) ]
    
    tbsc_list.sort(key= lambda x : (x[1][1], x[1][0]))
    
    t_list_, b_list_, s_list_, c_list_ = (list(), list(), list(), list())
    for tbsc in tbsc_list:
        t_list_.append(tbsc[0])
        b_list_.append(tbsc[1])
        s_list_.append(tbsc[2])
        c_list_.append(tbsc[3])
    
    return dict(
        texts=t_list_,
        boxes=b_list_,
        scores=s_list_,
        classes=c_list_
    )
