#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ToolSpecialist Agent - 工具专家
负责调用外部工具，如网络搜索、代码解释器（简单的数学/逻辑计算）。
"""

import logging
import json
import math
import datetime
from typing import Dict, Any, Optional

from src.infrastructure.utils import BaseAgent, AgentState

class ToolSpecialistAgent(BaseAgent):
    """ToolSpecialist Agent - 工具专家
    
    核心职责：
    1. 处理计算、实时信息获取等任务
    2. 支持 Web Search (Mock/Placeholder for now) 和 Code Interpreter (Safe Eval)
    """
    
    def __init__(self):
        super().__init__(
            name="ToolSpecialist",
            description="执行数学计算、网络搜索等工具调用"
        )
        self.logger = logging.getLogger(self.__class__.__name__)
        
    async def execute(self, state: AgentState) -> AgentState:
        """执行工具调用逻辑"""
        try:
            intent = ""
            if state.interpretation:
                intent = state.interpretation.get("intent", "")
            
            tool_outputs = {}
            
            # 简单的意图匹配来触发工具
            # 实际生产中应由 Orchestrator 指定调用哪个工具，或者根据 Plan 中的 Actions
            
            # 1. 计算器 (Calculator)
            if "calculate" in intent or self._is_calculation_request(state.user_query):
                result = self._safe_calculate(state.user_query)
                tool_outputs["calculator"] = result
                self.logger.info(f"Calculator executed: {result}")

            # 2. 网络搜索 (Web Search) - Placeholder
            if "current_news" in intent or "search" in intent or "news" in state.user_query:
                # 实际应调用 Tavily/Serper API
                # 这里返回模拟数据
                result = self._mock_search(state.user_query)
                tool_outputs["web_search"] = result
                self.logger.info("Web Search executed (Mock)")
            
            # 保存结果到 state
            if tool_outputs:
                # 合并到现有的 tool_outputs
                if not state.tool_outputs:
                    state.tool_outputs = {}
                state.tool_outputs.update(tool_outputs)
            
            return state
            
        except Exception as e:
            self.logger.error(f"ToolSpecialist 执行失败: {e}", exc_info=True)
            # 工具失败不应致命，记录错误即可
            state.tool_outputs["error"] = str(e)
            return state

    def _is_calculation_request(self, query: str) -> bool:
        """简单判断是否是计算请求"""
        keywords = ["计算", "多少", "+", "-", "*", "/", "sqrt", "pow"]
        return any(k in query for k in keywords) and any(char.isdigit() for char in query)

    def _safe_calculate(self, query: str) -> str:
        """安全的数学计算"""
        # 提取表达式（非常简化的提取，仅作示例）
        # 实际应使用 LLM 提取数学表达式
        import re
        # 匹配数字和运算符
        expression = "".join(re.findall(r'[0-9\+\-\*\/\(\)\.\s]', query))
        
        try:
            # 使用 eval 进行计算，注意：eval 很危险，生产环境需沙箱隔离
            # 这里仅允许简单数学运算
            allowed_names = {"sqrt": math.sqrt, "pow": math.pow, "abs": abs}
            code = compile(expression, "<string>", "eval")
            for name in code.co_names:
                if name not in allowed_names:
                    return f"不支持的运算: {name}"
            
            result = eval(code, {"__builtins__": {}}, allowed_names)
            return f"计算结果: {result}"
        except Exception as e:
            return f"计算出错: {e}"

    def _mock_search(self, query: str) -> str:
        """模拟搜索结果"""
        return f"""
[模拟搜索结果] 针对查询 "{query}":
1. 这是一个模拟的搜索结果条目 1...
2. 这是一个模拟的搜索结果条目 2...
(请在后续配置中集成 Tavily API 以获得真实结果)
"""

