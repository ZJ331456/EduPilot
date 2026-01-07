#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM 客户端使用示例
演示如何使用 Ollama 和 Qwen LLM 客户端
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# 加载环境变量
load_dotenv()

from infrastructure.llm import OllamaLLMClient, QwenLLMClient, Message, MessageRole
from infrastructure.llm.settings import OllamaSettings, QwenSettings


def example_ollama():
    """Ollama 客户端使用示例"""
    print("\n" + "="*60)
    print("Ollama LLM 客户端示例")
    print("="*60)
    
    try:
        # 初始化 Ollama 客户端
        client = OllamaLLMClient(settings=OllamaSettings.from_env())
        
        # 调用模型生成响应
        response = client.chat_completion([
            Message(role=MessageRole.USER, content="你好，请创建一首诗。")
        ])
        
        # 打印模型返回的内容
        print(f"\n✅ 响应成功:")
        print(f"{response.content}\n")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


def example_qwen():
    """Qwen 客户端使用示例"""
    print("\n" + "="*60)
    print("Qwen LLM 客户端示例")
    print("="*60)
    
    try:
        # 初始化 Qwen 客户端
        client = QwenLLMClient(settings=QwenSettings.from_env())
        
        # 调用模型生成响应
        response = client.chat_completion([
            Message(role=MessageRole.USER, content="你好，请简单介绍一下你自己。")
        ])
        
        # 打印模型返回的内容
        print(f"\n✅ 响应成功:")
        print(f"{response.content}\n")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


def main():
    """运行所有示例"""
    print("\n" + "="*70)
    print("LLM 客户端使用示例集")
    print("="*70)
    
    # 运行 Ollama 示例
    example_ollama()
    
    # 运行 Qwen 示例
    example_qwen()
    
    print("\n" + "="*70)
    print("所有示例运行完成！")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()

