#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的LLM配置测试脚本
"""

import yaml
import os

def test_config():
    """测试配置文件"""
    print("=" * 60)
    print("LLM配置测试")
    print("=" * 60)
    
    # 读取配置文件
    config_path = "src/config/config.yaml"
    if not os.path.exists(config_path):
        print(f"❌ 配置文件不存在: {config_path}")
        return
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"❌ 配置文件读取失败: {e}")
        return
    
    print("✅ 配置文件读取成功")
    
    # 检查LLM配置
    llm_config = config.get('llm', {})
    
    print(f"\n默认客户端: {llm_config.get('default_client', '未设置')}")
    
    # 检查Qwen配置
    qwen_config = llm_config.get('qwen', {})
    if qwen_config.get('enabled', False):
        print("✅ Qwen已启用")
        api_key = qwen_config.get('api_key', '')
        if api_key and api_key != "your_qwen_api_key_here":
            print(f"   API密钥: {api_key[:8]}...")
        else:
            print("   ❌ API密钥未设置")
        print(f"   模型: {qwen_config.get('default_model', '未设置')}")
    else:
        print("❌ Qwen未启用")
    
    # 检查Ollama配置
    ollama_config = llm_config.get('ollama', {})
    if ollama_config.get('enabled', False):
        print("✅ Ollama已启用")
        print(f"   嵌入模型: {ollama_config.get('embedding_model', '未设置')}")
        print(f"   服务地址: {ollama_config.get('base_url', '未设置')}")
    else:
        print("❌ Ollama未启用")
    
    print("\n配置验证完成！")

if __name__ == "__main__":
    test_config() 