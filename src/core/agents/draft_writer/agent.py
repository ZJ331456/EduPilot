#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DraftWriter Agent - 内容撰稿人
负责根据规划和工具执行结果生成内容草稿，或根据 Reviewer 的意见修改草稿。
"""

import logging
from typing import Dict, Any, Optional

from src.infrastructure.utils import BaseAgent, AgentState
from src.infrastructure.llm import Message, MessageRole, get_llm_manager
from .prompt import build_first_draft_prompt, build_revision_prompt

class DraftWriterAgent(BaseAgent):
    """DraftWriter Agent - 内容撰稿人
    
    核心职责：
    1. 整合 RAG 检索结果、工具输出生成初稿
    2. 根据 Reviewer 的 Critique 修改草稿
    """
    
    def __init__(self):
        super().__init__(
            name="DraftWriter",
            description="生成和修改教学内容草稿"
        )
        self.logger = logging.getLogger(self.__class__.__name__)
        
    async def execute(self, state: AgentState) -> AgentState:
        """执行撰稿逻辑"""
        try:
            # 判断是初稿还是修改
            if state.critique and not state.is_satisfactory:
                self.logger.info(f"开始修改草稿 (第 {state.revision_count + 1} 次修改)")
                draft = await self._revise_draft(state)
            else:
                self.logger.info("开始撰写初稿")
                draft = await self._write_first_draft(state)
            
            # 更新状态
            state.draft_content = draft
            # 清除 critique 状态以便下一轮 review
            state.critique = "" 
            # is_satisfactory 保持 False，等待 Reviewer 判定
            
            return state
            
        except Exception as e:
            self.logger.error(f"DraftWriter 执行失败: {e}", exc_info=True)
            state.set_error("draft_error", str(e))
            return state

    async def _write_first_draft(self, state: AgentState) -> str:
        """撰写初稿"""
        # 1. 收集上下文
        query = state.user_query
        
        # 知识库内容
        knowledge = self._format_knowledge(state.retrieved_knowledge)
        
        # 工具输出 (如果有)
        tool_outputs = self._format_tool_outputs(state.tool_outputs)
        
        # 用户画像
        user_level = "beginner"
        if state.metadata and "user_profile" in state.metadata:
            user_level = state.metadata["user_profile"].get("level", "beginner")

        # 2. 构建 Prompt
        prompt = build_first_draft_prompt(state, knowledge, tool_outputs, user_level)
        return await self._call_llm(prompt)

    async def _revise_draft(self, state: AgentState) -> str:
        """根据意见修改草稿"""
        original_draft = state.draft_content
        critique = state.critique
        query = state.user_query
        
        prompt = build_revision_prompt(state, original_draft, critique)
        return await self._call_llm(prompt)

    async def _call_llm(self, prompt: str) -> str:
        """调用 LLM"""
        llm_manager = get_llm_manager()
        client = llm_manager.get_client("qwen") or llm_manager.get_client("ollama")
        
        if not client:
            return "LLM Client not available. Cannot generate draft."
            
        messages = [Message(role=MessageRole.USER, content=prompt)]
        response = client.chat_completion(messages, temperature=0.7)
        
        if response.success:
            return response.content
        else:
            return f"Generation failed: {response.error}"

    def _format_knowledge(self, retrieved_knowledge: Any) -> str:
        """格式化知识库内容"""
        if not retrieved_knowledge:
            return "无相关知识库内容。"
        
        content = ""
        # 兼容不同的 retrieved_knowledge 结构
        if isinstance(retrieved_knowledge, dict):
            results = retrieved_knowledge.get('results', [])
            for i, res in enumerate(results, 1):
                content += f"[{i}] {res.get('content', '')}\n"
        elif isinstance(retrieved_knowledge, list):
             for i, res in enumerate(retrieved_knowledge, 1):
                # 假设是 list of dict 或 list of str
                if isinstance(res, dict):
                    content += f"[{i}] {res.get('content', '')}\n"
                else:
                    content += f"[{i}] {str(res)}\n"
        
        return content or "无有效内容。"

    def _format_tool_outputs(self, tool_outputs: Dict[str, Any]) -> str:
        """格式化工具输出"""
        if not tool_outputs:
            return "无工具运行结果。"
        
        content = ""
        for tool_name, output in tool_outputs.items():
            content += f"工具 [{tool_name}] 输出:\n{output}\n"
        return content

