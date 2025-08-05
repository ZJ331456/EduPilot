#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版多智能体路由器
集成MongoDB存储和查询分类功能
"""

import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from services.mongodb_integration import mongodb_service
from services.conversation_storage_manager import conversation_storage_manager

logger = logging.getLogger(__name__)

# 创建增强版路由器
enhanced_router = APIRouter(tags=["enhanced-multi-agent"])

# 请求模型
class EnhancedQueryRequest(BaseModel):
    """增强版查询请求模型"""
    query: str = Field(..., description="用户查询")
    session_id: Optional[str] = Field(None, description="会话ID")
    user_id: Optional[str] = Field(None, description="用户ID")
    user_context: Optional[Dict[str, Any]] = Field(None, description="用户上下文")
    config: Optional[Dict[str, Any]] = Field(None, description="查询配置")
    force_mode: Optional[str] = Field(None, description="强制模式：normal或socratic")

class UserProfileRequest(BaseModel):
    """用户画像请求模型"""
    user_id: str = Field(..., description="用户ID")

# 响应模型
class EnhancedQueryResponse(BaseModel):
    """增强版查询响应模型"""
    success: bool
    session_id: str
    final_response: str
    query_classification: Dict[str, Any]
    execution_summary: Dict[str, Any]
    user_profile_context: Optional[Dict[str, Any]] = None
    conversation_saved: bool = False
    timestamp: str
    error: Optional[str] = None

@enhanced_router.post("/enhanced-query", response_model=EnhancedQueryResponse)
async def enhanced_query(request: EnhancedQueryRequest, background_tasks: BackgroundTasks):
    """增强版查询处理"""
    start_time = time.time()
    
    try:
        # 获取多智能体系统
        from agents import get_multi_agent_system
        mas = get_multi_agent_system()
        
        if not mas:
            raise HTTPException(status_code=503, detail="多智能体系统不可用")
        
        # 准备用户上下文
        user_context = request.user_context or {}
        
        # 如果有用户ID，获取用户画像上下文
        if request.user_id:
            try:
                profile_context = await mongodb_service.get_user_profile_context(request.user_id)
                user_context.update(profile_context)
            except Exception as e:
                logger.warning(f"获取用户画像上下文失败: {e}")
        
        # 添加强制模式配置
        if request.force_mode:
            user_context['force_query_mode'] = request.force_mode
        
        # 处理查询
        result = await mas.process_query(
            user_query=request.query,
            session_id=request.session_id,
            user_context=user_context
        )
        
        # 准备响应
        response = EnhancedQueryResponse(
            success=result.get("success", False),
            session_id=result.get("session_id", ""),
            final_response=result.get("response", ""),
            query_classification=result.get("query_classification", {}),
            execution_summary=result.get("execution_summary", {}),
            user_profile_context=user_context if request.user_id else None,
            timestamp=datetime.now().isoformat()
        )
        
        # 后台保存对话记录
        if request.user_id and result.get("success"):
            background_tasks.add_task(
                save_conversation_data,
                session_id=result.get("session_id"),
                user_id=request.user_id,
                user_input=request.query,
                system_response=result.get("response", ""), 
                metadata={
                    'query_classification': result.get("query_classification", {}),
                    'execution_summary': result.get("execution_summary", {}),
                    'session_duration': time.time() - start_time,
                    'user_context': user_context
                }
            )
            response.conversation_saved = True
        
        return response
        
    except Exception as e:
        logger.error(f"增强版查询处理失败: {e}")
        return EnhancedQueryResponse(
            success=False,
            session_id=request.session_id or "",
            final_response="抱歉，处理您的查询时遇到了问题。请稍后重试。",
            query_classification={},
            execution_summary={},
            timestamp=datetime.now().isoformat(),
            error=str(e)
        )

@enhanced_router.get("/user-profile/{user_id}")
async def get_user_profile(user_id: str):
    """获取用户画像"""
    try:
        # 首先尝试从新的用户画像文件读取
        import json
        from pathlib import Path
        
        # 构建文件路径
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent  # src/routers -> src -> project_root
        profile_file = project_root / "data" / "user_profiles" / f"user_profile_{user_id}.json"
        
        if profile_file.exists():
            # 读取新的用户画像文件
            with open(profile_file, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)
            
            logger.info(f"从文件读取用户画像: {user_id}")
            return {
                "success": True,
                "user_id": user_id,
                "profile": profile_data,
                "timestamp": datetime.now().isoformat()
            }
        else:
            # 如果文件不存在，尝试从MongoDB读取
            context = await mongodb_service.get_user_profile_context(user_id)
            return {
                "success": True,
                "user_id": user_id,
                "profile": context,
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"获取用户画像失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取用户画像失败: {str(e)}")

@enhanced_router.get("/user-profile")
async def get_current_user_profile():
    """获取当前用户画像（默认用户）"""
    try:
        # 首先尝试从文件读取用户画像数据
        import json
        from pathlib import Path
        
        # 构建文件路径
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent  # src/routers -> src -> project_root
        
        # 尝试读取anonymous用户的画像（因为日志显示使用的是anonymous）
        profile_file = project_root / "data" / "user_profiles" / "user_profile_anonymous.json"
        
        if profile_file.exists():
            # 读取用户画像文件
            with open(profile_file, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)
            
            # 计算实体数量和关系数量
            triples = profile_data.get('triples', [])
            entities = set()
            relations = set()
            
            for triple in triples:
                entities.add(triple.get('subject', ''))
                entities.add(triple.get('object', ''))
                relations.add(triple.get('predicate', ''))
            
            # 移除空字符串
            entities.discard('')
            relations.discard('')
            
            entity_count = len(entities)
            relation_count = len(relations)
            
            logger.info(f"从文件读取用户画像: anonymous, 实体数: {entity_count}, 关系数: {relation_count}")
            
            return {
                "success": True,
                "user_id": "anonymous",
                "user_profile": {
                    "user_id": "anonymous",
                    "graph_statistics": {
                        "entity_count": entity_count,
                        "relation_count": relation_count
                    },
                    "user_context": {
                        "user_summary": f"用户有 {entity_count} 个实体和 {relation_count} 个关系",
                        "user_entities": list(entities),
                        "entity_count": entity_count,
                        "relation_count": relation_count,
                        "triples": triples
                    },
                    "profile_completeness": profile_data.get('profile_completeness', 0.0)
                },
                "timestamp": datetime.now().isoformat()
            }
        else:
            # 如果文件不存在，尝试从MongoDB读取
            default_user_id = "default_user"
            context = await mongodb_service.get_user_profile_context(default_user_id)
            return {
                "success": True,
                "user_id": default_user_id,
                "user_profile": {
                    "user_id": default_user_id,
                    "graph_statistics": {
                        "entity_count": context.get("entity_count", 0),
                        "relation_count": context.get("relation_count", 0)
                    },
                    "user_context": context,
                    "profile_completeness": context.get("profile_completeness", 0.0)
                },
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"获取当前用户画像失败: {e}")
        # 返回空的用户画像结构
        return {
            "success": True,
            "user_id": "anonymous",
            "user_profile": {
                "user_id": "anonymous",
                "graph_statistics": {
                    "entity_count": 0,
                    "relation_count": 0
                },
                "user_context": {
                    "user_summary": "暂无用户画像信息",
                    "user_entities": [],
                    "entity_count": 0,
                    "relation_count": 0
                },
                "profile_completeness": 0.0
            },
            "timestamp": datetime.now().isoformat()
        }

@enhanced_router.get("/user-profile-graph")
async def get_user_profile_graph():
    """获取用户画像图谱数据（用于图表展示）"""
    try:
        import json
        from pathlib import Path
        
        # 构建文件路径
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent
        profile_file = project_root / "data" / "user_profiles" / "user_profile_anonymous.json"
        
        if profile_file.exists():
            with open(profile_file, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)
            
            triples = profile_data.get('triples', [])
            
            # 构建图谱数据
            nodes = []
            edges = []
            node_ids = {}
            
            for triple in triples:
                subject = triple.get('subject', '')
                predicate = triple.get('predicate', '')
                obj = triple.get('object', '')
                
                if subject and obj:
                    # 添加节点
                    if subject not in node_ids:
                        node_ids[subject] = len(nodes)
                        nodes.append({
                            "id": subject,
                            "label": subject,
                            "type": "entity",
                            "size": 20
                        })
                    
                    if obj not in node_ids:
                        node_ids[obj] = len(nodes)
                        nodes.append({
                            "id": obj,
                            "label": obj,
                            "type": "entity", 
                            "size": 20
                        })
                    
                    # 添加边
                    edges.append({
                        "source": subject,
                        "target": obj,
                        "label": predicate,
                        "type": "relation"
                    })
            
            return {
                "success": True,
                "graph": {
                    "nodes": nodes,
                    "edges": edges
                },
                "statistics": {
                    "node_count": len(nodes),
                    "edge_count": len(edges)
                },
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": True,
                "graph": {
                    "nodes": [],
                    "edges": []
                },
                "statistics": {
                    "node_count": 0,
                    "edge_count": 0
                },
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"获取用户画像图谱数据失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "graph": {
                "nodes": [],
                "edges": []
            },
            "statistics": {
                "node_count": 0,
                "edge_count": 0
            },
            "timestamp": datetime.now().isoformat()
        }

@enhanced_router.post("/clear-user-profile")
async def clear_user_profile(user_id: str = "default_user"):
    """清空用户画像"""
    try:
        # 清空用户画像数据
        await mongodb_service.clear_user_profile(user_id)
        
        return {
            "success": True,
            "user_id": user_id,
            "message": "用户画像已清空",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"清空用户画像失败: {e}")
        raise HTTPException(status_code=500, detail=f"清空用户画像失败: {str(e)}")

@enhanced_router.get("/user-sessions/{user_id}")
async def get_user_sessions(user_id: str, limit: int = 10):
    """获取用户会话历史"""
    try:
        sessions = await mongodb_service.get_user_sessions(user_id, limit)
        return {
            "success": True,
            "user_id": user_id,
            "sessions": sessions,
            "total": len(sessions),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"获取用户会话历史失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取用户会话历史失败: {str(e)}")

@enhanced_router.get("/session-history/{session_id}")
async def get_session_history(session_id: str):
    """获取会话详细历史"""
    try:
        history = await mongodb_service.get_session_history(session_id)
        if history:
            return {
                "success": True,
                "session": history,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=404, detail="会话不存在")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取会话历史失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取会话历史失败: {str(e)}")

@enhanced_router.post("/test-classification")
async def test_query_classification(query: str):
    """测试查询分类功能"""
    try:
        from agents.query_interpreter_integrated import QueryInterpreterAgent
        from utils import AgentState
        
        classifier = QueryInterpreterAgent()
        state = AgentState(user_query=query)
        
        result_state = await classifier.execute(state)
        classification = result_state.interpretation.get('classification', {})
        
        return {
            "success": True,
            "query": query,
            "classification": classification,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"测试查询分类失败: {e}")
        raise HTTPException(status_code=500, detail=f"测试查询分类失败: {str(e)}")

@enhanced_router.get("/health")
async def health_check():
    """健康检查"""
    try:
        # 检查MongoDB连接
        mongodb_status = "connected" if mongodb_service.initialized else "disconnected"
        
        # 检查多智能体系统
        from agents import get_multi_agent_system
        mas = get_multi_agent_system()
        mas_status = "available" if mas else "unavailable"
        
        return {
            "status": "healthy" if mongodb_status == "connected" and mas_status == "available" else "degraded",
            "components": {
                "mongodb": mongodb_status,
                "multi_agent_system": mas_status
            },
            "timestamp": datetime.now().isoformat(),
            "service": "多智能体学习助手"
        }
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@enhanced_router.get("/stats")
async def get_stats():
    """获取系统统计信息"""
    try:
        # 获取基本统计信息
        stats = {
            "success_rate": 0.95,  # 默认成功率
            "total_queries": 0,
            "active_sessions": 0,
            "system_uptime": time.time(),
            "timestamp": datetime.now().isoformat()
        }
        
        # 如果有MongoDB连接，获取实际统计
        if mongodb_service.initialized:
            try:
                # 这里可以添加实际的统计查询
                pass
            except Exception as e:
                logger.warning(f"获取MongoDB统计失败: {e}")
        
        return stats
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")

@enhanced_router.post("/query")
async def process_query(request: EnhancedQueryRequest):
    """处理查询请求"""
    try:
        # 获取多智能体系统
        from agents import get_multi_agent_system
        mas = get_multi_agent_system()
        
        if not mas:
            raise HTTPException(status_code=503, detail="多智能体系统不可用")
        
        # 准备用户上下文
        user_context = request.user_context or {}
        
        # 处理查询
        result = await mas.process_query(
            user_query=request.query,
            session_id=request.session_id,
            user_context=user_context
        )
        
        return {
            "success": result.get("success", False),
            "session_id": result.get("session_id", ""),
            "final_response": result.get("response", ""), 
            "socratic_question": result.get("socratic_question"),
            "steps_completed": result.get("steps_completed", []),
            "state_summary": result.get("state_summary", {}),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"处理查询失败: {e}")
        raise HTTPException(status_code=500, detail=f"处理查询失败: {str(e)}")

@enhanced_router.get("/session/{session_id}")
async def get_session_info(session_id: str):
    """获取会话信息"""
    try:
        # 这里可以添加实际的会话查询逻辑
        return {
            "exists": True,
            "session_id": session_id,
            "status": "active",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"获取会话信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取会话信息失败: {str(e)}")

@enhanced_router.get("/health-enhanced")
async def enhanced_health_check():
    """增强版健康检查"""
    try:
        # 检查MongoDB连接
        mongodb_status = "connected" if mongodb_service.initialized else "disconnected"
        
        # 检查多智能体系统
        from agents import get_multi_agent_system
        mas = get_multi_agent_system()
        mas_status = "available" if mas else "unavailable"
        
        return {
            "status": "healthy" if mongodb_status == "connected" and mas_status == "available" else "degraded",
            "components": {
                "mongodb": mongodb_status,
                "multi_agent_system": mas_status
            },
            "timestamp": datetime.now().isoformat(),
            "service": "增强版多智能体学习助手"
        }
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

async def save_conversation_data(session_id: str, user_id: str, user_input: str, 
                               system_response: str, metadata: Dict[str, Any]):
    """后台保存对话数据"""
    try:
        # 创建会话（如果不存在）
        await mongodb_service.create_session(session_id, user_id)
        
        # 保存对话轮次
        await mongodb_service.save_conversation_turn(
            session_id=session_id,
            user_input=user_input,
            system_response=system_response,
            metadata=metadata
        )
        
        # 保存知识查询记录
        if 'query_classification' in metadata:
            query_data = {
                'query_id': f"{session_id}_{int(time.time())}",
                'session_id': session_id,
                'user_id': user_id,
                'query_text': user_input,
                'query_type': metadata['query_classification'].get('query_mode', 'normal'),
                'classification_confidence': metadata['query_classification'].get('confidence', 0.5),
                'detected_topics': metadata.get('topics', []),
                'response_text': system_response,
                'response_type': 'direct_answer',
                'generation_time': metadata.get('session_duration', 0),
                'timestamp': datetime.now()
            }
            await mongodb_service.save_knowledge_query(query_data)
        
        logger.info(f"对话数据保存成功: {session_id}")
        
    except Exception as e:
        logger.error(f"保存对话数据失败: {e}")

# 将增强版路由器导出
router = enhanced_router

# 数据管理相关API端点
@enhanced_router.post("/storage/cleanup")
async def cleanup_old_data(days: int = 30):
    """清理旧数据"""
    try:
        await conversation_storage_manager.cleanup_old_sessions(days)
        return {
            "success": True,
            "message": f"已清理 {days} 天前的数据",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"清理数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"清理数据失败: {str(e)}")

@enhanced_router.get("/storage/stats")
async def get_storage_statistics():
    """获取存储统计信息"""
    try:
        stats = await conversation_storage_manager.get_storage_stats()
        return {
            "success": True,
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"获取存储统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取存储统计失败: {str(e)}")

@enhanced_router.post("/storage/export-user-data/{user_id}")
async def export_user_data(user_id: str):
    """导出用户数据"""
    try:
        export_data = await conversation_storage_manager.export_user_data(user_id)
        return {
            "success": True,
            "user_id": user_id,
            "export_data": export_data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"导出用户数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"导出用户数据失败: {str(e)}")

@enhanced_router.post("/storage/backup")
async def backup_all_data():
    """备份所有数据"""
    try:
        backup_path = await conversation_storage_manager.backup_data()
        return {
            "success": True,
            "backup_path": backup_path,
            "message": "数据备份完成",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"数据备份失败: {e}")
        raise HTTPException(status_code=500, detail=f"数据备份失败: {str(e)}")

@enhanced_router.post("/storage/restore")
async def restore_data(backup_dir: str):
    """从备份恢复数据"""
    try:
        success = await conversation_storage_manager.restore_data(backup_dir)
        if success:
            return {
                "success": True,
                "backup_dir": backup_dir,
                "message": "数据恢复完成",
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="数据恢复失败")
    except Exception as e:
        logger.error(f"数据恢复失败: {e}")
        raise HTTPException(status_code=500, detail=f"数据恢复失败: {str(e)}")

@enhanced_router.get("/storage/user-sessions/{user_id}")
async def get_user_session_history(user_id: str, limit: int = 10):
    """获取用户会话历史"""
    try:
        sessions = await conversation_storage_manager.get_user_sessions(user_id, limit)
        return {
            "success": True,
            "user_id": user_id,
            "sessions": sessions,
            "total_count": len(sessions),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"获取用户会话历史失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取用户会话历史失败: {str(e)}")

@enhanced_router.get("/storage/session/{session_id}")
async def get_session_details(session_id: str):
    """获取会话详细信息"""
    try:
        session_data = await conversation_storage_manager.get_session_history(session_id)
        if session_data:
            return {
                "success": True,
                "session_id": session_id,
                "session_data": session_data,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=404, detail="会话不存在")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取会话详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取会话详情失败: {str(e)}")

@enhanced_router.delete("/storage/clear-user-data/{user_id}")
async def clear_user_data(user_id: str):
    """清空用户数据"""
    try:
        # 清空MongoDB中的用户画像
        await mongodb_service.clear_user_profile(user_id)
        
        # 清空本地文件
        import os
        from pathlib import Path
        
        # 删除用户画像文件
        profile_file = Path(__file__).parent.parent.parent / "data" / "user_profiles" / f"user_profile_{user_id}.json"
        if profile_file.exists():
            profile_file.unlink()
        
        # 删除用户的会话文件
        sessions_dir = Path(__file__).parent.parent.parent / "data" / "sessions"
        conversations_dir = Path(__file__).parent.parent.parent / "data" / "conversations"
        
        # 删除会话文件
        for session_file in sessions_dir.glob("session_*.json"):
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                if session_data.get('user_id') == user_id:
                    session_file.unlink()
            except Exception as e:
                logger.warning(f"处理会话文件失败: {session_file}, 错误: {e}")
        
        # 删除对话轮次文件
        for session_dir in conversations_dir.iterdir():
            if session_dir.is_dir():
                session_file = sessions_dir / f"session_{session_dir.name}.json"
                if session_file.exists():
                    try:
                        with open(session_file, 'r', encoding='utf-8') as f:
                            session_data = json.load(f)
                        if session_data.get('user_id') == user_id:
                            import shutil
                            shutil.rmtree(session_dir)
                    except Exception as e:
                        logger.warning(f"处理会话目录失败: {session_dir}, 错误: {e}")
        
        return {
            "success": True,
            "user_id": user_id,
            "message": "用户数据已清空",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"清空用户数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"清空用户数据失败: {str(e)}")

@enhanced_router.get("/storage/health")
async def storage_health_check():
    """存储系统健康检查"""
    try:
        # 检查MongoDB连接
        mongodb_status = "connected" if mongodb_service.initialized else "disconnected"
        
        # 检查本地文件系统
        local_status = "ok"
        try:
            stats = await conversation_storage_manager.get_storage_stats()
            local_stats = stats.get("local_files", {})
            if "error" in local_stats:
                local_status = "error"
        except Exception as e:
            local_status = "error"
            logger.warning(f"本地存储检查失败: {e}")
        
        # 检查存储管理器
        storage_manager_status = "initialized" if conversation_storage_manager.initialized else "not_initialized"
        
        overall_status = "healthy"
        if mongodb_status == "disconnected" or local_status == "error" or storage_manager_status == "not_initialized":
            overall_status = "degraded"
        
        return {
            "status": overall_status,
            "components": {
                "mongodb": mongodb_status,
                "local_storage": local_status,
                "storage_manager": storage_manager_status
            },
            "timestamp": datetime.now().isoformat(),
            "service": "存储管理系统"
        }
    except Exception as e:
        logger.error(f"存储健康检查失败: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
