#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LangGraph Checkpoint管理
支持状态持久化、分支管理和时光回溯
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

from .state import LearningWorkflowState


logger = logging.getLogger(__name__)


class CheckpointManager:
    """Checkpoint管理器
    
    支持：
    - 状态快照保存
    - 分支状态管理
    - 时光回溯
    """
    
    def __init__(self, checkpoint_dir: str = "data/checkpoints"):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def save_checkpoint(
        self,
        session_id: str,
        state: LearningWorkflowState,
        checkpoint_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """保存状态快照
        
        Args:
            session_id: 会话ID
            state: 工作流状态
            checkpoint_id: 快照ID（可选，自动生成）
            metadata: 额外元数据
            
        Returns:
            快照ID
        """
        import uuid
        
        if checkpoint_id is None:
            checkpoint_id = str(uuid.uuid4())
        
        checkpoint_data = {
            "checkpoint_id": checkpoint_id,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "state": state,
            "metadata": metadata or {}
        }
        
        # 保存到文件
        checkpoint_file = self.checkpoint_dir / f"{session_id}_{checkpoint_id}.json"
        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_data, f, ensure_ascii=False, indent=2, default=str)
        
        # 更新会话的checkpoint索引
        self._update_checkpoint_index(session_id, checkpoint_id)
        
        self.logger.info(f"保存checkpoint: {checkpoint_id} for session: {session_id}")
        return checkpoint_id
    
    def load_checkpoint(
        self,
        session_id: str,
        checkpoint_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """加载状态快照
        
        Args:
            session_id: 会话ID
            checkpoint_id: 快照ID（可选，加载最新的）
            
        Returns:
            快照数据，不存在返回None
        """
        if checkpoint_id is None:
            # 加载最新的checkpoint
            checkpoint_id = self._get_latest_checkpoint_id(session_id)
            if checkpoint_id is None:
                return None
        
        checkpoint_file = self.checkpoint_dir / f"{session_id}_{checkpoint_id}.json"
        
        if not checkpoint_file.exists():
            return None
        
        try:
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"加载checkpoint失败: {e}")
            return None
    
    def list_checkpoints(self, session_id: str) -> List[Dict[str, Any]]:
        """列出会话的所有checkpoint
        
        Args:
            session_id: 会话ID
            
        Returns:
            checkpoint列表
        """
        checkpoints = []
        pattern = f"{session_id}_*.json"
        
        for checkpoint_file in self.checkpoint_dir.glob(pattern):
            try:
                with open(checkpoint_file, 'r', encoding='utf-8') as f:
                    checkpoint_data = json.load(f)
                    checkpoints.append({
                        "checkpoint_id": checkpoint_data["checkpoint_id"],
                        "timestamp": checkpoint_data["timestamp"],
                        "metadata": checkpoint_data.get("metadata", {})
                    })
            except Exception as e:
                self.logger.warning(f"读取checkpoint文件失败: {checkpoint_file}, {e}")
        
        # 按时间排序
        checkpoints.sort(key=lambda x: x["timestamp"], reverse=True)
        return checkpoints
    
    def create_branch(
        self,
        session_id: str,
        parent_checkpoint_id: str,
        branch_name: str
    ) -> str:
        """创建分支checkpoint
        
        Args:
            session_id: 会话ID
            parent_checkpoint_id: 父checkpoint ID
            branch_name: 分支名称
            
        Returns:
            新分支的checkpoint ID
        """
        parent_checkpoint = self.load_checkpoint(session_id, parent_checkpoint_id)
        if parent_checkpoint is None:
            raise ValueError(f"父checkpoint不存在: {parent_checkpoint_id}")
        
        # 创建分支checkpoint
        branch_metadata = {
            "branch_name": branch_name,
            "parent_checkpoint_id": parent_checkpoint_id,
            "is_branch": True
        }
        
        branch_state = parent_checkpoint["state"].copy()
        branch_checkpoint_id = self.save_checkpoint(
            session_id=session_id,
            state=branch_state,
            metadata=branch_metadata
        )
        
        self.logger.info(f"创建分支: {branch_name} from checkpoint: {parent_checkpoint_id}")
        return branch_checkpoint_id
    
    def _update_checkpoint_index(self, session_id: str, checkpoint_id: str):
        """更新checkpoint索引"""
        index_file = self.checkpoint_dir / f"{session_id}_index.json"
        
        if index_file.exists():
            with open(index_file, 'r', encoding='utf-8') as f:
                index = json.load(f)
        else:
            index = {"checkpoints": []}
        
        index["checkpoints"].append({
            "checkpoint_id": checkpoint_id,
            "timestamp": datetime.now().isoformat()
        })
        index["latest_checkpoint_id"] = checkpoint_id
        
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
    
    def _get_latest_checkpoint_id(self, session_id: str) -> Optional[str]:
        """获取最新的checkpoint ID"""
        index_file = self.checkpoint_dir / f"{session_id}_index.json"
        
        if not index_file.exists():
            return None
        
        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                index = json.load(f)
                return index.get("latest_checkpoint_id")
        except Exception as e:
            self.logger.error(f"读取checkpoint索引失败: {e}")
            return None


# 全局checkpoint管理器实例
_global_checkpoint_manager: Optional[CheckpointManager] = None


def get_checkpoint_manager() -> CheckpointManager:
    """获取全局checkpoint管理器"""
    global _global_checkpoint_manager
    if _global_checkpoint_manager is None:
        _global_checkpoint_manager = CheckpointManager()
    return _global_checkpoint_manager

