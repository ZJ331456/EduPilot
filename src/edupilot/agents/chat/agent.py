"""
统一对话 Agent：支持直接回答和苏格拉底式引导两种模式。

设计原则：
1. 单 Agent 多模式：mode=direct（直接回答）/ mode=socratic（苏格拉底引导）
2. 流程：意图分析 -> 路由选择 -> 知识检索（可选）-> 回复生成
3. 流式输出，支持事件追踪
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Any, AsyncGenerator, Dict, List, Optional

from edupilot.agents.base.agent import AgentConfig, BaseAgent
from edupilot.core.protocol import AgentMode, UnifiedContext
from edupilot.core.stream import ResponseBuilder
from edupilot.services.llm import get_llm_client
from edupilot.services.prompt.loader import load_agent_prompt


class ChatMode(str, Enum):
    """对话模式枚举。"""
    DIRECT = "direct"       # 直接回答模式
    SOCRATIC = "socratic"  # 苏格拉底式提问模式


@dataclass
class IntentResult:
    """意图分析结果。"""
    intent: str           # 意图类型: question/explanation/summary/plan/other
    query_type: str       # 查询类型: factual/procedural/conceptual/analytical
    confidence: float      # 置信度 0-1
    keywords: List[str]   # 关键词
    suggested_mode: ChatMode  # 建议模式


@dataclass
class RouteResult:
    """路由决策结果。"""
    mode: ChatMode
    reasoning: str
    use_rag: bool         # 是否使用知识库检索
    use_tools: bool        # 是否使用工具


class QueryAnalyzer:
    """意图分析器：快速分析用户查询的意图和类型。"""

    def __init__(self) -> None:
        self._llm = get_llm_client()

    async def analyze(self, context: str) -> IntentResult:
        """分析查询意图。"""
        prompt = """分析以下用户查询，返回 JSON 格式结果：
{
    "intent": "question|explanation|summary|plan|other",
    "query_type": "factual|procedural|conceptual|analytical",
    "confidence": 0.0-1.0,
    "keywords": ["关键词1", "关键词2"],
    "reasoning": "简短分析理由"
}

查询内容：
{context}

直接返回 JSON，不要其他内容。""".format(context=context[:2000])

        messages = [
            {"role": "system", "content": "你是一个专业的意图分析助手。"},
            {"role": "user", "content": prompt}
        ]

        try:
            response = await self._llm.chat(messages, temperature=0.3, max_tokens=500)
            # 解析 JSON
            import json
            import re
            m = re.search(r'\{[\s\S]*\}', response)
            if m:
                data = json.loads(m.group(0))
                return IntentResult(
                    intent=data.get("intent", "other"),
                    query_type=data.get("query_type", "factual"),
                    confidence=data.get("confidence", 0.5),
                    keywords=data.get("keywords", []),
                    suggested_mode=ChatMode.SOCRATIC if data.get("intent") in ["analytical", "conceptual"] else ChatMode.DIRECT
                )
        except Exception:
            pass

        return IntentResult(
            intent="other",
            query_type="factual",
            confidence=0.5,
            keywords=[],
            suggested_mode=ChatMode.DIRECT
        )


class DialogueRouter:
    """对话路由：根据意图选择最佳响应策略。"""

    # 模式选择规则
    MODE_RULES = {
        # (intent, query_type) -> ChatMode
        ("question", "conceptual"): ChatMode.SOCRATIC,
        ("question", "analytical"): ChatMode.SOCRATIC,
        ("question", "procedural"): ChatMode.DIRECT,
        ("question", "factual"): ChatMode.DIRECT,
        ("explanation", "any"): ChatMode.DIRECT,
        ("summary", "any"): ChatMode.DIRECT,
        ("plan", "any"): ChatMode.DIRECT,
        ("other", "any"): ChatMode.DIRECT,
    }

    def route(self, intent: IntentResult, user_mode: Optional[ChatMode] = None) -> RouteResult:
        """根据意图和用户选择进行路由。"""
        # 优先使用用户指定的模式
        if user_mode:
            return RouteResult(
                mode=user_mode,
                reasoning=f"用户指定模式: {user_mode.value}",
                use_rag=intent.intent in ["question", "explanation"],
                use_tools=intent.query_type == "procedural"
            )

        # 根据意图自动选择
        key = (intent.intent, intent.query_type)
        mode = self.MODE_RULES.get(key, ChatMode.DIRECT)

        return RouteResult(
            mode=mode,
            reasoning=f"意图分析建议: {intent.intent} + {intent.query_type}",
            use_rag=intent.intent in ["question", "explanation"],
            use_tools=intent.query_type == "procedural"
        )


class ChatAgent(BaseAgent):
    """
    统一对话 Agent。

    特点：
    1. 支持两种模式：直接回答（direct）和苏格拉底引导（socratic）
    2. 意图分析：自动理解用户查询意图
    3. 智能路由：根据意图选择最佳响应策略
    4. 知识检索：可选择性接入 GraphRAG
    5. 流式输出：支持实时流式响应

    使用示例：
    ```python
    agent = ChatAgent()
    ctx = UnifiedContext(session_id="s1", user_id="u1", user_message="什么是机器学习?")
    result = await agent.execute(ctx, builder)
    ```
    """

    def __init__(self, config: Optional[AgentConfig] = None) -> None:
        super().__init__(config)
        self._analyzer = QueryAnalyzer()
        self._router = DialogueRouter()

    def _default_config(self) -> AgentConfig:
        """返回默认配置。"""
        return AgentConfig(
            name="ChatAgent",
            temperature=0.7,
            max_tokens=4096,
            system_prompt="你是一个专业、耐心的中文学习助手。",
            streaming_enabled=True,
            tools_enabled=True
        )

    async def _execute(self, ctx: UnifiedContext, builder: ResponseBuilder) -> str:
        """执行对话主流程。"""
        # 获取用户指定的模式
        user_mode = ChatMode.DIRECT
        if hasattr(ctx.mode, 'value'):
            if ctx.mode.value == "socratic":
                user_mode = ChatMode.SOCRATIC

        # Step 1: 意图分析
        await builder.start_step("intent_analysis")
        context_text = ctx.get_context_summary(max_chars=6000)
        intent = await self._analyzer.analyze(context_text)
        await builder.send_analysis({
            "intent": intent.intent,
            "query_type": intent.query_type,
            "confidence": intent.confidence,
            "keywords": intent.keywords
        })
        await builder.end_step("intent_analysis")

        # Step 2: 路由决策
        await builder.start_step("routing")
        route = self._router.route(intent, user_mode)

        # 如果用户指定了模式，优先使用用户模式
        if ctx.metadata.get("user_mode"):
            try:
                user_specified = ChatMode(ctx.metadata["user_mode"])
                route = RouteResult(
                    mode=user_specified,
                    reasoning=f"用户指定模式: {user_specified.value}",
                    use_rag=route.use_rag,
                    use_tools=route.use_tools
                )
            except Exception:
                pass

        await builder.end_step("routing")

        # Step 3: 回复生成
        await builder.start_step("response_generation")
        response = await self._generate_response(ctx, route, builder)
        await builder.end_step("response_generation")

        return response

    async def _generate_response(
        self,
        ctx: UnifiedContext,
        route: RouteResult,
        builder: ResponseBuilder
    ) -> str:
        """根据路由生成回复。"""
        # 加载对应模式的提示词
        agent_folder = "chat_direct" if route.mode == ChatMode.DIRECT else "chat_socratic"
        p = load_agent_prompt(agent_folder)

        system = p.get("system", self._get_system_prompt(route.mode))
        user_tpl = p.get("user") or "{context}"
        user = user_tpl.format(context=ctx.get_context_summary(max_chars=8000))

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ]

        # 流式输出
        llm = get_llm_client()
        chunks = []

        async for chunk in llm.stream_chat(
            messages,
            temperature=self._config.temperature,
            max_tokens=self._config.max_tokens
        ):
            chunks.append(chunk)
            await builder.send_content(chunk)

        return "".join(chunks)

    def _get_system_prompt(self, mode: ChatMode) -> str:
        """根据模式获取系统提示词。"""
        if mode == ChatMode.SOCRATIC:
            return (
                "你采用苏格拉底式教学：不直接给长篇标准答案，"
                "优先用简短、层层递进的问题，引导用户自己思考。"
                "每次回复里最多提出一到两个关键问题，必要时给一句提示。"
                "全程使用中文。"
            )
        return (
            "你是一个耐心的中文学习助手。回答要清晰、结构化，适当举例。"
            "若用户在学习某一科目，请先简要确认理解再展开讲解。"
        )

    async def execute_stream(
        self,
        ctx: UnifiedContext
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式执行接口，返回事件生成器。

        适用于 WebSocket/SSE 实时推送。
        """
        from edupilot.core.stream import StreamBus, StreamEvent
        from edupilot.core.protocol import AgentResponse

        bus = StreamBus()
        builder = ResponseBuilder(bus, ctx.session_id, self._config.name)

        async def run():
            try:
                result = await self._execute(ctx, builder)
            except Exception as e:
                await builder.send_error(str(e), "EXECUTION_ERROR")

        task = asyncio.create_task(run())

        async for event in bus.subscribe(f"stream_{ctx.session_id}"):
            yield event.to_dict()

        await task

    def execute_sync(self, ctx: UnifiedContext) -> str:
        """
        同步执行接口（兼容旧接口）。

        适用于简单的非流式调用。
        """
        return asyncio.get_event_loop().run_until_complete(
            self.execute(ctx, builder=None, stream=False)
        )
