#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实多智能体系统实验框架
使用实际的智能体系统进行性能测试和对比分析
"""

import time
import json
import asyncio
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import sys
import traceback

# 添加src目录到Python路径
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

try:
    from agents.multi_agent_system import MultiAgentSystem, get_multi_agent_system
    from agents.query_interpreter_integrated import QueryInterpreterAgent
    from agents.decision_agent import DecisionAgent
    from agents.knowledge_retriever import KnowledgeRetrieverAgent
    from agents.executor import ExecutorAgent
    from agents.socratic_guide import SocraticGuideAgent
    from agents.planner import PlannerAgent
    from agents.learner import LearnerAgent
    from agents.user_profile_integrated import UserProfileAgent
    from utils import AgentState
    from utils.enums import QueryType, ConversationStage
except ImportError as e:
    print(f"Warning: Some agent modules not available: {e}")
    print("Please ensure all dependencies are installed and src directory is accessible")

class RealExperimentFramework:
    """真实智能体系统实验框架"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = self._setup_logging()
        
        # 实验配置
        self.experiment_config = {
            "test_queries": self._generate_test_queries(),
            "user_profiles": self._generate_user_profiles(),
            "evaluation_metrics": self._define_metrics(),
            "statistical_tests": ["t_test", "mann_whitney", "effect_size"]
        }
        
        # 初始化系统
        self.systems = self._initialize_systems()
        
        # 结果存储
        self.results = {
            "full_multi_agent": [],
            "core_agents": [],
            "traditional_rag": [],
            "statistics": {}
        }
        
        # 数据收集器
        self.data_collector = ExperimentDataCollector()
    
    def _setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def _generate_test_queries(self) -> List[Dict[str, Any]]:
        """生成测试查询集"""
        return [
            {
                "id": "Q001",
                "query": "什么是机器学习？",
                "type": "concept_definition",
                "complexity": "basic",
                "expected_components": ["definition", "examples", "applications"]
            },
            {
                "id": "Q002", 
                "query": "深度学习与传统机器学习有什么区别？",
                "type": "comparison",
                "complexity": "intermediate",
                "expected_components": ["differences", "similarities", "use_cases"]
            },
            {
                "id": "Q003",
                "query": "如何设计一个神经网络来解决图像分类问题？",
                "type": "problem_solving",
                "complexity": "advanced",
                "expected_components": ["architecture", "training", "evaluation"]
            },
            {
                "id": "Q004",
                "query": "强化学习在游戏AI中的应用原理是什么？",
                "type": "application",
                "complexity": "intermediate",
                "expected_components": ["principles", "algorithms", "examples"]
            },
            {
                "id": "Q005",
                "query": "自然语言处理中的注意力机制是如何工作的？",
                "type": "technical_detail",
                "complexity": "advanced",
                "expected_components": ["mechanism", "mathematics", "implementation"]
            }
        ]
    
    def _generate_user_profiles(self) -> List[Dict[str, Any]]:
        """生成用户画像"""
        return [
            {
                "user_id": "U001",
                "learning_style": "visual",
                "knowledge_level": "beginner",
                "interests": ["AI", "programming"],
                "background": "computer_science_student"
            },
            {
                "user_id": "U002", 
                "learning_style": "auditory",
                "knowledge_level": "intermediate",
                "interests": ["machine_learning", "data_science"],
                "background": "data_scientist"
            },
            {
                "user_id": "U003",
                "learning_style": "kinesthetic",
                "knowledge_level": "advanced",
                "interests": ["deep_learning", "research"],
                "background": "research_scientist"
            }
        ]
    
    def _define_metrics(self) -> Dict[str, Any]:
        """定义评估指标"""
        return {
            "response_quality": {
                "accuracy": {"weight": 0.3, "scale": "1-5"},
                "completeness": {"weight": 0.25, "scale": "1-5"},
                "explanation_quality": {"weight": 0.25, "scale": "1-5"},
                "learning_value": {"weight": 0.2, "scale": "1-5"}
            },
            "system_performance": {
                "response_time": {"weight": 0.4, "scale": "seconds"},
                "throughput": {"weight": 0.3, "scale": "requests/min"},
                "resource_usage": {"weight": 0.3, "scale": "percentage"}
            },
            "user_experience": {
                "satisfaction": {"weight": 0.4, "scale": "1-5"},
                "engagement": {"weight": 0.3, "scale": "1-5"},
                "learning_progress": {"weight": 0.3, "scale": "1-5"}
            }
        }
    
    def _initialize_systems(self) -> Dict[str, Any]:
        """初始化对比系统"""
        try:
            # 完整多智能体系统
            full_system = MultiAgentSystem({
                "max_iterations": 5,
                "timeout_seconds": 300,
                "enable_learning": True,
                "enable_socratic": True,
                "auto_continue": False
            })
            
            # 核心智能体系统（仅核心组件）
            core_system = {
                "query_interpreter": QueryInterpreterAgent(),
                "executor": ExecutorAgent()
            }
            
            # 传统RAG系统（知识检索+生成）
            rag_system = {
                "retriever": KnowledgeRetrieverAgent(),
                "generator": ExecutorAgent()
            }
            
            return {
                "full_multi_agent": full_system,
                "core_agents": core_system,
                "traditional_rag": rag_system
            }
        except Exception as e:
            self.logger.error(f"System initialization failed: {e}")
            return {}
    
    async def run_comparison_experiment(self) -> Dict[str, Any]:
        """运行完整的对比实验"""
        self.logger.info("开始运行真实智能体系统对比实验...")
        
        # 运行各系统测试
        for system_name, system in self.systems.items():
            self.logger.info(f"测试系统: {system_name}")
            system_results = await self._test_system(system, system_name)
            self.results[system_name] = system_results
        
        # 进行统计分析
        self.results["statistics"] = self._perform_statistical_analysis()
        
        # 生成实验报告
        report = self._generate_experiment_report()
        
        # 保存结果
        self._save_results()
        
        return report
    
    async def _test_system(self, system: Any, system_name: str) -> List[Dict[str, Any]]:
        """测试单个系统"""
        results = []
        
        for query in self.experiment_config["test_queries"]:
            for user_profile in self.experiment_config["user_profiles"]:
                try:
                    # 记录开始时间
                    start_time = time.time()
                    
                    # 执行查询
                    if system_name == "full_multi_agent":
                        response = await self._execute_full_system(system, query, user_profile)
                    elif system_name == "core_agents":
                        response = await self._execute_core_system(system, query, user_profile)
                    else:  # traditional_rag
                        response = await self._execute_rag_system(system, query, user_profile)
                    
                    # 记录结束时间
                    end_time = time.time()
                    
                    # 评估响应质量
                    quality_scores = self._evaluate_response_quality(
                        response, query, user_profile
                    )
                    
                    # 记录结果
                    result = {
                        "query_id": query["id"],
                        "user_id": user_profile["user_id"],
                        "system": system_name,
                        "response": response,
                        "response_time": end_time - start_time,
                        "quality_scores": quality_scores,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    results.append(result)
                    
                    self.logger.info(f"  - 查询 {query['id']} + 用户 {user_profile['user_id']}: "
                                   f"质量评分 {quality_scores['accuracy']:.2f}, "
                                   f"响应时间 {end_time - start_time:.2f}s")
                    
                except Exception as e:
                    self.logger.error(f"Error testing {system_name}: {e}")
                    result = {
                        "query_id": query["id"],
                        "user_id": user_profile["user_id"],
                        "system": system_name,
                        "error": str(e),
                        "response_time": 0,
                        "quality_scores": {"accuracy": 0, "completeness": 0, "explanation_quality": 0, "learning_value": 0},
                        "timestamp": datetime.now().isoformat()
                    }
                    results.append(result)
        
        return results
    
    async def _execute_full_system(self, system: MultiAgentSystem, query: Dict, user_profile: Dict) -> str:
        """执行完整多智能体系统"""
        try:
            # 创建初始状态
            initial_state = AgentState(
                query=query["query"],
                context=user_profile,
                metadata={"query_type": query["type"], "complexity": query["complexity"]}
            )
            
            # 执行工作流
            result = await system.process_conversation(initial_state)
            
            if result.get("success"):
                return result.get("response", "No response generated")
            else:
                return f"System error: {result.get('error', 'Unknown error')}"
                
        except Exception as e:
            return f"Error in full system: {str(e)}"
    
    async def _execute_core_system(self, system: Dict, query: Dict, user_profile: Dict) -> str:
        """执行核心智能体系统"""
        try:
            # 查询解释
            interpretation = await system["query_interpreter"].process(
                query["query"], user_profile, {}
            )
            
            # 直接执行
            response = await system["executor"].execute(
                interpretation, user_profile, {}
            )
            
            if hasattr(response, 'execution_result') and response.execution_result:
                return response.execution_result.get("final_response", "No response generated")
            else:
                return "No response generated"
                
        except Exception as e:
            return f"Error in core system: {str(e)}"
    
    async def _execute_rag_system(self, system: Dict, query: Dict, user_profile: Dict) -> str:
        """执行传统RAG系统"""
        try:
            # 知识检索
            retrieved_knowledge = await system["retriever"].retrieve(
                query["query"], user_profile, {}
            )
            
            # 生成响应
            response = await system["generator"].execute(
                retrieved_knowledge, user_profile, {}
            )
            
            if hasattr(response, 'execution_result') and response.execution_result:
                return response.execution_result.get("final_response", "No response generated")
            else:
                return "No response generated"
                
        except Exception as e:
            return f"Error in RAG system: {str(e)}"
    
    def _evaluate_response_quality(self, response: str, query: Dict, user_profile: Dict) -> Dict[str, float]:
        """评估响应质量"""
        # 简化的质量评估（实际应用中可以使用更复杂的评估模型）
        scores = {}
        
        # 准确性评分（基于关键词匹配）
        expected_components = query.get("expected_components", [])
        accuracy_score = self._calculate_accuracy_score(response, expected_components)
        scores["accuracy"] = accuracy_score
        
        # 完整性评分（基于长度和内容覆盖）
        completeness_score = self._calculate_completeness_score(response, expected_components)
        scores["completeness"] = completeness_score
        
        # 解释质量评分（基于结构化程度）
        explanation_score = self._calculate_explanation_score(response)
        scores["explanation_quality"] = explanation_score
        
        # 学习价值评分（基于教育价值）
        learning_value_score = self._calculate_learning_value_score(response, user_profile)
        scores["learning_value"] = learning_value_score
        
        return scores
    
    def _calculate_accuracy_score(self, response: str, expected_components: List[str]) -> float:
        """计算准确性评分"""
        if not response or response.startswith("Error"):
            return 0.0
        
        # 简单的关键词匹配评分
        score = 0.0
        total_components = len(expected_components)
        
        for component in expected_components:
            if component.lower() in response.lower():
                score += 1.0
        
        return min(5.0, (score / total_components) * 5.0)
    
    def _calculate_completeness_score(self, response: str, expected_components: List[str]) -> float:
        """计算完整性评分"""
        if not response or response.startswith("Error"):
            return 0.0
        
        # 基于响应长度和内容覆盖的评分
        length_score = min(5.0, len(response) / 100.0)  # 每100字符1分
        coverage_score = self._calculate_accuracy_score(response, expected_components)
        
        return (length_score + coverage_score) / 2.0
    
    def _calculate_explanation_score(self, response: str) -> float:
        """计算解释质量评分"""
        if not response or response.startswith("Error"):
            return 0.0
        
        # 基于结构化程度的评分
        structure_indicators = [
            "首先", "其次", "最后", "例如", "比如", "因此", "所以",
            "first", "second", "finally", "for example", "therefore"
        ]
        
        structure_score = 0.0
        for indicator in structure_indicators:
            if indicator in response:
                structure_score += 1.0
        
        return min(5.0, structure_score / len(structure_indicators) * 5.0)
    
    def _calculate_learning_value_score(self, response: str, user_profile: Dict) -> float:
        """计算学习价值评分"""
        if not response or response.startswith("Error"):
            return 0.0
        
        # 基于用户画像和学习价值的评分
        knowledge_level = user_profile.get("knowledge_level", "beginner")
        complexity = response.count("因为") + response.count("由于") + response.count("原理")
        
        base_score = 3.0
        if knowledge_level == "beginner":
            base_score += 1.0 if complexity > 2 else 0.5
        elif knowledge_level == "intermediate":
            base_score += 1.5 if complexity > 3 else 1.0
        else:  # advanced
            base_score += 2.0 if complexity > 4 else 1.5
        
        return min(5.0, base_score)
    
    def _perform_statistical_analysis(self) -> Dict[str, Any]:
        """执行统计分析"""
        try:
            # 提取数据
            full_system_data = self.results.get("full_multi_agent", [])
            core_system_data = self.results.get("core_agents", [])
            rag_system_data = self.results.get("traditional_rag", [])
            
            if not full_system_data or not core_system_data or not rag_system_data:
                return {"error": "Insufficient data for analysis"}
            
            # 计算综合评分
            full_scores = self._calculate_composite_scores(full_system_data)
            core_scores = self._calculate_composite_scores(core_system_data)
            rag_scores = self._calculate_composite_scores(rag_system_data)
            
            # 统计分析
            statistics = {
                "descriptive_stats": {
                    "full_multi_agent": self._calculate_descriptive_stats(full_scores),
                    "core_agents": self._calculate_descriptive_stats(core_scores),
                    "traditional_rag": self._calculate_descriptive_stats(rag_scores)
                },
                "comparison_tests": {
                    "full_vs_core": self._compare_systems(full_scores, core_scores),
                    "full_vs_rag": self._compare_systems(full_scores, rag_scores),
                    "core_vs_rag": self._compare_systems(core_scores, rag_scores)
                },
                "effect_sizes": {
                    "full_vs_core": self._calculate_effect_size(full_scores, core_scores),
                    "full_vs_rag": self._calculate_effect_size(full_scores, rag_scores),
                    "core_vs_rag": self._calculate_effect_size(core_scores, rag_scores)
                }
            }
            
            return statistics
            
        except Exception as e:
            self.logger.error(f"Statistical analysis failed: {e}")
            return {"error": str(e)}
    
    def _calculate_composite_scores(self, data: List[Dict]) -> List[float]:
        """计算综合评分"""
        scores = []
        for item in data:
            if "quality_scores" in item and isinstance(item["quality_scores"], dict):
                quality = item["quality_scores"]
                composite_score = (
                    quality.get("accuracy", 0) * 0.3 +
                    quality.get("completeness", 0) * 0.25 +
                    quality.get("explanation_quality", 0) * 0.25 +
                    quality.get("learning_value", 0) * 0.2
                )
                scores.append(composite_score)
        return scores
    
    def _calculate_descriptive_stats(self, scores: List[float]) -> Dict[str, float]:
        """计算描述性统计"""
        if not scores:
            return {"mean": 0, "std": 0, "min": 0, "max": 0, "count": 0}
        
        return {
            "mean": np.mean(scores),
            "std": np.std(scores),
            "min": np.min(scores),
            "max": np.max(scores),
            "count": len(scores)
        }
    
    def _compare_systems(self, scores1: List[float], scores2: List[float]) -> Dict[str, Any]:
        """比较两个系统"""
        try:
            from scipy import stats
            
            # t检验
            t_stat, p_value = stats.ttest_ind(scores1, scores2)
            
            # Mann-Whitney U检验
            u_stat, u_p_value = stats.mannwhitneyu(scores1, scores2, alternative='two-sided')
            
            return {
                "t_test": {"statistic": t_stat, "p_value": p_value, "significant": p_value < 0.05},
                "mann_whitney": {"statistic": u_stat, "p_value": u_p_value, "significant": u_p_value < 0.05}
            }
        except ImportError:
            return {"error": "scipy not available for statistical tests"}
        except Exception as e:
            return {"error": str(e)}
    
    def _calculate_effect_size(self, scores1: List[float], scores2: List[float]) -> Dict[str, float]:
        """计算效应量"""
        try:
            # Cohen's d
            pooled_std = np.sqrt(
                ((len(scores1) - 1) * np.var(scores1, ddof=1) + 
                 (len(scores2) - 1) * np.var(scores2, ddof=1)) / 
                (len(scores1) + len(scores2) - 2)
            )
            
            if pooled_std == 0:
                cohens_d = 0
            else:
                cohens_d = (np.mean(scores1) - np.mean(scores2)) / pooled_std
            
            # 效应量解释
            if abs(cohens_d) < 0.2:
                effect_size = "negligible"
            elif abs(cohens_d) < 0.5:
                effect_size = "small"
            elif abs(cohens_d) < 0.8:
                effect_size = "medium"
            else:
                effect_size = "large"
            
            return {
                "cohens_d": cohens_d,
                "effect_size": effect_size,
                "interpretation": f"{effect_size} effect size"
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _generate_experiment_report(self) -> Dict[str, Any]:
        """生成实验报告"""
        report = {
            "experiment_info": {
                "title": "真实多智能体教育系统对比实验",
                "timestamp": datetime.now().isoformat(),
                "test_queries_count": len(self.experiment_config["test_queries"]),
                "user_profiles_count": len(self.experiment_config["user_profiles"]),
                "systems_tested": list(self.systems.keys())
            },
            "summary": {
                "total_tests": sum(len(results) for results in self.results.values() if isinstance(results, list)),
                "successful_tests": sum(
                    len([r for r in results if "error" not in r]) 
                    for results in self.results.values() if isinstance(results, list)
                ),
                "average_response_time": self._calculate_average_response_time(),
                "overall_quality_score": self._calculate_overall_quality()
            },
            "detailed_results": self.results,
            "recommendations": self._generate_recommendations()
        }
        
        return report
    
    def _calculate_average_response_time(self) -> float:
        """计算平均响应时间"""
        all_times = []
        for system_name, results in self.results.items():
            if isinstance(results, list):
                for result in results:
                    if "response_time" in result and isinstance(result["response_time"], (int, float)):
                        all_times.append(result["response_time"])
        
        return np.mean(all_times) if all_times else 0.0
    
    def _calculate_overall_quality(self) -> float:
        """计算整体质量评分"""
        all_scores = []
        for system_name, results in self.results.items():
            if isinstance(results, list):
                for result in results:
                    if "quality_scores" in result and isinstance(result["quality_scores"], dict):
                        quality = result["quality_scores"]
                        composite_score = (
                            quality.get("accuracy", 0) * 0.3 +
                            quality.get("completeness", 0) * 0.25 +
                            quality.get("explanation_quality", 0) * 0.25 +
                            quality.get("learning_value", 0) * 0.2
                        )
                        all_scores.append(composite_score)
        
        return np.mean(all_scores) if all_scores else 0.0
    
    def _generate_recommendations(self) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # 基于统计结果生成建议
        if "statistics" in self.results and "error" not in self.results["statistics"]:
            stats = self.results["statistics"]
            
            # 检查显著性
            for comparison, result in stats.get("comparison_tests", {}).items():
                if "t_test" in result and result["t_test"]["significant"]:
                    recommendations.append(f"{comparison} 对比显示显著差异，建议进一步分析")
                
                if "mann_whitney" in result and result["mann_whitney"]["significant"]:
                    recommendations.append(f"{comparison} 非参数检验显示显著差异")
        
        # 基于质量评分生成建议
        overall_quality = self._calculate_overall_quality()
        if overall_quality < 3.0:
            recommendations.append("整体质量评分较低，建议优化智能体协作机制")
        elif overall_quality > 4.0:
            recommendations.append("整体质量评分较高，系统表现良好")
        
        # 基于响应时间生成建议
        avg_response_time = self._calculate_average_response_time()
        if avg_response_time > 10.0:
            recommendations.append("响应时间较长，建议优化性能瓶颈")
        
        if not recommendations:
            recommendations.append("系统运行正常，建议进行更多测试以验证稳定性")
        
        return recommendations
    
    def _save_results(self):
        """保存实验结果"""
        try:
            # 创建结果目录
            results_dir = Path(__file__).parent / "results"
            results_dir.mkdir(exist_ok=True)
            
            # 保存详细结果
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # JSON格式
            json_file = results_dir / f"real_experiment_results_{timestamp}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2, default=str)
            
            # CSV格式（用于进一步分析）
            csv_file = results_dir / f"real_experiment_data_{timestamp}.csv"
            self._save_to_csv(csv_file)
            
            self.logger.info(f"Results saved to {results_dir}")
            
        except Exception as e:
            self.logger.error(f"Failed to save results: {e}")
    
    def _save_to_csv(self, csv_file: Path):
        """保存数据到CSV格式"""
        try:
            # 准备CSV数据
            csv_data = []
            for system_name, results in self.results.items():
                if isinstance(results, list):
                    for result in results:
                        row = {
                            "system": system_name,
                            "query_id": result.get("query_id", ""),
                            "user_id": result.get("user_id", ""),
                            "response_time": result.get("response_time", 0),
                            "accuracy": result.get("quality_scores", {}).get("accuracy", 0),
                            "completeness": result.get("quality_scores", {}).get("completeness", 0),
                            "explanation_quality": result.get("quality_scores", {}).get("explanation_quality", 0),
                            "learning_value": result.get("quality_scores", {}).get("learning_value", 0),
                            "timestamp": result.get("timestamp", ""),
                            "error": result.get("error", "")
                        }
                        csv_data.append(row)
            
            # 保存为CSV
            if csv_data:
                df = pd.DataFrame(csv_data)
                df.to_csv(csv_file, index=False, encoding='utf-8')
                
        except Exception as e:
            self.logger.error(f"Failed to save CSV: {e}")


class ExperimentDataCollector:
    """实验数据收集器"""
    
    def __init__(self):
        self.metrics = {}
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def collect_metrics(self, metrics: Dict[str, Any]):
        """收集指标数据"""
        try:
            timestamp = datetime.now().isoformat()
            self.metrics[timestamp] = metrics
        except Exception as e:
            self.logger.error(f"Failed to collect metrics: {e}")
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """获取指标摘要"""
        if not self.metrics:
            return {"error": "No metrics collected"}
        
        summary = {
            "total_metrics": len(self.metrics),
            "time_range": {
                "start": min(self.metrics.keys()),
                "end": max(self.metrics.keys())
            },
            "metrics_types": list(set(
                key for metrics in self.metrics.values() 
                for key in metrics.keys()
            ))
        }
        
        return summary


async def main():
    """主函数"""
    print("🚀 启动真实多智能体系统实验框架...")
    print("="*80)
    
    # 创建实验框架
    framework = RealExperimentFramework()
    
    # 运行实验
    try:
        start_time = time.time()
        results = await framework.run_comparison_experiment()
        end_time = time.time()
        
        print("\n" + "="*80)
        print("🎉 真实智能体系统实验完成！")
        print("="*80)
        print(f"⏱️  总耗时: {end_time - start_time:.2f}秒")
        print(f"📊 总测试数: {results['summary']['total_tests']}")
        print(f"✅ 成功测试数: {results['summary']['successful_tests']}")
        print(f"⚡ 平均响应时间: {results['summary']['average_response_time']:.3f}秒")
        print(f"⭐ 整体质量评分: {results['summary']['overall_quality_score']:.3f}/5.0")
        
        print("\n💡 改进建议:")
        for i, rec in enumerate(results['recommendations'], 1):
            print(f"  {i}. {rec}")
        
        print("\n" + "="*80)
        print("📁 结果已保存到 eval/results/ 目录")
        print("="*80)
        
    except Exception as e:
        print(f"❌ 实验运行失败: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    # 运行异步主函数
    asyncio.run(main())
