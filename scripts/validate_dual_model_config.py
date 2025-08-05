#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
双模型架构配置验证脚本
"""

import sys
import os
import logging

# 添加项目根目录到Python路径
project_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, project_root)

try:
    from src.utils.llm import validate_llm_config, test_llm_connections
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保在项目根目录下运行此脚本")
    sys.exit(1)

def main():
    """主函数"""
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 80)
    print("双模型架构配置验证")
    print("=" * 80)
    
    # 验证配置
    validation = validate_llm_config()
    
    if not validation['valid']:
        print("❌ 配置验证失败")
        for error in validation['errors']:
            print(f"  - {error}")
        return
    
    print("✅ 配置验证通过")
    
    # 检查Agent对话生成配置
    print("\nAgent对话生成配置:")
    if 'qwen' in validation['clients'] and validation['clients']['qwen']['enabled']:
        config = validation['clients']['qwen']['config']
        print(f"✅ Qwen: {config.get('default_model')}")
        api_key = config.get('api_key', '')
        if api_key and api_key != "your_qwen_api_key_here":
            print(f"   API密钥: {api_key[:8]}...")
        else:
            print("   ❌ API密钥未设置")
    else:
        print("❌ Qwen未启用")
    
    # 检查嵌入检索配置
    print("\n嵌入检索配置:")
    if 'ollama' in validation['clients'] and validation['clients']['ollama']['enabled']:
        config = validation['clients']['ollama']['config']
        print(f"✅ Ollama: {config.get('embedding_model')}")
    else:
        print("❌ Ollama未启用")
    
    # 测试连接
    print("\n连接测试:")
    try:
        results = test_llm_connections()
        for client_name, result in results.items():
            if result['success']:
                print(f"✅ {client_name}: 连接成功")
            else:
                print(f"❌ {client_name}: 连接失败 - {result['error']}")
    except Exception as e:
        print(f"❌ 连接测试失败: {e}")

if __name__ == "__main__":
    main() 