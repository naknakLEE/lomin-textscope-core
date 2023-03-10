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

html = """

<!DOCTYPE html>

<html>

    <head>

        <title>Chat</title>

    </head>

    <body>

        <h1>WebSocket Chat</h1>

        <h2>Your ID: <span id="ws-id"></span></h2>

        <form action="" onsubmit="sendMessage(event)">

            <input type="text" id="messageText" autocomplete="off"/>

            <button>Send</button>

        </form>

        <ul id='messages'>

        </ul>

        <script>

            var client_id = Date.now()

            document.querySelector("#ws-id").textContent = client_id;

            var ws = new WebSocket(`ws://localhost:8000/ws/eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJndWVzdEBsb21pbi5haSIsInNjb3BlcyI6W10sImV4cCI6MTY1Mzk4ODE1M30.dk8FnLCBhLwMMSt5RP5QtkmvMqesgRKWC5eEWSwK0zc`);

            ws.onmessage = function(event) {

                var messages = document.getElementById('messages')

                var message = document.createElement('li')

                var content = document.createTextNode(event.data)

                message.appendChild(content)

                messages.appendChild(message)

            };

            function sendMessage(event) {

                var input = document.getElementById("messageText")

                ws.send(input.value)

                input.value = ''

                event.preventDefault()

            }

        </script>

    </body>

</html>
"""

def get_html_content() -> str:
    return  (
        """
            <!DOCTYPE html>
            <html>
                <head>
                    <title>textscope ws moniotr</title>
                </head>
                <body>
                    <h2>Your ID: <span id="ws-id"></span></h2>
                    <form action="" onsubmit="sendMessage(event)">
                        <input type="text" id="messageText" autocomplete="off"/>
                        <button>Send</button>
                    </form>
                    <ul id='messages'>
                    </ul>
                    <script>
                        var client_id = Date.now()
                        document.querySelector("#ws-id").textContent = client_id;
                        var ws = new WebSocket(`ws://localhost:8000/ws/eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJndWVzdEBsb21pbi5haSIsInNjb3BlcyI6W10sImV4cCI6MTY1Mzk4ODE1M30.dk8FnLCBhLwMMSt5RP5QtkmvMqesgRKWC5eEWSwK0zc`);
                        ws.onmessage = function(event) {
                            var messages = document.getElementById('messages')
                            var message = document.createElement('li')
                            var content = document.createTextNode(event.data)
                            message.appendChild(content)
                            messages.appendChild(message)
                        };
                        function sendMessage(event) {
                            var input = document.getElementById("messageText")
                            ws.send(input.value)
                            input.value = ''
                            event.preventDefault()
                        }
                    </script>
                </body>
            </html>
            """
            # .replace("Tws_urlS", ws_url)
            # .replace("Tteam_nameS", team_name)
    )
    
@router.get("/test/client2")
async def get():
    return HTMLResponse(get_html_content())

@router.get("/test/client")
async def get():
    return HTMLResponse(html)

@router.websocket("/{token}")
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
                # raise "???????????? json ????????? ????????????."
                # await manager.send_message_to({"data":"???????????? json ????????? ????????????."},websocket,  token_user.id)
                await websocket.send_text(f"{response_data}: ???????????? json ????????? ????????????.")
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
                
            elif method == "inspect_status": # ??? ??????
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
                data = {"rx_msg": "?????? ?????? ???????????? ????????????."}
            
            # await manager.send_message_to(json.dumps(data, ensure_ascii=False), user_id = token_user.id)
            await websocket.send_text(json.dumps(data, ensure_ascii=False))
            # await manager.broadcast(f"{user_id}  Send a message :{data}")
            # await manager.send_personal_message(f" Server reply {user_id}: The message you sent is :{data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket, token_user.id)
        # await manager.broadcast(f"{user_id}  Left the chat room ")

# TODO ????????? ?????? ??????, ?????? ?????? ????????? ???????????? ?????? ??????
# @router.websocket("/login/{team_name}/{sso_emp_num}") # ?????? ?????? ??? ????????? ??????????????? ??????
# async def get_login_status(websocket: WebSocket, team_name: str, sso_emp_num: int):
#     await login_status_manager.connect(websocket, team_name, sso_emp_num)
#     try:
#         while True:
#             try:
#                 response_data = await websocket.receive_json()
#             except:
#                 raise WebSocketDisconnect
            
#             method = get_method_in_ws_message(response_data)
            
#             if method == "logon_emp":
#                 active_list = login_status_manager.get_login_info_emp_num(response_data.get("emp_num", []))
                
#             elif method == "logon_team":
#                 active_list = login_status_manager.get_login_info_team_name(response_data.get("team_name", []))
            
            
#             data = dict(method=method, emp_num=active_list)
#             await websocket.send_text(json.dumps(data, ensure_ascii=False))
            
#     except WebSocketDisconnect:
#         login_status_manager.disconnect(team_name, sso_emp_num)
        

# @router.websocket("/inspect/{team_name}/{sso_emp_num}") # ?????? ?????? ?????? ??????
# async def get_login_status(websocket: WebSocket, sso_emp_num: int):
#     await inspect_status_manager.connect(websocket, sso_emp_num)
#     try:
#         while True:
#             try:
#                 response_data = await websocket.receive_json()
#             except:
#                 raise WebSocketDisconnect
            
#             method = get_method_in_ws_message(response_data)
#             data = dict()
            
#             if method == "check_working_inspect":
#                 message = inspect_status_manager.get_inspect_info(response_data.get("inspect_num", []))
#                 data = dict(method=method, inspect_num=message)
                
#             elif method == "start_inspect": # ??? ??????
#                 result, inspector = inspect_status_manager.start_inspect(response_data.get("inspect_num", -1), sso_emp_num)
#                 data = dict(method=method, result=result, inspector=inspector)
                
#             elif method == "stop_inspect": # ??? ??????
#                 result, inspector = inspect_status_manager.stop_inspect(response_data.get("inspect_num", -1))
#                 data = dict(method=method, result=result, inspector=inspector)
            
            
#             await websocket.send_text(json.dumps(data, ensure_ascii=False))
            
#     except WebSocketDisconnect:
#         inspect_status_manager.disconnect(sso_emp_num)



def get_method_in_ws_message(response_data: dict) -> str:
    return response_data.get("func", "")