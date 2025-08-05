#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志系统测试脚本
测试日志配置、文件输出、级别控制等功能
"""

import os
import sys
import time
import asyncio
from pathlib import Path

# 添加src目录到Python路径
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from config.logging_config import get_logger, setup_logging, LoggerNames
from config.logging_env import LoggingEnvConfig
from tools.log_manager import LogManager

def test_basic_logging():
    """测试基础日志功能"""
    print("=== 测试基础日志功能 ===")
    
    # 初始化日志配置
    setup_logging('hw_agent')
    
    # 获取不同模块的日志器
    app_logger = get_logger(LoggerNames.APP)
    agent_logger = get_logger(LoggerNames.AGENT)
    llm_logger = get_logger(LoggerNames.LLM)
    api_logger = get_logger(LoggerNames.API)
    
    # 测试不同级别的日志
    app_logger.debug("这是DEBUG级别的日志")
    app_logger.info("这是INFO级别的日志")
    app_logger.warning("这是WARNING级别的日志")
    app_logger.error("这是ERROR级别的日志")
    app_logger.critical("这是CRITICAL级别的日志")
    
    # 测试不同模块的日志
    agent_logger.info("智能体模块日志测试")
    llm_logger.info("LLM模块日志测试")
    api_logger.info("API模块日志测试")
    
    print("基础日志功能测试完成\n")

def test_structured_logging():
    """测试结构化日志"""
    print("=== 测试结构化日志 ===")
    
    logger = get_logger("hw_agent.structured_test")
    
    # 模拟用户操作日志
    user_id = "user_123"
    session_id = "session_456"
    query = "什么是人工智能？"
    
    logger.info(f"用户 {user_id} 在会话 {session_id} 中查询: {query}")
    
    # 模拟系统状态日志
    memory_usage = 75.5
    cpu_usage = 45.2
    response_time = 1.23
    
    logger.info(f"系统状态 - 内存: {memory_usage}%, CPU: {cpu_usage}%, 响应时间: {response_time}s")
    
    # 模拟错误日志
    try:
        # 模拟一个错误
        result = 10 / 0
    except ZeroDivisionError as e:
        logger.error(f"除零错误: {e}", exc_info=True)
    
    print("结构化日志测试完成\n")

async def test_async_logging():
    """测试异步日志"""
    print("=== 测试异步日志 ===")
    
    logger = get_logger(LoggerNames.CONVERSATION)
    
    logger.info("开始异步日志测试")
    
    for i in range(3):
        logger.info(f"异步操作 {i+1}/3")
        await asyncio.sleep(0.5)
    
    logger.info("异步日志测试完成")
    print("异步日志测试完成\n")

def test_log_levels():
    """测试日志级别控制"""
    print("=== 测试日志级别控制 ===")
    
    logger = get_logger("hw_agent.level_test")
    
    # 测试所有级别
    levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    
    for level in levels:
        log_func = getattr(logger, level.lower())
        log_func(f"这是 {level} 级别的测试消息")
    
    print("日志级别控制测试完成\n")

def test_log_manager():
    """测试日志管理器"""
    print("=== 测试日志管理器 ===")
    
    log_manager = LogManager("logs")
    
    # 列出日志文件
    files = log_manager.list_log_files()
    print(f"当前日志文件数量: {len(files)}")
    
    for file_info in files:
        print(f"  {file_info['name']} - {file_info['size_mb']}MB")
    
    # 获取日志摘要
    summary = log_manager.get_log_summary()
    print(f"日志摘要: {summary['total_files']} 个文件, 总大小 {summary['total_size_mb']}MB")
    
    print("日志管理器测试完成\n")

def test_environment_config():
    """测试环境变量配置"""
    print("=== 测试环境变量配置 ===")
    
    # 打印当前配置
    LoggingEnvConfig.print_config()
    
    # 获取所有配置
    config = LoggingEnvConfig.get_all_config()
    print(f"配置项总数: {len(config)}")
    
    print("环境变量配置测试完成\n")

def test_log_file_creation():
    """测试日志文件创建"""
    print("=== 测试日志文件创建 ===")
    
    # 确保日志目录存在
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 创建测试日志器
    test_logger = get_logger("hw_agent.test_file_creation")
    
    # 写入一些测试日志
    for i in range(10):
        test_logger.info(f"测试日志条目 {i+1}")
        test_logger.debug(f"调试信息 {i+1}")
        if i % 3 == 0:
            test_logger.warning(f"警告信息 {i+1}")
        if i % 5 == 0:
            test_logger.error(f"错误信息 {i+1}")
    
    # 检查文件是否创建
    log_files = list(log_dir.glob("*.log"))
    print(f"创建的日志文件: {[f.name for f in log_files]}")
    
    print("日志文件创建测试完成\n")

def test_log_rotation():
    """测试日志轮转"""
    print("=== 测试日志轮转 ===")
    
    log_manager = LogManager("logs")
    
    # 模拟创建大文件（这里只是演示，实际需要真实的大文件）
    print("注意: 日志轮转需要真实的大文件才能测试")
    print("可以使用 --max-size 参数设置较小的阈值进行测试")
    
    # 测试清理功能
    cleaned = log_manager.clean_old_logs(days=365)  # 清理一年前的文件
    print(f"清理了 {len(cleaned)} 个旧文件")
    
    print("日志轮转测试完成\n")

async def main():
    """主测试函数"""
    print("开始日志系统测试...\n")
    
    try:
        # 基础功能测试
        test_basic_logging()
        
        # 结构化日志测试
        test_structured_logging()
        
        # 异步日志测试
        await test_async_logging()
        
        # 日志级别测试
        test_log_levels()
        
        # 环境配置测试
        test_environment_config()
        
        # 文件创建测试
        test_log_file_creation()
        
        # 日志管理器测试
        test_log_manager()
        
        # 日志轮转测试
        test_log_rotation()
        
        print("所有测试完成！")
        print("\n检查 logs/ 目录中的日志文件:")
        
        log_dir = Path("logs")
        if log_dir.exists():
            for log_file in log_dir.glob("*.log"):
                size = log_file.stat().st_size
                print(f"  {log_file.name} - {size} bytes")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 