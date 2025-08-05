# Unique and complete code without duplicates
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学习器智能体（整合版）
分析交互结果，提取新知识并更新知识库
整合了基础学习分析和增强学习分析功能
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
from utils import BaseAgent, AgentState
from utils.llm import Message, MessageRole

class LearnerAgent(BaseAgent):
    """学习器智能体（整合版）
    
    基础功能：
    - 分析交互结果，提取新知识并更新知识库
    
    增强功能：
    - 利用决策代理和增强苏格拉底引导的结果
    - 更智能的学习路径推荐
    - 个性化学习策略调整
    """
    
    def __init__(self, learning_data_dir: str = None, enable_enhanced_mode: bool = None):
        super().__init__(
            name="Learner",
            description="分析交互结果，提取新知识并更新知识库"
        )
        
        # 导入配置管理器
        from config import get_agent_config
        
        learner_config = get_agent_config('learner')
        
        # 使用相对路径指向项目根目录
        project_root = Path(__file__).parent.parent.parent
        if learning_data_dir is None:
            self.learning_data_dir = project_root / learner_config.get('learning_data_dir', "data/learning")
        else:
            self.learning_data_dir = Path(learning_data_dir)
        self.enhanced_learning_dir = project_root / "data" / "enhanced_learning"
        
        # 确保目录存在
        self.learning_data_dir.mkdir(parents=True, exist_ok=True)
        self.enhanced_learning_dir.mkdir(parents=True, exist_ok=True)
        
        self.interaction_log = []
        self.knowledge_updates = []
        self.learning_patterns = {}
        self.user_profiles = {}  # 用户学习档案（增强功能）
        
        # 学习配置
        self.min_interaction_quality = 0.6
        self.max_learning_entries = learner_config.get('max_learning_records', 1000)
        self.enable_enhanced_mode = enable_enhanced_mode if enable_enhanced_mode is not None else learner_config.get('enhanced_mode', True)
        
        # 增强学习配置
        self.coherence_weight = 0.3  # 苏格拉底问答连贯性权重
        self.decision_weight = 0.2   # 决策代理分析权重
    
    def can_execute(self, state: AgentState) -> bool:
        """检查是否可以执行"""
        return (
            state.execution_result is not None and
            state.execution_result.get("success", False)
        )
    
    async def execute(self, state: AgentState) -> AgentState:
        """执行学习分析（支持基础和增强模式）"""
        try:
            if self.enable_enhanced_mode:
                return self._execute_enhanced_learning(state)
            else:
                return self._execute_basic_learning(state)
                
        except Exception as e:
            self.logger.error(f"Learning analysis failed: {e}")
            state.set_error(
                "learning_error",
                f"Failed to analyze learning: {str(e)}"
            )
            return state
    
    def _execute_basic_learning(self, state: AgentState) -> AgentState:
        """执行基础学习分析"""
        # 1. 分析交互质量
        interaction_analysis = self._analyze_interaction(state)
        
        # 2. 提取学习要点
        learning_insights = self._extract_learning_insights(state, interaction_analysis)
        
        # 3. 识别知识缺口
        knowledge_gaps = self._identify_knowledge_gaps(state, interaction_analysis)
        
        # 4. 生成学习反馈
        learning_feedback = self._generate_learning_feedback(
            state, interaction_analysis, learning_insights, knowledge_gaps
        )
        
        # 5. 更新学习模式
        self._update_learning_patterns(state, interaction_analysis)
        
        # 6. 保存学习数据
        self._save_learning_data(state, {
            "interaction_analysis": interaction_analysis,
            "learning_insights": learning_insights,
            "knowledge_gaps": knowledge_gaps,
            "learning_feedback": learning_feedback
        })
        
        # 7. 更新状态
        state.learning_feedback = learning_feedback
        state.knowledge_gaps = knowledge_gaps
        state.learning_insights = learning_insights
        
        # 8. 记录交互日志
        self.interaction_log.append({
            "session_id": state.session_id,
            "timestamp": state.timestamp,
            "query": state.user_query,
            "quality_score": interaction_analysis.get("quality_score", 0),
            "learning_value": interaction_analysis.get("learning_value", 0)
        })
        
        self.logger.info(f"Basic learning analysis completed with quality score: {interaction_analysis.get('quality_score', 0):.2f}")
        
        return state
    
    def _execute_enhanced_learning(self, state: AgentState) -> AgentState:
        """执行增强学习分析"""
        # 1. 增强交互质量分析
        interaction_analysis = self._analyze_enhanced_interaction(state)
        
        # 2. 提取多维度学习洞察
        learning_insights = self._extract_enhanced_learning_insights(state, interaction_analysis)
        
        # 3. 识别个性化知识缺口
        knowledge_gaps = self._identify_personalized_knowledge_gaps(state, interaction_analysis)
        
        # 4. 生成智能学习反馈
        learning_feedback = self._generate_intelligent_learning_feedback(
            state, interaction_analysis, learning_insights, knowledge_gaps
        )
        
        # 5. 更新用户学习档案
        self._update_user_profile(state, interaction_analysis)
        
        # 6. 推荐个性化学习路径
        learning_path = self._recommend_learning_path(state, interaction_analysis, learning_insights)
        
        # 7. 保存增强学习数据
        self._save_enhanced_learning_data(state, {
            "interaction_analysis": interaction_analysis,
            "learning_insights": learning_insights,
            "knowledge_gaps": knowledge_gaps,
            "learning_feedback": learning_feedback,
            "learning_path": learning_path
        })
        
        # 8. 更新状态
        state.enhanced_learning_feedback = learning_feedback
        state.knowledge_gaps = knowledge_gaps
        state.learning_insights = learning_insights
        state.recommended_learning_path = learning_path
        
        # 9. 记录增强交互日志
        self.interaction_log.append({
            "session_id": state.session_id,
            "timestamp": state.timestamp,
            "query": state.user_query,
            "quality_score": interaction_analysis.get("quality_score", 0),
            "learning_value": interaction_analysis.get("learning_value", 0),
            "coherence_score": interaction_analysis.get("coherence_score", 0),
            "decision_quality": interaction_analysis.get("decision_quality", 0)
        })
        
        self.logger.info(
            f"Enhanced learning analysis completed - Quality: {interaction_analysis.get('quality_score', 0):.2f}, "
            f"Coherence: {interaction_analysis.get('coherence_score', 0):.2f}"
        )
        
        return state
    
    def _analyze_interaction(self, state: AgentState) -> Dict[str, Any]:
        """分析交互质量"""
        analysis = {
            "quality_score": 0.0,
            "learning_value": 0.0,
            "engagement_level": 0.0,
            "knowledge_coverage": 0.0,
            "response_effectiveness": 0.0,
            "areas_for_improvement": []
        }
        
        # 1. 评估用户参与度
        engagement_score = self._evaluate_user_engagement(state)
        analysis["engagement_level"] = engagement_score
        
        # 2. 评估知识覆盖度
        coverage_score = self._evaluate_knowledge_coverage(state)
        analysis["knowledge_coverage"] = coverage_score
        
        # 3. 评估响应效果
        effectiveness_score = self._evaluate_response_effectiveness(state)
        analysis["response_effectiveness"] = effectiveness_score
        
        # 4. 计算学习价值
        learning_value = self._calculate_learning_value(state)
        analysis["learning_value"] = learning_value
        
        # 5. 计算综合质量分数
        analysis["quality_score"] = (
            engagement_score * 0.25 +
            coverage_score * 0.25 +
            effectiveness_score * 0.25 +
            learning_value * 0.25
        )
        
        # 6. 识别改进领域
        analysis["areas_for_improvement"] = self._identify_improvement_areas(analysis)
        
        return analysis
    
    def _evaluate_user_engagement(self, state: AgentState) -> float:
        """评估用户参与度"""
        if not state.user_responses:
            return 0.3  # 基础分数
        
        # 基于响应数量和质量评估
        response_count = len(state.user_responses)
        avg_response_length = sum(len(r) for r in state.user_responses) / response_count
        
        # 响应数量分数
        count_score = min(response_count / 5, 1.0)  # 最多5个响应得满分
        
        # 响应长度分数
        length_score = min(avg_response_length / 100, 1.0)  # 100字符得满分
        
        # 响应质量分数
        quality_score = 0.5
        if hasattr(state, 'response_analyses') and state.response_analyses:
            quality_scores = []
            for analysis in state.response_analyses:
                quality = analysis.get("quality", "medium")
                if quality == "high":
                    quality_scores.append(1.0)
                elif quality == "medium":
                    quality_scores.append(0.6)
                else:
                    quality_scores.append(0.3)
            quality_score = sum(quality_scores) / len(quality_scores)
        
        return (count_score * 0.3 + length_score * 0.3 + quality_score * 0.4)
    
    def _evaluate_knowledge_coverage(self, state: AgentState) -> float:
        """评估知识覆盖度"""
        coverage_factors = []
        
        # 检索知识的可用性
        if state.retrieved_knowledge:
            results = state.retrieved_knowledge.get("results", [])
            if results:
                avg_relevance = sum(r.get("relevance_score", 0) for r in results) / len(results)
                coverage_factors.append(avg_relevance)
            else:
                coverage_factors.append(0.1)
        else:
            coverage_factors.append(0.0)
        
        # 查询解释的完整性
        if state.interpretation:
            interpretation_completeness = 0.8 if "keywords" in state.interpretation else 0.5
            coverage_factors.append(interpretation_completeness)
        else:
            coverage_factors.append(0.2)
        
        # 执行结果的成功率
        if state.execution_result:
            success_rate = 1.0 if state.execution_result.get("success", False) else 0.3
            coverage_factors.append(success_rate)
        else:
            coverage_factors.append(0.0)
        
        return sum(coverage_factors) / len(coverage_factors) if coverage_factors else 0.0
    
    def _evaluate_response_effectiveness(self, state: AgentState) -> float:
        """评估响应效果"""
        if not state.execution_result:
            return 0.0
        
        effectiveness_factors = []
        
        # 执行成功率
        execution_summary = state.execution_result.get("execution_summary", {})
        success_rate = execution_summary.get("success_rate", 0)
        effectiveness_factors.append(success_rate)
        
        # 行动完成度
        total_actions = execution_summary.get("total_actions", 0)
        successful_actions = execution_summary.get("successful_actions", 0)
        if total_actions > 0:
            completion_rate = successful_actions / total_actions
            effectiveness_factors.append(completion_rate)
        
        # 响应内容质量（基于长度和结构）
        final_response = state.execution_result.get("final_response", "")
        if final_response:
            # 简单的内容质量评估
            content_quality = min(len(final_response) / 500, 1.0)  # 500字符为满分
            effectiveness_factors.append(content_quality)
        else:
            effectiveness_factors.append(0.0)
        
        return sum(effectiveness_factors) / len(effectiveness_factors) if effectiveness_factors else 0.0
    
    def _calculate_learning_value(self, state: AgentState) -> float:
        """计算学习价值"""
        learning_indicators = []
        
        # 苏格拉底式问答的价值
        if state.socratic_questions and state.user_responses:
            question_count = len(state.socratic_questions)
            response_count = len(state.user_responses)
            interaction_ratio = min(response_count / question_count, 1.0) if question_count > 0 else 0
            learning_indicators.append(interaction_ratio)
        
        # 概念探索的深度
        if state.query_type and "explanation" in str(state.query_type).lower():
            learning_indicators.append(0.8)  # 概念解释类查询有较高学习价值
        
        # 知识连接的建立
        if state.retrieved_knowledge:
            sources = state.retrieved_knowledge.get("successful_sources", [])
            if len(sources) > 1:
                learning_indicators.append(0.7)  # 多源知识连接
        
        # 用户思考的深度
        if hasattr(state, 'response_analyses'):
            deep_thinking_count = sum(
                1 for analysis in state.response_analyses
                if len(analysis.get("insights", [])) > 0
            )
            if deep_thinking_count > 0:
                learning_indicators.append(0.6)
        
        return sum(learning_indicators) / len(learning_indicators) if learning_indicators else 0.3
    
    def _identify_improvement_areas(self, analysis: Dict[str, Any]) -> List[str]:
        """识别改进领域"""
        improvements = []
        
        if analysis["engagement_level"] < 0.5:
            improvements.append("提高用户参与度")
        
        if analysis["knowledge_coverage"] < 0.6:
            improvements.append("增强知识覆盖度")
        
        if analysis["response_effectiveness"] < 0.7:
            improvements.append("优化响应效果")
        
        if analysis["learning_value"] < 0.5:
            improvements.append("增加学习价值")
        
        return improvements
    
    def _extract_learning_insights(self, state: AgentState, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取学习洞察
        
        从用户响应和知识检索结果中提取有价值的学习洞察，
        包括质量评估、情感分析和主题分类
        
        Args:
            state: 智能体状态
            analysis: 分析结果
            
        Returns:
            List[Dict[str, Any]]: 洞察列表
        """
        insights = []
        
        # 从用户响应中提取洞察
        if state.user_responses:
            for i, response in enumerate(state.user_responses):
                # 评估响应质量
                quality_score = self._evaluate_response_quality(response)
                
                # 提取关键词和主题
                keywords = self._extract_keywords(response)
                topic = self._classify_topic(response, state.user_query)
                
                # 情感分析
                sentiment = self._analyze_sentiment(response)
                
                insight = {
                    "type": "user_insight",
                    "content": response,
                    "source": f"user_response_{i+1}",
                    "timestamp": datetime.now().isoformat(),
                    "quality_score": quality_score,
                    "quality_level": self._get_quality_level(quality_score),
                    "keywords": keywords,
                    "topic": topic,
                    "sentiment": sentiment,
                    "length": len(response),
                    "complexity": self._assess_complexity(response)
                }
                insights.append(insight)
        
        # 从知识检索结果中提取洞察
        if state.retrieved_knowledge and state.retrieved_knowledge.get("results"):
            for i, result in enumerate(state.retrieved_knowledge["results"]):
                relevance_score = result.get("relevance_score", 0)
                
                # 提高相关性阈值并增加更多筛选条件
                if relevance_score > 0.6:  # 降低阈值以获取更多洞察
                    content = result.get("content", "")
                    
                    # 评估知识质量
                    knowledge_quality = self._evaluate_knowledge_quality(content, relevance_score)
                    
                    # 提取核心概念
                    core_concepts = self._extract_core_concepts(content)
                    
                    insight = {
                        "type": "knowledge_insight",
                        "content": content,
                        "source": result.get("source", "unknown"),
                        "relevance_score": relevance_score,
                        "knowledge_quality": knowledge_quality,
                        "core_concepts": core_concepts,
                        "content_length": len(content),
                        "timestamp": datetime.now().isoformat(),
                        "priority": self._calculate_insight_priority(relevance_score, knowledge_quality)
                    }
                    insights.append(insight)
        
        # 从苏格拉底问答中提取洞察
        if state.socratic_questions:
            for i, question in enumerate(state.socratic_questions):
                insight = {
                    "type": "socratic_insight",
                    "content": question,
                    "source": f"socratic_question_{i+1}",
                    "timestamp": datetime.now().isoformat(),
                    "question_type": self._classify_question_type(question),
                    "cognitive_level": self._assess_cognitive_level(question)
                }
                insights.append(insight)
        
        # 按优先级排序洞察
        insights.sort(key=lambda x: x.get("priority", 0.5), reverse=True)
        
        return insights
    
    def _evaluate_response_quality(self, response: str) -> float:
        """评估用户响应质量
        
        Args:
            response: 用户响应文本
            
        Returns:
            float: 质量分数 (0-1)
        """
        if not response or len(response.strip()) < 5:
            return 0.1
        
        score = 0.5  # 基础分数
        
        # 长度评估
        length = len(response)
        if 20 <= length <= 200:
            score += 0.2
        elif length > 200:
            score += 0.1
        
        # 内容复杂度评估
        if any(char in response for char in '？?！!。.'):
            score += 0.1  # 有标点符号
        
        # 关键词密度
        words = response.split()
        if len(words) >= 3:
            score += 0.1
        
        # 是否包含疑问或思考
        thinking_indicators = ['为什么', '怎么', '如何', '什么', '哪里', '谁', '何时']
        if any(indicator in response for indicator in thinking_indicators):
            score += 0.1
        
        return min(score, 1.0)
    
    def _get_quality_level(self, score: float) -> str:
        """根据分数获取质量等级"""
        if score >= 0.8:
            return "high"
        elif score >= 0.6:
            return "medium"
        elif score >= 0.4:
            return "low"
        else:
            return "very_low"
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        # 简单的关键词提取（可以后续用更复杂的NLP方法）
        import re
        
        # 移除标点符号并分词
        words = re.findall(r'\b\w+\b', text.lower())
        
        # 过滤停用词
        stop_words = {'的', '了', '在', '是', '我', '你', '他', '她', '它', '们', '这', '那', '有', '和', '与', '或', '但', '因为', '所以'}
        keywords = [word for word in words if word not in stop_words and len(word) > 1]
        
        # 返回前5个关键词
        return keywords[:5]
    
    def _classify_topic(self, response: str, query: str) -> str:
        """分类主题"""
        # 基于关键词的简单主题分类
        topics = {
            '历史': ['历史', '朝代', '皇帝', '战争', '古代', '三国', '汉朝', '唐朝'],
            '科学': ['科学', '实验', '理论', '公式', '数学', '物理', '化学'],
            '文学': ['文学', '小说', '诗歌', '作家', '文章', '故事'],
            '哲学': ['哲学', '思想', '理论', '观点', '思考', '意义'],
            '技术': ['技术', '编程', '代码', '算法', '软件', '计算机']
        }
        
        text = (response + ' ' + query).lower()
        
        for topic, keywords in topics.items():
            if any(keyword in text for keyword in keywords):
                return topic
        
        return '通用'
    
    def _analyze_sentiment(self, text: str) -> str:
        """分析情感倾向"""
        positive_words = ['好', '棒', '优秀', '喜欢', '满意', '高兴', '开心', '有趣']
        negative_words = ['不好', '差', '糟糕', '讨厌', '不满', '难过', '困难', '复杂']
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
    
    def _assess_complexity(self, text: str) -> str:
        """评估文本复杂度"""
        length = len(text)
        word_count = len(text.split())
        
        if length > 100 and word_count > 20:
            return 'high'
        elif length > 50 and word_count > 10:
            return 'medium'
        else:
            return 'low'
    
    def _evaluate_knowledge_quality(self, content: str, relevance_score: float) -> float:
        """评估知识质量"""
        base_score = relevance_score
        
        # 内容长度评估
        if 50 <= len(content) <= 500:
            base_score += 0.1
        
        # 结构化程度评估
        if any(marker in content for marker in ['1.', '2.', '•', '-', '：']):
            base_score += 0.1
        
        return min(base_score, 1.0)
    
    def _extract_core_concepts(self, content: str) -> List[str]:
        """提取核心概念"""
        # 简单的概念提取
        import re
        
        # 查找可能的概念（大写开头的词组或专有名词）
        concepts = re.findall(r'[A-Z][a-z]+|[\u4e00-\u9fff]{2,}', content)
        
        # 去重并限制数量
        unique_concepts = list(set(concepts))[:3]
        
        return unique_concepts
    
    def _calculate_insight_priority(self, relevance_score: float, knowledge_quality: float) -> float:
        """计算洞察优先级"""
        return (relevance_score * 0.6 + knowledge_quality * 0.4)
    
    def _classify_question_type(self, question: str) -> str:
        """分类问题类型"""
        if any(word in question for word in ['为什么', '原因', '因为']):
            return 'causal'
        elif any(word in question for word in ['如何', '怎么', '方法']):
            return 'procedural'
        elif any(word in question for word in ['什么', '哪个', '定义']):
            return 'definitional'
        elif any(word in question for word in ['比较', '区别', '不同']):
            return 'comparative'
        else:
            return 'general'
    
    def _assess_cognitive_level(self, question: str) -> str:
        """评估认知水平"""
        high_level_indicators = ['分析', '评估', '创造', '综合', '批判']
        medium_level_indicators = ['应用', '解释', '比较', '分类']
        
        if any(indicator in question for indicator in high_level_indicators):
            return 'high'
        elif any(indicator in question for indicator in medium_level_indicators):
            return 'medium'
        else:
            return 'basic'
    
    def _identify_knowledge_gaps(self, state: AgentState, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """识别知识缺口
        
        通过多维度分析识别用户的学习缺口和系统改进点
        
        Args:
            state: 智能体状态
            analysis: 分析结果
            
        Returns:
            List[Dict[str, Any]]: 知识缺口列表
        """
        gaps = []
        
        # 1. 基于用户响应质量识别缺口
        if state.user_responses:
            avg_quality = self._calculate_average_response_quality(state.user_responses)
            
            if avg_quality < 0.4:
                gaps.append({
                    "type": "low_engagement",
                    "description": "用户参与度严重不足",
                    "severity": "high",
                    "evidence": f"平均响应质量: {avg_quality:.2f}",
                    "suggestions": [
                        "简化问题复杂度",
                        "提供更多引导性提示",
                        "使用更生动的例子",
                        "增加互动元素"
                    ],
                    "priority": 0.9
                })
            elif avg_quality < 0.6:
                gaps.append({
                    "type": "moderate_engagement",
                    "description": "用户参与度有待提升",
                    "severity": "medium",
                    "evidence": f"平均响应质量: {avg_quality:.2f}",
                    "suggestions": [
                        "提供更多互动性内容",
                        "使用更吸引人的问题",
                        "增加实际应用场景"
                    ],
                    "priority": 0.6
                })
        
        # 2. 基于知识检索结果识别缺口
        if state.retrieved_knowledge:
            results = state.retrieved_knowledge.get("results", [])
            knowledge_coverage = len(results)
            avg_relevance = self._calculate_average_relevance(results)
            
            if knowledge_coverage < 2:
                gaps.append({
                    "type": "insufficient_knowledge",
                    "description": "知识库内容严重不足",
                    "severity": "critical",
                    "evidence": f"检索到的相关内容数量: {knowledge_coverage}",
                    "suggestions": [
                        "扩展知识库内容",
                        "增加相关主题资料",
                        "改进知识检索算法",
                        "添加外部知识源"
                    ],
                    "priority": 1.0
                })
            elif avg_relevance < 0.7:
                gaps.append({
                    "type": "low_relevance",
                    "description": "检索内容相关性不足",
                    "severity": "medium",
                    "evidence": f"平均相关性分数: {avg_relevance:.2f}",
                    "suggestions": [
                        "优化检索算法",
                        "改进关键词提取",
                        "增加语义理解能力"
                    ],
                    "priority": 0.7
                })
        
        # 3. 基于苏格拉底问答识别缺口
        if state.socratic_questions:
            question_quality = self._evaluate_socratic_quality(state.socratic_questions)
            if question_quality < 0.6:
                gaps.append({
                    "type": "poor_questioning",
                    "description": "苏格拉底式问答质量不佳",
                    "severity": "medium",
                    "evidence": f"问题质量分数: {question_quality:.2f}",
                    "suggestions": [
                        "改进问题生成算法",
                        "增加问题多样性",
                        "提高问题的启发性",
                        "根据用户水平调整问题难度"
                    ],
                    "priority": 0.5
                })
        
        # 4. 基于查询类型和复杂度识别缺口
        query_complexity = self._assess_query_complexity(state.user_query)
        if query_complexity == 'high' and len(gaps) > 0:
            gaps.append({
                "type": "complex_query_handling",
                "description": "复杂查询处理能力不足",
                "severity": "medium",
                "evidence": f"查询复杂度: {query_complexity}",
                "suggestions": [
                    "分解复杂问题为子问题",
                    "提供分步骤解答",
                    "增加背景知识介绍",
                    "使用多种解释方式"
                ],
                "priority": 0.6
            })
        
        # 5. 基于学习路径连贯性识别缺口
        if hasattr(state, 'learning_path') and state.learning_path:
            path_coherence = self._evaluate_path_coherence(state.learning_path)
            if path_coherence < 0.7:
                gaps.append({
                    "type": "incoherent_learning_path",
                    "description": "学习路径缺乏连贯性",
                    "severity": "medium",
                    "evidence": f"路径连贯性分数: {path_coherence:.2f}",
                    "suggestions": [
                        "改进学习路径规划",
                        "增加知识点之间的关联",
                        "提供更清晰的学习顺序",
                        "添加前置知识检查"
                    ],
                    "priority": 0.6
                })
        
        # 按优先级排序
        gaps.sort(key=lambda x: x.get('priority', 0.5), reverse=True)
        
        return gaps
    
    def _generate_learning_feedback(self, state: AgentState, analysis: Dict[str, Any], 
                                  insights: List[Dict[str, Any]], gaps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成个性化学习反馈
        
        基于分析结果、洞察和缺口生成全面的学习反馈
        
        Args:
            state: 智能体状态
            analysis: 交互分析结果
            insights: 学习洞察列表
            gaps: 知识缺口列表
            
        Returns:
            Dict[str, Any]: 详细的学习反馈
        """
        feedback = {
            "overall_score": analysis["quality_score"],
            "strengths": [],
            "areas_for_improvement": [],
            "recommendations": [],
            "next_steps": [],
            "personalized_insights": {},
            "learning_metrics": {},
            "improvement_suggestions": []
        }
        
        # 1. 详细分析优势
        self._analyze_detailed_strengths(analysis, insights, feedback)
        
        # 2. 识别改进领域
        self._identify_improvement_areas_detailed(analysis, gaps, feedback)
        
        # 3. 生成个性化建议
        self._generate_detailed_recommendations(state, analysis, gaps, feedback)
        
        # 4. 制定具体的下一步计划
        self._create_detailed_next_steps(state, analysis, insights, gaps, feedback)
        
        # 5. 生成个性化洞察
        self._generate_personalized_insights(state, insights, feedback)
        
        # 6. 计算学习指标
        self._calculate_learning_metrics(analysis, insights, gaps, feedback)
        
        return feedback
    
    def _analyze_detailed_strengths(self, analysis: Dict[str, Any], insights: List[Dict[str, Any]], 
                                   feedback: Dict[str, Any]):
        """详细分析学习优势"""
        # 基于分析结果识别优势
        if analysis["engagement_level"] > 0.8:
            feedback["strengths"].append({
                "area": "高度参与",
                "description": "展现出卓越的学习参与度和积极性",
                "score": analysis["engagement_level"],
                "evidence": "在交互过程中保持高度关注和响应"
            })
        elif analysis["engagement_level"] > 0.6:
            feedback["strengths"].append({
                "area": "良好参与",
                "description": "保持良好的学习参与度",
                "score": analysis["engagement_level"],
                "evidence": "积极参与学习过程"
            })
        
        if analysis["learning_value"] > 0.7:
            feedback["strengths"].append({
                "area": "高学习价值",
                "description": "学习交互产生了显著的教育价值",
                "score": analysis["learning_value"],
                "evidence": "知识获取和理解程度较高"
            })
        
        if analysis.get("coherence_score", 0) > 0.7:
            feedback["strengths"].append({
                "area": "思维连贯性",
                "description": "展现出良好的逻辑思维和问题解决能力",
                "score": analysis["coherence_score"],
                "evidence": "回答和问题之间保持良好的连贯性"
            })
        
        # 基于洞察识别优势
        user_insights = [i for i in insights if i.get("type") == "user_insight"]
        if user_insights:
            high_quality_count = len([i for i in user_insights if i.get("quality_score", 0) >= 0.7])
            if high_quality_count > 0:
                feedback["strengths"].append({
                    "area": "回应质量",
                    "description": f"提供了 {high_quality_count} 个高质量的回应",
                    "score": high_quality_count / len(user_insights),
                    "evidence": "回应内容丰富且有深度"
                })
    
    def _identify_improvement_areas_detailed(self, analysis: Dict[str, Any], gaps: List[Dict[str, Any]], 
                                           feedback: Dict[str, Any]):
        """识别具体的改进领域（详细版本）"""
        # 基于分析结果识别改进点
        if analysis["engagement_level"] < 0.5:
            feedback["areas_for_improvement"].append({
                "area": "参与度提升",
                "current_score": analysis["engagement_level"],
                "target_score": 0.7,
                "priority": "high",
                "description": "需要提高学习参与的积极性和深度"
            })
        
        if analysis["knowledge_coverage"] < 0.6:
            feedback["areas_for_improvement"].append({
                "area": "知识覆盖",
                "current_score": analysis["knowledge_coverage"],
                "target_score": 0.8,
                "priority": "medium",
                "description": "需要扩展相关知识的覆盖范围"
            })
        
        if analysis["response_effectiveness"] < 0.6:
            feedback["areas_for_improvement"].append({
                "area": "回应效果",
                "current_score": analysis["response_effectiveness"],
                "target_score": 0.8,
                "priority": "medium",
                "description": "需要提高回应的针对性和有效性"
            })
        
        # 基于缺口识别改进点
        for gap in gaps[:3]:  # 只处理前3个最重要的缺口
            feedback["areas_for_improvement"].append({
                "area": gap["type"],
                "description": gap["description"],
                "priority": gap.get("severity", "medium"),
                "evidence": gap.get("evidence", "")
            })
    
    def _generate_detailed_recommendations(self, state: AgentState, analysis: Dict[str, Any], 
                                         gaps: List[Dict[str, Any]], feedback: Dict[str, Any]):
        """生成详细的改进建议"""
        # 基于缺口生成具体建议
        for gap in gaps:
            if "suggestions" in gap:
                for suggestion in gap["suggestions"]:
                    feedback["recommendations"].append({
                        "suggestion": suggestion,
                        "category": gap["type"],
                        "priority": gap.get("priority", 0.5),
                        "implementation": self._get_implementation_guide(suggestion)
                    })
        
        # 基于分析结果生成系统性建议
        if analysis["quality_score"] < 0.6:
            feedback["improvement_suggestions"].append({
                "type": "systematic",
                "suggestion": "重新设计整体交互策略",
                "details": [
                    "分析当前交互模式的不足",
                    "设计更符合用户需求的交互方式",
                    "增加个性化元素",
                    "提高内容的相关性和吸引力"
                ],
                "timeline": "短期（1-2周）"
            })
    
    def _create_detailed_next_steps(self, state: AgentState, analysis: Dict[str, Any], 
                                   insights: List[Dict[str, Any]], gaps: List[Dict[str, Any]], 
                                   feedback: Dict[str, Any]):
        """制定详细的下一步计划"""
        # 立即行动项
        immediate_actions = []
        
        # 基于严重缺口制定立即行动
        critical_gaps = [g for g in gaps if g.get("severity") == "critical"]
        if critical_gaps:
            immediate_actions.append({
                "action": "解决关键缺口",
                "description": f"优先处理 {len(critical_gaps)} 个关键问题",
                "timeline": "立即",
                "priority": "critical"
            })
        
        # 短期目标（1-2周）
        short_term_goals = []
        if analysis["quality_score"] < 0.7:
            short_term_goals.append({
                "goal": "提升交互质量",
                "target": "将质量分数提升至0.7以上",
                "actions": [
                    "优化问答策略",
                    "增强内容相关性",
                    "改进用户体验"
                ],
                "timeline": "1-2周"
            })
        
        # 中期目标（1个月）
        medium_term_goals = []
        if len(insights) >= 3:
            medium_term_goals.append({
                "goal": "深化学习内容",
                "target": "建立完整的知识体系",
                "actions": [
                    "整合已学知识点",
                    "建立知识关联",
                    "实践应用所学内容"
                ],
                "timeline": "1个月"
            })
        
        feedback["next_steps"] = {
            "immediate": immediate_actions,
            "short_term": short_term_goals,
            "medium_term": medium_term_goals
        }
    
    def _generate_personalized_insights(self, state: AgentState, insights: List[Dict[str, Any]], 
                                       feedback: Dict[str, Any]):
        """生成个性化洞察"""
        user_insights = [i for i in insights if i.get("type") == "user_insight"]
        
        if user_insights:
            # 学习偏好分析
            topics = [i.get("topic") for i in user_insights if i.get("topic")]
            preferred_topic = max(set(topics), key=topics.count) if topics else "通用"
            
            # 交流风格分析
            avg_length = sum(i.get("length", 0) for i in user_insights) / len(user_insights)
            communication_style = "详细" if avg_length > 50 else "简洁"
            
            # 复杂度偏好
            complexities = [i.get("complexity", "low") for i in user_insights]
            preferred_complexity = max(set(complexities), key=complexities.count)
            
            feedback["personalized_insights"] = {
                "learning_preferences": {
                    "preferred_topic": preferred_topic,
                    "communication_style": communication_style,
                    "complexity_preference": preferred_complexity
                },
                "engagement_pattern": self._analyze_engagement_pattern(user_insights),
                "learning_style_recommendations": self._get_learning_style_recommendations(
                    preferred_topic, communication_style, preferred_complexity
                )
            }
    
    def _calculate_learning_metrics(self, analysis: Dict[str, Any], insights: List[Dict[str, Any]], 
                                   gaps: List[Dict[str, Any]], feedback: Dict[str, Any]):
        """计算详细的学习指标"""
        feedback["learning_metrics"] = {
            "overall_progress": analysis["quality_score"],
            "engagement_trend": self._calculate_engagement_trend(insights),
            "knowledge_acquisition_rate": self._calculate_knowledge_rate(insights),
            "improvement_potential": self._calculate_detailed_improvement_potential(gaps, insights),
            "learning_efficiency": self._calculate_learning_efficiency(analysis, insights)
        }
    
    def _get_implementation_guide(self, suggestion: str) -> str:
        """获取建议的实施指南"""
        guides = {
            "简化问题复杂度": "将复杂问题分解为更小的、易于理解的部分",
            "提供更多引导性提示": "在问题中加入更多背景信息和提示",
            "增加互动元素": "使用更多开放性问题和实际案例",
            "扩展知识库内容": "收集更多相关领域的高质量资料",
            "优化检索算法": "改进关键词匹配和语义理解能力"
        }
        return guides.get(suggestion, "请根据具体情况制定实施计划")
    
    def _analyze_engagement_pattern(self, user_insights: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析参与模式"""
        if not user_insights:
            return {"pattern": "未知", "consistency": 0.0}
        
        quality_scores = [i.get("quality_score", 0) for i in user_insights]
        avg_quality = sum(quality_scores) / len(quality_scores)
        consistency = 1.0 - (max(quality_scores) - min(quality_scores)) if quality_scores else 0.0
        
        pattern = "高度参与" if avg_quality >= 0.8 else \
                 "积极参与" if avg_quality >= 0.6 else \
                 "适度参与" if avg_quality >= 0.4 else "被动参与"
        
        return {
            "pattern": pattern,
            "consistency": consistency,
            "average_quality": avg_quality
        }
    
    def _get_learning_style_recommendations(self, topic: str, style: str, complexity: str) -> List[str]:
        """获取学习风格建议"""
        recommendations = []
        
        if style == "详细":
            recommendations.append("继续保持详细的表达方式，有助于深入理解")
        else:
            recommendations.append("可以尝试提供更多细节，有助于更好的个性化指导")
        
        if complexity == "high":
            recommendations.append("您善于处理复杂概念，可以挑战更高难度的内容")
        elif complexity == "low":
            recommendations.append("建议从基础概念开始，逐步提高难度")
        
        return recommendations
    
    def _calculate_engagement_trend(self, insights: List[Dict[str, Any]]) -> str:
        """计算参与度趋势"""
        user_insights = [i for i in insights if i.get("type") == "user_insight"]
        if len(user_insights) < 2:
            return "数据不足"
        
        # 简单的趋势分析
        first_half = user_insights[:len(user_insights)//2]
        second_half = user_insights[len(user_insights)//2:]
        
        first_avg = sum(i.get("quality_score", 0) for i in first_half) / len(first_half)
        second_avg = sum(i.get("quality_score", 0) for i in second_half) / len(second_half)
        
        if second_avg > first_avg + 0.1:
            return "上升"
        elif second_avg < first_avg - 0.1:
            return "下降"
        else:
            return "稳定"
    
    def _calculate_knowledge_rate(self, insights: List[Dict[str, Any]]) -> float:
        """计算知识获取率"""
        knowledge_insights = [i for i in insights if i.get("type") == "knowledge_insight"]
        if not knowledge_insights:
            return 0.0
        
        avg_relevance = sum(i.get("relevance_score", 0) for i in knowledge_insights) / len(knowledge_insights)
        return avg_relevance
    
    def _calculate_detailed_improvement_potential(self, gaps: List[Dict[str, Any]], 
                                                insights: List[Dict[str, Any]]) -> float:
        """计算详细的改进潜力"""
        if not gaps:
            return 0.9
        
        # 基于缺口严重程度
        severity_weights = {"low": 0.2, "medium": 0.5, "high": 0.8, "critical": 1.0}
        avg_severity = sum(severity_weights.get(g.get("severity", "medium"), 0.5) for g in gaps) / len(gaps)
        
        # 基于洞察质量
        user_insights = [i for i in insights if i.get("type") == "user_insight"]
        insight_quality = 0.5
        if user_insights:
            insight_quality = sum(i.get("quality_score", 0) for i in user_insights) / len(user_insights)
        
        # 改进潜力计算
        potential = (1.0 - avg_severity * 0.6) * (0.4 + insight_quality * 0.6)
        return min(max(potential, 0.1), 1.0)
    
    def _calculate_learning_efficiency(self, analysis: Dict[str, Any], 
                                     insights: List[Dict[str, Any]]) -> float:
        """计算学习效率"""
        # 基于质量分数和洞察数量
        quality_score = analysis["quality_score"]
        insight_count = len(insights)
        
        # 效率 = 质量 × 洞察密度
        efficiency = quality_score * min(insight_count / 5.0, 1.0)  # 假设5个洞察为满分
        return min(efficiency, 1.0)
    
    def _calculate_average_response_quality(self, responses: List[str]) -> float:
        """计算平均响应质量"""
        if not responses:
            return 0.0
        
        total_quality = sum(self._evaluate_response_quality(response) for response in responses)
        return total_quality / len(responses)
    
    def _calculate_average_relevance(self, results: List[Dict[str, Any]]) -> float:
        """计算平均相关性分数"""
        if not results:
            return 0.0
        
        total_relevance = sum(result.get('relevance_score', 0) for result in results)
        return total_relevance / len(results)
    
    def _evaluate_socratic_quality(self, questions: List[str]) -> float:
        """评估苏格拉底问题质量"""
        if not questions:
            return 0.0
        
        quality_scores = []
        for question in questions:
            score = 0.5  # 基础分数
            
            # 问题长度评估
            if 10 <= len(question) <= 100:
                score += 0.2
            
            # 问题类型评估
            if any(word in question for word in ['为什么', '如何', '什么', '怎样']):
                score += 0.2
            
            # 启发性评估
            if any(word in question for word in ['思考', '认为', '觉得', '分析']):
                score += 0.1
            
            quality_scores.append(min(score, 1.0))
        
        return sum(quality_scores) / len(quality_scores)
    
    def _assess_query_complexity(self, query: str) -> str:
        """评估查询复杂度"""
        if not query:
            return 'low'
        
        # 基于长度和关键词判断复杂度
        length = len(query)
        word_count = len(query.split())
        
        complex_indicators = ['分析', '比较', '评估', '综合', '创造', '设计', '解决']
        has_complex_words = any(word in query for word in complex_indicators)
        
        if length > 100 or word_count > 20 or has_complex_words:
            return 'high'
        elif length > 50 or word_count > 10:
            return 'medium'
        else:
            return 'low'
    
    def _evaluate_path_coherence(self, learning_path: Dict[str, Any]) -> float:
        """评估学习路径连贯性"""
        if not learning_path:
            return 0.0
        
        coherence_score = 0.5  # 基础分数
        
        # 检查是否有明确的步骤
        if 'next_steps' in learning_path and learning_path['next_steps']:
            coherence_score += 0.2
        
        # 检查是否有资源推荐
        if 'recommended_resources' in learning_path and learning_path['recommended_resources']:
            coherence_score += 0.2
        
        # 检查是否有难度递进
        if 'difficulty_progression' in learning_path:
            coherence_score += 0.1
        
        return min(coherence_score, 1.0)
    
    def _update_learning_patterns(self, state: AgentState, analysis: Dict[str, Any]):
        """更新学习模式"""
        pattern_key = f"{state.query_type}_{analysis['quality_score']:.1f}"
        
        if pattern_key not in self.learning_patterns:
            self.learning_patterns[pattern_key] = {
                "count": 0,
                "avg_quality": 0.0,
                "common_gaps": [],
                "successful_strategies": []
            }
        
        pattern = self.learning_patterns[pattern_key]
        pattern["count"] += 1
        pattern["avg_quality"] = (
            (pattern["avg_quality"] * (pattern["count"] - 1) + analysis["quality_score"]) / 
            pattern["count"]
        )
    
    def _save_learning_data(self, state: AgentState, data: Dict[str, Any]):
        """保存学习数据"""
        try:
            filename = f"learning_{state.session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = self.learning_data_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            self.logger.info(f"Learning data saved to {filepath}")
            
        except Exception as e:
            self.logger.error(f"Failed to save learning data: {e}")
    
    # 增强学习分析方法
    def _analyze_enhanced_interaction(self, state: AgentState) -> Dict[str, Any]:
        """增强交互质量分析"""
        # 基础分析
        analysis = self._analyze_interaction(state)
        
        # 增强分析：苏格拉底问答连贯性
        coherence_score = self._evaluate_socratic_coherence(state)
        analysis["coherence_score"] = coherence_score
        
        # 增强分析：决策代理质量
        decision_quality = self._evaluate_decision_quality(state)
        analysis["decision_quality"] = decision_quality
        
        # 增强分析：个性化程度
        personalization_score = self._evaluate_personalization(state)
        analysis["personalization_score"] = personalization_score
        
        # 重新计算综合质量分数（包含增强因子）
        analysis["quality_score"] = (
            analysis["engagement_level"] * 0.2 +
            analysis["knowledge_coverage"] * 0.2 +
            analysis["response_effectiveness"] * 0.2 +
            analysis["learning_value"] * 0.2 +
            coherence_score * self.coherence_weight * 0.1 +
            decision_quality * self.decision_weight * 0.1
        )
        
        return analysis
    
    def _evaluate_socratic_coherence(self, state: AgentState) -> float:
        """评估苏格拉底问答连贯性"""
        if not state.socratic_questions or not state.user_responses:
            return 0.0
        
        # 简化的连贯性评估
        question_count = len(state.socratic_questions)
        response_count = len(state.user_responses)
        
        # 响应覆盖率
        coverage_ratio = min(response_count / question_count, 1.0) if question_count > 0 else 0
        
        # 响应质量（基于长度和内容）
        if state.user_responses:
            avg_response_quality = sum(
                min(len(response) / 50, 1.0) for response in state.user_responses
            ) / len(state.user_responses)
        else:
            avg_response_quality = 0.0
        
        return (coverage_ratio * 0.6 + avg_response_quality * 0.4)
    
    def _evaluate_decision_quality(self, state: AgentState) -> float:
        """评估决策代理质量"""
        if not hasattr(state, 'decision_analysis') or not state.decision_analysis:
            return 0.5  # 默认中等质量
        
        decision_analysis = state.decision_analysis
        
        # 决策准确性
        accuracy = decision_analysis.get("accuracy", 0.5)
        
        # 决策置信度
        confidence = decision_analysis.get("confidence", 0.5)
        
        # 决策完整性
        completeness = 1.0 if decision_analysis.get("reasoning") else 0.5
        
        return (accuracy * 0.4 + confidence * 0.3 + completeness * 0.3)
    
    def _evaluate_personalization(self, state: AgentState) -> float:
        """评估个性化程度"""
        personalization_factors = []
        
        # 用户档案利用
        user_id = getattr(state, 'user_id', None)
        if user_id and user_id in self.user_profiles:
            personalization_factors.append(0.8)
        else:
            personalization_factors.append(0.2)
        
        # 学习历史考虑
        if hasattr(state, 'learning_history') and state.learning_history:
            personalization_factors.append(0.7)
        else:
            personalization_factors.append(0.3)
        
        # 适应性调整
        if hasattr(state, 'adaptive_adjustments') and state.adaptive_adjustments:
            personalization_factors.append(0.9)
        else:
            personalization_factors.append(0.4)
        
        return sum(personalization_factors) / len(personalization_factors)
    
    def _extract_enhanced_learning_insights(self, state: AgentState, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取增强学习洞察"""
        insights = self._extract_learning_insights(state, analysis)
        
        # 增强洞察：苏格拉底问答模式
        if state.socratic_questions:
            socratic_insight = {
                "type": "socratic_pattern",
                "content": f"苏格拉底问答连贯性: {analysis.get('coherence_score', 0):.2f}",
                "source": "socratic_analysis",
                "timestamp": datetime.now().isoformat(),
                "recommendations": self._get_socratic_recommendations(analysis.get('coherence_score', 0))
            }
            insights.append(socratic_insight)
        
        # 增强洞察：决策质量模式
        if hasattr(state, 'decision_analysis'):
            decision_insight = {
                "type": "decision_pattern",
                "content": f"决策质量评分: {analysis.get('decision_quality', 0):.2f}",
                "source": "decision_analysis",
                "timestamp": datetime.now().isoformat(),
                "recommendations": self._get_decision_recommendations(analysis.get('decision_quality', 0))
            }
            insights.append(decision_insight)
        
        return insights
    
    def _get_socratic_recommendations(self, coherence_score: float) -> List[str]:
        """获取苏格拉底问答改进建议"""
        if coherence_score < 0.4:
            return ["增加引导性问题", "简化问题复杂度", "提供更多背景信息"]
        elif coherence_score < 0.7:
            return ["优化问题序列", "增强问题间的逻辑联系"]
        else:
            return ["保持当前问答策略", "可以适当增加问题深度"]
    
    def _get_decision_recommendations(self, decision_quality: float) -> List[str]:
        """获取决策质量改进建议"""
        if decision_quality < 0.4:
            return ["增强决策逻辑", "提供更多决策依据", "改进决策流程"]
        elif decision_quality < 0.7:
            return ["优化决策准确性", "增强决策置信度"]
        else:
            return ["保持决策质量", "可以处理更复杂的决策场景"]
    
    def _identify_personalized_knowledge_gaps(self, state: AgentState, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """识别个性化知识缺口"""
        gaps = self._identify_knowledge_gaps(state, analysis)
        
        # 基于用户档案的个性化缺口识别
        user_id = getattr(state, 'user_id', None)
        if user_id and user_id in self.user_profiles:
            profile = self.user_profiles[user_id]
            
            # 基于学习偏好识别缺口
            learning_style = profile.get('learning_style', 'visual')
            if learning_style == 'visual' and analysis.get('visual_content_score', 0) < 0.5:
                gaps.append({
                    "type": "visual_content_gap",
                    "description": "缺少视觉化内容",
                    "severity": "medium",
                    "suggested_action": "增加图表、图像等视觉元素",
                    "personalized": True
                })
            
            # 基于知识水平识别缺口
            knowledge_level = profile.get('knowledge_level', 'beginner')
            if knowledge_level == 'beginner' and analysis.get('complexity_score', 0.5) > 0.7:
                gaps.append({
                    "type": "complexity_gap",
                    "description": "内容复杂度过高",
                    "severity": "high",
                    "suggested_action": "简化内容，增加基础概念解释",
                    "personalized": True
                })
        
        return gaps
    
    def _generate_intelligent_learning_feedback(self, state: AgentState, analysis: Dict[str, Any],
                                              insights: List[Dict[str, Any]], gaps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成智能学习反馈"""
        feedback = self._generate_learning_feedback(state, analysis, insights, gaps)
        
        # 增强反馈：个性化建议
        user_id = getattr(state, 'user_id', None)
        if user_id and user_id in self.user_profiles:
            profile = self.user_profiles[user_id]
            feedback["personalized_recommendations"] = self._get_personalized_recommendations(profile, analysis)
        
        # 增强反馈：学习路径建议
        feedback["learning_path_suggestions"] = self._get_learning_path_suggestions(analysis, insights)
        
        # 增强反馈：适应性调整
        feedback["adaptive_adjustments"] = self._get_adaptive_adjustments(analysis)
        
        return feedback
    
    def _get_personalized_recommendations(self, profile: Dict[str, Any], analysis: Dict[str, Any]) -> List[str]:
        """基于个性化程度的推荐"""
        recommendations = []
        
        learning_style = profile.get('learning_style', 'visual')
        if learning_style == 'auditory':
            recommendations.append("增加音频解释和口语化表达")
        elif learning_style == 'kinesthetic':
            recommendations.append("增加实践练习和互动操作")
        
        pace = profile.get('learning_pace', 'medium')
        if pace == 'slow' and analysis.get('content_density', 0.5) > 0.7:
            recommendations.append("减少单次内容量，增加重复和巩固")
        elif pace == 'fast' and analysis.get('content_density', 0.5) < 0.5:
            recommendations.append("增加内容深度和挑战性")
        
        return recommendations
    
    def _get_learning_path_suggestions(self, analysis: Dict[str, Any], insights: List[Dict[str, Any]]) -> List[str]:
        """获取学习路径建议"""
        suggestions = []
        
        if analysis.get('knowledge_coverage', 0) < 0.6:
            suggestions.append("补充基础知识点")
        
        if analysis.get('learning_value', 0) > 0.7:
            suggestions.append("深入探索相关高级主题")
        
        # 基于洞察的路径建议
        for insight in insights:
            if insight.get('type') == 'knowledge_insight' and insight.get('relevance_score', 0) > 0.8:
                suggestions.append(f"深入学习: {insight.get('source', '相关主题')}")
        
        return suggestions
    
    def _get_adaptive_adjustments(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """获取适应性调整建议"""
        adjustments = {
            "difficulty_level": "maintain",
            "interaction_frequency": "maintain",
            "content_type": "maintain"
        }
        
        # 难度调整
        if analysis.get('engagement_level', 0.5) < 0.4:
            adjustments["difficulty_level"] = "decrease"
        elif analysis.get('engagement_level', 0.5) > 0.8 and analysis.get('learning_value', 0.5) > 0.7:
            adjustments["difficulty_level"] = "increase"
        
        # 交互频率调整
        if analysis.get('coherence_score', 0.5) < 0.5:
            adjustments["interaction_frequency"] = "increase"
        
        # 内容类型调整
        if analysis.get('response_effectiveness', 0.5) < 0.5:
            adjustments["content_type"] = "more_visual"
        
        return adjustments
    
    def _update_user_profile(self, state: AgentState, analysis: Dict[str, Any]):
        """更新用户学习档案"""
        user_id = getattr(state, 'user_id', None)
        if not user_id:
            return
        
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = {
                "learning_style": "visual",
                "knowledge_level": "beginner",
                "learning_pace": "medium",
                "interaction_history": [],
                "performance_metrics": {
                    "avg_engagement": 0.0,
                    "avg_learning_value": 0.0,
                    "total_sessions": 0
                }
            }
        
        profile = self.user_profiles[user_id]
        
        # 更新性能指标
        metrics = profile["performance_metrics"]
        total_sessions = metrics["total_sessions"]
        
        metrics["avg_engagement"] = (
            (metrics["avg_engagement"] * total_sessions + analysis.get("engagement_level", 0)) /
            (total_sessions + 1)
        )
        
        metrics["avg_learning_value"] = (
            (metrics["avg_learning_value"] * total_sessions + analysis.get("learning_value", 0)) /
            (total_sessions + 1)
        )
        
        metrics["total_sessions"] += 1
        
        # 记录交互历史
        profile["interaction_history"].append({
            "session_id": state.session_id,
            "timestamp": state.timestamp,
            "quality_score": analysis.get("quality_score", 0),
            "query_type": state.query_type
        })
        
        # 保持历史记录在合理范围内
        if len(profile["interaction_history"]) > 50:
            profile["interaction_history"] = profile["interaction_history"][-50:]
    
    def _recommend_learning_path(self, state: AgentState, analysis: Dict[str, Any], insights: List[Dict[str, Any]]) -> Dict[str, Any]:
        """推荐个性化学习路径"""
        path = {
            "current_level": self._assess_current_level(analysis),
            "next_steps": [],
            "recommended_resources": [],
            "estimated_duration": "1-2 weeks",
            "difficulty_progression": "gradual"
        }
        
        # 基于当前水平推荐下一步
        current_level = path["current_level"]
        if current_level == "beginner":
            path["next_steps"] = ["掌握基础概念", "练习基本应用", "理解核心原理"]
        elif current_level == "intermediate":
            path["next_steps"] = ["深入理解高级概念", "实践复杂应用", "探索相关领域"]
        else:  # advanced
            path["next_steps"] = ["研究前沿发展", "创新应用实践", "知识体系整合"]
        
        # 基于洞察推荐资源
        for insight in insights:
            if insight.get('type') == 'knowledge_insight':
                source = insight.get('source', '')
                if source and source not in path["recommended_resources"]:
                    path["recommended_resources"].append(source)
        
        return path
    
    def _assess_current_level(self, analysis: Dict[str, Any]) -> str:
        """评估当前学习水平"""
        score = analysis.get("quality_score", 0)
        knowledge_coverage = analysis.get("knowledge_coverage", 0)
        
        combined_score = (score + knowledge_coverage) / 2
        
        if combined_score < 0.4:
            return "beginner"
        elif combined_score < 0.7:
            return "intermediate"
        else:
            return "advanced"
    
    def _save_enhanced_learning_data(self, state: AgentState, data: Dict[str, Any]):
        """保存增强学习数据"""
        try:
            filename = f"enhanced_learning_{state.session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = self.enhanced_learning_dir / filename
            
            # 添加元数据
            enhanced_data = {
                "metadata": {
                    "session_id": state.session_id,
                    "timestamp": datetime.now().isoformat(),
                    "user_id": getattr(state, 'user_id', None),
                    "query_type": state.query_type,
                    "enhanced_mode": True
                },
                "analysis_data": data
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(enhanced_data, f, ensure_ascii=False, indent=2)
                
            self.logger.info(f"Enhanced learning data saved to {filepath}")
            
            # 清理旧数据
            self._cleanup_old_learning_data()
            
        except Exception as e:
            self.logger.error(f"Failed to save enhanced learning data: {e}")
    
    def _cleanup_old_learning_data(self):
        """清理旧的增强学习数据"""
        try:
            # 保留最近30天的数据
            cutoff_date = datetime.now().timestamp() - (30 * 24 * 60 * 60)
            
            for data_dir in [self.learning_data_dir, self.enhanced_learning_dir]:
                for file_path in data_dir.glob("*.json"):
                    if file_path.stat().st_mtime < cutoff_date:
                        file_path.unlink()
                        self.logger.info(f"Cleaned up old learning data: {file_path}")
                        
        except Exception as e:
            self.logger.error(f"Failed to cleanup old learning data: {e}")
    
    # 公共接口方法
    def get_learning_statistics(self) -> Dict[str, Any]:
        """获取学习统计信息"""
        total_interactions = len(self.interaction_log)
        if total_interactions == 0:
            return {"message": "No learning data available"}
        
        avg_quality = sum(log.get("quality_score", 0) for log in self.interaction_log) / total_interactions
        avg_learning_value = sum(log.get("learning_value", 0) for log in self.interaction_log) / total_interactions
        
        return {
            "total_interactions": total_interactions,
            "average_quality_score": round(avg_quality, 2),
            "average_learning_value": round(avg_learning_value, 2),
            "learning_patterns_count": len(self.learning_patterns),
            "user_profiles_count": len(self.user_profiles)
        }
    
    def get_knowledge_gap_summary(self) -> Dict[str, Any]:
        """获取知识缺口总结"""
        # 这里可以实现更复杂的缺口分析逻辑
        return {
            "common_gaps": ["概念理解", "实践应用", "知识连接"],
            "improvement_suggestions": ["增加互动性", "提供更多示例", "建立知识关联"]
        }