from fastapi import APIRouter, WebSocket
from fastapi.responses import HTMLResponse
from fastapi import Depends

from sqlalchemy.orm import Session
from app.database.connection import db
from app.common.const import get_settings
from app.utils.websocket_manager import (
    ConnectionManager
)
from app.service.websocket import websocket_endpoint as websocket_endpoint_service

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
    
    return await websocket_endpoint_service(
        websocket = websocket, 
        token = token, 
        session = session
    )
    
    