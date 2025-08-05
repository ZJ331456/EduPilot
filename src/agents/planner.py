#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
规划器智能体
根据查询、检索到的知识和用户响应制定行动计划
"""

import logging
from typing import Dict, Any, List, Optional

from utils import BaseAgent, AgentState, QueryType
from utils.llm import Message, MessageRole

from utils import PlanType, ActionType

class PlannerAgent(BaseAgent):
    """规划器智能体
    
    根据查询、检索到的知识和用户响应制定行动计划
    """
    
    def __init__(self):
        super().__init__(
            name="Planner",
            description="制定行动计划和学习路径"
        )
        self.plan_history = []  # 计划历史
        self.max_plan_steps = 10  # 最大计划步骤数
    
    def can_execute(self, state: AgentState) -> bool:
        """检查是否可以执行"""
        return (
            state.interpretation is not None
        )
    
    async def execute(self, state: AgentState) -> AgentState:
        """执行计划制定"""
        try:
            # 1. 分析当前状态
            situation_analysis = self._analyze_situation(state)
            
            # 2. 确定计划类型
            plan_type = self._determine_plan_type(state, situation_analysis)
            
            # 3. 生成行动计划
            action_plan = self._generate_action_plan(state, plan_type, situation_analysis)
            
            # 4. 优化和验证计划
            optimized_plan = self._optimize_plan(action_plan, state)
            
            # 5. 更新状态
            state.plan = optimized_plan
            state.plan_type = plan_type
            
            # 6. 记录计划历史
            self.plan_history.append({
                "plan": optimized_plan,
                "plan_type": plan_type,
                "situation": situation_analysis,
                "timestamp": state.timestamp,
                "session_id": state.session_id
            })
            
            self.logger.info(f"Generated plan with type: {plan_type.value}, {len(optimized_plan['actions'])} actions")
            
            return state
            
        except Exception as e:
            self.logger.error(f"Planning failed: {e}")
            state.set_error(
                "planning_error",
                f"Failed to generate plan: {str(e)}"
            )
            return state
    
    def _analyze_situation(self, state: AgentState) -> Dict[str, Any]:
        """分析当前情况"""
        analysis = {
            "query_complexity": self._assess_query_complexity(state.user_query),
            "knowledge_availability": self._assess_knowledge_availability(state),
            "user_engagement": self._assess_user_engagement(state),
            "learning_progress": self._assess_learning_progress(state),
            "context_richness": self._assess_context_richness(state)
        }
        
        # 综合评估
        analysis["overall_complexity"] = (
            analysis["query_complexity"] * 0.3 +
            analysis["knowledge_availability"] * 0.2 +
            analysis["context_richness"] * 0.2 +
            (1 - analysis["user_engagement"]) * 0.15 +
            (1 - analysis["learning_progress"]) * 0.15
        )
        
        return analysis
    
    def _assess_query_complexity(self, query: str) -> float:
        """评估查询复杂度"""
        # 基于查询长度、关键词数量等评估复杂度
        complexity_indicators = [
            len(query.split()) > 10,  # 长查询
            "为什么" in query or "怎么" in query,  # 解释性问题
            "比较" in query or "区别" in query,  # 比较性问题
            "应用" in query or "实践" in query,  # 应用性问题
            "分析" in query or "评价" in query,  # 分析性问题
        ]
        
        return sum(complexity_indicators) / len(complexity_indicators)
    
    def _assess_knowledge_availability(self, state: AgentState) -> float:
        """评估知识可用性"""
        if not hasattr(state, 'retrieved_knowledge') or not state.retrieved_knowledge:
            return 0.0
        
        results = state.retrieved_knowledge.get("results", [])
        if not results:
            return 0.1
        
        # 基于检索结果数量和质量评估
        num_results = len(results)
        avg_relevance = sum(r.get("relevance_score", 0) for r in results) / num_results
        
        availability = min((num_results / 5) * 0.5 + avg_relevance * 0.5, 1.0)
        return availability
    
    def _assess_user_engagement(self, state: AgentState) -> float:
        """评估用户参与度"""
        if not state.user_responses:
            return 0.5  # 中等参与度（初始状态）
        
        # 基于响应长度和频率评估
        avg_response_length = sum(len(r) for r in state.user_responses) / len(state.user_responses)
        response_frequency = len(state.user_responses) / max(len(state.socratic_questions), 1)
        
        engagement = min((avg_response_length / 100) * 0.6 + response_frequency * 0.4, 1.0)
        return engagement
    
    def _assess_learning_progress(self, state: AgentState) -> float:
        """评估学习进度"""
        if not hasattr(state, 'response_analyses') or not state.response_analyses:
            return 0.3  # 初始进度
        
        # 基于响应质量的改善评估进度
        quality_scores = []
        for analysis in state.response_analyses:
            quality = analysis.get("quality", "medium")
            if quality == "high":
                quality_scores.append(1.0)
            elif quality == "medium":
                quality_scores.append(0.6)
            else:
                quality_scores.append(0.3)
        
        if len(quality_scores) > 1:
            # 计算进步趋势
            recent_avg = sum(quality_scores[-2:]) / 2
            overall_avg = sum(quality_scores) / len(quality_scores)
            progress = min(recent_avg, overall_avg)
        else:
            progress = quality_scores[0] if quality_scores else 0.3
        
        return progress
    
    def _assess_context_richness(self, state: AgentState) -> float:
        """评估上下文丰富度"""
        richness_factors = [
            bool(state.interpretation),
            bool(state.retrieved_knowledge),
            bool(state.socratic_questions),
            bool(state.user_responses),
            len(state.socratic_questions) > 1,
            len(state.user_responses) > 1
        ]
        
        return sum(richness_factors) / len(richness_factors)
    
    def _determine_plan_type(self, state: AgentState, analysis: Dict[str, Any]) -> PlanType:
        """确定计划类型"""
        # 基于查询类型和情况分析确定计划类型
        if state.query_type == QueryType.DIRECT_ANSWER:
            if analysis["query_complexity"] < 0.3:
                return PlanType.DIRECT_ANSWER
            else:
                return PlanType.GUIDED_LEARNING
        
        elif state.query_type == QueryType.CONCEPT_EXPLANATION:
            if analysis["knowledge_availability"] > 0.7:
                if analysis["user_engagement"] > 0.6:
                    return PlanType.CONCEPT_BUILDING
                else:
                    return PlanType.KNOWLEDGE_EXPLORATION
            else:
                return PlanType.GUIDED_LEARNING
        
        elif state.query_type == QueryType.KNOWLEDGE_RETRIEVAL:
            return PlanType.KNOWLEDGE_EXPLORATION
        
        elif state.query_type == QueryType.LEARNING_GUIDANCE:
            return PlanType.GUIDED_LEARNING
        
        # 注意：QueryType中没有PROBLEM_SOLVING，使用其他逻辑判断
        # elif state.query_type == QueryType.PROBLEM_SOLVING:
        #     return PlanType.PROBLEM_SOLVING
        
        else:
            # 默认计划类型
            if analysis["overall_complexity"] > 0.6:
                return PlanType.GUIDED_LEARNING
            else:
                return PlanType.DIRECT_ANSWER
    
    def _generate_action_plan(self, state: AgentState, plan_type: PlanType, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """生成行动计划"""
        plan = {
            "type": plan_type,
            "priority": self._calculate_plan_priority(analysis),
            "estimated_duration": self._estimate_duration(plan_type, analysis),
            "actions": [],
            "success_criteria": [],
            "fallback_options": []
        }
        
        # 根据计划类型生成具体行动
        if plan_type == PlanType.DIRECT_ANSWER:
            plan["actions"] = self._generate_direct_answer_actions(state, analysis)
        
        elif plan_type == PlanType.GUIDED_LEARNING:
            plan["actions"] = self._generate_guided_learning_actions(state, analysis)
        
        elif plan_type == PlanType.KNOWLEDGE_EXPLORATION:
            plan["actions"] = self._generate_exploration_actions(state, analysis)
        
        elif plan_type == PlanType.PROBLEM_SOLVING:
            plan["actions"] = self._generate_problem_solving_actions(state, analysis)
        
        elif plan_type == PlanType.CONCEPT_BUILDING:
            plan["actions"] = self._generate_concept_building_actions(state, analysis)
        
        # 添加成功标准
        plan["success_criteria"] = self._define_success_criteria(plan_type, state)
        
        # 添加备选方案
        plan["fallback_options"] = self._define_fallback_options(plan_type, state)
        
        return plan
    
    def _generate_direct_answer_actions(self, state: AgentState, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成直接回答行动"""
        actions = [
            {
                "type": ActionType.PROVIDE_ANSWER,
                "description": "基于检索到的知识提供直接答案",
                "priority": 1,
                "parameters": {
                    "answer_style": "concise",
                    "include_sources": True,
                    "confidence_level": analysis.get("knowledge_availability", 0.5)
                }
            }
        ]
        
        # 如果知识可用性较低，添加补充行动
        if analysis.get("knowledge_availability", 0) < 0.5:
            actions.append({
                "type": ActionType.RECOMMEND_RESOURCES,
                "description": "推荐额外的学习资源",
                "priority": 2,
                "parameters": {
                    "resource_types": ["external_links", "related_concepts"]
                }
            })
        
        return actions
    
    def _generate_guided_learning_actions(self, state: AgentState, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成引导式学习行动"""
        actions = []
        
        # 1. 评估当前理解
        if not state.socratic_questions:
            actions.append({
                "type": ActionType.ASK_QUESTION,
                "description": "评估用户当前理解水平",
                "priority": 1,
                "parameters": {
                    "question_type": "assessment",
                    "focus": "prior_knowledge"
                }
            })
        
        # 2. 提供概念解释
        if analysis.get("knowledge_availability", 0) > 0.3:
            actions.append({
                "type": ActionType.EXPLAIN_CONCEPT,
                "description": "解释核心概念",
                "priority": 2,
                "parameters": {
                    "explanation_depth": "adaptive",
                    "use_examples": True
                }
            })
        
        # 3. 引导思考
        actions.append({
            "type": ActionType.GUIDE_THINKING,
            "description": "引导深入思考",
            "priority": 3,
            "parameters": {
                "thinking_direction": "analytical",
                "encourage_questions": True
            }
        })
        
        # 4. 总结学习
        if len(state.user_responses) > 1:
            actions.append({
                "type": ActionType.SUMMARIZE_LEARNING,
                "description": "总结学习要点",
                "priority": 4,
                "parameters": {
                    "include_progress": True,
                    "highlight_insights": True
                }
            })
        
        return actions
    
    def _generate_exploration_actions(self, state: AgentState, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成知识探索行动"""
        actions = [
            {
                "type": ActionType.EXPLAIN_CONCEPT,
                "description": "详细解释相关概念",
                "priority": 1,
                "parameters": {
                    "explanation_depth": "comprehensive",
                    "include_relationships": True
                }
            },
            {
                "type": ActionType.SHOW_EXAMPLE,
                "description": "提供具体示例",
                "priority": 2,
                "parameters": {
                    "example_types": ["practical", "analogical"],
                    "relate_to_query": True
                }
            }
        ]
        
        # 如果用户参与度高，添加深入探索
        if analysis.get("user_engagement", 0) > 0.6:
            actions.append({
                "type": ActionType.ASK_QUESTION,
                "description": "引导深入探索",
                "priority": 3,
                "parameters": {
                    "question_type": "exploratory",
                    "encourage_discovery": True
                }
            })
        
        return actions
    
    def _generate_problem_solving_actions(self, state: AgentState, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成问题解决行动"""
        return [
            {
                "type": ActionType.GUIDE_THINKING,
                "description": "引导问题分析",
                "priority": 1,
                "parameters": {
                    "thinking_direction": "problem_decomposition",
                    "step_by_step": True
                }
            },
            {
                "type": ActionType.SHOW_EXAMPLE,
                "description": "展示解决方法",
                "priority": 2,
                "parameters": {
                    "example_types": ["solution_process"],
                    "highlight_reasoning": True
                }
            },
            {
                "type": ActionType.ASK_QUESTION,
                "description": "验证理解",
                "priority": 3,
                "parameters": {
                    "question_type": "verification",
                    "focus": "solution_understanding"
                }
            }
        ]
    
    def _generate_concept_building_actions(self, state: AgentState, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成概念构建行动"""
        return [
            {
                "type": ActionType.EXPLAIN_CONCEPT,
                "description": "构建概念框架",
                "priority": 1,
                "parameters": {
                    "explanation_depth": "structural",
                    "build_connections": True
                }
            },
            {
                "type": ActionType.GUIDE_THINKING,
                "description": "引导概念联系",
                "priority": 2,
                "parameters": {
                    "thinking_direction": "conceptual_connections",
                    "encourage_synthesis": True
                }
            },
            {
                "type": ActionType.SHOW_EXAMPLE,
                "description": "提供应用示例",
                "priority": 3,
                "parameters": {
                    "example_types": ["application", "transfer"],
                    "demonstrate_utility": True
                }
            }
        ]
    
    def _calculate_plan_priority(self, analysis: Dict[str, Any]) -> int:
        """计算计划优先级"""
        # 基于复杂度和紧急性计算优先级
        complexity = analysis.get("overall_complexity", 0.5)
        engagement = analysis.get("user_engagement", 0.5)
        
        if complexity > 0.7 or engagement < 0.3:
            return 1  # 高优先级
        elif complexity > 0.4 or engagement < 0.6:
            return 2  # 中优先级
        else:
            return 3  # 低优先级
    
    def _estimate_duration(self, plan_type: PlanType, analysis: Dict[str, Any]) -> str:
        """估算执行时长"""
        duration_map = {
            PlanType.DIRECT_ANSWER: "short",  # 1-2分钟
            PlanType.GUIDED_LEARNING: "medium",  # 5-10分钟
            PlanType.KNOWLEDGE_EXPLORATION: "medium",  # 5-15分钟
            PlanType.PROBLEM_SOLVING: "long",  # 10-20分钟
            PlanType.CONCEPT_BUILDING: "long"  # 15-30分钟
        }
        
        base_duration = duration_map.get(plan_type, "medium")
        
        # 根据复杂度调整
        complexity = analysis.get("overall_complexity", 0.5)
        if complexity > 0.7 and base_duration != "long":
            if base_duration == "short":
                return "medium"
            else:
                return "long"
        
        return base_duration
    
    def _define_success_criteria(self, plan_type: PlanType, state: AgentState) -> List[str]:
        """定义成功标准"""
        criteria_map = {
            PlanType.DIRECT_ANSWER: [
                "用户获得了准确的答案",
                "答案基于可靠的知识源",
                "用户表示满意"
            ],
            PlanType.GUIDED_LEARNING: [
                "用户展现了理解的进步",
                "用户能够回答引导性问题",
                "学习目标得到实现"
            ],
            PlanType.KNOWLEDGE_EXPLORATION: [
                "用户获得了全面的概念理解",
                "相关知识点得到充分探索",
                "用户能够建立知识联系"
            ],
            PlanType.PROBLEM_SOLVING: [
                "问题得到有效解决",
                "用户理解解决过程",
                "用户能够应用解决方法"
            ],
            PlanType.CONCEPT_BUILDING: [
                "概念框架得到构建",
                "用户能够解释概念关系",
                "知识结构得到完善"
            ]
        }
        
        return criteria_map.get(plan_type, ["用户需求得到满足"])
    
    def _define_fallback_options(self, plan_type: PlanType, state: AgentState) -> List[Dict[str, Any]]:
        """定义备选方案"""
        fallbacks = [
            {
                "condition": "用户理解困难",
                "action": "简化解释，提供更多示例"
            },
            {
                "condition": "知识不足",
                "action": "推荐外部资源，承认知识限制"
            },
            {
                "condition": "用户失去兴趣",
                "action": "调整教学方式，增加互动性"
            }
        ]
        
        return fallbacks
    
    def _optimize_plan(self, plan: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
        """优化计划"""
        # 检查行动数量
        if len(plan["actions"]) > self.max_plan_steps:
            # 保留最重要的行动
            plan["actions"] = sorted(
                plan["actions"],
                key=lambda x: x.get("priority", 999)
            )[:self.max_plan_steps]
        
        # 添加执行顺序
        for i, action in enumerate(plan["actions"]):
            action["execution_order"] = i + 1
        
        # 添加计划元数据
        plan["metadata"] = {
            "generated_at": state.timestamp,
            "session_id": state.session_id,
            "total_actions": len(plan["actions"]),
            "optimization_applied": True
        }
        
        return plan
    
    def get_next_action(self, state: AgentState) -> Optional[Dict[str, Any]]:
        """获取下一个要执行的行动"""
        if not state.plan or not state.plan.get("actions"):
            return None
        
        # 找到下一个未执行的行动
        for action in state.plan["actions"]:
            if not action.get("executed", False):
                return action
        
        return None
    
    def mark_action_completed(self, state: AgentState, action_id: int, result: Dict[str, Any]):
        """标记行动完成"""
        if not state.plan or not state.plan.get("actions"):
            return
        
        for action in state.plan["actions"]:
            if action.get("execution_order") == action_id:
                action["executed"] = True
                action["execution_result"] = result
                action["completed_at"] = state.timestamp
                break
    
    def is_plan_completed(self, state: AgentState) -> bool:
        """检查计划是否完成"""
        if not state.plan or not state.plan.get("actions"):
            return True
        
        return all(action.get("executed", False) for action in state.plan["actions"])
    
    def get_plan_progress(self, state: AgentState) -> Dict[str, Any]:
        """获取计划进度"""
        if not state.plan or not state.plan.get("actions"):
            return {"progress": 0, "completed": 0, "total": 0}
        
        total_actions = len(state.plan["actions"])
        completed_actions = sum(1 for action in state.plan["actions"] if action.get("executed", False))
        
        return {
            "progress": completed_actions / total_actions if total_actions > 0 else 0,
            "completed": completed_actions,
            "total": total_actions,
            "current_action": self.get_next_action(state)
        }