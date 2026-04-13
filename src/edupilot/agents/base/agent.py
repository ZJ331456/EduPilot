"""统一 Agent 基类：所有智能体继承此类，支持流式响应和工具系统。"""

from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, List, Optional, Type

from edupilot.config.settings import get_settings
from edupilot.core.stream import ResponseBuilder, StreamBus, StreamEvent, EventType
from edupilot.core.protocol import (
    AgentMode,
    BaseTool,
    ToolDefinition,
    ToolResult,
    UnifiedContext,
    AgentResponse
)
from edupilot.services.llm import get_llm_client
from edupilot.services.prompt.loader import load_agent_prompt


@dataclass
class AgentConfig:
    """Agent 配置参数。"""
    name: str = "BaseAgent"
    temperature: float = 0.7
    max_tokens: int = 4096
    system_prompt: str = "你是一个智能学习助手。"
    streaming_enabled: bool = True
    tools_enabled: bool = True
    max_retries: int = 3
    retry_delay: float = 1.0


class BaseAgent(ABC):
    """
    统一 Agent 基类。

    设计原则：
    1. 所有 Agent 继承此类，获得统一的消息处理流程
    2. 支持流式和非流式两种响应模式
    3. 集成工具系统，可扩展工具调用
    4. 内置重试机制和错误处理
    5. 支持多步骤执行流程追踪

    使用方式：
    ```python
    class MyAgent(BaseAgent):
        async def _execute(self, ctx: UnifiedContext, builder: ResponseBuilder) -> str:
            # 实现具体逻辑
            return result
    ```
    """

    def __init__(self, config: Optional[AgentConfig] = None) -> None:
        self._config = config or self._default_config()
        self._llm = get_llm_client()
        self._tools: Dict[str, BaseTool] = {}
        self._bus = StreamBus()

    @abstractmethod
    def _default_config(self) -> AgentConfig:
        """返回默认配置（子类实现）。"""
        pass

    @property
    def name(self) -> str:
        """Agent 名称。"""
        return self._config.name

    @property
    def tools(self) -> Dict[str, BaseTool]:
        """已注册的工具字典。"""
        return self._tools

    def register_tool(self, tool: BaseTool) -> None:
        """注册工具。"""
        self._tools[tool.get_definition().name] = tool

    def unregister_tool(self, tool_name: str) -> None:
        """取消注册工具。"""
        self._tools.pop(tool_name, None)

    async def execute(
        self,
        ctx: UnifiedContext,
        builder: Optional[ResponseBuilder] = None,
        stream: bool = True
    ) -> str:
        """
        执行 Agent 主流程。

        Args:
            ctx: 统一上下文
            builder: 响应构建器（用于流式事件）
            stream: 是否启用流式响应

        Returns:
            最终响应内容
        """
        if builder is None:
            builder = ResponseBuilder(self._bus, ctx.session_id, self._config.name)

        await builder.start_message(message_type=ctx.mode.value)

        try:
            result = await self._execute(ctx, builder)
            await builder.end_message(metadata={"success": True})
            return result
        except Exception as e:
            await builder.send_error(str(e), error_code="EXECUTION_ERROR")
            await builder.end_message(metadata={"success": False, "error": str(e)})
            raise

    async def execute_stream(
        self,
        ctx: UnifiedContext
    ) -> AsyncGenerator[StreamEvent, None]:
        """
        流式执行接口，返回事件生成器。

        Args:
            ctx: 统一上下文

        Yields:
            StreamEvent 事件流
        """
        bus = StreamBus()
        builder = ResponseBuilder(bus, ctx.session_id, self._config.name)
        result = ""

        async def run():
            nonlocal result
            try:
                result = await self._execute(ctx, builder)
            except Exception as e:
                await builder.send_error(str(e), "EXECUTION_ERROR")

        task = asyncio.create_task(run())

        async for event in bus.subscribe(f"stream_{ctx.session_id}"):
            yield event

        await task

    @abstractmethod
    async def _execute(self, ctx: UnifiedContext, builder: ResponseBuilder) -> str:
        """
        核心执行逻辑（子类必须实现）。

        Args:
            ctx: 统一上下文
            builder: 响应构建器

        Returns:
            执行结果
        """
        pass

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = True
    ) -> AsyncGenerator[str, None] | str:
        """
        LLM 对话接口。

        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大 token 数
            stream: 是否流式

        Returns:
            流式模式返回生成器，否则返回完整字符串
        """
        temp = temperature if temperature is not None else self._config.temperature
        maxt = max_tokens or self._config.max_tokens

        if stream:
            return self._stream_chat(messages, temp, maxt)
        else:
            return await self._llm.chat(messages, temperature=temp, max_tokens=maxt)

    async def _stream_chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int
    ) -> AsyncGenerator[str, None]:
        """流式 LLM 调用。"""
        temp = []
        async for chunk in self._llm.stream_chat(messages, temperature=temperature, max_tokens=max_tokens):
            temp.append(chunk)
            yield chunk

    async def call_with_retry(
        self,
        func,
        *args,
        retries: Optional[int] = None,
        **kwargs
    ) -> Any:
        """
        带重试的函数调用。

        Args:
            func: 要执行的函数
            args: 位置参数
            retries: 重试次数
            kwargs: 关键字参数

        Returns:
            函数返回值
        """
        max_retries = retries or self._config.max_retries
        delay = self._config.retry_delay

        for attempt in range(max_retries):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(delay * (attempt + 1))

    def get_system_prompt(self, ctx: UnifiedContext) -> str:
        """获取系统提示词（可被子类重写）。"""
        return self._config.system_prompt

    def format_messages(
        self,
        ctx: UnifiedContext,
        system_override: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """格式化消息列表。"""
        msgs = []
        if system_override:
            msgs.append({"role": "system", "content": system_override})
        else:
            msgs.append({"role": "system", "content": self.get_system_prompt(ctx)})
        msgs.extend(ctx.to_llm_messages())
        return msgs


class SingleTurnAgent(BaseAgent):
    """
    单轮对话 Agent 基类。

    适用于简单的问答场景，如直接对话、用户画像分析等。
    """

    async def _execute(self, ctx: UnifiedContext, builder: ResponseBuilder) -> str:
        """执行单轮对话。"""
        await builder.start_step("llm_call")

        messages = self.format_messages(ctx)
        response = await self._llm.chat(
            messages,
            temperature=self._config.temperature,
            max_tokens=self._config.max_tokens
        )

        await builder.end_step("llm_call", result={"response_length": len(response)})
        return response


class MultiTurnAgent(BaseAgent):
    """
    多轮对话 Agent 基类。

    适用于复杂场景，支持多步骤执行和工具调用。
    """

    async def _execute(self, ctx: UnifiedContext, builder: ResponseBuilder) -> str:
        """执行多轮对话。"""
        steps = self._get_execution_steps(ctx)

        all_content = []
        for i, step in enumerate(steps):
            await builder.start_step(step["name"], step_index=i)

            result = await self._execute_step(step, ctx, builder)
            all_content.append(result)

            await builder.end_step(step["name"], result={"output": str(result)[:500]})

        return "\n\n".join(all_content)

    @abstractmethod
    def _get_execution_steps(self, ctx: UnifiedContext) -> List[Dict[str, Any]]:
        """获取执行步骤列表（子类实现）。"""
        pass

    @abstractmethod
    async def _execute_step(
        self,
        step: Dict[str, Any],
        ctx: UnifiedContext,
        builder: ResponseBuilder
    ) -> str:
        """执行单个步骤（子类实现）。"""
        pass


class OrchestratorAgent(BaseAgent):
    """
    编排 Agent 基类。

    适用于复杂任务编排，支持子 Agent 调度和并行执行。
    """

    def __init__(self, config: Optional[AgentConfig] = None) -> None:
        super().__init__(config)
        self._sub_agents: Dict[str, BaseAgent] = {}

    def register_sub_agent(self, name: str, agent: BaseAgent) -> None:
        """注册子 Agent。"""
        self._sub_agents[name] = agent

    def get_sub_agent(self, name: str) -> Optional[BaseAgent]:
        """获取子 Agent。"""
        return self._sub_agents.get(name)

    @abstractmethod
    async def _orchestrate(self, ctx: UnifiedContext, builder: ResponseBuilder) -> str:
        """编排逻辑（子类实现）。"""
        pass

    async def _execute(self, ctx: UnifiedContext, builder: ResponseBuilder) -> str:
        """执行编排。"""
        return await self._orchestrate(ctx, builder)
