import json

from typing import List, Dict, Tuple
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: Dict[int, WebSocket] = dict()
        self.active_team: Dict[str, List[int]] = dict()
        self.active_inspect: Dict[int, int] = dict()

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections.update(dict({user_id: WebSocket}))
        
        team_name = 1 # TODO DB에서 팀 가져오기
        emp_num_list = self.active_team.get(team_name)
        if emp_num_list is None:
            self.active_team.update(dict({team_name:list()}))
        
        self.active_team.get(team_name).append(user_id)

    def disconnect(self, websocket: WebSocket, user_id: int):
        self.active_connections.pop(user_id)
        
        team_name = 1 # TODO DB에서 팀 가져오기
        self.active_team.get(team_name, []).remove(user_id)
        if len(self.active_team.get(team_name, [])) == 0:
            self.active_team.pop(team_name)
    
    def get_login_info_emp_num(self, user_list: List[int]) -> List[int]:
        active_list = list()
        
        if len(user_list) == 0:
            user_list = self.active_connections.keys()
        
        for user in user_list:
            if user in self.active_connections.keys():
                active_list.append(user)
        
        return active_list
    
    
    def get_login_info_team_name(self, team_name_list: List[str]) -> Dict[str, List[int]]:
        active_list = dict()
        
        if len(team_name_list) == 0:
            team_name_list = self.active_team.keys()
        
        for team_name in team_name_list:
            active_list.update(dict({
                team_name:self.active_team.get(team_name, [])
            }))
        
        return active_list

    def get_inspect_info(self, inspect_id_list: List[int]) -> List[int]:
        active_list = list()
        
        if len(inspect_id_list) == 0:
            inspect_id_list = self.active_inspect.keys()
        
        for inspect_id in inspect_id_list:
            if inspect_id in self.active_inspect.keys():
                active_list.append(inspect_id)
        
        return active_list
    
    def start_inspect(self, inspect_id: int, sso_emp_num: int) -> Tuple[bool, int]:
        inspector = self.active_inspect.get(inspect_id)
        
        if inspector is None:
            self.active_inspect.update(dict({inspect_id:sso_emp_num}))
            return (True, sso_emp_num)
        
        else:
            return (False, inspector)
    
    
    def stop_inspect(self, inspect_id: int, sso_emp_num: int) -> Tuple[bool, int]:
        isActive = self.active_inspect.get(inspect_id)
        
        if isActive is not None:
            self.active_inspect.pop(inspect_id)
            return (True, sso_emp_num)
        
        else:
            return (False, -1)

    async def send_message_to(self, message: str, websocket: WebSocket, user_id: int):
        dest_websocket = self.active_connections.get(user_id, None)
        if dest_websocket is not None:
            await dest_websocket.send_text(data=json.dumps(message, ensure_ascii=False))

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

# TODO 필중님 작업 사항, 추후 상위 코드가 완벽하면 제거 예정
# class SocketManager:
#     def __init__(self) -> None:
#         # Dict[사원번호, 웹소켓]
#         self.active_connections: Dict[int, WebSocket] = dict()
    
#     async def connect(self, websocket: WebSocket, user: int) -> None:
#         await websocket.accept()
#         self.active_connections.update(dict({user: WebSocket}))
    
    
#     def disconnect(self, user) -> None:
#         self.active_connections.pop(user)
    
    
#     def get_websocket(self, user: int) -> WebSocket:
#         return self.active_connections.get(user, None)
    
    
#     async def send_message_to(self, user: int, message: dict) -> None:
#         dest_websocket = self.active_connections.get(user, None)
#         if dest_websocket is not None:
#             await dest_websocket.send_text(json.dumps(message, ensure_ascii=False))
    
    
#     def get_login_info_emp_num(self, user_list: List[int]) -> List[int]:
#         active_list = list()
        
#         if len(user_list) == 0:
#             user_list = self.active_connections.keys()
        
#         for sso_emp_num in user_list:
#             if sso_emp_num in self.active_connections.keys():
#                 active_list.append(sso_emp_num)
        
#         return active_list



# class LoginStatusManager(SocketManager):
#     # Dict[팀이름, 리스트[사원번호]]
#     active_team: Dict[str, List[int]] = dict()
    
    
#     async def connect(self, websocket: WebSocket, team_name: str, sso_emp_num: int):
#         await super().connect(websocket, sso_emp_num)
        
#         emp_num_list = self.active_team.get(team_name)
#         if emp_num_list is None:
#             self.active_team.update(dict({team_name:list()}))
        
#         self.active_team.get(team_name).append(sso_emp_num)
    
    
#     def disconnect(self, team_name: str, sso_emp_num: int):
#         super().disconnect(sso_emp_num)
        
#         self.active_team.get(team_name, []).remove(sso_emp_num)
#         if len(self.active_team.get(team_name, [])) == 0:
#             self.active_team.pop(team_name)
    
    
#     def get_login_info_team_name(self, team_name_list: List[str]) -> Dict[str, List[int]]:
#         active_list = dict()
        
#         if len(team_name_list) == 0:
#             team_name_list = self.active_team.keys()
        
#         for team_name in team_name_list:
#             active_list.update(dict({
#                 team_name:self.active_team.get(team_name, [])
#             }))
        
#         return active_list


# class InspectStatusManager(SocketManager):
#     # Dict[업무번호?, 사원번호]
#     active_inspect: Dict[int, int] = dict()
    
#     def get_inspect_info(self, inspect_id_list: List[int]) -> List[int]:
#         active_list = list()
        
#         if len(inspect_id_list) == 0:
#             inspect_id_list = self.active_inspect.keys()
        
#         for inspect_id in inspect_id_list:
#             if inspect_id in self.active_inspect.keys():
#                 active_list.append(inspect_id)
        
#         return active_list
    
    
#     def start_inspect(self, inspect_id: int, sso_emp_num: int) -> Tuple[bool, int]:
#         inspector = self.active_inspect.get(inspect_id)
        
#         if inspector is None:
#             self.active_inspect.update(dict({inspect_id:sso_emp_num}))
#             return (True, sso_emp_num)
        
#         else:
#             return (False, inspector)
    
    
#     def stop_inspect(self, inspect_id: int, sso_emp_num: int) -> Tuple[bool, int]:
#         isActive = self.active_inspect.get(inspect_id)
        
#         if isActive is not None:
#             self.active_inspect.pop(inspect_id)
#             return (True, sso_emp_num)
        
#         else:
#             return (False, -1)
