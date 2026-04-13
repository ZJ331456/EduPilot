"""学习计划 Agent：结合用户画像生成结构化周计划。继承 BaseAgent。"""

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


class LearningPlannerAgent(SingleTurnAgent):
    """
    学习计划 Agent。

    特点：
    - 结合用户画像定制学习计划
    - 输出结构化周计划 JSON
    - 包含每日目标、学习资源推荐、时间安排等
    """

    def _default_config(self) -> AgentConfig:
        """返回默认配置。"""
        p = load_agent_prompt("learning_planner")
        return AgentConfig(
            name="LearningPlannerAgent",
            temperature=0.5,  # 计划生成温度适中
            max_tokens=3072,
            system_prompt=p.get("system", "你是一个专业的学习规划师，擅长根据用户特点制定个性化学习计划。"),
            streaming_enabled=False,
            tools_enabled=False
        )

    async def _execute(self, ctx: UnifiedContext, builder: ResponseBuilder) -> str:
        """执行学习计划生成。"""
        await builder.start_step("load_profile")
        profile = ctx.metadata.get("profile", {})
        goal_hint = ctx.metadata.get("goal_hint", "")

        if not profile and ctx.history:
            # 尝试从历史消息中提取
            try:
                for m in reversed(ctx.history):
                    if m.get("role") == "assistant":
                        content = m.get("content", "")
                        if "{" in content:
                            m2 = re.search(r"\{[\s\S]*\}", content)
                            if m2:
                                profile = json.loads(m2.group(0))
                                break
            except Exception:
                pass

        await builder.end_step("load_profile")

        await builder.start_step("plan_generation")
        p = load_agent_prompt("learning_planner")
        system = p.get("system", self._config.system_prompt)
        user_tpl = p.get("user") or ""
        user = user_tpl.format(
            profile_json=json.dumps(profile, ensure_ascii=False, indent=2),
            goal_hint=goal_hint or "无"
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
            plan_data = _parse_json(raw)
            await builder.send_analysis({
                "plan": plan_data,
                "user_id": ctx.user_id
            })
        except Exception:
            pass

        await builder.end_step("plan_generation", result={"plan_length": len(raw)})

        return raw


# 兼容旧版函数式接口
async def plan(profile: Dict[str, Any], goal_hint: str = "") -> Dict[str, Any]:
    """生成学习计划（兼容旧接口）。"""
    p = load_agent_prompt("learning_planner")
    system = p.get("system", "")
    user = (p.get("user") or "").format(
        profile_json=json.dumps(profile, ensure_ascii=False, indent=2),
        goal_hint=goal_hint or "无",
    )
    llm = get_llm_client()
    raw = await llm.chat(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.5,
    )
    return _parse_json(raw)
