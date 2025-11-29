from starlette.websockets import WebSocketState
from fastapi import WebSocket
from master_agent.base import SystemMessageStructure, WebSocketMessageToClient
import json 
from typing import Any

class ConnectionManager:
    def __init__(self, logger):
        self.logger = logger
        self.logger.info("Initializing ConnectionManager")
        self.active_connections: list[WebSocket] = []
        self.user_id_mapping: dict[str, Any] = {}
        self.user_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def add_user_connection(self, user_id, websocket: WebSocket):
        self.user_connections[user_id] = websocket

    def remove_user_connection(self, user_id):
        if user_id in self.user_connections:
            self.logger.info(f"Removing websocket connection for {user_id}")
            del self.user_connections[user_id]

    async def disconnect(self, user_id, websocket: WebSocket):
        if websocket in self.active_connections:
            self.logger.info(f"Disconnecting websocket for {user_id}")
            self.active_connections.remove(websocket)

        if user_id in self.user_id_mapping:
            self.logger.info(f"Removing user_id mapping for {user_id}")
            del self.user_id_mapping[user_id]
        
        self.remove_user_connection(user_id)
        
    def is_connected(self, websocket: WebSocket) -> bool:
        return websocket.application_state == WebSocketState.CONNECTED
    
    def set_master_instance(self, user_id, master_instance:Any):
        self.user_id_mapping[user_id] = master_instance

    def get_master_instance(self, user_id)->Any | None:
        if user_id not in self.user_id_mapping:
            return None
        
        return self.user_id_mapping[user_id]

    async def send_message(self, message: str, websocket: WebSocket):
        if self.is_connected(websocket):
            try:
                await websocket.send_text(message)
            except Exception as e:
                self.logger.error(f"Error sending message: {e}")
        else:
            self.logger.warning(f"WebSocket is not connected. Cannot send message: {message}")

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await self.send_message(message, connection)


# async def start_websocket_server(app):
#     config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
#     server = uvicorn.Server(config)
#     await server.serve()

# async def start_websocket(app):
#     uvicorn_task = asyncio.create_task(start_websocket_server(app))
#     await asyncio.sleep(5)  # Wait for 5 seconds to ensure WebSocket server is up
#     await uvicorn_task

async def send_data(data:WebSocketMessageToClient, manager:ConnectionManager):
    json_data = data.model_dump_json()
    await manager.broadcast(json_data)

async def send_system_data(system_data, system_message_type, manager:ConnectionManager):
    if 'system_message_type' not in system_data:
        data:SystemMessageStructure = SystemMessageStructure()
        data.system_message_type = system_message_type
        data.system_message = system_data.model_dump_json()
    else:
        data = system_data
    
    json_str = data.model_dump_json()
    json_data = json.loads(json_str)
    message = json.dumps(json_data)
    await manager.broadcast(message)


