#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reviewer Agent - 质量审核员
负责审核 DraftWriter 生成的内容，确保准确性、教学性和结构清晰。
"""

import logging
from typing import Dict, Any, Optional

from src.infrastructure.utils import BaseAgent, AgentState
from src.infrastructure.llm import Message, MessageRole, get_llm_manager
from .prompt import build_review_prompt

class ReviewerAgent(BaseAgent):
    """Reviewer Agent - 质量审核员
    
    核心职责：
    1. 检查幻觉、语气、难度匹配度
    2. 决定是否重写
    3. 给出修改意见
    """
    
    def __init__(self):
        super().__init__(
            name="Reviewer",
            description="审核内容质量，提供改进意见"
        )
        self.logger = logging.getLogger(self.__class__.__name__)
        
    async def execute(self, state: AgentState) -> AgentState:
        """执行审核逻辑"""
        try:
            draft = state.draft_content
            if not draft:
                self.logger.warning("没有草稿内容可审核")
                state.is_satisfactory = True # 没草稿就直接过，避免死循环（或者报错）
                return state
                
            # 检查修改次数，防止无限循环
            if state.revision_count >= 3:
                self.logger.info(f"修改次数已达上限 ({state.revision_count})，强制通过")
                state.is_satisfactory = True
                return state

            # 获取用户水平
            user_level = "beginner"
            if state.metadata and "user_profile" in state.metadata:
                user_level = state.metadata["user_profile"].get("level", "beginner")
            elif "user_context" in state.user_context:
                 user_level = state.user_context.get("level", "beginner")

            # 构建 Prompt
            prompt = build_review_prompt(draft, user_level)
            
            # 调用 LLM
            llm_manager = get_llm_manager()
            client = llm_manager.get_client("qwen") or llm_manager.get_client("ollama")
            
            if not client:
                self.logger.warning("LLM 客户端不可用，默认审核通过")
                state.is_satisfactory = True
                return state
                
            messages = [Message(role=MessageRole.USER, content=prompt)]
            response = client.chat_completion(messages, temperature=0.3) # 低温以保持严谨
            
            if not response.success:
                self.logger.error(f"LLM 调用失败: {response.error}")
                state.is_satisfactory = True # 失败则通过
                return state
                
            result_content = response.content
            
            # 解析结果
            if "REJECT" in result_content:
                state.is_satisfactory = False
                state.critique = result_content
                state.revision_count += 1
                self.logger.info(f"审核不通过，提出意见 (第 {state.revision_count} 次)")
            else:
                state.is_satisfactory = True
                self.logger.info("审核通过")
                
            return state
            
        except Exception as e:
            self.logger.error(f"Reviewer 执行失败: {e}", exc_info=True)
            state.is_satisfactory = True # 出错则默认通过，避免卡死
            return state


