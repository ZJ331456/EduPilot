"""用户画像 Agent：基于会话与图谱生成结构化 JSON 画像。继承 BaseAgent。"""

from __future__ import annotations

import json
import re
from typing import Any, Dict

from edupilot.agents.base.agent import AgentConfig, SingleTurnAgent
from edupilot.core.protocol import AgentMode, UnifiedContext
from edupilot.core.stream import ResponseBuilder
from edupilot.services.llm import get_llm_client
from edupilot.services.prompt.loader import load_agent_prompt


def _parse_json(text: str) -> Dict[str, Any]:
    """解析 JSON（兼容旧接口）。"""
    text = text.strip()
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        raise ValueError("未解析到 JSON")
    return json.loads(m.group(0))


class UserProfileAgent(SingleTurnAgent):
    """
    用户画像 Agent。

    特点：
    - 基于对话历史和知识图谱生成画像
    - 输出结构化 JSON 数据
    - 包含学习风格、优势、薄弱点、兴趣等维度
    """

    def _default_config(self) -> AgentConfig:
        """返回默认配置。"""
        p = load_agent_prompt("user_profile")
        return AgentConfig(
            name="UserProfileAgent",
            temperature=0.4,  # 画像分析温度较低，保证一致性
            max_tokens=2048,
            system_prompt=p.get("system", "你是一个专业的学习分析师，擅长从对话中分析用户的学习特点。"),
            streaming_enabled=False,  # 画像分析不需要流式
            tools_enabled=False
        )

    async def _execute(self, ctx: UnifiedContext, builder: ResponseBuilder) -> str:
        """执行用户画像分析。"""
        # 从 metadata 中获取额外信息
        user_id = ctx.user_id
        summary = ctx.metadata.get("summary", "")
        graph_summary = ctx.metadata.get("graph_summary", "")

        await builder.start_step("load_data")

        # 如果没有传入摘要，从历史中提取
        if not summary and ctx.history:
            summary = "\n".join([
                f'{m.get("role")}: {m.get("content", "")}'
                for m in ctx.history[-20:]
            ])

        await builder.end_step("load_data")

        await builder.start_step("profile_analysis")
        p = load_agent_prompt("user_profile")
        system = p.get("system", self._config.system_prompt)
        user_tpl = p.get("user") or ""
        user = user_tpl.format(
            user_id=user_id,
            summary=summary,
            graph_summary=graph_summary
        )

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ]

        llm = get_llm_client()
        raw = await llm.chat(
            messages,
            temperature=self._config.temperature,
            max_tokens=self._config.max_tokens
        )

        # 发送分析结果
        try:
            profile_data = _parse_json(raw)
            await builder.send_analysis({
                "profile": profile_data,
                "user_id": user_id
            })
        except Exception:
            pass

        await builder.end_step("profile_analysis", result={"profile_length": len(raw)})

        return raw


# 兼容旧版函数式接口
async def analyze(
    user_id: str,
    summary: str,
    graph_summary: str,
) -> Dict[str, Any]:
    """分析用户画像（兼容旧接口）。"""
    p = load_agent_prompt("user_profile")
    system = p.get("system", "")
    user = (p.get("user") or "").format(
        user_id=user_id,
        summary=summary,
        graph_summary=graph_summary,
    )
    llm = get_llm_client()
    raw = await llm.chat(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.4,
    )
    return _parse_json(raw)
