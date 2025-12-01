#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API依赖注入模块
管理共享资源、智能体实例和工作流实例
直接使用 LangGraph 实现
"""

import logging
from functools import lru_cache
from typing import Optional, Dict, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# 直接使用 LangGraph 工作流
from src.core.workflow import LangGraphLearningWorkflow, get_langgraph_learning_workflow, initialize_langgraph_learning_workflow
# 智能体现在在 core.agents - 导入所有10个agent
from src.core.agents import (
    QueryAnalyzerAgent,
    OrchestratorAgent,
    MemoryManagerAgent,
    KnowledgeManagerAgent,
    SocraticGuideAgent,
    DraftWriterAgent,
    ReviewerAgent,
    CurriculumDesignerAgent,
    QuizMasterAgent,
    ToolSpecialistAgent,
    AgentRegistry,
)


# ============================================================================
# 全局状态管理
# ============================================================================

class APIState:
    """API全局状态"""
    
    def __init__(self):
        self.logger = logging.getLogger("EduPilotAPI")
        self.workflow_instance: Optional[LangGraphLearningWorkflow] = None
        self.agent_registry: Optional[AgentRegistry] = None
        self.start_time: Optional[float] = None
        self.request_count: int = 0
        
        # 性能统计
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0,
        }


# 全局状态实例
_api_state = APIState()


def get_api_state() -> APIState:
    """获取API全局状态"""
    return _api_state


# ============================================================================
# 工作流依赖
# ============================================================================

@lru_cache()
def get_workflow_config() -> Dict[str, Any]:
    """获取工作流配置"""
    return {
        "max_iterations": 5,
        "timeout_seconds": 300,
        "enable_learning": True,
        "enable_socratic": True,
        "auto_continue": False,
        # 特征开关，便于消融实验切换
        "feature_flags": {
            "enable_memory_manager": True,
            "enable_knowledge_manager": True,
            "enable_socratic_guide": True,
        },
    }


async def get_learning_workflow_instance() -> LangGraphLearningWorkflow:
    """获取学习工作流实例（依赖注入）"""
    global _api_state
    
    if _api_state.workflow_instance is None:
        # 初始化工作流
        config = get_workflow_config()
        _api_state.workflow_instance = initialize_langgraph_learning_workflow(config)
        _api_state.logger.info("学习工作流实例已初始化")
    
    return _api_state.workflow_instance


# ============================================================================
# 智能体依赖
# ============================================================================

async def get_query_analyzer() -> QueryAnalyzerAgent:
    """获取查询分析器实例（LangGraph 版本）"""
    workflow = await get_learning_workflow_instance()
    return workflow.nodes.agents.get("query_analyzer")


async def get_planner() -> OrchestratorAgent:
    """获取规划器实例（LangGraph 版本）"""
    workflow = await get_learning_workflow_instance()
    return workflow.nodes.agents.get("planner")


# ExecutorAgent 已被移除，功能已迁移到 DraftWriter 和 Orchestrator
# async def get_executor() -> ExecutorAgent:
#     """获取执行器实例（LangGraph 版本）"""
#     workflow = await get_learning_workflow_instance()
#     return workflow.nodes.agents.get("executor")


async def get_memory_manager() -> MemoryManagerAgent:
    """获取记忆管理器实例（LangGraph 版本）"""
    workflow = await get_learning_workflow_instance()
    return workflow.nodes.agents.get("memory_manager")


async def get_knowledge_manager() -> KnowledgeManagerAgent:
    """获取知识管理器实例（LangGraph 版本）"""
    workflow = await get_learning_workflow_instance()
    return workflow.nodes.agents.get("knowledge_manager")


async def get_socratic_guide() -> SocraticGuideAgent:
    """获取苏格拉底引导实例（LangGraph 版本）"""
    workflow = await get_learning_workflow_instance()
    return workflow.nodes.agents.get("socratic_guide")


async def get_draft_writer() -> DraftWriterAgent:
    """获取初稿撰写器实例（LangGraph 版本）"""
    workflow = await get_learning_workflow_instance()
    return workflow.nodes.agents.get("draft_writer")


async def get_reviewer() -> ReviewerAgent:
    """获取审核器实例（LangGraph 版本）"""
    workflow = await get_learning_workflow_instance()
    return workflow.nodes.agents.get("reviewer")


async def get_curriculum_designer() -> CurriculumDesignerAgent:
    """获取课程设计器实例（LangGraph 版本）"""
    workflow = await get_learning_workflow_instance()
    return workflow.nodes.agents.get("curriculum_designer")


async def get_quiz_master() -> QuizMasterAgent:
    """获取测验大师实例（LangGraph 版本）"""
    workflow = await get_learning_workflow_instance()
    return workflow.nodes.agents.get("quiz_master")


async def get_tool_specialist() -> ToolSpecialistAgent:
    """获取工具专家实例（LangGraph 版本）"""
    workflow = await get_learning_workflow_instance()
    return workflow.nodes.agents.get("tool_specialist")


async def get_agent_registry() -> AgentRegistry:
    """获取智能体注册表
    
    注意：LangGraph 版本不再使用 AgentRegistry，
    智能体现在通过 LearningWorkflowNodes 管理
    """
    # 返回所有智能体的字典作为注册表
    workflow = await get_learning_workflow_instance()
    
    # 创建一个简单的注册表对象
    class SimpleRegistry:
        def __init__(self, agents_dict):
            self._agents = agents_dict
        
        def get(self, name):
            return self._agents.get(name)
        
        def list_agents(self):
            return list(self._agents.keys())
    
    return SimpleRegistry(workflow.nodes.agents)


# ============================================================================
# 认证和授权（可选）
# ============================================================================

security = HTTPBearer(auto_error=False)


async def verify_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[str]:
    """
    验证访问令牌（可选）
    
    如果需要认证，可以在这里添加JWT验证逻辑
    目前返回None表示允许所有请求
    """
    # TODO: 实现真实的令牌验证
    # if credentials:
    #     token = credentials.credentials
    #     # 验证JWT令牌
    #     return user_id
    
    return None  # 暂不启用认证


async def get_current_user(user_id: Optional[str] = Depends(verify_token)) -> Optional[str]:
    """获取当前用户ID"""
    # 如果启用了认证但没有提供有效令牌，抛出401错误
    # if user_id is None:
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="未授权访问",
    #     )
    return user_id


# ============================================================================
# 请求验证辅助函数
# ============================================================================

def validate_user_id(user_id: str) -> str:
    """验证用户ID格式"""
    if not user_id or len(user_id) < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的用户ID",
        )
    return user_id


def validate_session_id(session_id: str) -> str:
    """验证会话ID格式"""
    if not session_id or len(session_id) < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的会话ID",
        )
    return session_id


def validate_query(query: str, min_length: int = 1, max_length: int = 10000) -> str:
    """验证查询文本"""
    if not query or len(query) < min_length:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"查询文本长度至少为 {min_length} 个字符",
        )
    if len(query) > max_length:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"查询文本长度不能超过 {max_length} 个字符",
        )
    return query


# ============================================================================
# 日志记录辅助
# ============================================================================

def log_request(endpoint: str, params: Dict[str, Any]):
    """记录请求日志"""
    logger = logging.getLogger("EduPilotAPI")
    logger.info(f"API请求: {endpoint}, 参数: {params}")


def log_response(endpoint: str, success: bool, duration_ms: float):
    """记录响应日志"""
    logger = logging.getLogger("EduPilotAPI")
    status = "成功" if success else "失败"
    logger.info(f"API响应: {endpoint}, 状态: {status}, 耗时: {duration_ms:.2f}ms")


# ============================================================================
# 错误处理辅助
# ============================================================================

def handle_agent_error(agent_name: str, error: Exception) -> HTTPException:
    """处理智能体错误"""
    logger = logging.getLogger("EduPilotAPI")
    logger.error(f"{agent_name} 执行错误: {str(error)}", exc_info=True)
    
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"{agent_name}执行失败: {str(error)}",
    )


def handle_workflow_error(error: Exception) -> HTTPException:
    """处理工作流错误"""
    logger = logging.getLogger("EduPilotAPI")
    logger.error(f"工作流执行错误: {str(error)}", exc_info=True)
    
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"工作流执行失败: {str(error)}",
    )

