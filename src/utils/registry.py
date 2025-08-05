#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能体注册表
"""

import logging
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
import time

class BaseAgent(ABC):
    """智能体基类"""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"Agent.{name}")
        self._execution_count = 0
        self._last_execution_time = None
    
    @abstractmethod
    async def execute(self, state) -> 'AgentState':
        """执行智能体逻辑
        
        Args:
            state: 当前状态对象
            
        Returns:
            更新后的状态对象
        """
        pass
    
    def can_execute(self, state) -> bool:
        """检查是否可以执行
        
        Args:
            state: 当前状态对象
            
        Returns:
            是否可以执行
        """
        return True
    
    def pre_execute(self, state) -> 'AgentState':
        """执行前的预处理
        
        Args:
            state: 当前状态对象
            
        Returns:
            预处理后的状态对象
        """
        self.logger.info(f"Agent {self.name} starting execution")
        self._execution_count += 1
        self._last_execution_time = time.time()
        
        # 清除之前的错误信息
        state.clear_error()
        
        return state
    
    def post_execute(self, state) -> 'AgentState':
        """执行后的后处理
        
        Args:
            state: 当前状态对象
            
        Returns:
            后处理后的状态对象
        """
        execution_time = time.time() - self._last_execution_time
        self.logger.info(f"Agent {self.name} completed execution in {execution_time:.2f}s")
        
        # 更新元数据
        if "agent_executions" not in state.metadata:
            state.metadata["agent_executions"] = []
        
        state.metadata["agent_executions"].append({
            "agent_name": self.name,
            "execution_count": self._execution_count,
            "execution_time": execution_time,
            "timestamp": self._last_execution_time,
            "success": state.error_info is None
        })
        
        return state
    
    async def run(self, state) -> 'AgentState':
        """运行智能体（包含前后处理）
        
        Args:
            state: 当前状态对象
            
        Returns:
            处理后的状态对象
        """
        try:
            # 检查是否可以执行
            if not self.can_execute(state):
                self.logger.warning(f"Agent {self.name} cannot execute with current state")
                state.set_error(
                    "execution_condition_not_met",
                    f"Agent {self.name} execution conditions not met"
                )
                return state
            
            # 前处理
            state = self.pre_execute(state)
            
            # 执行主逻辑
            state = await self.execute(state)
            
            # 后处理
            state = self.post_execute(state)
            
            return state
            
        except Exception as e:
            self.logger.error(f"Agent {self.name} execution failed: {e}", exc_info=True)
            state.set_error(
                "agent_execution_error",
                f"Agent {self.name} execution failed: {str(e)}",
                {"exception_type": type(e).__name__}
            )
            return state
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取智能体统计信息"""
        return {
            "name": self.name,
            "description": self.description,
            "execution_count": self._execution_count,
            "last_execution_time": self._last_execution_time
        }
    
    def __str__(self) -> str:
        return f"Agent({self.name})"
    
    def __repr__(self) -> str:
        return f"Agent(name='{self.name}', description='{self.description}')"

class AgentRegistry:
    """智能体注册表"""
    
    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def register(self, agent: BaseAgent):
        """注册智能体"""
        if agent.name in self._agents:
            self.logger.warning(f"Agent {agent.name} already registered, overwriting")
        
        self._agents[agent.name] = agent
        self.logger.info(f"Registered agent: {agent.name}")
    
    def get(self, name: str) -> Optional[BaseAgent]:
        """获取智能体"""
        return self._agents.get(name)
    
    def list_agents(self) -> List[str]:
        """列出所有智能体名称"""
        return list(self._agents.keys())
    
    def get_all_agents(self) -> Dict[str, BaseAgent]:
        """获取所有智能体"""
        return self._agents.copy()
    
    def unregister(self, name: str) -> bool:
        """注销智能体"""
        if name in self._agents:
            del self._agents[name]
            self.logger.info(f"Unregistered agent: {name}")
            return True
        return False
    
    def clear(self):
        """清除所有智能体"""
        self._agents.clear()
        self.logger.info("Cleared all agents")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取注册表统计信息"""
        return {
            "total_agents": len(self._agents),
            "agent_names": list(self._agents.keys()),
            "agent_statistics": {name: agent.get_statistics() for name, agent in self._agents.items()}
        }

# 全局智能体注册表
_global_registry = AgentRegistry()

def get_global_agent_registry() -> AgentRegistry:
    """获取全局智能体注册表"""
    return _global_registry

def register_agent(agent: BaseAgent):
    """注册智能体到全局注册表"""
    _global_registry.register(agent)

def get_agent(name: str) -> Optional[BaseAgent]:
    """从全局注册表获取智能体"""
    return _global_registry.get(name) 