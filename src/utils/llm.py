#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM核心模块
提供大语言模型操作的抽象接口，支持Ollama和阿里云百炼API
"""

import os
import asyncio
import time
import json
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union, Callable, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from pathlib import Path
import numpy as np

# 第三方库
import requests
from openai import OpenAI
from dotenv import load_dotenv

# Ollama import with fallback
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    ollama = None

# 加载环境变量
load_dotenv()

class MessageRole(str, Enum):
    """消息角色枚举"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

@dataclass
class Message:
    """消息数据类"""
    role: MessageRole
    content: str
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "role": self.role.value,
            "content": self.content,
            **self.metadata
        }

@dataclass
class LLMResponse:
    """LLM响应数据类"""
    content: str
    model: str
    usage: Optional[Dict[str, int]] = None
    metadata: Optional[Dict[str, Any]] = None
    success: bool = True
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.usage is None:
            self.usage = {}
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "content": self.content,
            "model": self.model,
            "usage": self.usage,
            "metadata": self.metadata,
            "success": self.success,
            "error": self.error
        }

class BaseLLMClient(ABC):
    """LLM客户端基类"""
    
    def __init__(self, model: str, max_retries: int = 3, timeout: int = 30):
        self.model = model
        self.max_retries = max_retries
        self.timeout = timeout
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def chat_completion(self, messages: List[Message], **kwargs) -> LLMResponse:
        """聊天完成"""
        pass
    
    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        """测试连接"""
        pass
    
    def generate_response(
        self, 
        user_input: str, 
        system_prompt: Optional[str] = None, 
        context: Optional[List[Message]] = None
    ) -> str:
        """生成响应"""
        messages = []
        
        # 添加系统提示词
        if system_prompt:
            messages.append(Message(MessageRole.SYSTEM, system_prompt))
        
        # 添加上下文
        if context:
            messages.extend(context)
        
        # 添加用户输入
        messages.append(Message(MessageRole.USER, user_input))
        
        # 调用聊天完成
        response = self.chat_completion(messages)
        
        if response.success:
            return response.content
        else:
            self.logger.error(f"Failed to generate response: {response.error}")
            return f"抱歉，生成回复时出现错误：{response.error}"

class OllamaLLMClient(BaseLLMClient):
    """Ollama LLM客户端"""
    
    def __init__(self, model: str = None, base_url: str = None, **kwargs):
        # 从配置文件获取配置
        from config import get_llm_config
        
        # 获取Ollama配置
        ollama_config = get_llm_config("ollama")
        
        # 优先使用传入的参数，然后使用配置文件
        model = model or ollama_config.get('default_model', 'qwen2.5:latest')
        base_url = base_url or ollama_config.get('base_url', 'http://localhost:11434')
        
        super().__init__(model, **kwargs)
        self.base_url = base_url
        self.client = None
        self.async_client = None
        
        # 从配置文件获取模型参数
        self.max_tokens = ollama_config.get('max_tokens', 2000)
        self.temperature = ollama_config.get('temperature', 0.7)
        self.top_p = ollama_config.get('top_p', 0.9)
        self.debug = ollama_config.get('debug', False)
        
        if OLLAMA_AVAILABLE:
            try:
                self.client = ollama.Client(host=base_url)
                self.async_client = ollama.AsyncClient(host=base_url)
                self.logger.info(f"Ollama client initialized with base_url: {base_url}")
                self.logger.info(f"Using Ollama model: {model}")
            except Exception as e:
                self.logger.warning(f"Failed to initialize Ollama client: {e}")
        else:
            self.logger.warning("Ollama module not available")
    
    def chat_completion(self, messages: List[Message], **kwargs) -> LLMResponse:
        """聊天完成"""
        if not self.client:
            return LLMResponse(
                content="",
                model=self.model,
                success=False,
                error="Ollama client not available"
            )
            
        try:
            # 转换消息格式
            ollama_messages = [msg.to_dict() for msg in messages]
            
            # 设置默认参数，优先使用传入的参数，然后使用实例变量
            params = {
                "model": self.model,
                "messages": ollama_messages,
                "temperature": kwargs.get('temperature', self.temperature),
                "top_p": kwargs.get('top_p', self.top_p),
                **{k: v for k, v in kwargs.items() if k not in ['temperature', 'top_p']}
            }
            
            # 调试信息
            if self.debug:
                self.logger.debug(f"Ollama API call params: {params}")
            
            # 调用Ollama API
            response = self.client.chat(**params)
            
            return LLMResponse(
                content=response['message']['content'],
                model=self.model,
                usage={
                    "prompt_tokens": response.get('prompt_eval_count', 0),
                    "completion_tokens": response.get('eval_count', 0),
                    "total_tokens": response.get('prompt_eval_count', 0) + response.get('eval_count', 0)
                },
                metadata={
                    "eval_duration": response.get('eval_duration', 0),
                    "load_duration": response.get('load_duration', 0)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Ollama API call failed: {e}")
            return LLMResponse(
                content="",
                model=self.model,
                success=False,
                error=str(e)
            )
    
    def test_connection(self) -> Dict[str, Any]:
        """测试连接"""
        if not self.client:
            return {
                "success": False,
                "model": self.model,
                "error": "Ollama client not available"
            }
            
        try:
            # 测试模型列表
            models = self.client.list()
            
            # 测试简单对话
            test_response = self.chat_completion([
                Message(MessageRole.USER, "你好，请简单介绍一下你自己。")
            ])
            
            return {
                "success": test_response.success,
                "model": self.model,
                "available_models": [model['name'] for model in models.get('models', [])],
                "response": test_response.content if test_response.success else test_response.error,
                "usage": test_response.usage
            }
        except Exception as e:
            return {
                "success": False,
                "model": self.model,
                "error": str(e)
            }
    
    async def async_chat_completion(
        self, 
        messages: List[Message], 
        system_prompt: Optional[str] = None,
        history_messages: Optional[List[Dict]] = None,
        **kwargs
    ) -> LLMResponse:
        """异步聊天完成，支持历史消息和系统提示词"""
        if not self.async_client:
            return LLMResponse(
                content="",
                model=self.model,
                success=False,
                error="Ollama async client not available"
            )
        
        try:
            # 构建消息列表
            ollama_messages = []
            
            # 添加系统提示词（如果提供）
            if system_prompt:
                ollama_messages.append({"role": "system", "content": system_prompt})
            
            # 添加历史消息（如果提供）
            if history_messages:
                ollama_messages.extend(history_messages)
            
            # 添加当前消息
            ollama_messages.extend([msg.to_dict() for msg in messages])
            
            # 移除ollama不支持的参数
            filtered_kwargs = {k: v for k, v in kwargs.items() 
                             if k not in ['max_tokens', 'response_format']}
            
            # 调用Ollama异步API
            response = await self.async_client.chat(
                model=self.model,
                messages=ollama_messages,
                **filtered_kwargs
            )
            
            return LLMResponse(
                content=response['message']['content'],
                model=self.model,
                usage={
                    "prompt_tokens": response.get('prompt_eval_count', 0),
                    "completion_tokens": response.get('eval_count', 0),
                    "total_tokens": response.get('prompt_eval_count', 0) + response.get('eval_count', 0)
                },
                metadata={
                    "eval_duration": response.get('eval_duration', 0),
                    "load_duration": response.get('load_duration', 0)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Ollama async API call failed: {e}")
            return LLMResponse(
                content="",
                model=self.model,
                success=False,
                error=str(e)
            )
    
    def generate_embeddings(self, texts: List[str], embedding_model: str = None) -> np.ndarray:
        """生成文本嵌入向量"""
        if not OLLAMA_AVAILABLE or not self.client:
            self.logger.error("Ollama client not available for embeddings")
            return np.array([])
        
        model = embedding_model or "bge-m3:latest"
        embeddings = []
        
        try:
            for text in texts:
                data = ollama.embeddings(model=model, prompt=text)
                embeddings.append(data["embedding"])
            
            return np.array(embeddings)
            
        except Exception as e:
            self.logger.error(f"Failed to generate embeddings: {e}")
            return np.array([])
    
    async def async_generate_embeddings(self, texts: List[str], embedding_model: str = None) -> np.ndarray:
        """异步生成文本嵌入向量"""
        if not OLLAMA_AVAILABLE or not self.async_client:
            self.logger.error("Ollama async client not available for embeddings")
            return np.array([])
        
        model = embedding_model or "bge-m3:latest"
        embeddings = []
        
        try:
            for text in texts:
                data = await ollama.aembeddings(model=model, prompt=text)
                embeddings.append(data["embedding"])
            
            return np.array(embeddings)
            
        except Exception as e:
            self.logger.error(f"Failed to generate async embeddings: {e}")
            return np.array([])
    
    def list_models(self) -> List[str]:
        """列出可用的模型"""
        if not OLLAMA_AVAILABLE or not self.client:
            return []
        
        try:
            models = ollama.list()
            model_names = []
            
            if hasattr(models, 'models') and isinstance(models.models, list):
                for model in models.models:
                    if hasattr(model, 'model'):
                        model_names.append(model.model)
                    elif isinstance(model, dict):
                        name = model.get('name') or model.get('model') or model.get('id')
                        if name:
                            model_names.append(name)
                    elif isinstance(model, str):
                        model_names.append(model)
            elif isinstance(models, dict) and 'models' in models:
                for model in models['models']:
                    if isinstance(model, dict):
                        name = model.get('name') or model.get('model') or model.get('id')
                        if name:
                            model_names.append(name)
                    elif isinstance(model, str):
                        model_names.append(model)
            
            return model_names
            
        except Exception as e:
            self.logger.error(f"Failed to list models: {e}")
            return []

class QwenLLMClient(BaseLLMClient):
    """阿里云百炼Qwen LLM客户端"""
    
    def __init__(
        self, 
        model: str = None,
        api_key: str = None,
        base_url: str = None,
        **kwargs
    ):
        # 从配置文件获取配置
        from config import get_llm_config, get_config
        
        # 获取Qwen配置
        qwen_config = get_llm_config("qwen")
        
        # 优先使用传入的参数，然后使用配置文件，最后使用环境变量作为备用
        self.api_key = api_key or qwen_config.get('api_key')
        self.base_url = base_url or qwen_config.get('base_url', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
        model = model or qwen_config.get('default_model', 'qwen-plus')
        
        # 如果配置文件中没有API密钥，尝试从环境变量获取（向后兼容）
        if not self.api_key and get_config('llm.fallback_to_env', True):
            self.api_key = os.getenv('QWEN_API_KEY') or os.getenv('DASHSCOPE_API_KEY')
        
        # 调试信息
        if not self.api_key:
            self.logger.warning("Qwen API key not found in config or environment variables")
        else:
            self.logger.info(f"Using Qwen API key: {self.api_key[:8]}...")
            self.logger.info(f"Using Qwen base URL: {self.base_url}")
            self.logger.info(f"Using Qwen model: {model}")
        
        super().__init__(model, **kwargs)
        
        if not self.api_key:
            raise ValueError("API key is required for Qwen client")
        
        # 创建OpenAI兼容客户端
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
        # 从配置文件获取模型参数
        self.max_tokens = qwen_config.get('max_tokens', 2000)
        self.temperature = qwen_config.get('temperature', 0.7)
        self.top_p = qwen_config.get('top_p', 0.9)
        self.debug = qwen_config.get('debug', False)
    
    def chat_completion(self, messages: List[Message], **kwargs) -> LLMResponse:
        """聊天完成"""
        try:
            # 转换消息格式
            openai_messages = [msg.to_dict() for msg in messages]
            
            # 设置默认参数，优先使用传入的参数，然后使用实例变量
            params = {
                "model": self.model,
                "messages": openai_messages,
                "max_tokens": kwargs.get('max_tokens', self.max_tokens),
                "temperature": kwargs.get('temperature', self.temperature),
                "top_p": kwargs.get('top_p', self.top_p),
                **{k: v for k, v in kwargs.items() if k not in ['max_tokens', 'temperature', 'top_p']}
            }
            
            # 调试信息
            if self.debug:
                self.logger.debug(f"Qwen API call params: {params}")
            
            # 调用API
            response = self.client.chat.completions.create(**params)
            
            return LLMResponse(
                content=response.choices[0].message.content,
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                } if response.usage else {},
                metadata={
                    "finish_reason": response.choices[0].finish_reason,
                    "created": response.created
                }
            )
            
        except Exception as e:
            self.logger.error(f"Qwen API call failed: {e}")
            return LLMResponse(
                content="",
                model=self.model,
                success=False,
                error=str(e)
            )
    
    def test_connection(self) -> Dict[str, Any]:
        """测试连接"""
        try:
            # 测试简单对话
            test_response = self.chat_completion([
                Message(MessageRole.USER, "你好，请简单介绍一下你自己。")
            ])
            
            return {
                "success": test_response.success,
                "model": self.model,
                "response": test_response.content if test_response.success else test_response.error,
                "usage": test_response.usage,
                "base_url": self.base_url
            }
        except Exception as e:
            return {
                "success": False,
                "model": self.model,
                "error": str(e)
            }
    
    async def async_chat_completion(
        self, 
        messages: List[Message], 
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """异步聊天完成"""
        try:
            # 转换消息格式
            openai_messages = []
            
            # 添加系统提示词（如果提供）
            if system_prompt:
                openai_messages.append({"role": "system", "content": system_prompt})
            
            # 添加当前消息
            openai_messages.extend([msg.to_dict() for msg in messages])
            
            # 设置默认参数
            params = {
                "model": self.model,
                "messages": openai_messages,
                "max_tokens": kwargs.get('max_tokens', self.max_tokens),
                "temperature": kwargs.get('temperature', self.temperature),
                **{k: v for k, v in kwargs.items() if k not in ['max_tokens', 'temperature']}
            }
            
            # 创建异步客户端
            from openai import AsyncOpenAI
            async_client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            
            # 调用API
            response = await async_client.chat.completions.create(**params)
            
            return LLMResponse(
                content=response.choices[0].message.content,
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                } if response.usage else {},
                metadata={
                    "finish_reason": response.choices[0].finish_reason,
                    "created": response.created
                }
            )
            
        except Exception as e:
            self.logger.error(f"Qwen async API call failed: {e}")
            return LLMResponse(
                content="",
                model=self.model,
                success=False,
                error=str(e)
            )

class LLMManager:
    """LLM管理器，统一管理多个LLM客户端"""
    
    def __init__(self):
        self.clients: Dict[str, BaseLLMClient] = {}
        self.default_client = None
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def add_client(self, name: str, client: BaseLLMClient, set_as_default: bool = False):
        """添加LLM客户端"""
        self.clients[name] = client
        if set_as_default or self.default_client is None:
            self.default_client = name
        self.logger.info(f"Added LLM client: {name} (model: {client.model})")
    
    def get_client(self, name: Optional[str] = None) -> Optional[BaseLLMClient]:
        """获取LLM客户端"""
        if name is None:
            name = self.default_client
        return self.clients.get(name)
    
    def list_clients(self) -> List[str]:
        """列出所有客户端"""
        return list(self.clients.keys())
    
    def test_all_clients(self) -> Dict[str, Dict[str, Any]]:
        """测试所有客户端"""
        results = {}
        for name, client in self.clients.items():
            self.logger.info(f"Testing client: {name}")
            results[name] = client.test_connection()
        return results
    
    def generate_response(
        self, 
        user_input: str, 
        client_name: Optional[str] = None,
        system_prompt: Optional[str] = None, 
        context: Optional[List[Message]] = None
    ) -> str:
        """使用指定客户端生成响应"""
        client = self.get_client(client_name)
        if not client:
            available = ", ".join(self.list_clients())
            return f"错误：找不到LLM客户端 '{client_name}'。可用客户端：{available}"
        
        return client.generate_response(user_input, system_prompt, context)
    
    async def async_generate_response(
        self, 
        user_input: str, 
        client_name: Optional[str] = None,
        system_prompt: Optional[str] = None, 
        context: Optional[List[Message]] = None,
        **kwargs
    ) -> str:
        """异步生成响应"""
        client = self.get_client(client_name)
        if not client:
            available = ", ".join(self.list_clients())
            return f"错误：找不到LLM客户端 '{client_name}'。可用客户端：{available}"
        
        # 构建消息列表
        messages = []
        
        # 添加上下文
        if context:
            messages.extend(context)
        
        # 添加用户输入
        messages.append(Message(MessageRole.USER, user_input))
        
        # 调用异步聊天完成
        if hasattr(client, 'async_chat_completion'):
            response = await client.async_chat_completion(messages, system_prompt, **kwargs)
        else:
            # 对于不支持异步的客户端，使用同步方法
            response = client.chat_completion(messages, **kwargs)
        
        if response.success:
            return response.content
        else:
            self.logger.error(f"Failed to generate async response: {response.error}")
            return f"抱歉，生成回复时出现错误：{response.error}"
    
    def generate_embeddings(
        self, 
        texts: List[str], 
        client_name: Optional[str] = None,
        embedding_model: Optional[str] = None
    ) -> np.ndarray:
        """生成文本嵌入向量"""
        client = self.get_client(client_name)
        if not client:
            self.logger.error(f"Client '{client_name}' not found")
            return np.array([])
        
        if hasattr(client, 'generate_embeddings'):
            return client.generate_embeddings(texts, embedding_model)
        else:
            self.logger.error(f"Client '{client_name}' does not support embeddings")
            return np.array([])
    
    async def async_generate_embeddings(
        self, 
        texts: List[str], 
        client_name: Optional[str] = None,
        embedding_model: Optional[str] = None
    ) -> np.ndarray:
        """异步生成文本嵌入向量"""
        client = self.get_client(client_name)
        if not client:
            self.logger.error(f"Client '{client_name}' not found")
            return np.array([])
        
        if hasattr(client, 'async_generate_embeddings'):
            return await client.async_generate_embeddings(texts, embedding_model)
        elif hasattr(client, 'generate_embeddings'):
            # 对于不支持异步的客户端，使用同步方法
            return client.generate_embeddings(texts, embedding_model)
        else:
            self.logger.error(f"Client '{client_name}' does not support embeddings")
            return np.array([])
    
    def get_llm_function(
        self, 
        client_name: Optional[str] = None,
        force_chinese: bool = True
    ) -> Callable:
        """获取适用于GraphRAG的LLM函数"""
        client = self.get_client(client_name)
        if not client:
            raise ValueError(f"Client '{client_name}' not found")
        
        async def llm_func(
            prompt: str, 
            system_prompt: Optional[str] = None, 
            history_messages: Optional[List[Dict]] = None, 
            **kwargs
        ) -> str:
            """适用于GraphRAG的LLM函数"""
            # 处理强制中文回答
            if force_chinese:
                chinese_system_prompt = "你是一个专业的中文AI助手。请始终使用中文回答所有问题，不要使用英文或其他语言。"
                if system_prompt:
                    chinese_system_prompt += "\n\n" + system_prompt + "\n\n请确保你的回答完全使用中文。"
                system_prompt = chinese_system_prompt
                prompt += "\n\n请用中文回答。"
            
            # 构建消息列表
            messages = []
            
            # 添加历史消息
            if history_messages:
                for msg in history_messages:
                    if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                        messages.append(Message(MessageRole(msg['role']), msg['content']))
            
            # 添加当前提示
            messages.append(Message(MessageRole.USER, prompt))
            
            # 调用客户端
            if hasattr(client, 'async_chat_completion'):
                response = await client.async_chat_completion(messages, system_prompt, **kwargs)
            else:
                response = client.chat_completion(messages, **kwargs)
            
            return response.content if response.success else f"生成回复时出现错误：{response.error}"
        
        return llm_func
    
    def get_embedding_function(
        self, 
        client_name: Optional[str] = None,
        embedding_model: Optional[str] = None,
        embedding_dim: int = 1024,
        max_token_size: int = 8192
    ) -> Callable:
        """获取适用于GraphRAG的embedding函数"""
        client = self.get_client(client_name)
        if not client:
            raise ValueError(f"Client '{client_name}' not found")
        
        # 从nano_graphrag导入装饰器
        try:
            from nano_graphrag._utils import wrap_embedding_func_with_attrs
            
            @wrap_embedding_func_with_attrs(
                embedding_dim=embedding_dim,
                max_token_size=max_token_size,
            )
            async def embedding_func(texts: List[str]) -> np.ndarray:
                """适用于GraphRAG的embedding函数"""
                if hasattr(client, 'async_generate_embeddings'):
                    return await client.async_generate_embeddings(texts, embedding_model)
                elif hasattr(client, 'generate_embeddings'):
                    return client.generate_embeddings(texts, embedding_model)
                else:
                    self.logger.error(f"Client does not support embeddings")
                    return np.array([[0.0] * embedding_dim] * len(texts))
            
            return embedding_func
            
        except ImportError:
            # 如果无法导入装饰器，返回简单版本
            async def simple_embedding_func(texts: List[str]) -> np.ndarray:
                if hasattr(client, 'async_generate_embeddings'):
                    return await client.async_generate_embeddings(texts, embedding_model)
                elif hasattr(client, 'generate_embeddings'):
                    return client.generate_embeddings(texts, embedding_model)
                else:
                    self.logger.error(f"Client does not support embeddings")
                    return np.array([[0.0] * embedding_dim] * len(texts))
            
            return simple_embedding_func

# 全局LLM管理器实例
_llm_manager = None

def get_llm_manager() -> LLMManager:
    """获取全局LLM管理器实例"""
    global _llm_manager
    if _llm_manager is None:
        _llm_manager = LLMManager()
        _initialize_default_clients()
    return _llm_manager

def _initialize_default_clients():
    """初始化默认的LLM客户端"""
    manager = _llm_manager
    logger = logging.getLogger("LLMManager")
    
    # 导入配置管理器
    from config import get_llm_config, get_config
    
    # 获取默认客户端名称
    default_client = get_config('llm.default_client', 'ollama')
    
    # 尝试初始化Qwen客户端（百炼API）
    try:
        qwen_config = get_llm_config("qwen")
        if qwen_config.get("enabled", True):
            qwen_client = QwenLLMClient(
                model=qwen_config.get("default_model"),
                api_key=qwen_config.get("api_key"),
                base_url=qwen_config.get("base_url"),
                timeout=qwen_config.get("timeout", 30),
                max_retries=qwen_config.get("max_retries", 3)
            )
            manager.add_client("qwen", qwen_client, set_as_default=(default_client == "qwen"))
            logger.info("Initialized Qwen LLM client")
        else:
            logger.info("Qwen client is disabled in config")
    except Exception as e:
        logger.warning(f"Failed to initialize Qwen client: {e}")
    
    # 尝试初始化Ollama客户端
    try:
        ollama_config = get_llm_config("ollama")
        if ollama_config.get("enabled", True):
            ollama_client = OllamaLLMClient(
                model=ollama_config.get("default_model", "qwen2.5:latest"),
                base_url=ollama_config.get("base_url", "http://localhost:11434"),
                timeout=ollama_config.get("timeout", 30),
                max_retries=ollama_config.get("max_retries", 3)
            )
            manager.add_client("ollama", ollama_client, set_as_default=(default_client == "ollama" or len(manager.clients) == 0))
            logger.info("Initialized Ollama LLM client")
        else:
            logger.info("Ollama client is disabled in config")
    except Exception as e:
        logger.warning(f"Failed to initialize Ollama client: {e}")
    
    # 尝试初始化OpenAI客户端（可选）
    try:
        openai_config = get_llm_config("openai")
        if openai_config.get("enabled", False):
            # 这里可以添加OpenAI客户端的初始化代码
            logger.info("OpenAI client support not yet implemented")
    except Exception as e:
        logger.warning(f"Failed to initialize OpenAI client: {e}")
    
    if not manager.clients:
        logger.error("No LLM clients were successfully initialized")
        logger.info("Please check your config.yaml file and ensure at least one LLM client is enabled")

# 便捷函数
def chat_completion(messages: List[Message], client_name: Optional[str] = None, **kwargs) -> LLMResponse:
    """聊天完成便捷函数"""
    manager = get_llm_manager()
    client = manager.get_client(client_name)
    if not client:
        return LLMResponse(
            content="",
            model="unknown",
            success=False,
            error=f"Client '{client_name}' not found"
        )
    return client.chat_completion(messages, **kwargs)

def generate_response(
    user_input: str, 
    client_name: Optional[str] = None,
    system_prompt: Optional[str] = None, 
    context: Optional[List[Message]] = None
) -> str:
    """生成响应便捷函数"""
    manager = get_llm_manager()
    return manager.generate_response(user_input, client_name, system_prompt, context)

def test_llm_connections() -> Dict[str, Dict[str, Any]]:
    """测试所有LLM连接"""
    manager = get_llm_manager()
    return manager.test_all_clients()

async def async_generate_response(
    user_input: str, 
    client_name: Optional[str] = None,
    system_prompt: Optional[str] = None, 
    context: Optional[List[Message]] = None,
    **kwargs
) -> str:
    """异步生成响应便捷函数"""
    manager = get_llm_manager()
    return await manager.async_generate_response(user_input, client_name, system_prompt, context, **kwargs)

def generate_embeddings(
    texts: List[str], 
    client_name: Optional[str] = None,
    embedding_model: Optional[str] = None
) -> np.ndarray:
    """生成嵌入向量便捷函数"""
    manager = get_llm_manager()
    return manager.generate_embeddings(texts, client_name, embedding_model)

async def async_generate_embeddings(
    texts: List[str], 
    client_name: Optional[str] = None,
    embedding_model: Optional[str] = None
) -> np.ndarray:
    """异步生成嵌入向量便捷函数"""
    manager = get_llm_manager()
    return await manager.async_generate_embeddings(texts, client_name, embedding_model)

def get_llm_function_for_graphrag(
    client_name: Optional[str] = None,
    force_chinese: bool = True
) -> Callable:
    """获取适用于GraphRAG的LLM函数便捷函数"""
    manager = get_llm_manager()
    return manager.get_llm_function(client_name, force_chinese)

def get_embedding_function_for_graphrag(
    client_name: Optional[str] = None,
    embedding_model: Optional[str] = None,
    embedding_dim: int = 1024,
    max_token_size: int = 8192
) -> Callable:
    """获取适用于GraphRAG的embedding函数便捷函数"""
    manager = get_llm_manager()
    return manager.get_embedding_function(client_name, embedding_model, embedding_dim, max_token_size)

def create_unified_processor_functions(
    llm_client_name: Optional[str] = None,
    embedding_client_name: Optional[str] = None,
    embedding_model: Optional[str] = None,
    embedding_dim: int = 1024,
    max_token_size: int = 8192,
    force_chinese: bool = True
) -> Tuple[Callable, Callable]:
    """创建统一的处理器函数，返回(llm_func, embedding_func)"""
    manager = get_llm_manager()
    
    llm_func = manager.get_llm_function(llm_client_name, force_chinese)
    embedding_func = manager.get_embedding_function(
        embedding_client_name, embedding_model, embedding_dim, max_token_size
    )
    
    return llm_func, embedding_func

def validate_llm_config() -> Dict[str, Any]:
    """验证LLM配置的有效性"""
    from config import get_llm_config, get_config
    
    validation_results = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "clients": {}
    }
    
    # 检查默认客户端
    default_client = get_config('llm.default_client', 'ollama')
    if default_client not in ['ollama', 'qwen', 'openai']:
        validation_results["errors"].append(f"Invalid default client: {default_client}")
        validation_results["valid"] = False
    
    # 验证Ollama配置
    try:
        ollama_config = get_llm_config("ollama")
        if ollama_config.get("enabled", True):
            if not ollama_config.get("base_url"):
                validation_results["warnings"].append("Ollama base_url not specified")
            if not ollama_config.get("default_model"):
                validation_results["warnings"].append("Ollama default_model not specified")
            validation_results["clients"]["ollama"] = {
                "enabled": True,
                "config": ollama_config
            }
        else:
            validation_results["clients"]["ollama"] = {"enabled": False}
    except Exception as e:
        validation_results["errors"].append(f"Ollama config error: {e}")
        validation_results["valid"] = False
    
    # 验证Qwen配置
    try:
        qwen_config = get_llm_config("qwen")
        if qwen_config.get("enabled", True):
            if not qwen_config.get("api_key") or qwen_config.get("api_key") == "your_qwen_api_key_here":
                validation_results["warnings"].append("Qwen API key not set or using placeholder")
            if not qwen_config.get("base_url"):
                validation_results["warnings"].append("Qwen base_url not specified")
            if not qwen_config.get("default_model"):
                validation_results["warnings"].append("Qwen default_model not specified")
            validation_results["clients"]["qwen"] = {
                "enabled": True,
                "config": qwen_config
            }
        else:
            validation_results["clients"]["qwen"] = {"enabled": False}
    except Exception as e:
        validation_results["errors"].append(f"Qwen config error: {e}")
        validation_results["valid"] = False
    
    # 验证OpenAI配置
    try:
        openai_config = get_llm_config("openai")
        if openai_config.get("enabled", False):
            if not openai_config.get("api_key") or openai_config.get("api_key") == "your_openai_api_key_here":
                validation_results["warnings"].append("OpenAI API key not set or using placeholder")
            if not openai_config.get("base_url"):
                validation_results["warnings"].append("OpenAI base_url not specified")
            if not openai_config.get("default_model"):
                validation_results["warnings"].append("OpenAI default_model not specified")
            validation_results["clients"]["openai"] = {
                "enabled": True,
                "config": openai_config
            }
        else:
            validation_results["clients"]["openai"] = {"enabled": False}
    except Exception as e:
        validation_results["errors"].append(f"OpenAI config error: {e}")
        validation_results["valid"] = False
    
    return validation_results

def print_llm_config_status():
    """打印LLM配置状态"""
    validation = validate_llm_config()
    
    print("=== LLM配置状态 ===")
    print(f"配置有效性: {'✓' if validation['valid'] else '✗'}")
    
    if validation['errors']:
        print("\n错误:")
        for error in validation['errors']:
            print(f"  ✗ {error}")
    
    if validation['warnings']:
        print("\n警告:")
        for warning in validation['warnings']:
            print(f"  ⚠ {warning}")
    
    print("\n客户端状态:")
    for client_name, client_info in validation['clients'].items():
        status = "启用" if client_info['enabled'] else "禁用"
        print(f"  {client_name}: {status}")
        if client_info['enabled'] and 'config' in client_info:
            config = client_info['config']
            print(f"    模型: {config.get('default_model', '未设置')}")
            if 'api_key' in config:
                api_key = config['api_key']
                if api_key and api_key != "your_qwen_api_key_here" and api_key != "your_openai_api_key_here":
                    print(f"    API密钥: {api_key[:8]}...")
                else:
                    print(f"    API密钥: 未设置")
    
    print("\n=== 测试连接 ===")
    try:
        results = test_llm_connections()
        for client_name, result in results.items():
            status = "✓" if result['success'] else "✗"
            print(f"  {client_name}: {status}")
            if result['success']:
                print(f"    模型: {result['model']}")
                print(f"    响应: {result['response'][:50]}...")
            else:
                print(f"    错误: {result['error']}")
    except Exception as e:
        print(f"  连接测试失败: {e}")

if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    print_llm_config_status()