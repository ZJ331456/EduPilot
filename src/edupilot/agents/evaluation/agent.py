"""学习评测 Agent：评估用户学习效果并给出建议。继承 BaseAgent。"""

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


class EvaluationAgent(SingleTurnAgent):
    """
    学习评测 Agent。

    特点：
    - 评估用户学习掌握程度
    - 输出分数和详细建议
    - 支持按知识点评测
    """

    def _default_config(self) -> AgentConfig:
        """返回默认配置。"""
        p = load_agent_prompt("evaluation")
        return AgentConfig(
            name="EvaluationAgent",
            temperature=0.35,  # 评测温度较低，保证客观
            max_tokens=2048,
            system_prompt=p.get("system", "你是一个严谨的学习评测专家，擅长评估用户的学习效果并给出改进建议。"),
            streaming_enabled=False,
            tools_enabled=False
        )

    async def _execute(self, ctx: UnifiedContext, builder: ResponseBuilder) -> str:
        """执行学习评测。"""
        await builder.start_step("collect_data")
        summary = ctx.metadata.get("summary", "")
        goals = ctx.metadata.get("goals", "")

        if not summary and ctx.history:
            summary = "\n".join([
                f'{m.get("role")}: {m.get("content", "")}'
                for m in ctx.history[-20:]
            ])

        await builder.end_step("collect_data")

        await builder.start_step("evaluation")
        p = load_agent_prompt("evaluation")
        system = p.get("system", self._config.system_prompt)
        user_tpl = p.get("user") or ""
        user = user_tpl.format(summary=summary, goals=goals or "未指定")

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
            eval_data = _parse_json(raw)
            await builder.send_analysis({
                "evaluation": eval_data
            })
        except Exception:
            pass

        await builder.end_step("evaluation", result={"eval_length": len(raw)})

        return raw


# 兼容旧版函数式接口
async def evaluate(summary: str, goals: str = "") -> Dict[str, Any]:
    """评估学习效果（兼容旧接口）。"""
    p = load_agent_prompt("evaluation")
    system = p.get("system", "")
    user = (p.get("user") or "").format(summary=summary, goals=goals or "未指定")
    llm = get_llm_client()
    raw = await llm.chat(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.35,
    )
    return _parse_json(raw)
