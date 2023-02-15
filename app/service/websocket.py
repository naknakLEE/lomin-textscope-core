import json

from typing import List, Dict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse
from starlette.responses import JSONResponse
from fastapi import Depends, Query, status

from sqlalchemy.orm import Session
from app.utils.auth import ws_get_token2user
from app.database.connection import db
from app.common.const import get_settings
from app.utils.logging import logger
from app.utils.websocket_manager import (
    ConnectionManager
)

manager = ConnectionManager()
settings = get_settings()
router = APIRouter()


def get_method_in_ws_message(response_data: dict) -> str:
    return response_data.get("func", "")

async def websocket_endpoint(
    websocket: WebSocket,
    token: str,
    session: Session = Depends(db.session),
    ):
    
    
    if not token:
        return "Token does not exist."
    
    token_user = await ws_get_token2user(token=token, session=session)
    if not token_user:
        return "The token is invalid."
    
    await manager.connect(websocket, token_user.id)
    
    try:
        while True:
            response_data = await websocket.receive_text()
            try:
                response_data = json.loads(response_data)
            except ValueError:
                # raise "입력값이 json 형식이 아닙니다."
                # await manager.send_message_to({"data":"입력값이 json 형식이 아닙니다."},websocket,  token_user.id)
                await websocket.send_text(f"{response_data}: 입력값이 json 형식이 아닙니다.")
                continue
            method = get_method_in_ws_message(response_data)
                
            if method == "logon_user":
                # active_list = manager.get_login_info_team_name(response_data.get("team_name", []))
                # data = dict(method=method, emp_num=active_list)
                example_rx = {
                    "func": "logon_team",
                    "rx_msg": ["111", "222", "333"]
                    }
                data = example_rx
                
            
            elif method == "working_inspect":
                # message = manager.get_inspect_info(response_data.get("inspect_num", []))
                # data = dict(method=method, inspect_num=message)
                example_rx = {
                    "func": "working_inspect",
                    "rx_msg": {
                        "docs_1": "user_1",
                        "docs_2": "user_2"
                    }
                }
                data = example_rx
                
            elif method == "inspect_status": # 일 시작
                # result, inspector = manager.start_inspect(response_data.get("inspect_num", -1), token_user.id)
                # data = dict(method=method, result=result, inspector=inspector)
                example_rx = {
                    "func": "inspect_status",
                    "rx_msg":"success"
                }
                data = example_rx
                
            elif method == 'upload_document':
                example_rx = {
                    "func": "upload_document",
                    "rx_msg": "success"
                }
                data = example_rx

            else:
                data = {"rx_msg": "요청 값이 유효하지 않습니다."}
            
            # await manager.send_message_to(json.dumps(data, ensure_ascii=False), user_id = token_user.id)
            await websocket.send_text(json.dumps(data, ensure_ascii=False))
            # await manager.broadcast(f"{user_id}  Send a message :{data}")
            # await manager.send_personal_message(f" Server reply {user_id}: The message you sent is :{data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket, token_user.id)
        # await manager.broadcast(f"{user_id}  Left the chat room ")