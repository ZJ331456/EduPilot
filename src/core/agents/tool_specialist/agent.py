#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ToolSpecialist Agent - 工具专家
负责调用外部工具，如网络搜索、代码解释器（简单的数学/逻辑计算）。
"""

import logging
from typing import Dict, Any, Optional

from src.infrastructure.utils import BaseAgent, AgentState

# 导入工具模块
from .tools import CalculatorTool, WebSearchTool


class ToolSpecialistAgent(BaseAgent):
    """ToolSpecialist Agent - 工具专家
    
    核心职责：
    1. 处理计算、实时信息获取等任务
    2. 支持 Web Search 和 Calculator 工具
    3. 根据意图自动选择合适的工具执行
    """
    
    def __init__(self):
        super().__init__(
            name="ToolSpecialist",
            description="执行数学计算、网络搜索等工具调用"
        )
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 初始化工具
        self.calculator = CalculatorTool()
        self.web_search = WebSearchTool()
        
        self.logger.info("ToolSpecialist 初始化完成")
        
    def can_execute(self, state: AgentState) -> bool:
        """检查是否可以执行"""
        # 检查是否有计算或搜索需求
        query = state.user_query.lower() if state.user_query else ""
        
        has_calculation = self.calculator.is_calculation_request(state.user_query or "")
        has_search = self.web_search.is_search_request(state.user_query or "")
        
        # 检查意图
        intent = ""
        if state.interpretation:
            intent = state.interpretation.get("intent", "").lower()
        
        calculation_intent = "calculate" in intent or "计算" in intent
        search_intent = "search" in intent or "current_news" in intent or "news" in intent
        
        return has_calculation or has_search or calculation_intent or search_intent
        
    async def execute(self, state: AgentState) -> AgentState:
        """执行工具调用逻辑"""
        try:
            intent = ""
            if state.interpretation:
                intent = state.interpretation.get("intent", "").lower()
            
            tool_outputs = {}
            query = state.user_query or ""
            
            # 1. 计算器 (Calculator)
            if ("calculate" in intent or 
                self.calculator.is_calculation_request(query)):
                try:
                    calc_result = self.calculator.execute(query)
                    if calc_result["success"]:
                        tool_outputs["calculator"] = {
                            "success": True,
                            "result": calc_result["result"],
                            "expression": calc_result.get("expression", ""),
                            "output": f"计算结果: {calc_result['result']}"
                        }
                    else:
                        tool_outputs["calculator"] = {
                            "success": False,
                            "error": calc_result.get("error", "计算失败"),
                            "output": f"计算出错: {calc_result.get('error', '未知错误')}"
                        }
                    self.logger.info(f"Calculator executed: {calc_result.get('result', 'N/A')}")
                except Exception as e:
                    self.logger.error(f"计算器执行失败: {e}")
                    tool_outputs["calculator"] = {
                        "success": False,
                        "error": str(e),
                        "output": f"计算出错: {str(e)}"
                    }

            # 2. 网络搜索 (Web Search)
            if ("current_news" in intent or 
                "search" in intent or 
                "news" in intent or
                self.web_search.is_search_request(query)):
                try:
                    search_result = await self.web_search.execute(query)
                    if search_result.get("success"):
                        tool_outputs["web_search"] = {
                            "success": True,
                            "query": search_result.get("query", ""),
                            "results": search_result.get("results", []),
                            "total_results": search_result.get("total_results", 0),
                            "source": search_result.get("source", "unknown"),
                            "output": self.web_search.format_output(search_result)
                        }
                    else:
                        tool_outputs["web_search"] = {
                            "success": False,
                            "error": search_result.get("error", "搜索失败"),
                            "output": f"搜索失败: {search_result.get('error', '未知错误')}"
                        }
                    self.logger.info(f"Web Search executed: {search_result.get('source', 'mock')}")
                except Exception as e:
                    self.logger.error(f"网络搜索执行失败: {e}")
                    tool_outputs["web_search"] = {
                        "success": False,
                        "error": str(e),
                        "output": f"搜索出错: {str(e)}"
                    }
            
            # 保存结果到 state
            if tool_outputs:
                # 合并到现有的 tool_outputs
                if not state.tool_outputs:
                    state.tool_outputs = {}
                state.tool_outputs.update(tool_outputs)
                self.logger.info(f"工具执行完成，共 {len(tool_outputs)} 个工具")
            else:
                self.logger.warning("未识别到需要执行的工具")
            
            return state
            
        except Exception as e:
            self.logger.error(f"ToolSpecialist 执行失败: {e}", exc_info=True)
            # 工具失败不应致命，记录错误即可
            if not state.tool_outputs:
                state.tool_outputs = {}
            state.tool_outputs["error"] = {
                "success": False,
                "error": str(e),
                "output": f"工具执行出错: {str(e)}"
            }
            return state

