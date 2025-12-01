#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QuizMaster Agent - 测评与出题官
负责在知识点讲解后生成测试题，评估用户掌握度。
"""

import logging
import json
from typing import Dict, Any, Optional

from src.infrastructure.utils import BaseAgent, AgentState
from src.infrastructure.llm import Message, MessageRole, get_llm_manager
from .prompt import build_quiz_prompt

class QuizMasterAgent(BaseAgent):
    """QuizMaster Agent - 测评与出题官
    
    核心职责：
    1. 根据讲解内容生成单选题
    2. 评估用户回答（如果是交互式测评）- 当前主要实现生成题目
    """
    
    def __init__(self):
        super().__init__(
            name="QuizMaster",
            description="生成测试题以评估学习效果"
        )
        self.logger = logging.getLogger(self.__class__.__name__)
        
    async def execute(self, state: AgentState) -> AgentState:
        """执行出题逻辑"""
        try:
            # 只有在内容生成并审核通过后才出题
            if not state.is_satisfactory:
                self.logger.info("内容尚未审核通过，跳过出题")
                return state

            self.logger.info("开始生成测试题...")
            
            # 使用已生成的草稿内容作为上下文
            content_context = state.draft_content
            if not content_context:
                self.logger.warning("没有内容可供出题")
                return state

            # 构建 Prompt
            prompt = build_quiz_prompt(state, content_context)
            
            # 调用 LLM
            llm_manager = get_llm_manager()
            client = llm_manager.get_client("qwen") or llm_manager.get_client("ollama")
            
            if not client:
                self.logger.warning("LLM 客户端不可用，无法生成题目")
                return state
                
            messages = [Message(role=MessageRole.USER, content=prompt)]
            response = client.chat_completion(messages, temperature=0.7, json_mode=True)
            
            if not response.success:
                self.logger.error(f"LLM 调用失败: {response.error}")
                return state
                
            # 解析结果
            try:
                content = response.content.strip()
                if content.startswith("```json"):
                    content = content[7:-3].strip()
                elif content.startswith("```"):
                    content = content[3:-3].strip()
                    
                quiz_data = json.loads(content)
                
                # 保存到 tool_outputs，供前端展示或后续使用
                # 注意：我们使用专门的 key 'quiz_cards'
                state.tool_outputs["quiz_data"] = quiz_data
                self.logger.info(f"成功生成 {len(quiz_data.get('questions', []))} 道题目")
                
                # 将题目追加到最终响应中 (可选，如果前端能独立渲染更好，这里作为文本备份)
                state.draft_content += "\n\n" + self._format_quiz(quiz_data)
                
            except json.JSONDecodeError:
                self.logger.error("LLM 返回的题目格式错误")
            
            return state
            
        except Exception as e:
            self.logger.error(f"QuizMaster 执行失败: {e}", exc_info=True)
            return state # 出题失败不应阻断主流程


    def _format_quiz(self, data: Dict[str, Any]) -> str:
        """将题目格式化为文本"""
        output = ["\n📝 **小测验**"]
        
        for q in data.get("questions", []):
            output.append(f"\n{q.get('id')}. {q.get('question')}")
            for i, opt in enumerate(q.get("options", [])):
                letter = chr(65 + i) # A, B, C...
                output.append(f"   {letter}. {opt}")
            # output.append(f"   (答案: {chr(65 + q.get('correct_index', 0))})") # 暂时不直接显示答案
            
        return "\n".join(output)

