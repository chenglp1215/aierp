import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional
import logging
from jose import JWTError, jwt

from services.ws_manager import ws_manager
from config import settings
from models.auth import TokenPayload
from services.auth_service import auth_service
from app.agent import agent_manager

logger = logging.getLogger(__name__)

ws_router = APIRouter(tags=["WebSocket"])


@ws_router.websocket("/chat/{agent_id}")
async def websocket_chat(
    websocket: WebSocket,
    agent_id: str,
    user_id: Optional[str] = Query(default=None, description="用户ID"),
    token: Optional[str] = Query(default=None, description="认证Token")
):
    """WebSocket聊天接口"""
    logger.info(f"【WebSocket chat request】: {user_id}, {agent_id}")

    if not user_id:
        await websocket.close(code=4001, reason="Missing user_id")
        return

    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        token_data = TokenPayload(**payload)

        user = await auth_service.get_user_by_id(token_data.sub)
        if not user:
            await websocket.close(code=4002, reason="User not found")
            return

        if user.get("status") != "active":
            await websocket.close(code=4003, reason="User is disabled")
            return

    except JWTError as e:
        logger.error(f"JWT validation failed: {e}")
        await websocket.close(code=4004, reason="Invalid token")
        return

    connection_key = await ws_manager.connect(websocket, user_id, agent_id)
    logger.info(f"【WebSocket chat connected】: {connection_key}")

    agent = agent_manager.get_agent(agent_id)

    user_permissions = user.get("permissions", []) if user else []
    if "super_admin" in [each_role.get("code") for each_role in user.get("roles", [])]:
        user_permissions = None
    try:
        start = True

        while True:
            if start:
                data = "介绍下你自己, 并推荐一些提交创建类的相关功能"
                start = False
            else:
                data = await websocket.receive_text()

            try:
                message_data = json.loads(data)
            except json.JSONDecodeError:
                message_data = {"type": "text", "content": data}

            message_type = message_data.get("type", "text")
            content = message_data.get("content", "")
            files = message_data.get("files", [])

            if message_type == "ping":
                await websocket.send_json({"type": "pong", "content": ""})
                continue

            if not agent:
                await websocket.send_json({
                    "type": "error",
                    "content": f"Agent {agent_id} not found",
                    "agent_id": agent_id
                })
                continue

            try:
                if message_type == "clear_history":
                    agent.clear_history()
                    await websocket.send_json({
                        "type": "system",
                        "content": "对话历史已清除",
                        "agent_id": agent_id
                    })
                    continue

                if message_type == "image" or files:
                    content = f"[用户上传了{len(files)}个文件] {content}"

                if message_type == "voice":
                    content = f"[用户发送了语音消息] {content}"

                async def tool_call_callback(tool_name: str, tool_args: dict):
                    try:
                        await websocket.send_json({
                            "type": "tool_call_start",
                            "tool": tool_name,
                            "args": tool_args,
                            "agent_id": agent_id
                        })
                    except Exception as e:
                        logger.error(f"Send tool_call_start failed: {e}")

                async def tool_result_callback(result: dict):
                    try:
                        await websocket.send_json({
                            "type": "tool_call_end",
                            "tool": result.get("tool"),
                            "success": result.get("success"),
                            "content": result.get("content"),
                            "error": result.get("error"),
                            "agent_id": agent_id
                        })
                    except Exception as e:
                        logger.error(f"Send tool_call_end failed: {e}")
                
                async def text_callback(result: str):
                    try:
                        await websocket.send_json({
                            "type": "text",
                            "content": result,
                            "agent_id": agent_id
                        })
                    except Exception as e:
                        logger.error(f"Send text failed: {e}")

                async def form_result_callback(result: dict):
                    try:
                        await websocket.send_json({
                            "type": "form_result",
                            "form_data": result.get("form_data"),
                            "content": result.get("content"),
                            "submit_tool": result.get("submit_tool"),
                            "agent_id": agent_id
                        })
                    except Exception as e:
                        logger.error(f"Send form_result failed: {e}")
                try:
                    await agent.chat_with_tools(
                        user_message=content,
                        session_id=connection_key,
                        user=user,
                        tool_call_callback=tool_call_callback,
                        tool_result_callback=tool_result_callback,
                        text_callback=text_callback,
                        form_result_callback=form_result_callback,
                        user_permissions=user_permissions,
                    )
                except Exception as e:
                    logger.error(f"Agent chat error for {connection_key}: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "content": f"处理消息失败: {str(e)}",
                        "agent_id": agent_id
                    })
                    continue

            except Exception as e:
                logger.error(f"Agent chat error for {connection_key}: {e}")
                await websocket.send_json({
                    "type": "error",
                    "content": f"处理消息失败: {str(e)}",
                    "agent_id": agent_id
                })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {connection_key}")
    except Exception as e:
        logger.error(f"WebSocket error for {connection_key}: {e}")
    finally:
        await ws_manager.disconnect(user_id, agent_id)


@ws_router.get("/ws/status")
async def ws_status():
    return {
        "status": "running",
        "active_connections": ws_manager.get_connection_count()
    }
