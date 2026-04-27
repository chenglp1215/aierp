import logging
from typing import Optional, Dict, Any, List, Callable

from .config import AgentConfig
from .llm import llm_client
from .tools import tool_registry, ToolResult, SkillAsTool
from models.auth import User

logger = logging.getLogger(__name__)


ToolCallback = Callable[[str, Dict[str, Any]], Any]
ToolResultCallback = Callable[[Dict[str, Any]], Any]
TextCallback = Callable[[str], None]
FormResultCallback = Callable[[Dict[str, Any]], Any]



class Agent:
    def __init__(self, config: AgentConfig):
        self.config = config
        self.tools = tool_registry.get_tools(self.config.tools_range)
        self._conversation_history: List[Dict[str, str]] = []

    async def initialize(self) -> None:
        logger.info(f"Initializing agent: {self.config.name}")

    async def chat(
        self,
        user_message: str,
        session_id: Optional[str] = None,
        user: Optional[User] = None,
        stream_callback: Optional[Callable[[str], None]] = None,
        user_permissions: Optional[List[str]] = None
    ) -> str:
        messages = self._build_messages(user_message)
        tools = await self._get_tools_with_skills(user_permissions)
        logger.info(f"【chat: 加载工具列表】 {[t.get('function', {}).get('name') for t in tools]}, 共 {len(tools)} 个工具")

        try:
            if stream_callback:
                full_response = ""
                async for token in llm_client.chat_stream(
                    messages=messages,
                    model_name=self.config.model_name,
                    tools=tools if len(tools) > 0 else None
                ):
                    full_response += token
                    await stream_callback(token)
                return full_response
            else:
                response = await llm_client.chat(
                    messages=messages,
                    model_name=self.config.model_name,
                    stream=False,
                    tools=tools if len(tools) > 0 else None
                )
                return response

        except Exception as e:
            logger.error(f"Agent chat error: {e}")
            raise

    async def chat_with_tools_stream(
        self,
        user_message: str,
        session_id: Optional[str] = None,
        user: Optional[User] = None,
        stream_callback: Optional[Callable[[str], None]] = None,
        tool_call_callback: Optional[ToolCallback] = None,
        tool_result_callback: Optional[ToolResultCallback] = None,
        user_permissions: Optional[List[str]] = None
    ) -> str:
        messages = self._build_messages(user_message)
        tools = await self._get_tools_with_skills(user_permissions)
        logger.info(f"【chat_with_tools_stream: 加载工具列表】 {[t.get('function', {}).get('name') for t in tools]}, 共 {len(tools)} 个工具")

        full_response = ""
        max_turns = 10
        current_turn = 0

        while current_turn < max_turns:
            current_turn += 1

            has_tool_call = False
            accumulated_content = ""
            async for chunk in llm_client.chat_with_tools_stream(
                messages=messages,
                model_name=self.config.model_name,
                tools=tools if len(tools) > 0 else None
            ):
                chunk_type = chunk.get("type")
                if chunk_type == "tool_call":
                    has_tool_call = True
                    tool_name = chunk.get("name")
                    tool_args = chunk.get("args", {})
                    tool_call_id = chunk.get("id", f"call_{current_turn}")
                    tool = tool_registry.get(tool_name)
                    tool_cn_name = tool.cn_name or tool_name
                    if tool_call_callback:
                        await tool_call_callback(tool_cn_name, tool_args)

                    if tool:
                        try:
                            tool_result = await tool.execute_with_validation(**tool_args)
                        except Exception as e:
                            logger.error(f"Tool {tool_cn_name} execution failed: {e}")
                            tool_result = ToolResult(success=False, content="", error=str(e))
                    else:
                        tool_result = ToolResult(success=False, content="", error="Tool not found")

                    result_data = {
                        "tool": tool_cn_name,
                        "success": tool_result.success,
                        "content": tool_result.content,
                        "error": tool_result.error
                    }
                    if tool_result_callback:
                        await tool_result_callback(result_data)

                    assistant_msg = {
                        "role": "assistant",
                        "content": accumulated_content,
                        "tool_calls": [{
                            "id": tool_call_id,
                            "name": tool_name,
                            "args": tool_args
                        }]
                    }
                    messages.append(assistant_msg)
                    self._conversation_history.append(assistant_msg)

                    tool_result_content = tool_result.content if tool_result.success else f"Error: {tool_result.error}"
                    tool_msg = {
                        "role": "tool",
                        "content": tool_result_content,
                        "tool_call_id": tool_call_id,
                        "name": tool_name
                    }
                    messages.append(tool_msg)
                    self._conversation_history.append(tool_msg)

                elif chunk_type == "content":
                    content = chunk.get("content", "")
                    accumulated_content += content
                    full_response += content
                    if stream_callback:
                        await stream_callback(content)

            if not has_tool_call:
                if accumulated_content:
                    assistant_msg = {
                        "role": "assistant",
                        "content": accumulated_content
                    }
                    messages.append(assistant_msg)
                    self._conversation_history.append(assistant_msg)
                break

        if current_turn >= max_turns:
            logger.warning(f"Max tool call turns ({max_turns}) reached")

        return full_response

    async def chat_with_tools(
        self,
        user_message: str,
        session_id: Optional[str] = None,
        user: Optional[User] = None,
        tool_call_callback: Optional[ToolCallback] = None,
        tool_result_callback: Optional[ToolResultCallback] = None,
        text_callback: Optional[TextCallback] = None,
        form_result_callback: Optional[FormResultCallback] = None,
        user_permissions: Optional[List[str]] = None
    ) -> str:
        messages = self._build_messages(user_message)
        tools = await self._get_tools_with_skills(user_permissions)
        logger.info(f"【chat_with_tools: 加载工具列表】 共 {len(tools)} 个工具， 分别是：{[tool['function']['name'] for tool in tools]}")
        self.add_to_history("user", user_message)
        
        last_response = ""
        max_turns = 10
        current_turn = 0

        while current_turn < max_turns:
            current_turn += 1

            llm_result = await llm_client.chat_with_tools(
                messages=messages,
                model_name=self.config.model_name,
                tools=tools if len(tools) > 0 else None
            )

            content = llm_result.get("content", "")
            if content and text_callback:
                await text_callback(content)
                last_response = content
            tool_calls = llm_result.get("tool_calls", [])

            if not tool_calls:
                break

            for tc_idx, tc in enumerate(tool_calls):
                tool_name = tc.get("name")
                tool_args = tc.get("args", {})
                tool_call_id = tc.get("id", f"call_{current_turn}_{tc_idx}")
                logger.info(f"【chat_with_tools: 工具调用】tool_name: {tool_name} tool_call_id: {tool_call_id}")
                tool = tool_registry.get(tool_name)
                tool_cn_name = tool.cn_name or tool_name

                if tool_call_callback:
                    await tool_call_callback(tool_cn_name, tool_args)

                if tool:
                    try:
                        logger.info(f"【chat_with_tools: 调用工具】 {tool_cn_name}({tool_args})")
                        tool_result = await tool.execute_with_validation(**tool_args)
                    except Exception as e:
                        logger.error(f"Tool {tool_cn_name} execution failed: {e}")
                        tool_result = ToolResult(success=False, content="", error=str(e))
                else:
                    tool_result = ToolResult(success=False, content="", error="Tool not found")

                result_data = {
                    "tool": tool_cn_name,
                    "success": tool_result.success,
                    "content": tool_result.content,
                    "error": tool_result.error
                }
                if tool_result_callback:
                    await tool_result_callback(result_data)

                assistant_msg = {
                    "role": "assistant",
                    "content": content,
                    "tool_calls": [{
                        "id": tool_call_id,
                        "name": tool_name,
                        "args": tool_args
                    }]
                }
                messages.append(assistant_msg)
                self._conversation_history.append(assistant_msg)

                tool_result_content = tool_result.content if tool_result.success else f"Error: {tool_result.error}"
                tool_msg = {
                    "role": "tool",
                    "content": tool_result_content,
                    "tool_call_id": tool_call_id,
                    "name": tool_name
                }
                messages.append(tool_msg)
                self._conversation_history.append(tool_msg)
        if current_turn >= max_turns:
            logger.warning(f"Max tool call turns ({max_turns}) reached")

        if last_response and text_callback:
            self.add_to_history("assistant", last_response)


    def _build_messages(self, user_message: str) -> List[Dict[str, str]]:
        messages = []

        from app.agent.prompts import GLOBAL_SYSTEM_PROMPT
        if GLOBAL_SYSTEM_PROMPT:
            messages.append({
                "role": "system",
                "content": GLOBAL_SYSTEM_PROMPT
            })
        if self.config.system_prompt:
            messages.append({
                "role": "system",
                "content": self.config.system_prompt
            })

        for msg in self._conversation_history:
            messages.append(msg)

        messages.append({
            "role": "user",
            "content": user_message
        })

        return messages

    async def _get_tools_with_skills(self, user_permissions: List[str] = None) -> List[Dict[str, Any]]:
        skill_names = []
        if self.config.skill_ids:
            from services.ai_service import skill_service
            skill_datas = await skill_service.get_skills_by_ids(self.config.skill_ids)
            for skill_data in skill_datas:
                skill_tool = SkillAsTool(skill_data)
                tool_registry.register(skill_tool)
                skill_names.append(skill_data.get("name", ""))

        if self.config.tools_range:
            tools_range = list(set(self.config.tools_range + skill_names))
        elif skill_names:
            tools_range = skill_names
        else:
            tools_range = []
        logger.info(f"_get_tools_with_skills: 加载工具中】 agent的tools范围：{tools_range}， 用户权限：{user_permissions}")
        schemas = tool_registry.get_tools(tools_range, user_permissions)
        return schemas

    def add_to_history(self, role: str, content: str) -> None:
        self._conversation_history.append({
            "role": role,
            "content": content
        })

        if len(self._conversation_history) > 50:
            self._conversation_history = self._conversation_history[-50:]

    def clear_history(self) -> None:
        self._conversation_history = []

    def get_history(self) -> List[Dict[str, str]]:
        return self._conversation_history.copy()
