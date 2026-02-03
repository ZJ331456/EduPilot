#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流相关API路由
提供完整的学习工作流接口
直接使用 LangGraph 实现
"""

import time
import logging
import uuid
from typing import Dict, Any, List

from fastapi import APIRouter, Depends, HTTPException, status

from ..models import (
    LearningSessionRequest,
    LearningSessionResponse,
    ContinueSessionRequest,
    WorkflowStepResult,
    ExecutionStatusEnum,
    SocraticDialogueInfo,
)
from ..dependencies import (
    get_learning_workflow_instance,
    handle_workflow_error,
    log_request,
    log_response,
    validate_user_id,
    validate_query,
)
from ..utils import workflow_limiter
# 直接使用 LangGraph 工作流
from src.core.workflow import LangGraphLearningWorkflow


logger = logging.getLogger("EduPilotAPI.Workflow")
router = APIRouter()


def extract_socratic_dialogue_info(result: Dict[str, Any]) -> SocraticDialogueInfo:
    """从工作流结果中提取苏格拉底式对话信息
    
    对齐 socratic_guide.py 的数据结构：
    - 从 socratic_guidance 字段提取数据
    - 保持与 SocraticGuideResponse 的一致性
    """
    try:
        # 优先从 socratic_guidance 字段提取（对齐 socratic_guide.py）
        socratic_guidance = result.get("socratic_guidance", {})
        
        # 检查是否有苏格拉底式问题
        socratic_question = result.get("socratic_question", "")
        if not socratic_question and socratic_guidance:
            # 从 socratic_guidance 中提取引导文本作为问题
            socratic_question = socratic_guidance.get("guidance_text", "")
        
        is_socratic_mode = bool(socratic_question) or result.get("waiting_for_user", False)
        
        # 提取问题类型和目的（对齐 socratic_guide.py 的字段）
        question_type = socratic_guidance.get("question_type", "clarifying")
        question_purpose = socratic_guidance.get("purpose", "")
        
        # 如果没有从 socratic_guidance 获取到，尝试从其他字段获取
        if not question_type and socratic_question:
            question_data = result.get("socratic_questions", [])
            if question_data and isinstance(question_data, list) and len(question_data) > 0:
                last_question = question_data[-1]
                if isinstance(last_question, dict):
                    question_type = last_question.get("type", "clarifying")
                    question_purpose = last_question.get("purpose", "")
        
        # 🔧 修复：正确计算已提问次数
        # 确保 socratic_questions 列表存在且正确计算长度
        socratic_questions = result.get("socratic_questions", [])
        if not isinstance(socratic_questions, list):
            socratic_questions = []
        
        # 过滤掉空问题，确保只计算有效问题
        valid_questions = [q for q in socratic_questions if q and (isinstance(q, str) and q.strip()) or (isinstance(q, dict) and q.get("question", "").strip())]
        questions_asked = len(valid_questions)
        
        logger.debug(f"苏格拉底问题统计: 总数={len(socratic_questions)}, 有效数={questions_asked}")
        
        # 构建对话历史
        dialogue_history = []
        messages = result.get("messages", [])
        for msg in messages:
            if isinstance(msg, dict) and "role" in msg and "content" in msg:
                dialogue_history.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        # 提取理解水平（对齐 socratic_guide.py）
        understanding_level = socratic_guidance.get("understanding_level", result.get("understanding_level", "unknown"))
        
        # 提取下一步建议（对齐 socratic_guide.py）
        next_steps = socratic_guidance.get("next_steps", [])
        
        # 提取元数据（对齐 socratic_guide.py）
        metadata = socratic_guidance.get("metadata", {})
        
        # 确定引导策略（基于理解水平）
        guidance_strategy = None
        if is_socratic_mode:
            if understanding_level in ["beginner", "low"]:
                guidance_strategy = "基础引导"
            elif understanding_level in ["intermediate", "medium"]:
                guidance_strategy = "深度探索"
            else:
                guidance_strategy = "高级思辨"
        
        return SocraticDialogueInfo(
            is_socratic_mode=is_socratic_mode,
            current_question=socratic_question,
            question_type=question_type,
            understanding_level=understanding_level,
            question_purpose=question_purpose,
            questions_asked=questions_asked,
            max_questions=5,  # 默认最大提问次数
            dialogue_history=dialogue_history,
            guidance_strategy=guidance_strategy,
            next_steps=next_steps,
            metadata=metadata
        )
        
    except Exception as e:
        logger.warning(f"提取苏格拉底式对话信息失败: {e}")
        return SocraticDialogueInfo()


# ============================================================================
# 学习会话路由
# ============================================================================

@router.post(
    "/session/start",
    response_model=LearningSessionResponse,
    summary="开始学习会话",
    description="启动一个完整的学习会话，包含查询分析、规划和执行全流程",
)
async def start_learning_session(
    request: LearningSessionRequest,
    workflow: LangGraphLearningWorkflow = Depends(get_learning_workflow_instance),
):
    """
    开始学习会话接口
    
    这是最核心的API，执行完整的三步工作流：
    1. 查询分析 (QueryAnalyzer)
    2. 学习规划 (Planner)
    3. 计划执行 (Executor)
    
    返回：
    - 完整的学习响应
    - 各步骤的详细结果
    - 下一步建议
    """
    start_time = time.time()
    
    try:
        # 验证输入
        user_id = validate_user_id(request.user_id)
        query = validate_query(request.query)
        
        log_request("workflow/session/start", {
            "user_id": user_id,
            "query": query[:100],
        })
        
        # 生成会话ID
        session_id = request.session_id or str(uuid.uuid4())
        
        # 准备工作流配置
        workflow_config = request.workflow_config or {}
        
        # 执行完整工作流
        logger.info(f"开始执行工作流 - session_id={session_id}, user_id={user_id}")
        
        # 准备用户上下文
        user_context = {
            "user_id": user_id,
            "preferences": request.user_preferences or {},
        }
        
        result = await workflow_limiter.run(
            workflow.process_query(
                user_query=query,
                session_id=session_id,
                user_context=user_context,
                workflow_config=workflow_config,
            )
        )
        
        # 检查工作流执行结果
        if not result or not result.get("success", False):
            error_msg = result.get("error", "工作流执行失败") if result else "工作流无响应"
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg,
            )
        
        # 提取工作流结果
        response_text = result.get("response", "")
        analysis = result.get("analysis", {})
        plan = result.get("plan", {})
        execution_summary = result.get("execution_summary", {})
        
        # 构建工作流步骤结果
        workflow_steps: List[WorkflowStepResult] = []
        
        # 步骤1: 查询分析
        if "analysis" in result and result["analysis"]:
            workflow_steps.append(WorkflowStepResult(
                step_name="query_analysis",
                agent_name="QueryAnalyzer",
                status=ExecutionStatusEnum.SUCCESS,
                result=result["analysis"],
                duration_ms=result.get("performance_data", {}).get("query_analyzer_ms", 0),
            ))
        
        # 步骤2: 编排/规划
        if "plan" in result and result["plan"]:
            workflow_steps.append(WorkflowStepResult(
                step_name="orchestration",
                agent_name="Orchestrator",
                status=ExecutionStatusEnum.SUCCESS,
                result=result["plan"],
                duration_ms=result.get("performance_data", {}).get("orchestrator_ms", 0),
            ))
        
        # 步骤3: 执行与生成 (动态步骤)
        # 检查是否有特定的执行结果
        execution_summary = result.get("execution_summary", {})
        performance_data = result.get("performance_data", {})
        
        # 工具执行
        if execution_summary.get("tool_outputs"):
            workflow_steps.append(WorkflowStepResult(
                step_name="tool_execution",
                agent_name="ToolSpecialist",
                status=ExecutionStatusEnum.SUCCESS,
                result={"outputs": execution_summary["tool_outputs"]},
                duration_ms=performance_data.get("tool_specialist_ms", 0),
            ))
            
        # 课程设计
        if execution_summary.get("curriculum_plan"):
             workflow_steps.append(WorkflowStepResult(
                step_name="curriculum_design",
                agent_name="CurriculumDesigner",
                status=ExecutionStatusEnum.SUCCESS,
                result=execution_summary["curriculum_plan"],
                duration_ms=performance_data.get("curriculum_designer_ms", 0),
            ))

        # 初稿生成
        if performance_data.get("draft_writer_ms"):
             workflow_steps.append(WorkflowStepResult(
                step_name="content_generation",
                agent_name="DraftWriter",
                status=ExecutionStatusEnum.SUCCESS,
                result={"draft_content": "Draft generated (internal)"}, # 简化展示
                duration_ms=performance_data.get("draft_writer_ms", 0),
            ))
            
        # 审核与修订
        if performance_data.get("reviewer_ms"):
             workflow_steps.append(WorkflowStepResult(
                step_name="content_review",
                agent_name="Reviewer",
                status=ExecutionStatusEnum.SUCCESS,
                result={"critique": "Review completed (internal)"}, # 简化展示
                duration_ms=performance_data.get("reviewer_ms", 0),
            ))

        
        # 提取下一步建议
        next_suggestions = result.get("next_suggestions", [])
        if not next_suggestions:
            # 根据查询类型提供默认建议
            query_type = analysis.get("query_type", "")
            if query_type == "concept_explanation":
                next_suggestions = [
                    "你可以询问相关的应用示例",
                    "你可以请求更深入的解释",
                    "你可以询问相关的其他概念",
                ]
            elif query_type == "direct_answer":
                next_suggestions = [
                    "你可以要求解释背后的原理",
                    "你可以询问相关的例子",
                    "你可以提出进一步的问题",
                ]
            else:
                next_suggestions = [
                    "你可以继续深入探讨",
                    "你可以换个角度提问",
                    "你可以请求更多示例",
                ]
        
        # 提取苏格拉底式对话信息
        socratic_dialogue = extract_socratic_dialogue_info(result)
        
        # 构建响应
        duration_ms = (time.time() - start_time) * 1000
        log_response("workflow/session/start", True, duration_ms)
        
        logger.info(f"工作流执行成功 - session_id={session_id}, 耗时={duration_ms:.2f}ms")
        
        # 如果处于苏格拉底式对话模式，记录相关信息
        if socratic_dialogue.is_socratic_mode:
            logger.info(f"苏格拉底式对话模式 - 问题类型: {socratic_dialogue.question_type}, 引导策略: {socratic_dialogue.guidance_strategy}")
        
        return LearningSessionResponse(
            success=True,
            message="学习会话启动成功",
            session_id=session_id,
            user_id=user_id,
            query=query,
            response=response_text,
            workflow_steps=workflow_steps,
            analysis=analysis,
            plan=plan,
            execution_summary=execution_summary,
            next_suggestions=next_suggestions,
            # 添加 workflow 状态字段
            workflow_complete=result.get("workflow_complete", False),
            waiting_for_user=result.get("waiting_for_user", False),
            conversation_stage=result.get("conversation_stage"),
            understanding_level=result.get("understanding_level"),
            conversation_round=result.get("conversation_round", 0),
            # 添加苏格拉底式对话信息
            socratic_dialogue=socratic_dialogue,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_response("workflow/session/start", False, duration_ms)
        logger.error(f"工作流执行失败: {str(e)}", exc_info=True)
        raise handle_workflow_error(e)


@router.post(
    "/session/continue",
    response_model=LearningSessionResponse,
    summary="继续学习会话",
    description="基于用户的后续响应继续学习会话",
)
async def continue_learning_session(
    request: ContinueSessionRequest,
    workflow: LangGraphLearningWorkflow = Depends(get_learning_workflow_instance),
):
    """
    继续学习会话接口
    
    功能：
    1. 基于用户响应继续对话
    2. 评估理解程度
    3. 调整引导策略
    4. 生成后续响应
    """
    start_time = time.time()
    
    try:
        # 验证输入
        user_id = validate_user_id(request.user_id)
        session_id = request.session_id
        user_response = validate_query(request.user_response, min_length=1)
        
        log_request("workflow/session/continue", {
            "user_id": user_id,
            "session_id": session_id,
            "response": user_response[:100],
        })
        
        # 继续工作流
        logger.info(f"继续执行工作流 - session_id={session_id}")
        
        result = await workflow_limiter.run(
            workflow.continue_session(
                session_id=session_id,
                user_id=user_id,
                user_response=user_response,
            )
        )
        
        # 检查执行结果
        if not result or not result.get("success", False):
            error_msg = result.get("error", "会话继续失败") if result else "工作流无响应"
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg,
            )
        
        # 提取结果
        response_text = result.get("response", "")
        analysis = result.get("analysis", {})
        plan = result.get("plan", {})
        execution_summary = result.get("execution_summary", {})
        next_suggestions = result.get("next_suggestions", [])
        
        # 构建工作流步骤
        workflow_steps: List[WorkflowStepResult] = []
        
        # 步骤1: 响应分析
        if "analysis" in result and result["analysis"]:
            workflow_steps.append(WorkflowStepResult(
                step_name="response_analysis",
                agent_name="QueryAnalyzer",
                status=ExecutionStatusEnum.SUCCESS,
                result=result["analysis"],
                duration_ms=result.get("performance_data", {}).get("query_analyzer_ms", 0),
            ))
        
        # 步骤2: 自适应规划
        if "plan" in result and result["plan"]:
            workflow_steps.append(WorkflowStepResult(
                step_name="adaptive_orchestration",
                agent_name="Orchestrator",
                status=ExecutionStatusEnum.SUCCESS,
                result=result["plan"],
                duration_ms=result.get("performance_data", {}).get("orchestrator_ms", 0),
            ))
        
        # 步骤3: 引导与生成 (动态步骤)
        execution_summary = result.get("execution_summary", {})
        performance_data = result.get("performance_data", {})
        
        if performance_data.get("socratic_guide_ms"):
            workflow_steps.append(WorkflowStepResult(
                step_name="socratic_guidance",
                agent_name="SocraticGuide",
                status=ExecutionStatusEnum.SUCCESS,
                result=execution_summary,
                duration_ms=performance_data.get("socratic_guide_ms", 0),
            ))
        elif performance_data.get("draft_writer_ms"):
             workflow_steps.append(WorkflowStepResult(
                step_name="content_generation",
                agent_name="DraftWriter",
                status=ExecutionStatusEnum.SUCCESS,
                result={"draft_content": "Response generated"},
                duration_ms=performance_data.get("draft_writer_ms", 0),
            ))
        
        # 提取苏格拉底式对话信息
        socratic_dialogue = extract_socratic_dialogue_info(result)
        
        # 构建响应
        duration_ms = (time.time() - start_time) * 1000
        log_response("workflow/session/continue", True, duration_ms)
        
        logger.info(f"会话继续成功 - session_id={session_id}, 耗时={duration_ms:.2f}ms")
        
        # 如果处于苏格拉底式对话模式，记录相关信息
        if socratic_dialogue.is_socratic_mode:
            logger.info(f"苏格拉底式对话继续 - 问题类型: {socratic_dialogue.question_type}, 已提问: {socratic_dialogue.questions_asked}/{socratic_dialogue.max_questions}")
        
        return LearningSessionResponse(
            success=True,
            message="会话继续成功",
            session_id=session_id,
            user_id=user_id,
            query=user_response,
            response=response_text,
            workflow_steps=workflow_steps,
            analysis=analysis,
            plan=plan,
            execution_summary=execution_summary,
            next_suggestions=next_suggestions,
            # 添加 workflow 状态字段
            workflow_complete=result.get("workflow_complete", False),
            waiting_for_user=result.get("waiting_for_user", False),
            conversation_stage=result.get("conversation_stage"),
            understanding_level=result.get("understanding_level"),
            conversation_round=result.get("conversation_round", 0),
            # 添加苏格拉底式对话信息
            socratic_dialogue=socratic_dialogue,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_response("workflow/session/continue", False, duration_ms)
        logger.error(f"会话继续失败: {str(e)}", exc_info=True)
        raise handle_workflow_error(e)


@router.get(
    "/session/{session_id}",
    summary="获取会话信息",
    description="获取指定会话的详细信息和当前工作流状态",
)
async def get_session_info(
    session_id: str,
    include_state: bool = False,
    workflow: LangGraphLearningWorkflow = Depends(get_learning_workflow_instance),
):
    """
    获取会话信息接口
    
    返回：
    - 会话基本信息
    - 交互历史
    - 会话状态
    - 工作流状态（可选）
    
    Args:
        session_id: 会话ID
        include_state: 是否包含完整的 workflow state（默认 False）
    """
    try:
        # 从工作流获取会话信息
        session_info = workflow.active_sessions.get(session_id)
        
        if not session_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"会话不存在: {session_id}",
            )
        
        # 从 state 中提取信息
        state = session_info.get("state", {})
        
        response_data = {
            "success": True,
            "message": "会话信息获取成功",
            "data": {
                "session_id": session_id,
                "user_id": state.get("user_context", {}).get("user_id"),
                "started_at": session_info.get("start_time").isoformat() if session_info.get("start_time") else None,
                "last_activity": session_info.get("last_activity").isoformat() if session_info.get("last_activity") else None,
                "interaction_count": state.get("conversation_round", 0),
                "current_stage": state.get("conversation_stage"),
                "understanding_level": state.get("understanding_level"),
                "workflow_complete": state.get("workflow_complete", False),
                "waiting_for_user": state.get("waiting_for_user", False),
            }
        }
        
        # 如果请求包含完整状态，添加 workflow state
        if include_state:
            response_data["data"]["workflow_state"] = state
            response_data["data"]["current_step"] = session_info.get("current_step")
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取会话信息失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取会话信息失败: {str(e)}",
        )


@router.delete(
    "/session/{session_id}",
    summary="结束会话",
    description="结束并清理指定的学习会话",
)
async def end_session(
    session_id: str,
    workflow: LangGraphLearningWorkflow = Depends(get_learning_workflow_instance),
):
    """
    结束会话接口
    
    功能：
    1. 保存会话记录
    2. 更新用户画像
    3. 清理临时数据
    """
    try:
        # 检查会话是否存在
        if session_id not in workflow.active_sessions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"会话不存在: {session_id}",
            )
        
        # 移除活跃会话
        session_info = workflow.active_sessions.pop(session_id)
        
        logger.info(f"会话已结束: {session_id}")
        
        return {
            "success": True,
            "message": "会话已结束",
            "data": {
                "session_id": session_id,
                "ended_at": time.time(),
                "summary": session_info,
            },
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"结束会话失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"结束会话失败: {str(e)}",
        )


@router.get(
    "/session/{session_id}/socratic",
    summary="获取苏格拉底式对话详情",
    description="获取指定会话的苏格拉底式对话详细信息",
)
async def get_socratic_dialogue_info(
    session_id: str,
    workflow: LangGraphLearningWorkflow = Depends(get_learning_workflow_instance),
):
    """
    获取苏格拉底式对话详情接口
    
    返回：
    - 苏格拉底式对话状态
    - 问题历史
    - 引导策略
    - 对话质量评估
    """
    try:
        # 检查会话是否存在
        session_info = workflow.active_sessions.get(session_id)
        if not session_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"会话不存在: {session_id}",
            )
        
        # 从会话状态中提取苏格拉底式对话信息
        state = session_info.get("state", {})
        socratic_dialogue = extract_socratic_dialogue_info(state)
        
        # 构建详细的苏格拉底式对话信息
        dialogue_details = {
            "session_id": session_id,
            "socratic_info": socratic_dialogue.dict(),
            "conversation_quality": {
                "engagement_score": _calculate_engagement_score(state),
                "understanding_progress": _assess_understanding_progress(state),
                "question_effectiveness": _evaluate_question_effectiveness(state),
            },
            "learning_insights": {
                "key_concepts_covered": state.get("key_concepts_covered", []),
                "learning_objectives": state.get("learning_objectives", []),
                "achieved_objectives": state.get("achieved_objectives", []),
            }
        }
        
        return {
            "success": True,
            "message": "苏格拉底式对话详情获取成功",
            "data": dialogue_details,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取苏格拉底式对话详情失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取苏格拉底式对话详情失败: {str(e)}",
        )


def _calculate_engagement_score(state: Dict[str, Any]) -> float:
    """计算用户参与度分数"""
    try:
        user_responses = state.get("user_responses", [])
        if not user_responses:
            return 0.0
        
        # 基于回答长度和内容质量计算参与度
        total_length = sum(len(response) for response in user_responses)
        avg_length = total_length / len(user_responses)
        
        # 标准化分数 (0-1)
        if avg_length < 20:
            return 0.3
        elif avg_length < 50:
            return 0.6
        elif avg_length < 100:
            return 0.8
        else:
            return 1.0
            
    except Exception:
        return 0.5


def _assess_understanding_progress(state: Dict[str, Any]) -> Dict[str, Any]:
    """评估理解进度"""
    try:
        understanding_level = state.get("understanding_level", "unknown")
        conversation_round = state.get("conversation_round", 0)
        
        # 基于对话轮次和理解水平评估进度
        progress_score = min(conversation_round / 5.0, 1.0)  # 假设5轮为满分
        
        return {
            "current_level": understanding_level,
            "progress_score": progress_score,
            "conversation_rounds": conversation_round,
            "estimated_completion": f"{int(progress_score * 100)}%"
        }
        
    except Exception:
        return {
            "current_level": "unknown",
            "progress_score": 0.0,
            "conversation_rounds": 0,
            "estimated_completion": "0%"
        }


def _evaluate_question_effectiveness(state: Dict[str, Any]) -> Dict[str, Any]:
    """评估问题有效性"""
    try:
        socratic_questions = state.get("socratic_questions", [])
        user_responses = state.get("user_responses", [])
        
        if not socratic_questions or not user_responses:
            return {
                "effectiveness_score": 0.0,
                "question_types_used": [],
                "response_quality": "unknown"
            }
        
        # 统计问题类型
        question_types = []
        for q in socratic_questions:
            if isinstance(q, dict) and "type" in q:
                question_types.append(q["type"])
        
        # 评估响应质量
        response_quality = "good" if len(user_responses) >= len(socratic_questions) else "needs_improvement"
        
        return {
            "effectiveness_score": min(len(user_responses) / len(socratic_questions), 1.0),
            "question_types_used": list(set(question_types)),
            "response_quality": response_quality,
            "total_questions": len(socratic_questions),
            "total_responses": len(user_responses)
        }
        
    except Exception:
        return {
            "effectiveness_score": 0.0,
            "question_types_used": [],
            "response_quality": "unknown"
        }


@router.get(
    "/socratic/question-types",
    summary="获取苏格拉底式问题类型",
    description="获取所有可用的苏格拉底式问题类型及其说明",
)
async def get_socratic_question_types():
    """
    获取苏格拉底式问题类型接口
    
    返回：
    - 所有可用的苏格拉底式问题类型
    - 每种类型的说明和示例
    """
    question_types = {
        "clarification": {
            "name": "澄清类问题",
            "description": "帮助学生澄清概念和想法",
            "example": "当你使用'XX'这个词时，你心中想到的具体含义是什么？",
            "purpose": "澄清基础理解，消除歧义"
        },
        "assumption": {
            "name": "假设类问题", 
            "description": "引导学生发现隐含假设",
            "example": "在你的思考中，你是否假设了XX一定会导致YY？",
            "purpose": "发现隐含假设，培养批判思维"
        },
        "evidence": {
            "name": "证据类问题",
            "description": "引导学生寻找和评估证据",
            "example": "什么样的例子能够帮助我们理解XX的这个特点？",
            "purpose": "培养证据意识，提高论证能力"
        },
        "perspective": {
            "name": "视角类问题",
            "description": "引导学生换位思考",
            "example": "如果站在XX的立场，他们会如何看待这个问题？",
            "purpose": "培养多角度思维，增强同理心"
        },
        "implication": {
            "name": "含义类问题",
            "description": "引导学生推演后果和影响",
            "example": "如果XX成立，那么对YY会产生什么影响？",
            "purpose": "培养逻辑推理，预测能力"
        },
        "meta": {
            "name": "元认知类问题",
            "description": "引导学生反思思维过程",
            "example": "在思考这个问题时，你经历了怎样的思维过程？",
            "purpose": "提高自我觉察，优化思维方法"
        },
        "synthesis": {
            "name": "综合类问题",
            "description": "引导学生整合知识",
            "example": "XX和YY之间有什么共同的规律吗？",
            "purpose": "培养综合思维，建立知识联系"
        },
        "application": {
            "name": "应用类问题",
            "description": "引导学生联系实际应用",
            "example": "这个原理在我们今天的生活中，可能出现在哪些场景？",
            "purpose": "促进知识迁移，提高应用能力"
        }
    }
    
    return {
        "success": True,
        "message": "苏格拉底式问题类型获取成功",
        "data": {
            "total_types": len(question_types),
            "question_types": question_types,
            "usage_guide": {
                "beginner": ["clarification", "evidence"],
                "intermediate": ["assumption", "perspective", "implication"],
                "advanced": ["meta", "synthesis", "application"]
            }
        }
    }


@router.get(
    "/socratic/strategies",
    summary="获取苏格拉底式引导策略",
    description="获取不同理解水平下的苏格拉底式引导策略",
)
async def get_socratic_strategies():
    """
    获取苏格拉底式引导策略接口
    
    返回：
    - 不同理解水平的引导策略
    - 策略说明和实施建议
    """
    strategies = {
        "beginner": {
            "name": "基础引导策略",
            "description": "适用于初学者，重点澄清基础概念",
            "question_types": ["clarification", "evidence"],
            "approach": "从基础概念开始，逐步建立理解",
            "characteristics": [
                "使用简单直接的问题",
                "提供具体例子",
                "鼓励学生表达想法",
                "及时澄清误解"
            ]
        },
        "intermediate": {
            "name": "深度探索策略", 
            "description": "适用于有一定基础的学习者，深入探索概念",
            "question_types": ["assumption", "perspective", "implication"],
            "approach": "挑战假设，多角度思考",
            "characteristics": [
                "引导学生发现隐含假设",
                "鼓励换位思考",
                "推演逻辑后果",
                "培养批判思维"
            ]
        },
        "advanced": {
            "name": "高级思辨策略",
            "description": "适用于高级学习者，培养元认知和综合能力",
            "question_types": ["meta", "synthesis", "application"],
            "approach": "反思思维过程，整合知识体系",
            "characteristics": [
                "反思思维过程",
                "整合不同知识",
                "联系实际应用",
                "培养创新思维"
            ]
        }
    }
    
    return {
        "success": True,
        "message": "苏格拉底式引导策略获取成功",
        "data": {
            "strategies": strategies,
            "adaptation_guide": {
                "how_to_choose": "根据学生的理解水平和学习目标选择合适策略",
                "progression": "从基础引导逐步过渡到高级思辨",
                "flexibility": "根据学生反应灵活调整策略"
            }
        }
    }


@router.get(
    "/sessions/active",
    summary="获取活跃会话列表",
    description="获取当前所有活跃的学习会话",
)
async def get_active_sessions(
    workflow: LangGraphLearningWorkflow = Depends(get_learning_workflow_instance),
):
    """
    获取活跃会话列表
    
    返回：
    - 活跃会话ID列表
    - 会话基本信息
    """
    try:
        active_sessions = []
        
        for session_id, session_info in workflow.active_sessions.items():
            state = session_info.get("state", {})
            active_sessions.append({
                "session_id": session_id,
                "user_id": state.get("user_context", {}).get("user_id"),
                "started_at": session_info.get("start_time").isoformat() if session_info.get("start_time") else None,
                "last_activity": session_info.get("last_activity").isoformat() if session_info.get("last_activity") else None,
                "interaction_count": state.get("conversation_round", 0),
                "current_step": session_info.get("current_step", "unknown"),
            })
        
        return {
            "success": True,
            "message": "活跃会话列表",
            "data": {
                "total_count": len(active_sessions),
                "sessions": active_sessions,
            },
        }
        
    except Exception as e:
        logger.error(f"获取活跃会话列表失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取活跃会话列表失败: {str(e)}",
        )

