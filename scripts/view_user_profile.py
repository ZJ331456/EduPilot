#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户画像查看工具
用于查看和分析用户画像数据
"""

import os
import sys
import json
import asyncio
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# 添加src目录到Python路径
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from config.logging_config import get_logger, setup_logging

class UserProfileViewer:
    """用户画像查看器"""
    
    def __init__(self):
        self.logger = get_logger("hw_agent.user_profile_viewer")
        self.base_url = "http://localhost:8000/api/multi-agent"
        
    def print_profile_summary(self, profile_data: Dict[str, Any]):
        """打印用户画像摘要"""
        print("\n" + "="*60)
        print("用户画像摘要")
        print("="*60)
        
        user_id = profile_data.get('user_id', '未知')
        print(f"用户ID: {user_id}")
        
        # 检查是否是新的用户画像格式
        if 'triples' in profile_data:
            # 新格式：包含三元组、情感分析、学习模式等
            triples = profile_data.get('triples', [])
            emotions = profile_data.get('emotions', [])
            learning_patterns = profile_data.get('learning_patterns', [])
            profile_completeness = profile_data.get('profile_completeness', 0.0)
            
            print(f"\n📊 统计信息:")
            print(f"   三元组数量: {len(triples)}")
            print(f"   情感记录数量: {len(emotions)}")
            print(f"   学习模式数量: {len(learning_patterns)}")
            print(f"   完整度: {profile_completeness:.1%}")
            
            # 显示三元组信息
            if triples:
                print(f"\n🔗 用户信息三元组:")
                for i, triple in enumerate(triples[:5], 1):  # 只显示前5个
                    subject = triple.get('subject', '')
                    predicate = triple.get('predicate', '')
                    obj = triple.get('object', '')
                    dimension = triple.get('dimension', '')
                    confidence = triple.get('confidence', 0)
                    print(f"   {i}. {subject} - {predicate} - {obj}")
                    print(f"      维度: {dimension}, 置信度: {confidence:.2f}")
                if len(triples) > 5:
                    print(f"   ... 还有 {len(triples) - 5} 个三元组")
            
            # 显示情感分析
            if emotions:
                print(f"\n😊 情感分析:")
                recent_emotions = emotions[-3:]  # 显示最近3次
                for i, emotion in enumerate(recent_emotions, 1):
                    primary = emotion.get('primary_emotion', '')
                    confidence = emotion.get('confidence', 0)
                    indicators = emotion.get('emotional_indicators', [])
                    timestamp = emotion.get('timestamp', '')
                    print(f"   {i}. 主要情感: {primary} (置信度: {confidence:.2f})")
                    if indicators:
                        print(f"      情感指标: {', '.join(indicators)}")
            
            # 显示学习模式
            if learning_patterns:
                print(f"\n📚 学习模式:")
                recent_patterns = learning_patterns[-3:]  # 显示最近3次
                for i, pattern in enumerate(recent_patterns, 1):
                    pattern_type = pattern.get('pattern', '')
                    score = pattern.get('score', 0)
                    confidence = pattern.get('confidence', 0)
                    indicators = pattern.get('indicators', [])
                    print(f"   {i}. 模式: {pattern_type} (得分: {score}, 置信度: {confidence:.2f})")
                    if indicators:
                        print(f"      指标: {', '.join(indicators)}")
            
            # 显示创建和更新时间
            created_at = profile_data.get('created_at')
            updated_at = profile_data.get('updated_at')
            if created_at:
                print(f"\n📅 创建时间: {created_at}")
            if updated_at:
                print(f"📅 更新时间: {updated_at}")
                
        else:
            # 旧格式：兼容原有的显示方式
            # 基本信息
            basic_info = profile_data.get('basic_info', {})
            if basic_info:
                print(f"\n📋 基本信息:")
                for key, value in basic_info.items():
                    print(f"   {key}: {value}")
            
            # 兴趣爱好
            interests = profile_data.get('interests', {})
            if interests:
                primary_interests = interests.get('primary_interests', [])
                if primary_interests:
                    print(f"\n🎯 主要兴趣:")
                    for interest in primary_interests:
                        print(f"   • {interest}")
            
            # 学习档案
            learning_profile = profile_data.get('learning_profile', {})
            if learning_profile:
                print(f"\n📚 学习档案:")
                learning_style = learning_profile.get('learning_style', '未知')
                knowledge_level = learning_profile.get('knowledge_level', '未知')
                print(f"   学习风格: {learning_style}")
                print(f"   知识水平: {knowledge_level}")
                
                strengths = learning_profile.get('strengths', [])
                if strengths:
                    print(f"   优势领域:")
                    for strength in strengths:
                        print(f"     • {strength}")
            
            # 性格特征
            personality_profile = profile_data.get('personality_profile', {})
            if personality_profile:
                print(f"\n👤 性格特征:")
                traits = personality_profile.get('traits', [])
                if traits:
                    for trait in traits:
                        print(f"   • {trait}")
            
            # 洞察和建议
            insights = profile_data.get('insights', [])
            if insights:
                print(f"\n💡 洞察和建议:")
                for i, insight in enumerate(insights, 1):
                    title = insight.get('title', '')
                    description = insight.get('description', '')
                    print(f"   {i}. {title}")
                    print(f"      {description}")
            
            # 统计信息
            stats = profile_data.get('statistics', {})
            if stats:
                print(f"\n📊 统计信息:")
                print(f"   三元组数量: {stats.get('triple_count', 0)}")
                print(f"   实体数量: {stats.get('entity_count', 0)}")
                print(f"   关系数量: {stats.get('relation_count', 0)}")
                print(f"   对话轮次: {stats.get('conversation_turns', 0)}")
    
    def print_triples(self, triples: list):
        """打印三元组信息"""
        if not triples:
            print("暂无三元组数据")
            return
        
        print(f"用户信息三元组 (共 {len(triples)} 条):")
        for i, triple in enumerate(triples, 1):
            subject = triple.get('subject', '')
            predicate = triple.get('predicate', '')
            obj = triple.get('object', '')
            dimension = triple.get('dimension', '')
            confidence = triple.get('confidence', 0)
            source = triple.get('source', '')
            timestamp = triple.get('timestamp', '')
            
            print(f"  {i}. {subject} - {predicate} - {obj}")
            print(f"     维度: {dimension}")
            print(f"     置信度: {confidence:.2f}")
            print(f"     来源: {source}")
            if timestamp:
                print(f"     时间: {timestamp}")
            print()
    
    def print_emotion_analysis(self, emotion_data: Dict[str, Any]):
        """打印情感分析信息"""
        emotions = emotion_data.get('emotions', [])
        if not emotions:
            print("暂无情感分析数据")
            return
        
        print(f"情感分析记录 (共 {len(emotions)} 条):")
        for i, emotion in enumerate(emotions, 1):
            primary = emotion.get('primary_emotion', '未知')
            confidence = emotion.get('confidence', 0)
            indicators = emotion.get('emotional_indicators', [])
            timestamp = emotion.get('timestamp', '')
            
            print(f"  {i}. 主要情感: {primary}")
            print(f"     置信度: {confidence:.2f}")
            if indicators:
                print(f"     情感指标: {', '.join(indicators)}")
            if timestamp:
                print(f"     时间: {timestamp}")
            print()
    
    def print_learning_patterns(self, patterns: list):
        """打印学习模式信息"""
        if not patterns:
            print("暂无学习模式数据")
            return
        
        print(f"学习模式记录 (共 {len(patterns)} 条):")
        for i, pattern in enumerate(patterns, 1):
            pattern_type = pattern.get('pattern', '未知')
            score = pattern.get('score', 0)
            confidence = pattern.get('confidence', 0)
            indicators = pattern.get('indicators', [])
            timestamp = pattern.get('timestamp', '')
            
            print(f"  {i}. 学习模式: {pattern_type}")
            print(f"     得分: {score}")
            print(f"     置信度: {confidence:.2f}")
            if indicators:
                print(f"     指标: {', '.join(indicators)}")
            if timestamp:
                print(f"     时间: {timestamp}")
            print()
    
    async def get_user_profile_from_api(self, user_id: str) -> Optional[Dict[str, Any]]:
        """从API获取用户画像"""
        try:
            response = requests.get(f"{self.base_url}/user-profile/{user_id}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    return data.get('profile', {})
            else:
                print(f"API请求失败，状态码: {response.status_code}")
                return None
        except requests.exceptions.ConnectionError:
            print("无法连接到API服务器，请确保服务器正在运行")
            return None
        except Exception as e:
            print(f"获取用户画像失败: {e}")
            return None
    
    def load_profile_from_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """从文件加载用户画像"""
        try:
            if not Path(file_path).exists():
                print(f"文件不存在: {file_path}")
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return data
        except Exception as e:
            print(f"加载文件失败: {e}")
            return None
    
    def save_profile_to_file(self, profile_data: Dict[str, Any], file_path: str):
        """保存用户画像到文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, ensure_ascii=False, indent=2)
            print(f"用户画像已保存到: {file_path}")
        except Exception as e:
            print(f"保存文件失败: {e}")
    
    def compare_profiles(self, profile1: Dict[str, Any], profile2: Dict[str, Any]):
        """比较两个用户画像"""
        print("\n" + "="*60)
        print("用户画像比较")
        print("="*60)
        
        # 比较基本信息
        basic1 = profile1.get('basic_info', {})
        basic2 = profile2.get('basic_info', {})
        
        print("📋 基本信息比较:")
        all_keys = set(basic1.keys()) | set(basic2.keys())
        for key in all_keys:
            val1 = basic1.get(key, '无')
            val2 = basic2.get(key, '无')
            if val1 != val2:
                print(f"   {key}: {val1} vs {val2}")
            else:
                print(f"   {key}: {val1} (相同)")
        
        # 比较兴趣
        interests1 = profile1.get('interests', {}).get('primary_interests', [])
        interests2 = profile2.get('interests', {}).get('primary_interests', [])
        
        print(f"\n🎯 兴趣比较:")
        print(f"   用户1兴趣: {', '.join(interests1) if interests1 else '无'}")
        print(f"   用户2兴趣: {', '.join(interests2) if interests2 else '无'}")
        
        # 比较学习风格
        style1 = profile1.get('learning_profile', {}).get('learning_style', '未知')
        style2 = profile2.get('learning_profile', {}).get('learning_style', '未知')
        
        print(f"\n📚 学习风格比较:")
        print(f"   用户1: {style1}")
        print(f"   用户2: {style2}")
    
    def interactive_viewer(self):
        """交互式查看器"""
        print("用户画像查看工具")
        print("="*30)
        
        while True:
            print("\n请选择操作:")
            print("1. 从API获取用户画像")
            print("2. 从文件加载用户画像")
            print("3. 比较两个用户画像")
            print("4. 退出")
            
            choice = input("\n请输入选择 (1-4): ").strip()
            
            if choice == '1':
                user_id = input("请输入用户ID: ").strip()
                if user_id:
                    asyncio.run(self.view_profile_from_api(user_id))
            
            elif choice == '2':
                file_path = input("请输入文件路径: ").strip()
                if file_path:
                    self.view_profile_from_file(file_path)
            
            elif choice == '3':
                file1 = input("请输入第一个用户画像文件路径: ").strip()
                file2 = input("请输入第二个用户画像文件路径: ").strip()
                if file1 and file2:
                    profile1 = self.load_profile_from_file(file1)
                    profile2 = self.load_profile_from_file(file2)
                    if profile1 and profile2:
                        self.compare_profiles(profile1, profile2)
            
            elif choice == '4':
                print("退出查看器")
                break
            
            else:
                print("无效选择，请重新输入")
    
    async def view_profile_from_api(self, user_id: str):
        """从API查看用户画像"""
        print(f"\n正在从API获取用户 {user_id} 的画像...")
        
        profile_data = await self.get_user_profile_from_api(user_id)
        if profile_data:
            self.print_profile_summary(profile_data)
            
            # 检查是否是新的用户画像格式
            if 'triples' in profile_data:
                # 新格式：显示详细信息
                triples = profile_data.get('triples', [])
                emotions = profile_data.get('emotions', [])
                learning_patterns = profile_data.get('learning_patterns', [])
                
                # 显示所有三元组
                if triples:
                    print(f"\n" + "="*60)
                    print("详细三元组信息")
                    print("="*60)
                    self.print_triples(triples)
                
                # 显示情感分析
                if emotions:
                    print(f"\n" + "="*60)
                    print("详细情感分析")
                    print("="*60)
                    self.print_emotion_analysis({"emotions": emotions})
                
                # 显示学习模式
                if learning_patterns:
                    print(f"\n" + "="*60)
                    print("详细学习模式")
                    print("="*60)
                    self.print_learning_patterns(learning_patterns)
            else:
                # 旧格式：保持原有逻辑
                triples = profile_data.get('triples', [])
                self.print_triples(triples)
                
                emotion_data = profile_data.get('emotion_analysis', {})
                self.print_emotion_analysis(emotion_data)
                
                patterns = profile_data.get('learning_patterns', [])
                self.print_learning_patterns(patterns)
            
            # 询问是否保存
            save_choice = input("\n是否保存到文件? (y/n): ").strip().lower()
            if save_choice == 'y':
                file_path = f"user_profile_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                self.save_profile_to_file(profile_data, file_path)
        else:
            print("获取用户画像失败")
    
    def view_profile_from_file(self, file_path: str):
        """从文件查看用户画像"""
        print(f"\n正在从文件加载用户画像: {file_path}")
        
        profile_data = self.load_profile_from_file(file_path)
        if profile_data:
            self.print_profile_summary(profile_data)
            
            # 显示详细信息
            triples = profile_data.get('triples', [])
            self.print_triples(triples)
            
            emotion_data = profile_data.get('emotion_analysis', {})
            self.print_emotion_analysis(emotion_data)
            
            patterns = profile_data.get('learning_patterns', [])
            self.print_learning_patterns(patterns)
        else:
            print("加载用户画像失败")

def main():
    """主函数"""
    # 初始化日志
    setup_logging('hw_agent')
    
    viewer = UserProfileViewer()
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] == '--api':
            if len(sys.argv) > 2:
                user_id = sys.argv[2]
                asyncio.run(viewer.view_profile_from_api(user_id))
            else:
                print("请提供用户ID: python view_user_profile.py --api <user_id>")
        elif sys.argv[1] == '--file':
            if len(sys.argv) > 2:
                file_path = sys.argv[2]
                viewer.view_profile_from_file(file_path)
            else:
                print("请提供文件路径: python view_user_profile.py --file <file_path>")
        elif sys.argv[1] == '--compare':
            if len(sys.argv) > 3:
                file1 = sys.argv[2]
                file2 = sys.argv[3]
                profile1 = viewer.load_profile_from_file(file1)
                profile2 = viewer.load_profile_from_file(file2)
                if profile1 and profile2:
                    viewer.compare_profiles(profile1, profile2)
            else:
                print("请提供两个文件路径: python view_user_profile.py --compare <file1> <file2>")
        else:
            print("用法:")
            print("  python view_user_profile.py --api <user_id>     # 从API获取用户画像")
            print("  python view_user_profile.py --file <file_path>  # 从文件加载用户画像")
            print("  python view_user_profile.py --compare <file1> <file2>  # 比较两个用户画像")
            print("  python view_user_profile.py                     # 交互式模式")
    else:
        # 交互式模式
        viewer.interactive_viewer()

if __name__ == "__main__":
    main() 