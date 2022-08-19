from fastapi import Depends, APIRouter, HTTPException, Body, Response
from sqlalchemy.orm import Session
import base64

from app.utils.auth import get_current_active_user
from app.database.connection import db
from app.common.const import get_settings

from app import models
from app.utils.drm import DRM


settings = get_settings()
router = APIRouter()
drm = DRM()


@router.post("/encryption")
async def post_drm_encryption(
    params: dict = Body(...),
    session: Session = Depends(db.session),
    current_user: models.UserInfo = Depends(get_current_active_user),
) -> Response:
    
    file_data: str = params.get("file")
    filename: str = params.get("file_name")
    
    encrypted_file = await drm.drm_encryption(base64_data=file_data, file_name=filename, user_email=current_user.email)
    
    
    return Response(
        content=base64.b64decode(encrypted_file), 
        headers={'Content-Disposition': f'attachment; filename="{filename}"'},
        media_type="application/vnd.ms-excel"
    )
