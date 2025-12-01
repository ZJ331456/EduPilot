#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CurriculumDesigner Agent - 课程设计师
负责生成系统化的学习路径（思维导图结构）。
"""

import logging
import json
from typing import Dict, Any, Optional

from src.infrastructure.utils import BaseAgent, AgentState
from src.infrastructure.llm import Message, MessageRole, get_llm_manager
from .prompt import build_curriculum_prompt

class CurriculumDesignerAgent(BaseAgent):
    """CurriculumDesigner Agent - 课程设计师
    
    核心职责：
    1. 当用户想要系统学习时，生成知识树结构
    2. 输出 JSON 格式的 MindMap 数据
    """
    
    def __init__(self):
        super().__init__(
            name="CurriculumDesigner",
            description="设计系统化学习路径和课程结构"
        )
        self.logger = logging.getLogger(self.__class__.__name__)
        
    async def execute(self, state: AgentState) -> AgentState:
        """执行课程设计逻辑"""
        try:
            self.logger.info("开始生成课程结构...")
            
            # 构建 Prompt
            prompt = build_curriculum_prompt(state)
            
            # 调用 LLM
            llm_manager = get_llm_manager()
            client = llm_manager.get_client("qwen") or llm_manager.get_client("ollama")
            
            if not client:
                self.logger.warning("LLM 客户端不可用，无法生成课程")
                return state
                
            messages = [Message(role=MessageRole.USER, content=prompt)]
            # 使用较高的温度以获得更有创意的结构，或者较低的温度以获得标准结构
            response = client.chat_completion(messages, temperature=0.5, json_mode=True)
            
            if not response.success:
                self.logger.error(f"LLM 调用失败: {response.error}")
                state.set_error("curriculum_error", "无法生成课程结构")
                return state
                
            # 解析结果
            try:
                # 尝试解析 JSON
                # 有些 LLM 可能返回 markdown code block，需要清洗
                content = response.content.strip()
                if content.startswith("```json"):
                    content = content[7:-3].strip()
                elif content.startswith("```"):
                    content = content[3:-3].strip()
                    
                curriculum_data = json.loads(content)
                
                # 保存到 state
                state.curriculum_plan = curriculum_data
                self.logger.info("课程结构生成成功")
                
                # 同时将课程大纲添加到工具输出，供 DraftWriter 使用
                state.tool_outputs["curriculum_outline"] = self._format_outline(curriculum_data)
                
            except json.JSONDecodeError:
                self.logger.error("LLM 返回的不是有效的 JSON")
                state.set_error("curriculum_error", "生成的课程结构格式错误")
            
            return state
            
        except Exception as e:
            self.logger.error(f"CurriculumDesigner 执行失败: {e}", exc_info=True)
            state.set_error("curriculum_error", str(e))
            return state


    def _format_outline(self, data: Dict[str, Any]) -> str:
        """将 JSON 结构格式化为文本大纲"""
        output = []
        topic = data.get("topic", "未命名课程")
        output.append(f"# {topic}")
        
        for module in data.get("modules", []):
            output.append(f"\n## {module.get('name')}")
            output.append(f"{module.get('description', '')}")
            for topic in module.get("topics", []):
                output.append(f"- **{topic.get('name')}**: {topic.get('description', '')}")
                
        return "\n".join(output)

