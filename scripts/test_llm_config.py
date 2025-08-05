#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试LLM配置的脚本
用于验证config.yaml中的LLM配置是否正确
"""

import sys
import os
import logging

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils.llm import validate_llm_config, print_llm_config_status, test_llm_connections

def main():
    """主函数"""
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("LLM配置测试工具")
    print("=" * 60)
    
    # 验证配置
    print("\n1. 验证配置文件...")
    validation = validate_llm_config()
    
    if validation['valid']:
        print("✓ 配置文件格式正确")
    else:
        print("✗ 配置文件有错误")
        for error in validation['errors']:
            print(f"  - {error}")
        return
    
    # 显示配置状态
    print("\n2. 配置状态:")
    print_llm_config_status()
    
    # 测试连接
    print("\n3. 测试LLM连接...")
    try:
        results = test_llm_connections()
        
        success_count = 0
        for client_name, result in results.items():
            if result['success']:
                success_count += 1
                print(f"✓ {client_name}: 连接成功")
                print(f"  模型: {result['model']}")
                print(f"  响应: {result['response'][:100]}...")
            else:
                print(f"✗ {client_name}: 连接失败")
                print(f"  错误: {result['error']}")
        
        print(f"\n总结: {success_count}/{len(results)} 个客户端连接成功")
        
        if success_count == 0:
            print("\n建议:")
            print("1. 检查config.yaml中的配置是否正确")
            print("2. 确保API密钥已正确设置")
            print("3. 检查网络连接")
            print("4. 对于Ollama，确保服务正在运行")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")

if __name__ == "__main__":
    main() 