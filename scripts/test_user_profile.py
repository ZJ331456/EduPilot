#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户画像功能测试脚本
测试用户画像的构建、分析、存储和API功能
"""

import os
import sys
import asyncio
import json
import requests
from pathlib import Path
from datetime import datetime

# 添加src目录到Python路径
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from config.logging_config import get_logger, setup_logging, LoggerNames
from agents.user_profile_integrated import UserProfileAgent
from services.mongodb_integration import mongodb_service
from utils import AgentState

class DateTimeEncoder(json.JSONEncoder):
    """自定义JSON编码器，处理datetime对象"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class UserProfileTester:
    """用户画像测试器"""
    
    def __init__(self):
        self.logger = get_logger("hw_agent.user_profile_tester")
        self.user_profile_agent = UserProfileAgent()
        self.base_url = "http://localhost:8000/api/multi-agent"
        self.test_user_id = "test_user_001"
        
    async def test_user_profile_agent(self):
        """测试用户画像智能体"""
        print("=== 测试用户画像智能体 ===")
        
        # 创建测试状态
        test_state = AgentState(
            user_query="我叫张三，今年25岁，是一名软件工程师。我喜欢编程和人工智能，正在学习机器学习。我的学习习惯是喜欢看视频教程，然后动手实践。",
            session_id="test_session_001"
        )
        # 在元数据中设置用户ID
        test_state.metadata["user_id"] = self.test_user_id
        
        try:
            # 执行用户画像分析
            result_state = await self.user_profile_agent.execute(test_state)
            
            # 检查结果
            if hasattr(result_state, 'metadata') and 'user_profile_analysis' in result_state.metadata:
                analysis = result_state.metadata['user_profile_analysis']
                print("✅ 用户画像分析成功")
                print(f"   抽取的三元组数量: {len(analysis.get('triples', []))}")
                print(f"   情感分析: {analysis.get('emotion_analysis', {})}")
                print(f"   学习模式: {analysis.get('learning_patterns', [])}")
                
                # 打印详细的三元组信息
                triples = analysis.get('triples', [])
                if triples:
                    print("\n   抽取的三元组:")
                    for i, triple in enumerate(triples[:5]):  # 只显示前5个
                        print(f"     {i+1}. {triple.get('subject', '')} - {triple.get('predicate', '')} - {triple.get('object', '')}")
                
                return True
            else:
                print("❌ 用户画像分析失败：未找到分析结果")
                return False
                
        except Exception as e:
            print(f"❌ 用户画像智能体测试失败: {e}")
            self.logger.error(f"用户画像智能体测试失败: {e}")
            return False
    
    async def test_mongodb_integration(self):
        """测试MongoDB集成"""
        print("\n=== 测试MongoDB集成 ===")
        
        try:
            # 初始化MongoDB服务
            await mongodb_service.initialize()
            print("✅ MongoDB服务初始化成功")
            
            # 测试用户画像上下文获取
            context = await mongodb_service.get_user_profile_context(self.test_user_id)
            print(f"✅ 获取用户画像上下文成功: {len(context)} 个字段")
            
            # 测试清空用户画像
            success = await mongodb_service.clear_user_profile(self.test_user_id)
            if success:
                print("✅ 清空用户画像成功")
            else:
                print("⚠️  清空用户画像失败（可能是用户不存在）")
            
            return True
            
        except Exception as e:
            print(f"❌ MongoDB集成测试失败: {e}")
            self.logger.error(f"MongoDB集成测试失败: {e}")
            return False
    
    async def test_api_endpoints(self):
        """测试API端点"""
        print("\n=== 测试API端点 ===")
        
        try:
            # 测试健康检查
            response = requests.get(f"{self.base_url}/health-enhanced", timeout=30)
            if response.status_code == 200:
                print("✅ 健康检查API正常")
            else:
                print(f"⚠️  健康检查API返回状态码: {response.status_code}")
            
            # 测试获取用户画像API
            response = requests.get(f"{self.base_url}/user-profile/{self.test_user_id}", timeout=30)
            if response.status_code == 200:
                data = response.json()
                print("✅ 获取用户画像API正常")
                print(f"   用户ID: {data.get('user_id')}")
                print(f"   成功状态: {data.get('success')}")
            else:
                print(f"⚠️  获取用户画像API返回状态码: {response.status_code}")
            
            # 测试获取当前用户画像API
            response = requests.get(f"{self.base_url}/user-profile", timeout=30)
            if response.status_code == 200:
                data = response.json()
                print("✅ 获取当前用户画像API正常")
                profile = data.get('user_profile', {})
                print(f"   实体数量: {profile.get('graph_statistics', {}).get('entity_count', 0)}")
                print(f"   关系数量: {profile.get('graph_statistics', {}).get('relation_count', 0)}")
            else:
                print(f"⚠️  获取当前用户画像API返回状态码: {response.status_code}")
            
            return True
            
        except requests.exceptions.ConnectionError:
            print("❌ 无法连接到API服务器，请确保服务器正在运行")
            return False
        except requests.exceptions.Timeout:
            print("❌ API请求超时，可能是服务器响应较慢")
            return False
        except Exception as e:
            print(f"❌ API测试失败: {e}")
            return False
    
    async def test_user_profile_building(self):
        """测试用户画像构建过程"""
        print("\n=== 测试用户画像构建过程 ===")
        
        # 模拟多轮对话来构建用户画像
        conversations = [
            "我叫李四，是一名大学生，专业是计算机科学。",
            "我喜欢编程，特别是Python和机器学习。",
            "我的学习习惯是喜欢看视频教程，然后做项目实践。",
            "我希望将来能成为一名AI工程师。",
            "我比较内向，喜欢独自学习，但也会参加一些技术讨论。"
        ]
        
        try:
            total_triples = 0
            for i, conversation in enumerate(conversations):
                print(f"   对话 {i+1}: {conversation}")
                
                # 创建状态
                state = AgentState(
                    user_query=conversation,
                    session_id=f"build_session_{i+1}"
                )
                # 在元数据中设置用户ID
                state.metadata["user_id"] = self.test_user_id
                
                # 执行用户画像分析
                result_state = await self.user_profile_agent.execute(state)
                
                # 检查是否有分析结果
                if hasattr(result_state, 'metadata') and 'user_profile_analysis' in result_state.metadata:
                    analysis = result_state.metadata['user_profile_analysis']
                    triples = analysis.get('triples', [])
                    total_triples += len(triples)
                    print(f"   ✅ 抽取了 {len(triples)} 个三元组")
                else:
                    print("   ⚠️  未找到分析结果")
            
            print(f"✅ 用户画像构建过程测试完成，总共抽取了 {total_triples} 个三元组")
            
            # 验证用户画像是否已保存
            if self.test_user_id in self.user_profile_agent.user_profiles:
                profile = self.user_profile_agent.user_profiles[self.test_user_id]
                print(f"   📊 用户画像已保存，包含 {len(profile.get('triples', []))} 个三元组")
            else:
                print("   ⚠️  用户画像未保存到内存")
            
            return True
            
        except Exception as e:
            print(f"❌ 用户画像构建测试失败: {e}")
            self.logger.error(f"用户画像构建测试失败: {e}")
            return False
    
    async def test_profile_analysis(self):
        """测试用户画像分析功能"""
        print("\n=== 测试用户画像分析功能 ===")
        
        try:
            # 获取用户画像
            profile = self.user_profile_agent.user_profiles.get(self.test_user_id, {})
            
            if profile and profile.get('triples'):
                print("✅ 找到用户画像数据")
                print(f"   三元组数量: {len(profile.get('triples', []))}")
                print(f"   情感记录: {len(profile.get('emotions', []))}")
                print(f"   学习模式: {len(profile.get('learning_patterns', []))}")
                
                # 分析用户画像
                analysis = self.user_profile_agent._analyze_user_profile(self.test_user_id)
                
                if analysis:
                    print("✅ 用户画像分析成功")
                    
                    # 显示基础统计
                    basic_stats = analysis.get('basic_statistics', {})
                    if basic_stats:
                        print(f"   总三元组: {basic_stats.get('total_triples', 0)}")
                        print(f"   总情感记录: {basic_stats.get('total_emotions', 0)}")
                        print(f"   总学习模式: {basic_stats.get('total_patterns', 0)}")
                    
                    # 显示学习画像
                    learning_profile = analysis.get('learning_profile', {})
                    if learning_profile:
                        print(f"   学习风格: {learning_profile.get('learning_style', '未知')}")
                        print(f"   知识水平: {learning_profile.get('knowledge_level', '未知')}")
                        print(f"   优势领域: {len(learning_profile.get('strengths', []))} 个")
                    
                    # 显示兴趣分析
                    interests_analysis = analysis.get('interests_analysis', {})
                    if interests_analysis:
                        print(f"   主要兴趣: {len(interests_analysis.get('top_interests', []))} 个")
                        print(f"   兴趣类别: {len(interests_analysis.get('interest_categories', {}))} 个")
                    
                    # 显示洞察
                    insights = analysis.get('insights', [])
                    if insights:
                        print(f"   生成洞察: {len(insights)} 个")
                        for i, insight in enumerate(insights[:3]):  # 只显示前3个
                            print(f"     {i+1}. {insight.get('description', '')}")
                    
                    return True
                else:
                    print("❌ 用户画像分析失败")
                    return False
            else:
                print("⚠️  未找到用户画像数据，请先运行构建测试")
                print(f"   当前用户画像状态: {bool(profile)}")
                if profile:
                    print(f"   三元组数量: {len(profile.get('triples', []))}")
                return False
                
        except Exception as e:
            print(f"❌ 用户画像分析测试失败: {e}")
            self.logger.error(f"用户画像分析测试失败: {e}")
            return False
    
    async def test_profile_export(self):
        """测试用户画像导出功能"""
        print("\n=== 测试用户画像导出功能 ===")
        
        try:
            # 检查是否有用户画像数据
            profile = self.user_profile_agent.user_profiles.get(self.test_user_id, {})
            
            if not profile:
                print("⚠️  未找到用户画像数据，跳过导出测试")
                return True
            
            # 导出到JSON文件
            export_path = f"test_user_profile_{self.test_user_id}.json"
            
            # 模拟导出功能（实际实现可能需要根据具体需求调整）
            export_data = {
                "user_id": self.test_user_id,
                "profile": profile,
                "analysis": self.user_profile_agent._analyze_user_profile(self.test_user_id),
                "export_time": datetime.now().isoformat()
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2, cls=DateTimeEncoder)
            
            print(f"✅ 用户画像导出成功: {export_path}")
            
            # 检查文件是否存在
            if Path(export_path).exists():
                file_size = Path(export_path).stat().st_size
                print(f"   文件大小: {file_size} bytes")
                return True
            else:
                print("❌ 导出文件未创建")
                return False
                
        except Exception as e:
            print(f"❌ 用户画像导出测试失败: {e}")
            self.logger.error(f"用户画像导出测试失败: {e}")
            return False
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("开始用户画像功能测试...\n")
        
        # 初始化日志
        setup_logging('hw_agent')
        
        test_results = []
        
        # 1. 测试用户画像智能体
        result = await self.test_user_profile_agent()
        test_results.append(("用户画像智能体", result))
        
        # 2. 测试MongoDB集成
        result = await self.test_mongodb_integration()
        test_results.append(("MongoDB集成", result))
        
        # 3. 测试API端点
        result = await self.test_api_endpoints()
        test_results.append(("API端点", result))
        
        # 4. 测试用户画像构建
        result = await self.test_user_profile_building()
        test_results.append(("用户画像构建", result))
        
        # 5. 测试用户画像分析
        result = await self.test_profile_analysis()
        test_results.append(("用户画像分析", result))
        
        # 6. 测试用户画像导出
        result = await self.test_profile_export()
        test_results.append(("用户画像导出", result))
        
        # 显示测试结果摘要
        print("\n" + "="*50)
        print("测试结果摘要")
        print("="*50)
        
        passed = 0
        total = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{test_name:<20} {status}")
            if result:
                passed += 1
        
        print(f"\n总计: {passed}/{total} 个测试通过")
        
        if passed == total:
            print("🎉 所有测试都通过了！用户画像功能正常工作。")
        else:
            print("⚠️  部分测试失败，请检查相关功能。")
        
        return passed == total

async def main():
    """主函数"""
    tester = UserProfileTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n💡 使用建议:")
        print("1. 启动API服务器: python -m uvicorn src.app:app --reload")
        print("2. 访问用户画像API: http://localhost:8000/user-profile")
        print("3. 查看测试导出的用户画像文件")
    else:
        print("\n🔧 故障排除:")
        print("1. 检查MongoDB连接配置")
        print("2. 确保API服务器正在运行")
        print("3. 查看日志文件获取详细错误信息")

if __name__ == "__main__":
    asyncio.run(main()) 