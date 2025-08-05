#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
执行器智能体
执行计划，可能包括生成响应或与外部系统交互
"""

import logging
from typing import Dict, Any, List, Optional
from utils import BaseAgent, AgentState, ActionType
from prompts import get_prompt, PromptType
from utils.llm import Message, MessageRole

class ExecutorAgent(BaseAgent):
    """执行器智能体
    
    执行规划器制定的计划，生成最终响应
    """
    
    def __init__(self):
        super().__init__(
            name="Executor",
            description="执行行动计划并生成响应"
        )
        self.execution_history = []  # 执行历史
        self.response_templates = self._load_response_templates()
    
    def can_execute(self, state: AgentState) -> bool:
        """检查是否可以执行"""
        return (
            state.plan is not None and
            state.plan.get("actions") is not None and
            len(state.plan["actions"]) > 0
        )
    
    async def execute(self, state: AgentState) -> AgentState:
        """执行计划"""
        try:
            execution_results = []
            
            # 按优先级执行所有行动
            actions = sorted(
                state.plan["actions"],
                key=lambda x: x.get("priority", 999)
            )
            
            for action in actions:
                if action.get("executed", False):
                    continue
                
                result = self._execute_action(action, state)
                execution_results.append(result)
                
                # 标记行动完成
                action["executed"] = True
                action["execution_result"] = result
            
            # 生成最终响应
            final_response = self._generate_final_response(execution_results, state)
            
            # 更新状态
            state.execution_result = {
                "action_results": execution_results,
                "final_response": final_response,
                "execution_summary": self._create_execution_summary(execution_results),
                "success": all(r.get("success", False) for r in execution_results)
            }
            
            # 记录执行历史
            self.execution_history.append({
                "session_id": state.session_id,
                "timestamp": state.timestamp,
                "plan_type": state.plan.get("type"),
                "actions_executed": len(execution_results),
                "success": state.execution_result["success"]
            })
            
            self.logger.info(f"Executed {len(execution_results)} actions successfully")
            
            return state
            
        except Exception as e:
            self.logger.error(f"Execution failed: {e}")
            state.set_error(
                "execution_error",
                f"Failed to execute plan: {str(e)}"
            )
            return state
    
    def _execute_action(self, action: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """执行单个行动"""
        action_type = action.get("type")
        
        try:
            if action_type == ActionType.PROVIDE_ANSWER:
                return self._execute_provide_answer(action, state)
            elif action_type == ActionType.ASK_QUESTION:
                return self._execute_ask_question(action, state)
            elif action_type == ActionType.EXPLAIN_CONCEPT:
                return self._execute_explain_concept(action, state)
            elif action_type == ActionType.SHOW_EXAMPLE:
                return self._execute_show_example(action, state)
            elif action_type == ActionType.GUIDE_THINKING:
                return self._execute_guide_thinking(action, state)
            elif action_type == ActionType.SUMMARIZE_LEARNING:
                return self._execute_summarize_learning(action, state)
            elif action_type == ActionType.RECOMMEND_RESOURCES:
                return self._execute_recommend_resources(action, state)
            else:
                return {
                    "action_type": action_type,
                    "success": False,
                    "error": f"Unknown action type: {action_type}",
                    "content": None
                }
        
        except Exception as e:
            self.logger.error(f"Failed to execute action {action_type}: {e}")
            return {
                "action_type": action_type,
                "success": False,
                "error": str(e),
                "content": None
            }
    
    def _execute_provide_answer(self, action: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """执行提供答案行动"""
        try:
            from utils.llm import get_llm_manager
            
            # 优先使用百炼大模型
            llm_manager = get_llm_manager()
            client = llm_manager.get_client("qwen") or llm_manager.get_client("ollama")
            
            if not client:
                return {
                    "action_type": ActionType.PROVIDE_ANSWER,
                    "success": False,
                    "error": "No LLM client available",
                    "content": None
                }
            
            # 构建答案生成提示
            prompt = self._build_answer_prompt(action, state)
            
            messages = [
                Message(role=MessageRole.SYSTEM, content=self._get_answer_system_prompt()),
                Message(role=MessageRole.USER, content=prompt)
            ]
            
            response = client.chat_completion(messages)
            
            if response.success:
                return {
                    "action_type": ActionType.PROVIDE_ANSWER,
                    "success": True,
                    "content": response.content,
                    "confidence": action.get("parameters", {}).get("confidence_level", 0.8)
                }
            else:
                return {
                    "action_type": ActionType.PROVIDE_ANSWER,
                    "success": False,
                    "error": response.error,
                    "content": None
                }
        
        except Exception as e:
            return {
                "action_type": ActionType.PROVIDE_ANSWER,
                "success": False,
                "error": str(e),
                "content": None
            }
    
    def _execute_ask_question(self, action: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """执行提问行动"""
        # 这个行动通常由苏格拉底引导者处理，这里提供备用实现
        question_templates = {
            "assessment": "基于你目前的理解，你认为这个概念的核心是什么？",
            "exploratory": "你能想到这个概念在实际生活中的应用吗？",
            "verification": "你能用自己的话解释一下刚才讨论的要点吗？"
        }
        
        question_type = action.get("parameters", {}).get("question_type", "assessment")
        question = question_templates.get(question_type, "你对此有什么想法？")
        
        return {
            "action_type": ActionType.ASK_QUESTION,
            "success": True,
            "content": question,
            "question_type": question_type
        }
    
    def _execute_explain_concept(self, action: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """执行概念解释行动"""
        try:
            from utils.llm import get_llm_manager
            
            llm_manager = get_llm_manager()
            client = llm_manager.get_client("qwen") or llm_manager.get_client("ollama")
            
            if not client:
                return {
                    "action_type": ActionType.EXPLAIN_CONCEPT,
                    "success": False,
                    "error": "No LLM client available",
                    "content": None
                }
            
            # 构建概念解释提示
            prompt = self._build_explanation_prompt(action, state)
            
            messages = [
                Message(role=MessageRole.SYSTEM, content=self._get_explanation_system_prompt()),
                Message(role=MessageRole.USER, content=prompt)
            ]
            
            response = client.chat_completion(messages)
            
            if response.success:
                return {
                    "action_type": ActionType.EXPLAIN_CONCEPT,
                    "success": True,
                    "content": response.content,
                    "explanation_depth": action.get("parameters", {}).get("explanation_depth", "basic")
                }
            else:
                return {
                    "action_type": ActionType.EXPLAIN_CONCEPT,
                    "success": False,
                    "error": response.error,
                    "content": None
                }
        
        except Exception as e:
            return {
                "action_type": ActionType.EXPLAIN_CONCEPT,
                "success": False,
                "error": str(e),
                "content": None
            }
    
    def _execute_show_example(self, action: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """执行展示示例行动"""
        try:
            from utils.llm import get_llm_manager
            
            llm_manager = get_llm_manager()
            client = llm_manager.get_client("qwen") or llm_manager.get_client("ollama")
            
            if not client:
                return {
                    "action_type": ActionType.SHOW_EXAMPLE,
                    "success": False,
                    "error": "No LLM client available",
                    "content": None
                }
            
            # 构建示例生成提示
            prompt = self._build_example_prompt(action, state)
            
            messages = [
                Message(role=MessageRole.SYSTEM, content=self._get_example_system_prompt()),
                Message(role=MessageRole.USER, content=prompt)
            ]
            
            response = client.chat_completion(messages)
            
            if response.success:
                return {
                    "action_type": ActionType.SHOW_EXAMPLE,
                    "success": True,
                    "content": response.content,
                    "example_types": action.get("parameters", {}).get("example_types", ["practical"])
                }
            else:
                return {
                    "action_type": ActionType.SHOW_EXAMPLE,
                    "success": False,
                    "error": response.error,
                    "content": None
                }
        
        except Exception as e:
            return {
                "action_type": ActionType.SHOW_EXAMPLE,
                "success": False,
                "error": str(e),
                "content": None
            }
    
    def _execute_guide_thinking(self, action: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """执行引导思考行动"""
        try:
            from utils.llm import get_llm_manager
            
            llm_manager = get_llm_manager()
            client = llm_manager.get_client("qwen") or llm_manager.get_client("ollama")
            
            if not client:
                # 如果没有LLM客户端，使用默认引导
                thinking_guides = {
                    "analytical": "这是一个很好的问题，需要我们从多个角度来思考。",
                    "problem_decomposition": "让我们将这个问题分解来分析。",
                    "conceptual_connections": "这个问题涉及到多个层面的考虑。"
                }
                
                thinking_direction = action.get("parameters", {}).get("thinking_direction", "analytical")
                guide_content = thinking_guides.get(thinking_direction, "这是一个值得深入思考的问题...")
                
                return {
                    "action_type": ActionType.GUIDE_THINKING,
                    "success": True,
                    "content": guide_content,
                    "thinking_direction": thinking_direction
                }
            
            # 使用LLM生成思考引导
            thinking_direction = action.get("parameters", {}).get("thinking_direction", "analytical")
            
            prompt_parts = [
                f"用户查询: {state.user_query}",
                f"思考方向: {thinking_direction}"
            ]
            
            # 添加相关知识背景
            if state.retrieved_knowledge and state.retrieved_knowledge.get("results"):
                knowledge_content = "\n".join([
                    result.get('content', '')[:200]
                    for result in state.retrieved_knowledge["results"][:2]
                ])
                prompt_parts.append(f"相关知识:\n{knowledge_content}")
            
            if thinking_direction == "analytical":
                prompt_parts.append("请提供分析性的思考引导，帮助用户逐步理解问题。")
            elif thinking_direction == "problem_decomposition":
                prompt_parts.append("请帮助用户将复杂问题分解为更小的、可管理的部分。")
            elif thinking_direction == "conceptual_connections":
                prompt_parts.append("请引导用户思考概念之间的联系和关系。")
            
            prompt = "\n\n".join(prompt_parts)
            
            system_prompt = get_prompt(PromptType.THINKING_GUIDANCE)
            
            messages = [
                Message(role=MessageRole.SYSTEM, content=system_prompt),
                Message(role=MessageRole.USER, content=prompt)
            ]
            
            response = client.chat_completion(messages)
            
            if response.success:
                return {
                    "action_type": ActionType.GUIDE_THINKING,
                    "success": True,
                    "content": response.content,
                    "thinking_direction": thinking_direction
                }
            else:
                # LLM调用失败，使用默认引导
                thinking_guides = {
                    "analytical": "让我们一步步分析这个问题。首先，我们需要理解核心概念，然后分析其特点和应用。",
                    "problem_decomposition": "我们可以将这个复杂问题分解为几个小问题，逐一解决。",
                    "conceptual_connections": "这个概念与我们之前讨论的内容有什么联系？让我们建立知识之间的关联。"
                }
                
                guide_content = thinking_guides.get(thinking_direction, "让我们深入思考一下这个问题...")
                
                return {
                    "action_type": ActionType.GUIDE_THINKING,
                    "success": True,
                    "content": guide_content,
                    "thinking_direction": thinking_direction,
                    "fallback": True
                }
        
        except Exception as e:
            return {
                "action_type": ActionType.GUIDE_THINKING,
                "success": False,
                "error": str(e),
                "content": None
            }
    
    def _execute_summarize_learning(self, action: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """执行学习总结行动"""
        try:
            # 收集学习要点
            learning_points = []
            
            # 从用户响应中提取要点
            if state.user_responses:
                learning_points.extend([
                    f"你提到了: {response[:50]}..." for response in state.user_responses[-3:]
                ])
            
            # 从检索知识中提取要点
            if state.retrieved_knowledge and state.retrieved_knowledge.get("results"):
                for result in state.retrieved_knowledge["results"][:2]:
                    content = result.get("content", "")
                    if content:
                        learning_points.append(f"关键概念: {content[:80]}...")
            
            summary_content = "\n".join([
                "## 学习总结",
                "在我们的讨论中，主要涉及了以下要点：",
                "\n".join(f"- {point}" for point in learning_points),
                "\n这些讨论帮助我们更好地理解了相关概念。"
            ])
            
            return {
                "action_type": ActionType.SUMMARIZE_LEARNING,
                "success": True,
                "content": summary_content,
                "learning_points": learning_points
            }
        
        except Exception as e:
            return {
                "action_type": ActionType.SUMMARIZE_LEARNING,
                "success": False,
                "error": str(e),
                "content": None
            }
    
    def _execute_recommend_resources(self, action: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """执行推荐资源行动"""
        try:
            # 基于查询内容推荐相关资源
            recommendations = [
                "建议进一步阅读相关的学术文献和教材",
                "可以寻找相关的在线课程和视频教程",
                "尝试在实践中应用所学的概念",
                "与同行或专家讨论以加深理解"
            ]
            
            # 如果有具体的知识源，添加具体推荐
            if state.knowledge_sources:
                recommendations.insert(0, f"可以深入研究: {', '.join(state.knowledge_sources)}")
            
            resource_content = "\n".join([
                "## 推荐资源",
                "为了进一步学习，建议：",
                "\n".join(f"- {rec}" for rec in recommendations)
            ])
            
            return {
                "action_type": ActionType.RECOMMEND_RESOURCES,
                "success": True,
                "content": resource_content,
                "recommendations": recommendations
            }
        
        except Exception as e:
            return {
                "action_type": ActionType.RECOMMEND_RESOURCES,
                "success": False,
                "error": str(e),
                "content": None
            }
    
    def _build_answer_prompt(self, action: Dict[str, Any], state: AgentState) -> str:
        """构建答案生成提示"""
        prompt_parts = [
            f"用户查询: {state.user_query}",
        ]
        
        # 添加检索到的知识
        if state.retrieved_knowledge and state.retrieved_knowledge.get("results"):
            knowledge_content = "\n".join([
                f"知识源 {i+1}: {result.get('content', '')[:200]}..."
                for i, result in enumerate(state.retrieved_knowledge["results"][:3])
            ])
            prompt_parts.append(f"相关知识:\n{knowledge_content}")
        
        # 添加参数要求
        params = action.get("parameters", {})
        if params.get("answer_style") == "concise":
            prompt_parts.append("请提供简洁明了的答案。")
        
        if params.get("include_sources"):
            prompt_parts.append("请在答案中引用相关的知识源。")
        
        return "\n\n".join(prompt_parts)
    
    def _build_explanation_prompt(self, action: Dict[str, Any], state: AgentState) -> str:
        """构建解释提示"""
        prompt_parts = [
            f"需要解释的概念相关查询: {state.user_query}",
        ]
        
        # 添加知识背景
        if state.retrieved_knowledge and state.retrieved_knowledge.get("results"):
            knowledge_content = "\n".join([
                result.get('content', '')[:300]
                for result in state.retrieved_knowledge["results"][:2]
            ])
            prompt_parts.append(f"背景知识:\n{knowledge_content}")
        
        # 添加解释要求
        params = action.get("parameters", {})
        depth = params.get("explanation_depth", "basic")
        
        if depth == "comprehensive":
            prompt_parts.append("请提供全面深入的概念解释，包括定义、特征、应用等。")
        elif depth == "structural":
            prompt_parts.append("请重点解释概念的结构和组成部分。")
        else:
            prompt_parts.append("请提供清晰易懂的基础概念解释。")
        
        if params.get("use_examples"):
            prompt_parts.append("请在解释中包含具体的例子。")
        
        return "\n\n".join(prompt_parts)
    
    def _build_example_prompt(self, action: Dict[str, Any], state: AgentState) -> str:
        """构建示例生成提示"""
        prompt_parts = [
            f"相关概念查询: {state.user_query}",
            "请生成相关的具体示例来帮助理解。"
        ]
        
        # 添加示例类型要求
        params = action.get("parameters", {})
        example_types = params.get("example_types", ["practical"])
        
        if "practical" in example_types:
            prompt_parts.append("包含实际应用的例子。")
        if "analogical" in example_types:
            prompt_parts.append("使用类比来帮助理解。")
        if "solution_process" in example_types:
            prompt_parts.append("展示解决问题的具体步骤。")
        
        return "\n".join(prompt_parts)
    
    def _get_answer_system_prompt(self) -> str:
        """获取答案生成系统提示"""
        try:
            return get_prompt(PromptType.ANSWER_GENERATION)
        except:
            return get_prompt(PromptType.ANSWER_GENERATION)
    
    def _get_explanation_system_prompt(self) -> str:
        """获取解释系统提示"""
        return get_prompt(PromptType.CONCEPT_EXPLANATION)
    
    def _get_example_system_prompt(self) -> str:
        """获取示例生成系统提示"""
        return get_prompt(PromptType.EXAMPLE_GENERATION)
    
    def _generate_final_response(self, execution_results: List[Dict[str, Any]], state: AgentState) -> str:
        """生成最终响应"""
        try:
            # 收集所有成功的执行结果
            successful_results = [r for r in execution_results if r.get("success", False)]
            
            if not successful_results:
                return "抱歉，我无法为您提供满意的回答。请尝试重新表述您的问题。"
            
            # 获取用户画像上下文（如果有）
            user_profile_context = state.metadata.get("user_profile_context", {})
            
            # 按行动类型组织内容
            response_parts = []
            
            # 添加答案内容
            for result in successful_results:
                if result.get("action_type") == ActionType.PROVIDE_ANSWER:
                    response_parts.append(result.get("content", ""))
            
            # 添加概念解释
            for result in successful_results:
                if result.get("action_type") == ActionType.EXPLAIN_CONCEPT:
                    response_parts.append(result.get("content", ""))
            
            # 添加示例
            for result in successful_results:
                if result.get("action_type") == ActionType.SHOW_EXAMPLE:
                    response_parts.append(result.get("content", ""))
            
            # 添加思考引导
            for result in successful_results:
                if result.get("action_type") == ActionType.GUIDE_THINKING:
                    response_parts.append(result.get("content", ""))
            
            # 添加问题
            for result in successful_results:
                if result.get("action_type") == ActionType.ASK_QUESTION:
                    response_parts.append(f"\n💭 {result.get('content', '')}")
            
            # 添加学习总结
            for result in successful_results:
                if result.get("action_type") == ActionType.SUMMARIZE_LEARNING:
                    response_parts.append(result.get("content", ""))
            
            # 添加资源推荐
            for result in successful_results:
                if result.get("action_type") == ActionType.RECOMMEND_RESOURCES:
                    response_parts.append(result.get("content", ""))
            
            # 组合最终响应
            final_response = "\n\n".join(filter(None, response_parts))
            
            # 如果响应为空，提供默认响应
            if not final_response.strip():
                final_response = "我已经处理了您的请求，但可能需要更多信息来提供更好的帮助。"
            
            # 如果有用户画像上下文，个性化响应
            final_response = self._personalize_response_with_profile(final_response, user_profile_context)
            
            return final_response
            
        except Exception as e:
            self.logger.error(f"Failed to generate final response: {e}")
            return "抱歉，在生成响应时遇到了问题。请稍后再试。"
    
    def _create_execution_summary(self, execution_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """创建执行总结"""
        successful_actions = [r for r in execution_results if r.get("success", False)]
        failed_actions = [r for r in execution_results if not r.get("success", False)]
        
        action_types = [r.get("action_type") for r in successful_actions]
        
        return {
            "total_actions": len(execution_results),
            "successful_actions": len(successful_actions),
            "failed_actions": len(failed_actions),
            "success_rate": len(successful_actions) / len(execution_results) if execution_results else 0,
            "executed_action_types": action_types,
            "errors": [r.get("error") for r in failed_actions if r.get("error")]
        }
    
    def _load_response_templates(self) -> Dict[str, str]:
        """加载响应模板"""
        return {
            "error": "抱歉，处理您的请求时遇到了问题：{error}",
            "no_knowledge": "很抱歉，我没有找到关于这个问题的相关信息。建议您：\n- 尝试重新表述问题\n- 查阅相关资料\n- 咨询专业人士",
            "partial_success": "我为您找到了一些相关信息，但可能不够完整。{content}",
            "success": "{content}"
        }
    
    def get_execution_statistics(self) -> Dict[str, Any]:
        """获取执行统计信息"""
        if not self.execution_history:
            return {"total_executions": 0}
        
        total_executions = len(self.execution_history)
        successful_executions = sum(1 for h in self.execution_history if h.get("success", False))
        
        return {
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "success_rate": successful_executions / total_executions,
            "recent_executions": self.execution_history[-5:]
        }
    
    def _personalize_response_with_profile(self, response: str, user_profile_context: Dict[str, Any]) -> str:
        """根据用户画像个性化响应"""
        try:
            if not user_profile_context or not user_profile_context.get("user_summary"):
                return response
            
            # 获取用户画像摘要
            user_summary = user_profile_context.get("user_summary", "")
            user_entities = user_profile_context.get("user_entities", [])
            
            # 如果有用户信息，添加个性化的前缀或后缀
            personalization_notes = []
            
            # 基于用户实体添加个性化内容
            if user_entities:
                # 识别用户姓名
                user_names = [entity for entity in user_entities 
                             if len(entity) <= 4 and any('\u4e00' <= char <= '\u9fff' for char in entity)]
                if user_names:
                    # 使用发现的第一个用户名进行个性化
                    user_name = user_names[0]
                    if user_name not in ['我', '用户', '自己']:
                        personalization_notes.append(f"根据我对您({user_name})的了解")
            
            # 基于用户画像摘要添加相关建议
            if user_summary and len(user_summary) > 10:
                # 简单的个性化提示
                if any(keyword in user_summary for keyword in ['职业', '工作', '专业']):
                    personalization_notes.append("结合您的职业背景")
                if any(keyword in user_summary for keyword in ['兴趣', '爱好', '喜欢']):
                    personalization_notes.append("考虑到您的兴趣爱好")
                if any(keyword in user_summary for keyword in ['学习', '研究', '学生']):
                    personalization_notes.append("基于您的学习需求")
            
            # 如果有个性化注释，添加到响应中
            if personalization_notes:
                personalization_prefix = f"💡 {personalization_notes[0]}，"
                # 在响应开头添加个性化前缀
                response = personalization_prefix + response
            
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to personalize response with profile: {e}")
            return response  # 如果个性化失败，返回原始响应