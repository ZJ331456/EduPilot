#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
枚举类定义
"""

from enum import Enum

class QueryType(str, Enum):
    """查询类型枚举"""
    KNOWLEDGE_RETRIEVAL = "knowledge_retrieval"  # 知识检索
    DIRECT_ANSWER = "direct_answer"  # 直接回答
    SOCRATIC_DIALOGUE = "socratic_dialogue"  # 苏格拉底对话
    LEARNING_GUIDANCE = "learning_guidance"  # 学习指导
    CONCEPT_EXPLANATION = "concept_explanation"  # 概念解释

class ExecutionStatus(str, Enum):
    """执行状态枚举"""
    PENDING = "pending"  # 待处理
    RUNNING = "running"  # 运行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败
    CANCELLED = "cancelled"  # 已取消

class ConversationStage(str, Enum):
    """对话阶段枚举"""
    INITIAL_QUERY = "initial_query"  # 初始查询
    KNOWLEDGE_GATHERING = "knowledge_gathering"  # 知识收集
    UNDERSTANDING_CHECK = "understanding_check"  # 理解检查
    SOCRATIC_QUESTIONING = "socratic_questioning"  # 苏格拉底式提问
    DEEPER_EXPLORATION = "deeper_exploration"  # 深入探索
    COMPREHENSION_VALIDATION = "comprehension_validation"  # 理解验证
    CONCLUSION = "conclusion"  # 结论

class UnderstandingLevel(str, Enum):
    """理解水平枚举"""
    NO_UNDERSTANDING = "no_understanding"  # 不理解
    SURFACE_UNDERSTANDING = "surface_understanding"  # 表面理解
    BASIC_UNDERSTANDING = "basic_understanding"  # 基础理解
    GOOD_UNDERSTANDING = "good_understanding"  # 良好理解
    DEEP_UNDERSTANDING = "deep_understanding"  # 深度理解
    MASTERY = "mastery"  # 精通
    
    @property
    def level_value(self) -> int:
        """获取理解水平的数值，用于比较"""
        mapping = {
            "no_understanding": 0,
            "surface_understanding": 1,
            "basic_understanding": 2,
            "good_understanding": 3,
            "deep_understanding": 4,
            "mastery": 5
        }
        return mapping.get(self.value, 0)

class PlanType(str, Enum):
    """计划类型"""
    DIRECT_ANSWER = "direct_answer"  # 直接回答
    GUIDED_LEARNING = "guided_learning"  # 引导式学习
    KNOWLEDGE_EXPLORATION = "knowledge_exploration"  # 知识探索
    PROBLEM_SOLVING = "problem_solving"  # 问题解决
    CONCEPT_BUILDING = "concept_building"  # 概念构建

class ActionType(str, Enum):
    """行动类型"""
    PROVIDE_ANSWER = "provide_answer"  # 提供答案
    ASK_QUESTION = "ask_question"  # 提问
    EXPLAIN_CONCEPT = "explain_concept"  # 解释概念
    SHOW_EXAMPLE = "show_example"  # 展示示例
    GUIDE_THINKING = "guide_thinking"  # 引导思考
    SUMMARIZE_LEARNING = "summarize_learning"  # 总结学习
    RECOMMEND_RESOURCES = "recommend_resources"  # 推荐资源

class ProfileDimension(str, Enum):
    """用户画像维度枚举"""
    BASIC_INFO = "basic_info"  # 基本信息
    INTERESTS = "interests"  # 兴趣爱好
    LEARNING_STYLE = "learning_style"  # 学习风格
    KNOWLEDGE_LEVEL = "knowledge_level"  # 知识水平
    PERSONALITY = "personality"  # 性格特征
    GOALS = "goals"  # 目标动机
    SKILLS = "skills"  # 技能能力
    PREFERENCES = "preferences"  # 偏好设置
    SOCIAL = "social"  # 社交关系
    WORK = "work"  # 工作职业

class EmotionType(str, Enum):
    """情感类型枚举"""
    POSITIVE = "positive"  # 积极情感
    NEGATIVE = "negative"  # 消极情感
    NEUTRAL = "neutral"  # 中性情感
    EXCITED = "excited"  # 兴奋
    CURIOUS = "curious"  # 好奇
    CONFUSED = "confused"  # 困惑
    ANXIOUS = "anxious"  # 焦虑
    SATISFIED = "satisfied"  # 满意

class LearningPattern(str, Enum):
    """学习模式枚举"""
    VISUAL = "visual"  # 视觉型
    AUDITORY = "auditory"  # 听觉型
    KINESTHETIC = "kinesthetic"  # 动觉型
    READING = "reading"  # 阅读型
    SOCIAL = "social"  # 社交型
    SOLITARY = "solitary"  # 独立型 