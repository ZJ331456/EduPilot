#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API请求和响应数据模型
定义所有API接口的输入输出结构
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# 枚举类型
# ============================================================================

class QueryTypeEnum(str, Enum):
    """查询类型枚举"""
    DIRECT_ANSWER = "direct_answer"
    CONCEPT_EXPLANATION = "concept_explanation"
    EXAMPLE_REQUEST = "example_request"
    COMPARISON_ANALYSIS = "comparison_analysis"
    PROBLEM_SOLVING = "problem_solving"
    OPEN_ENDED = "open_ended"


class AgentTypeEnum(str, Enum):
    """智能体类型枚举"""
    QUERY_ANALYZER = "query_analyzer"
    ORCHESTRATOR = "orchestrator"  # 原 planner
    DRAFT_WRITER = "draft_writer"
    REVIEWER = "reviewer"
    CURRICULUM_DESIGNER = "curriculum_designer"
    QUIZ_MASTER = "quiz_master"
    TOOL_SPECIALIST = "tool_specialist"
    KNOWLEDGE_MANAGER = "knowledge_manager"
    SOCRATIC_GUIDE = "socratic_guide"
    MEMORY_MANAGER = "memory_manager"

    # 向后兼容
    PLANNER = "planner"
    EXECUTOR = "executor"


class ExecutionStatusEnum(str, Enum):
    """执行状态枚举"""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"
    PENDING = "pending"


# ============================================================================
# 基础模型
# ============================================================================

class BaseResponse(BaseModel):
    """API响应基础模型"""
    model_config = ConfigDict(extra="allow")
    
    success: bool = Field(..., description="请求是否成功")
    message: str = Field(default="", description="响应消息")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间戳")


class ErrorResponse(BaseResponse):
    """错误响应模型"""
    success: bool = Field(default=False, description="请求失败")
    error_code: str = Field(..., description="错误代码")
    error_detail: Optional[Dict[str, Any]] = Field(default=None, description="错误详情")


# ============================================================================
# 查询分析相关模型
# ============================================================================

class QueryAnalysisRequest(BaseModel):
    """查询分析请求"""
    model_config = ConfigDict(extra="allow")
    
    query: str = Field(..., description="用户查询文本", min_length=1)
    user_id: Optional[str] = Field(default=None, description="用户ID")
    session_id: Optional[str] = Field(default=None, description="会话ID")
    context: Optional[Dict[str, Any]] = Field(default=None, description="上下文信息")
    use_llm_refinement: bool = Field(default=True, description="是否使用LLM精修")


class IntentCandidateModel(BaseModel):
    """意图候选模型"""
    name: str = Field(..., description="意图名称")
    score: float = Field(..., description="置信度分数", ge=0, le=1)
    source: str = Field(..., description="来源(heuristic/llm)")
    rationale: str = Field(default="", description="推理原因")
    signals: Dict[str, Any] = Field(default_factory=dict, description="特征信号")


class RetrievalPlanModel(BaseModel):
    """检索计划模型"""
    need_retrieval: bool = Field(..., description="是否需要检索")
    confidence: float = Field(..., description="置信度", ge=0, le=1)
    reason: str = Field(..., description="决策原因")
    core_concepts: List[str] = Field(default_factory=list, description="核心概念")
    related_queries: List[str] = Field(default_factory=list, description="相关查询")
    optimized_queries: List[Dict[str, Any]] = Field(default_factory=list, description="优化查询")
    query_strategy: Dict[str, Any] = Field(default_factory=dict, description="查询策略")


class QueryAnalysisResponse(BaseResponse):
    """查询分析响应"""
    data: Dict[str, Any] = Field(..., description="分析结果数据")
    intent: str = Field(..., description="识别的意图")
    query_type: QueryTypeEnum = Field(..., description="查询类型")
    confidence: float = Field(..., description="置信度", ge=0, le=1)
    candidates: List[IntentCandidateModel] = Field(default_factory=list, description="候选意图列表")
    retrieval_plan: Optional[RetrievalPlanModel] = Field(default=None, description="检索计划")


# ============================================================================
# 规划器相关模型
# ============================================================================

class PlanningRequest(BaseModel):
    """规划请求"""
    model_config = ConfigDict(extra="allow")
    
    query: str = Field(..., description="用户查询")
    query_type: Optional[QueryTypeEnum] = Field(default=None, description="查询类型")
    retrieved_knowledge: Optional[Dict[str, Any]] = Field(default=None, description="检索到的知识")
    user_context: Optional[Dict[str, Any]] = Field(default=None, description="用户上下文")
    session_id: Optional[str] = Field(default=None, description="会话ID")


class ActionItemModel(BaseModel):
    """行动项模型"""
    action_type: str = Field(..., description="行动类型")
    description: str = Field(..., description="行动描述")
    priority: int = Field(default=1, description="优先级", ge=1, le=10)
    parameters: Dict[str, Any] = Field(default_factory=dict, description="行动参数")
    expected_outcome: str = Field(default="", description="期望结果")


class PlanningResponse(BaseResponse):
    """规划响应"""
    data: Dict[str, Any] = Field(..., description="规划结果数据")
    plan_type: str = Field(..., description="计划类型")
    action_items: List[ActionItemModel] = Field(default_factory=list, description="行动项列表")
    estimated_steps: int = Field(default=1, description="预计步骤数")
    reasoning: str = Field(default="", description="规划推理")


# ============================================================================
# 执行器相关模型
# ============================================================================

class ExecutionRequest(BaseModel):
    """执行请求"""
    model_config = ConfigDict(extra="allow")
    
    query: str = Field(..., description="用户查询")
    plan: Dict[str, Any] = Field(..., description="执行计划")
    retrieved_knowledge: Optional[Dict[str, Any]] = Field(default=None, description="检索到的知识")
    user_context: Optional[Dict[str, Any]] = Field(default=None, description="用户上下文")
    session_id: Optional[str] = Field(default=None, description="会话ID")


class ExecutionResponse(BaseResponse):
    """执行响应"""
    data: Dict[str, Any] = Field(..., description="执行结果数据")
    response_text: str = Field(..., description="生成的响应文本")
    execution_status: ExecutionStatusEnum = Field(..., description="执行状态")
    actions_completed: List[str] = Field(default_factory=list, description="已完成的行动")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="执行元数据")


# ============================================================================
# 工作流相关模型
# ============================================================================

class LearningSessionRequest(BaseModel):
    """学习会话请求"""
    model_config = ConfigDict(extra="allow")
    
    user_id: str = Field(..., description="用户ID")
    query: str = Field(..., description="用户查询", min_length=1)
    session_id: Optional[str] = Field(default=None, description="会话ID(可选，系统自动生成)")
    conversation_history: Optional[List[Dict[str, str]]] = Field(default=None, description="对话历史")
    user_preferences: Optional[Dict[str, Any]] = Field(default=None, description="用户偏好设置")
    workflow_config: Optional[Dict[str, Any]] = Field(default=None, description="工作流配置")


class WorkflowStepResult(BaseModel):
    """工作流步骤结果"""
    step_name: str = Field(..., description="步骤名称")
    agent_name: str = Field(..., description="执行的智能体")
    status: ExecutionStatusEnum = Field(..., description="执行状态")
    result: Dict[str, Any] = Field(default_factory=dict, description="步骤结果")
    duration_ms: float = Field(default=0, description="执行时长(毫秒)")
    error: Optional[str] = Field(default=None, description="错误信息")


class SocraticDialogueInfo(BaseModel):
    """苏格拉底式对话信息
    
    对齐 socratic_guide.py 的 SocraticGuideResponse 结构：
    - guidance_text -> current_question
    - question_type -> question_type
    - understanding_level -> understanding_level
    - next_steps -> next_steps
    - metadata -> metadata
    """
    is_socratic_mode: bool = Field(default=False, description="是否处于苏格拉底式对话模式")
    current_question: Optional[str] = Field(default=None, description="当前苏格拉底式问题（对应guidance_text）")
    question_type: Optional[str] = Field(default="clarifying", description="问题类型（对齐socratic_guide.py）")
    understanding_level: Optional[str] = Field(default="unknown", description="理解水平（对齐socratic_guide.py）")
    question_purpose: Optional[str] = Field(default=None, description="问题目的")
    questions_asked: int = Field(default=0, description="已提问次数")
    max_questions: int = Field(default=5, description="最大提问次数")
    dialogue_history: List[Dict[str, str]] = Field(default_factory=list, description="对话历史")
    guidance_strategy: Optional[str] = Field(default=None, description="引导策略")
    next_steps: List[str] = Field(default_factory=list, description="下一步建议（对齐socratic_guide.py）")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据（对齐socratic_guide.py）")


class LearningSessionResponse(BaseResponse):
    """学习会话响应
    
    对齐 LearningWorkflowState 的核心字段：
    - session_id: state["session_id"]
    - query: state["user_query"]
    - response: 从 execution_result 或 messages 提取
    - analysis: state["interpretation"]
    - plan: state["plan"]
    - execution_summary: state["execution_result"]
    - workflow_complete: state["workflow_complete"]
    - waiting_for_user: state["waiting_for_user"]
    """
    session_id: str = Field(..., description="会话ID")
    user_id: str = Field(..., description="用户ID")
    query: str = Field(..., description="用户查询")
    response: str = Field(..., description="系统响应")
    workflow_steps: List[WorkflowStepResult] = Field(default_factory=list, description="工作流步骤")
    analysis: Dict[str, Any] = Field(default_factory=dict, description="查询分析结果")
    plan: Dict[str, Any] = Field(default_factory=dict, description="学习计划")
    execution_summary: Dict[str, Any] = Field(default_factory=dict, description="执行摘要")
    next_suggestions: List[str] = Field(default_factory=list, description="下一步建议")
    
    # Workflow 状态字段（对齐 LearningWorkflowState）
    workflow_complete: bool = Field(default=False, description="工作流是否完成")
    waiting_for_user: bool = Field(default=False, description="是否等待用户输入")
    conversation_stage: Optional[str] = Field(default=None, description="对话阶段")
    understanding_level: Optional[str] = Field(default=None, description="理解水平")
    conversation_round: int = Field(default=0, description="对话轮次")
    
    # 苏格拉底式对话相关字段
    socratic_dialogue: SocraticDialogueInfo = Field(default_factory=SocraticDialogueInfo, description="苏格拉底式对话信息")


class ContinueSessionRequest(BaseModel):
    """继续会话请求"""
    model_config = ConfigDict(extra="allow")
    
    session_id: str = Field(..., description="会话ID")
    user_response: str = Field(..., description="用户响应", min_length=1)
    user_id: str = Field(..., description="用户ID")


# ============================================================================
# 记忆管理相关模型
# ============================================================================

class MemoryAnalysisRequest(BaseModel):
    """记忆分析请求"""
    model_config = ConfigDict(extra="allow")
    
    user_id: str = Field(..., description="用户ID")
    session_id: str = Field(..., description="会话ID")
    interaction_data: Dict[str, Any] = Field(..., description="交互数据")


class UserProfileRequest(BaseModel):
    """用户画像请求"""
    user_id: str = Field(..., description="用户ID")
    include_triples: bool = Field(default=False, description="是否包含三元组")
    include_emotions: bool = Field(default=False, description="是否包含情感分析")
    include_patterns: bool = Field(default=False, description="是否包含学习模式")


class UserProfileResponse(BaseResponse):
    """用户画像响应"""
    user_id: str = Field(..., description="用户ID")
    profile: Dict[str, Any] = Field(..., description="用户画像数据")
    triples: Optional[List[Dict[str, Any]]] = Field(default=None, description="知识三元组")
    emotions: Optional[Dict[str, Any]] = Field(default=None, description="情感分析")
    learning_patterns: Optional[List[Dict[str, Any]]] = Field(default=None, description="学习模式")
    statistics: Dict[str, Any] = Field(default_factory=dict, description="统计信息")


class SessionMemoryRequest(BaseModel):
    """会话记忆请求"""
    session_id: str = Field(..., description="会话ID")
    user_id: Optional[str] = Field(default=None, description="用户ID")


class SessionMemoryResponse(BaseResponse):
    """会话记忆响应"""
    session_id: str = Field(..., description="会话ID")
    memory_data: Dict[str, Any] = Field(..., description="会话记忆数据")
    interaction_count: int = Field(default=0, description="交互次数")
    quality_score: float = Field(default=0, description="质量分数", ge=0, le=1)


# ============================================================================
# 知识检索相关模型
# ============================================================================

class KnowledgeRetrievalRequest(BaseModel):
    """知识检索请求"""
    model_config = ConfigDict(extra="allow")
    
    query: str = Field(..., description="检索查询")
    top_k: int = Field(default=5, description="返回结果数量", ge=1, le=20)
    retrieval_strategy: Optional[str] = Field(default="hybrid", description="检索策略")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="过滤条件")


class KnowledgeRetrievalResponse(BaseResponse):
    """知识检索响应"""
    query: str = Field(..., description="检索查询")
    results: List[Dict[str, Any]] = Field(default_factory=list, description="检索结果")
    total_count: int = Field(default=0, description="结果总数")
    retrieval_time_ms: float = Field(default=0, description="检索耗时(毫秒)")


# ============================================================================
# 苏格拉底引导相关模型
# ============================================================================

class SocraticGuideRequest(BaseModel):
    """苏格拉底引导请求"""
    model_config = ConfigDict(extra="allow")
    
    user_query: str = Field(..., description="用户查询")
    user_response: Optional[str] = Field(default=None, description="用户响应")
    knowledge_context: Optional[Dict[str, Any]] = Field(default=None, description="知识上下文")
    session_id: Optional[str] = Field(default=None, description="会话ID")
    guidance_level: Optional[str] = Field(default="moderate", description="引导强度(light/moderate/strong)")


class SocraticGuideResponse(BaseResponse):
    """苏格拉底引导响应"""
    guidance_text: str = Field(..., description="引导文本")
    question_type: str = Field(..., description="问题类型")
    understanding_level: str = Field(..., description="理解水平")
    next_steps: List[str] = Field(default_factory=list, description="下一步建议")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


# ============================================================================
# 健康检查和系统状态模型
# ============================================================================

class HealthCheckResponse(BaseResponse):
    """健康检查响应"""
    status: str = Field(default="healthy", description="系统状态")
    version: str = Field(default="3.0", description="API版本")
    agents_status: Dict[str, str] = Field(default_factory=dict, description="各智能体状态")
    uptime_seconds: float = Field(default=0, description="运行时长(秒)")


class SystemStatsResponse(BaseResponse):
    """系统统计响应"""
    total_sessions: int = Field(default=0, description="总会话数")
    active_sessions: int = Field(default=0, description="活跃会话数")
    total_queries: int = Field(default=0, description="总查询数")
    average_response_time_ms: float = Field(default=0, description="平均响应时间(毫秒)")
    agents_metrics: Dict[str, Any] = Field(default_factory=dict, description="智能体指标")

