import copy
import json
import logging
from typing import Optional, Dict, Any, List, AsyncIterator
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage, ToolMessage

from .config import LLMConfig, ModelConfig

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self):
        self._config: Optional[LLMConfig] = None
        self._models: Dict[str, ModelConfig] = {}
        self._llm_instances: Dict[str, ChatOpenAI] = {}

    async def load_config(self) -> None:
        from services.ai_service import llm_config_service, llm_service

        config_data = await llm_config_service.get_config()
        if config_data:
            self._config = LLMConfig(**config_data)
        else:
            self._config = LLMConfig()

        models_data = await llm_service.list_models(1, 100)
        for model in models_data.get("items", []):
            model_config = ModelConfig(
                model_id=model["id"],
                name=model["name"],
                model_type=model["model_type"],
                status=model.get("status", "active")
            )
            self._models[model["id"]] = model_config

        logger.info(f"LLM config loaded: default_model={self._config.default_model}, models={len(self._models)}")

    def _get_llm(self, model_name: Optional[str] = None, config_override: Optional[Dict[str, Any]] = None) -> ChatOpenAI:
        if self._config is None:
            raise RuntimeError("LLM config not loaded")

        target_model = model_name or self._config.default_model

        cache_key = f"{target_model}"
        if config_override:
            cache_key += "_" + "_".join(f"{k}={v}" for k, v in sorted(config_override.items()))

        if cache_key in self._llm_instances:
            return self._llm_instances[cache_key]

        model_kwargs = {
            "model": target_model,
            "temperature": self._config.temperature,
            "max_tokens": self._config.max_tokens,
            "top_p": self._config.top_p,
            "frequency_penalty": self._config.frequency_penalty,
            "presence_penalty": self._config.presence_penalty,
            "timeout": self._config.timeout,
        }

        if self._config.api_key:
            model_kwargs["api_key"] = self._config.api_key
        if self._config.api_base_url:
            model_kwargs["base_url"] = self._config.api_base_url

        if config_override:
            model_kwargs.update(config_override)

        llm = ChatOpenAI(**model_kwargs)
        self._llm_instances[cache_key] = llm
        return llm

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model_name: Optional[str] = None,
        stream: bool = True,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None
    ) -> str:
        llm = self._get_llm(model_name)

        langchain_messages = self._build_messages(messages)

        if tools:
            params = {"tools": tools}
            if tool_choice:
                params["tool_choice"] = tool_choice
        else:
            params = {}

        response = await llm.agenerate([langchain_messages], **params)
        return response.generations[0][0].text

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model_name: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None
    ) -> AsyncIterator[str]:
        llm = self._get_llm(model_name)

        langchain_messages = self._build_messages(messages)

        if tools:
            params = {"tools": tools}
            if tool_choice:
                params["tool_choice"] = tool_choice
        else:
            params = {}

        try:
            async for chunk in llm.astream(langchain_messages, **params):
                if chunk.content:
                    yield chunk.content
        except Exception as e:
            logger.error(f"LLM stream error: {e}")
            raise

    async def chat_with_tools_stream(
        self,
        messages: List[Dict[str, str]],
        model_name: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        llm = self._get_llm(model_name)

        langchain_messages = self._build_messages(messages)

        params: Dict[str, Any] = {"tools": tools} if tools else {}

        pending_tool_calls = {}

        try:
            async for chunk in llm.astream(langchain_messages, **params):
                if hasattr(chunk, "tool_call_chunks") and chunk.tool_call_chunks:
                    for tc_chunk in chunk.tool_call_chunks:
                        if tc_chunk.get("type") == "tool_call_chunk":
                            tool_name = tc_chunk.get("name", "")
                            tool_args_str = tc_chunk.get("args", "{}")
                            tool_id = tc_chunk.get("id", "")

                            pending_tool_calls[tool_id] = {
                                "name": tool_name,
                                "args": tool_args_str,
                                "id": tool_id
                            }

                if chunk.content:
                    yield {"type": "content", "content": chunk.content}

                if hasattr(chunk, "response_metadata") and chunk.response_metadata:
                    finish_reason = chunk.response_metadata.get("finish_reason", "")
                    if finish_reason == "tool_calls":
                        last_chunk_has_tool_calls = True

                if hasattr(chunk, "chunk_position") and chunk.chunk_position == "last":
                    if pending_tool_calls:
                        for tool_id, tool_call in pending_tool_calls.items():
                            try:
                                args_dict = json.loads(tool_call["args"]) if tool_call["args"] else {}
                            except:
                                args_dict = {}

                            yield {
                                "type": "tool_call",
                                "name": tool_call["name"],
                                "args": args_dict,
                                "id": tool_id
                            }
                        pending_tool_calls = {}

        except Exception as e:
            logger.error(f"LLM chat_with_tools_stream error: {e}")
            raise

    async def chat_with_tools(
        self,
        messages: List[Dict[str, str]],
        model_name: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        llm = self._get_llm(model_name)

        langchain_messages = self._build_messages(messages)

        params: Dict[str, Any] = {"tools": tools} if tools else {}

        response = await llm.agenerate([langchain_messages], **params)
        generation = response.generations[0][0]

        result = {"content": generation.text}

        if hasattr(generation, "message") and hasattr(generation.message, "tool_calls"):
            if generation.message.tool_calls:
                tool_calls = []
                for tc in generation.message.tool_calls:
                    tool_calls.append({
                        "name": tc["name"],
                        "args": tc["args"]
                    })
                result["tool_calls"] = tool_calls

        return result

    def _build_messages(self, messages: List[Dict[str, str]]) -> List[BaseMessage]:
        result = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                result.append(SystemMessage(content=content))
            elif role == "user":
                result.append(HumanMessage(content=content))
            elif role == "assistant":
                tool_calls = msg.get("tool_calls", [])
                if tool_calls:
                    ai_msg = AIMessage(content=content)
                    ai_msg.tool_calls = copy.deepcopy(tool_calls)
                    result.append(ai_msg)
                else:
                    result.append(AIMessage(content=content))
            elif role == "tool":
                tool_call_id = msg.get("tool_call_id", "")
                tool_name = msg.get("name", "")
                result.append(ToolMessage(content=content, tool_call_id=tool_call_id, name=tool_name))

        return result

    def get_config(self) -> Optional[LLMConfig]:
        return self._config

    def get_models(self) -> Dict[str, ModelConfig]:
        return self._models


llm_client = LLMClient()
