#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理器
统一管理系统配置，支持YAML配置文件和环境变量
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
from functools import lru_cache

from .logging_config import get_logger, LoggerNames

logger = get_logger(LoggerNames.CONFIG)

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self._config: Dict[str, Any] = {}
        self._load_config()
    
    def _get_default_config_path(self) -> str:
        """获取默认配置文件路径"""
        current_dir = Path(__file__).parent
        return str(current_dir / "config.yaml")
    
    def _load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._config = yaml.safe_load(f) or {}
                logger.info(f"Configuration loaded from {self.config_path}")
            else:
                logger.warning(f"Configuration file not found: {self.config_path}")
                self._config = {}
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            self._config = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_with_env_override(self, key: str, env_key: Optional[str] = None, default: Any = None) -> Any:
        """获取配置值，支持环境变量覆盖"""
        if env_key is None:
            env_key = key.upper().replace('.', '_')
        
        env_value = os.getenv(env_key)
        if env_value is not None:
            return env_value
        
        return self.get(key, default)
    
    def get_llm_config(self, client_name: Optional[str] = None) -> Dict[str, Any]:
        """获取LLM配置"""
        if client_name is None:
            client_name = self.get('llm.default_client', 'ollama')
        
        llm_config = self.get('llm', {})
        client_config = llm_config.get(client_name, {})
        
        config = {
            'client_name': client_name,
            'timeout': 30,
            'max_retries': 3,
            **client_config
        }
        
        # 特殊处理Qwen API Key
        if client_name == 'qwen':
            api_key = self.get_with_env_override('llm.qwen.api_key', 'QWEN_API_KEY')
            if api_key:
                config['api_key'] = api_key
                logger.info(f"Qwen API key loaded from environment: {api_key[:8]}...")
            else:
                logger.warning("QWEN_API_KEY not found in environment variables")
        
        return config
    
    def get_database_config(self) -> Dict[str, Any]:
        """获取数据库配置"""
        db_config = self.get('database.mongodb', {})
        
        return {
            'url': self.get_with_env_override('database.mongodb.url', 'MONGODB_URL', 'mongodb://localhost:27017'),
            'database_name': self.get_with_env_override('database.mongodb.database_name', 'DATABASE_NAME', 'hw_agent_db'),
            'collections': db_config.get('collections', {}),
            'connection_pool': db_config.get('connection_pool', {})
        }
    
    def get_knowledge_base_config(self) -> Dict[str, Any]:
        """获取知识库配置"""
        return self.get('knowledge_base', {})
    
    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """获取智能体配置"""
        agents_config = self.get('agents', {})
        return agents_config.get(agent_name, {})
    
    def get_multi_agent_config(self) -> Dict[str, Any]:
        """获取多智能体系统配置"""
        return self.get('multi_agent_system', {})
    
    def get_storage_config(self) -> Dict[str, Any]:
        """获取存储配置"""
        return self.get('storage', {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """获取日志配置"""
        return self.get('logging', {})
    
    def get_security_config(self) -> Dict[str, Any]:
        """获取安全配置"""
        return self.get('security', {})
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """获取监控配置"""
        return self.get('monitoring', {})
    
    def get_development_config(self) -> Dict[str, Any]:
        """获取开发配置"""
        return self.get('development', {})
    
    def get_environment_config(self, environment: str = None) -> Dict[str, Any]:
        """获取环境特定配置"""
        if environment is None:
            environment = os.getenv('ENVIRONMENT', 'development')
        
        environments_config = self.get('environments', {})
        return environments_config.get(environment, {})
    
    def reload(self):
        """重新加载配置文件"""
        self._load_config()
        logger.info("Configuration reloaded")
    
    def save(self, path: Optional[str] = None):
        """保存配置到文件"""
        save_path = path or self.config_path
        
        try:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            with open(save_path, 'w', encoding='utf-8') as f:
                yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True)
            
            logger.info(f"Configuration saved to {save_path}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
    
    def to_dict(self) -> Dict[str, Any]:
        """获取完整配置字典"""
        return self._config.copy()
    
    def update(self, config_dict: Dict[str, Any]):
        """更新配置"""
        self._config.update(config_dict)
        logger.info("Configuration updated")
    
    def validate(self) -> bool:
        """验证配置"""
        try:
            required_keys = [
                'app.name',
                'database.mongodb.url',
                'llm.default_client'
            ]
            
            for key in required_keys:
                if self.get(key) is None:
                    logger.error(f"Missing required configuration: {key}")
                    return False
            
            logger.info("Configuration validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False

# 全局配置管理器实例
@lru_cache()
def get_config_manager() -> ConfigManager:
    """获取全局配置管理器实例"""
    return ConfigManager()

# 便捷函数
def get_config(key: str, default: Any = None) -> Any:
    """获取配置值"""
    return get_config_manager().get(key, default)

def get_llm_config(client_name: Optional[str] = None) -> Dict[str, Any]:
    """获取LLM配置"""
    return get_config_manager().get_llm_config(client_name)

def get_database_config() -> Dict[str, Any]:
    """获取数据库配置"""
    return get_config_manager().get_database_config()

def get_knowledge_base_config() -> Dict[str, Any]:
    """获取知识库配置"""
    return get_config_manager().get_knowledge_base_config()

def get_agent_config(agent_name: str) -> Dict[str, Any]:
    """获取智能体配置"""
    return get_config_manager().get_agent_config(agent_name)

def get_multi_agent_config() -> Dict[str, Any]:
    """获取多智能体系统配置"""
    return get_config_manager().get_multi_agent_config() 