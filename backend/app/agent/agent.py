import logging
import asyncio
import inspect
from typing import Optional, Dict, Any, List, Callable
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import AIMessage
from langchain_core.outputs import LLMResult
from .config import AgentConfig
from .llm.config import LLMConfig
from .tools import tool_registry
from models_mysql.auth import User
from langchain_core.messages.tool import ToolMessage
from langchain_core.tools import StructuredTool
from app.agent.tools.base import BaseTool


logger = logging.getLogger(__name__)


class AgentCallbackHandler(BaseCallbackHandler):
    def __init__(
        self,
        text_callback: Optional[Callable[..., Any]] = None,
        tool_call_callback: Optional[Callable[..., Any]] = None,
        tool_result_callback: Optional[Callable[..., Any]] = None
    ):
        self.text_callback = text_callback
        self.tool_call_callback = tool_call_callback
        self.tool_result_callback = tool_result_callback

    async def on_tool_start(self, serialized: Dict[str, Any], input: Any, **kwargs):
        if self.tool_call_callback:
            tool_name = serialized.get("name", "") if serialized else ""
            logger.info(f"Tool start: {serialized}, input: {input}， kwargs: {kwargs}")
            await self.tool_call_callback(tool_name, input)

    async def on_tool_end(self, output: ToolMessage, **kwargs):
        if self.tool_result_callback:
            content_str = output.content
            logger.info(f"Tool end: content: {type(content_str)}， {content_str}")
            import json
            content = json.loads(content_str)
            tool_name = output.name
            result = {
                "tool": tool_name,
                "success": content.get("success"),
                "content": content.get("content"),
                "error": content.get("error") if not content.get("success") else None
            }
            await self.tool_result_callback(result)
    
    async def on_llm_end(self, response: LLMResult, **kwargs) -> None:
        """
        LLM 每次生成完成时触发。
        可以同时处理：
        - 中间节点的文字输出（如"我现在帮你调用工具xxx"）
        - 最终回答（当没有后续工具调用时）
        """
        if hasattr(response, 'generations') and response.generations:
            generation = response.generations[0][0]
            text = generation.text
            if text:
                # 判断是否是最终回答：检查是否有 tool_calls
                has_tool_calls = hasattr(generation, 'message') and hasattr(generation.message, 'tool_calls') and generation.message.tool_calls
                if has_tool_calls:
                    logger.info(f"[中间输出] 模型正在思考: {text[:100]}...")
                    if self.text_callback:
                        await self.text_callback(text)
                else:
                    logger.info(f"[最终回答] {text[:100]}...")   
                    if self.text_callback:
                        await self.text_callback(text)

class Agent:
    def __init__(self, config: AgentConfig):
        self.config = config
        self._conversation_history: List[Dict[str, str]] = []
        self._llm: Optional[ChatOpenAI] = None
        self._agent = None

    async def initialize(self) -> None:
        logger.info(f"Initializing agent: {self.config.name}")
        self._llm = await self._get_llm()
        self._agent = await self._create_agent()

    async def _get_llm(self) -> ChatOpenAI:
        from services.ai_service import llm_config_service

        config_data = await llm_config_service.get_config()
        llm_config = LLMConfig(**config_data) if config_data else LLMConfig()

        model_kwargs = {
            "model": self.config.model_name or llm_config.default_model,
            "temperature": self.config.temperature or llm_config.temperature,
            "max_tokens": self.config.max_tokens or llm_config.max_tokens,
        }

        if llm_config.api_key:
            model_kwargs["api_key"] = llm_config.api_key
        if llm_config.api_base_url:
            model_kwargs["base_url"] = llm_config.api_base_url

        return ChatOpenAI(**model_kwargs)

    async def _create_agent(self):
        tools = await self._get_tools()
        system_prompt = await self._build_system_prompt()

        return create_agent(
            model=self._llm,
            tools=tools,
            system_prompt=system_prompt
        )

    async def _get_tools(self) -> List[Any]:
        tools = tool_registry.get_tools(self.config.tools_range, None)
        return [self._create_agent_tool(s) for s in tools]

    def _create_agent_tool(self, tools: BaseTool) -> StructuredTool:
        exec_func = tools.execute
        tool_name = tools.name
        tool_description = tools.description
        parameters = tools.parameters
        tools = StructuredTool.from_function(
            func=None,
            coroutine=exec_func,
            name=tool_name,
            description=tool_description,
            args_schema=parameters
        )
        return tools

    async def _build_system_prompt(self) -> str:
        from app.agent.prompts import GLOBAL_SYSTEM_PROMPT
        parts = [p for p in [GLOBAL_SYSTEM_PROMPT, self.config.system_prompt] if p]
        return "\n\n".join(parts) or "You are a helpful AI assistant."

    def _format_messages(self) -> List:
        from app.agent.prompts import GLOBAL_SYSTEM_PROMPT

        messages = []
        if GLOBAL_SYSTEM_PROMPT:
            messages.append(("system", GLOBAL_SYSTEM_PROMPT))
        if self.config.system_prompt:
            messages.append(("system", self.config.system_prompt))

        for msg in self._conversation_history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                messages.append(("user", content))
            elif role == "assistant":
                messages.append(("assistant", content))
            elif role == "tool":
                messages.append(("tool", content, msg.get("tool_call_id", ""), msg.get("name", "")))

        return messages

    async def single_chat(
        self,
        user_message: str,
        file_path: Optional[str] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        if not self._agent:
            await self.initialize()
        messages= []
        if self.config.system_prompt:
            messages.append(("system", self.config.system_prompt))
        if system_prompt:
            messages.append(("system", system_prompt))

        if file_path:
            image_content = self._read_image_as_base64(file_path)
            if image_content:
                content = [
                    {"type": "text", "text": user_message or ""},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_content}"}}
                ]
                messages.append(("user", content))
            else:
                if user_message:
                    messages.append(("user", user_message))
        else:
            if user_message:
                messages.append(("user", user_message))

        result = await self._agent.ainvoke({"messages": messages})
        return result.get("messages", [[]])[-1].content

    def _read_image_as_base64(self, file_path: str) -> Optional[str]:
        """读取图片文件并转为 base64 编码"""
        import base64
        import os
        try:
            if os.path.exists(file_path):
                with open(file_path, "rb") as image_file:
                    return base64.b64encode(image_file.read()).decode("utf-8")
        except Exception as e:
            logger.error(f"读取图片文件失败: {file_path}, error: {e}")
        return None

    async def chat_with_tools(
        self,
        user_message: str,
        session_id: Optional[str] = None,
        user: Optional[User] = None,
        tool_call_callback: Optional[Callable[..., Any]] = None,
        tool_result_callback: Optional[Callable[..., Any]] = None,
        text_callback: Optional[Callable[..., Any]] = None,
        form_result_callback: Optional[Callable[..., Any]] = None,
        user_permissions: Optional[List[str]] = None
    ) -> str:
        if not self._agent:
            await self.initialize()

        self.add_to_history("user", user_message)
        messages = self._format_messages()
        messages.append(("user", user_message))

        callback_handler = AgentCallbackHandler(
            text_callback=text_callback,
            tool_call_callback=tool_call_callback,
            tool_result_callback=tool_result_callback
        )

        result = await self._agent.ainvoke(
            {"messages": messages},
            config={"callbacks": [callback_handler]}
        )

        output_messages = result.get("messages", [])
        response = ""
        for msg in output_messages:
            if isinstance(msg, AIMessage):
                response = msg.content
        if response:
            self.add_to_history("assistant", response)
        return response

    async def chat_with_tools_stream(
        self,
        user_message: str,
        session_id: Optional[str] = None,
        user: Optional[User] = None,
        stream_callback: Optional[Callable[..., Any]] = None,
        tool_call_callback: Optional[Callable[..., Any]] = None,
        tool_result_callback: Optional[Callable[..., Any]] = None,
        user_permissions: Optional[List[str]] = None
    ) -> str:
        return await self.chat_with_tools(
            user_message=user_message,
            session_id=session_id,
            user=user,
            tool_call_callback=tool_call_callback,
            tool_result_callback=tool_result_callback,
            text_callback=stream_callback,
            form_result_callback=None,
            user_permissions=user_permissions
        )

    def add_to_history(self, role: str, content: str) -> None:
        self._conversation_history.append({"role": role, "content": content})
        if len(self._conversation_history) > 50:
            self._conversation_history = self._conversation_history[-50:]

    def clear_history(self) -> None:
        self._conversation_history = []

    def get_history(self) -> List[Dict[str, str]]:
        return self._conversation_history.copy()
