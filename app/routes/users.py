from datetime import datetime
from typing import Any, Optional, List, Dict
from fastapi import Depends, APIRouter, Body
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic.networks import EmailStr
import urllib.parse

from app.database.connection import db
# from app.database.schema import Users, Usage
from app.utils.auth import get_password_hash
from app.errors import exceptions as ex
from app.schemas.json_schema import users_me_responses
from app import models
from app.models import UserInfo as UserInfoInModel
from app.schemas import error_models as ErrorResponse

from app.config import hydra_cfg
from app.database import query, schema
from app.utils.utils import is_admin
from app.service.user import get_user_info_by_user_email as get_user_info_by_user_email_service
if hydra_cfg.route.use_token:
    from app.utils.auth import get_current_active_user as get_current_active_user
else:
    from app.utils.auth import get_current_active_user_fake as get_current_active_user

router = APIRouter()


# 이메일 정보로 사원정보 조회
@router.get("/{user_email}")
def get_user_info_by_user_email(
    user_email:   str,
    session:      Session         = Depends(db.session),
    current_user: UserInfoInModel = Depends(get_current_active_user),
) -> JSONResponse:
    
    
    return get_user_info_by_user_email_service(
        user_email = user_email,
        session = session,
        current_user = current_user
    )