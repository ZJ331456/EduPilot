#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查询分析器智能体 (Query Analyzer Agent)

统一的查询分析器，整合意图识别和检索决策功能
合并自 IntentRecognitionAgent 和 DecisionAgent

设计理念：
1. 统一的查询理解入口：一次分析完成意图识别和检索决策
2. 信息复用：避免重复的文本分析和特征提取
3. 联合优化：意图和检索策略相互关联，统一决策
4. 性能优化：减少状态传递，降低序列化开销

核心职责：
1. 意图识别：启发式 + LLM 精修，识别用户真实意图
2. 检索决策：基于意图和查询特征，判断是否需要知识检索
3. 查询优化：提取核心概念，生成优化查询，构建检索策略
4. 路由建议：为下游 agent 提供执行路径建议
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

from src.infrastructure.utils import AgentState, BaseAgent, QueryType

try:
    from config import get_agent_config  # type: ignore[import]
except Exception:
    get_agent_config = None  # type: ignore[assignment]

from src.infrastructure.llm import LLMClientError, get_llm_manager
from .prompt import (
    build_intent_recognition_system_prompt,
    build_question_validation_prompt,
    build_question_validation_system_prompt
)


# ---------------------------------------------------------------------------
# 数据结构
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class IntentCandidate:
    """候选意图条目"""
    name: str
    score: float
    source: str
    rationale: str = ""
    signals: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "score": round(self.score, 4),
            "source": self.source,
            "rationale": self.rationale,
            "signals": self.signals,
        }


@dataclass(slots=True)
class RetrievalPlan:
    """检索计划"""
    need_retrieval: bool
    confidence: float
    reason: str
    core_concepts: List[str] = field(default_factory=list)
    related_queries: List[str] = field(default_factory=list)
    optimized_queries: List[Dict[str, Any]] = field(default_factory=list)
    query_strategy: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "need_retrieval": self.need_retrieval,
            "confidence": round(self.confidence, 4),
            "reason": self.reason,
            "core_concepts": self.core_concepts,
            "related_queries": self.related_queries,
            "optimized_queries": self.optimized_queries,
            "query_strategy": self.query_strategy,
        }


@dataclass(slots=True)
class QueryAnalysisResult:
    """查询分析完整结果"""
    # 意图识别结果
    intent: str
    query_type: QueryType
    confidence: float
    confidence_band: str
    reasoning: str
    candidates: List[IntentCandidate]
    open_intent: bool = False
    
    # 检索决策结果
    retrieval_plan: Optional[RetrievalPlan] = None
    
    # 路由建议
    routing_target: str = "executor"
    next_agents: List[str] = field(default_factory=list)
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent": self.intent,
            "query_type": self.query_type.value if isinstance(self.query_type, QueryType) else self.query_type,
            "confidence": round(self.confidence, 4),
            "confidence_band": self.confidence_band,
            "reasoning": self.reasoning,
            "open_intent": self.open_intent,
            "candidates": [c.to_dict() for c in self.candidates],
            "retrieval_plan": self.retrieval_plan.to_dict() if self.retrieval_plan else None,
            "routing_target": self.routing_target,
            "next_agents": self.next_agents,
            "metadata": self.metadata,
        }


# ---------------------------------------------------------------------------
# 核心智能体
# ---------------------------------------------------------------------------

class QueryAnalyzerAgent(BaseAgent):
    """
    统一的查询分析器
    
    整合意图识别和检索决策，提供一站式查询理解服务
    """
    
    # 意图配置：包含关键词、模式、查询类型、路由目标
    DEFAULT_INTENT_CONFIG: Dict[str, Dict[str, Any]] = {
        "concept_explanation": {
            "keywords": ["什么是", "定义", "解释", "意味着", "原理", "特点", "概念"],
            "patterns": [r"(什么是|介绍一下|解释).*", r".*的(概念|含义|原理)", r"如何理解"],
            "weight": 1.0,
            "query_type": QueryType.CONCEPT_EXPLANATION,
            "routing": "planner",
            "need_retrieval_score": 0.9,  # 强烈需要检索
        },
        "knowledge_retrieval": {
            "keywords": ["查找", "资料", "检索", "有哪些", "列举", "详细说明", "参考"],
            "patterns": [r"给我(.*)资料", r"有哪些(.*)资源", r"列举.*"],
            "weight": 0.9,
            "query_type": QueryType.KNOWLEDGE_RETRIEVAL,
            "routing": "knowledge_manager",
            "need_retrieval_score": 1.0,  # 必须检索
        },
        "learning_guidance": {
            "keywords": ["学习计划", "学习路线", "如何学习", "推荐课程", "练习建议", "提升", "系统地学习"],
            "patterns": [r"如何.*学习", r"学习路线.*", r"学习计划", r"系统.*学习"],
            "weight": 1.2,  # 提高权重，确保优先级
            "query_type": QueryType.LEARNING_GUIDANCE,
            "routing": "planner",
            "need_retrieval_score": 0.8,
        },
        "socratic_dialogue": {
            "keywords": ["为什么", "原因是什么", "推导", "证明", "思考", "启发我"],
            "patterns": [r"为什么.*而不是.*", r"为什么(?!.*学习)", r"帮我思考", r"引导我"],  # 排除"为什么...学习"这种模式
            "weight": 0.8,
            "query_type": QueryType.SOCRATIC_DIALOGUE,
            "routing": "socratic_guide",
            "need_retrieval_score": 0.7,
        },
        "direct_answer": {
            "keywords": ["直接告诉我", "答案是", "我只想知道", "总结一下", "一句话"],
            "patterns": [r"直接(告诉|给)我", r"答案是.*"],
            "weight": 0.7,
            "query_type": QueryType.DIRECT_ANSWER,
            "routing": "executor",
            "need_retrieval_score": 0.6,
        },
        "profile_update": {
            "keywords": ["我的喜好", "我喜欢", "请记住", "以后", "偏好", "设置"],
            "patterns": [r"记住我", r"以后.*"],
            "weight": 0.6,
            "query_type": QueryType.DIRECT_ANSWER,
            "routing": "user_profile",
            "need_retrieval_score": 0.0,  # 无需检索
        },
        "smalltalk": {
            "keywords": ["你好", "早上好", "天气", "聊天", "最近", "怎么样"],
            "patterns": [r"我们聊聊", r"讲个笑话", r"最近怎么样"],
            "weight": 0.5,
            "query_type": QueryType.DIRECT_ANSWER,
            "routing": "executor",
            "need_retrieval_score": 0.0,
        },
        "meta_question": {
            "keywords": ["你能做什么", "能力", "如何工作", "介绍你自己", "能否"],
            "patterns": [r"你能.*吗", r"你如何"],
            "weight": 0.6,
            "query_type": QueryType.DIRECT_ANSWER,
            "routing": "executor",
            "need_retrieval_score": 0.0,
        },
    }
    
    # 明确不需要检索的模式
    NO_RETRIEVAL_PATTERNS = [
        r"你好|您好|hello|hi",
        r"谢谢|感谢|thank",
        r"再见|拜拜|goodbye|bye",
        r"今天天气|现在几点|当前时间",
        r"计算|算一下|\d+[+\-*/]\d+",
        r"翻译.*成|translate.*to",
    ]
    
    # 核心概念提取模式（优化版：支持多字概念）
    CONCEPT_PATTERNS = [
        r"(\w{2,})是什么",
        r"什么是(\w{2,})",
        r"介绍一?下?(\w{2,})",
        r"(\w{2,})的(概念|定义|含义|特点|历史|作用|原理|意义|内容|过程)",
        r"解释一?下?(\w{2,})",
        r"说明一?下?(\w{2,})",
        r"(\w{2,})有(什么|哪些)",
        r"如何(学习|理解)(\w{2,})",
        r"(\w{2,})和(\w{2,})",  # 捕获比较对象
        r"([^？?。！!，,\s]{2,})$",  # 简短查询，直接提取主体
    ]
    
    # 置信度阈值
    CONFIDENCE_BANDS = [
        (0.75, "high"),
        (0.55, "medium"),
        (0.35, "low"),
    ]
    
    OPEN_INTENT_THRESHOLD = 0.4
    LLM_ENSURE_THRESHOLD = 0.6
    RETRIEVAL_DECISION_THRESHOLD = 0.5
    
    def __init__(
        self,
        *,
        enable_llm: bool = True,
        llm_client_name: Optional[str] = None,
        intent_config: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> None:
        super().__init__(
            name="QueryAnalyzer",
            description="统一的查询分析器：意图识别 + 检索决策 + 查询优化",
        )
        
        # 加载配置
        config = get_agent_config("query_analyzer") if get_agent_config else {}
        self.enable_llm = config.get("enable_llm", enable_llm)
        self.llm_client_name = config.get("llm_client", llm_client_name)
        
        # 合并意图配置
        custom_config = config.get("intent_config", {})
        base_config = intent_config or self.DEFAULT_INTENT_CONFIG
        self.intent_config: Dict[str, Dict[str, Any]] = {}
        for intent, payload in base_config.items():
            merged = dict(payload)
            if intent in custom_config:
                merged.update(custom_config[intent])
            self.intent_config[intent] = merged
        
        # 阈值配置
        self.high_threshold = config.get("high_threshold", 0.75)
        self.low_threshold = config.get("low_threshold", 0.35)
        self.open_intent_threshold = config.get("open_intent_threshold", self.OPEN_INTENT_THRESHOLD)
        self.retrieval_threshold = config.get("retrieval_threshold", self.RETRIEVAL_DECISION_THRESHOLD)
        
        # 初始化 LLM
        self.llm_manager = None
        if self.enable_llm:
            try:
                self.llm_manager = get_llm_manager()
            except Exception as exc:
                self.logger.warning("LLM 管理器初始化失败，降级为纯启发式：%s", exc)
                self.enable_llm = False
    
    # ------------------------------------------------------------------
    # 生命周期
    # ------------------------------------------------------------------
    
    def can_execute(self, state: AgentState) -> bool:
        """检查是否可以执行"""
        return bool(state.user_query and state.user_query.strip())
    
    async def execute(self, state: AgentState) -> AgentState:
        """
        执行查询分析
        
        流程：
        1. 提取全局特征（一次性）
        2. 阶段一：意图识别（启发式 + LLM）
        3. 阶段二：基于意图决定检索策略
        4. 阶段三：生成路由建议
        5. 写回状态
        """
        try:
            query = state.user_query.strip()
            
            # 提取全局特征（信息复用）
            global_features = self._extract_global_features(query)
            
            # 阶段1: 意图识别
            intent_result = await self._recognize_intent(query, global_features)
            
            # 阶段2: 检索决策
            retrieval_plan = None
            if self._should_consider_retrieval(intent_result):
                retrieval_plan = self._plan_retrieval(query, intent_result, global_features)
            
            # 阶段3: 路由建议
            next_agents = self._suggest_next_agents(intent_result, retrieval_plan)
            
            # 构建完整结果
            analysis_result = QueryAnalysisResult(
                intent=intent_result.intent,
                query_type=intent_result.query_type,
                confidence=intent_result.confidence,
                confidence_band=intent_result.confidence_band,
                reasoning=intent_result.reasoning,
                candidates=intent_result.candidates,
                open_intent=intent_result.open_intent,
                retrieval_plan=retrieval_plan,
                routing_target=intent_result.routing_target,
                next_agents=next_agents,
                metadata={
                    **intent_result.metadata,
                    "global_features": global_features,
                },
            )
            
            # 写回状态
            self._write_back_to_state(state, analysis_result)
            
            self.logger.info(
                f"查询分析完成 - 意图: {analysis_result.intent}, "
                f"置信度: {analysis_result.confidence:.2f}, "
                f"需要检索: {retrieval_plan.need_retrieval if retrieval_plan else False}"
            )
            
            return state
            
        except Exception as exc:
            self.logger.error("查询分析失败: %s", exc, exc_info=True)
            state.set_error("query_analysis_error", str(exc))
            return state
    
    # ------------------------------------------------------------------
    # 阶段一：意图识别
    # ------------------------------------------------------------------
    
    async def _recognize_intent(
        self, query: str, global_features: Dict[str, Any]
    ) -> QueryAnalysisResult:
        """意图识别：启发式 + LLM"""
        # 启发式分析
        heuristic_candidates = self._run_heuristics(query, global_features)
        
        # 决定是否需要 LLM 精修
        top_score = heuristic_candidates[0].score if heuristic_candidates else 0.0
        
        llm_candidate: Optional[IntentCandidate] = None
        llm_metadata: Dict[str, Any] = {}
        
        if self.enable_llm and (top_score < self.LLM_ENSURE_THRESHOLD or not heuristic_candidates):
            llm_candidate, llm_metadata = await self._invoke_llm(query, heuristic_candidates)
        
        # 融合候选意图
        fused_candidates = self._fuse_candidates(heuristic_candidates, llm_candidate)
        
        if fused_candidates:
            best = fused_candidates[0]
        else:
            best = IntentCandidate("open_intent", 0.0, "fallback", "无匹配", {})
        
        # 获取配置信息
        intent_payload = self.intent_config.get(best.name, {})
        query_type = intent_payload.get("query_type", QueryType.DIRECT_ANSWER)
        routing_target = intent_payload.get("routing", "executor")
        
        # 判断置信度区间
        confidence_band = self._confidence_band(best.score)
        open_intent = best.score < self.open_intent_threshold or best.name == "open_intent"
        
        # 构建推理链
        reasoning_parts = [best.rationale]
        if llm_candidate and llm_candidate.source == "llm":
            reasoning_parts.append("LLM 校正结果参与决策")
        
        metadata = {
            "llm_enabled": self.enable_llm,
            "llm_used": llm_candidate is not None,
            "llm_metadata": llm_metadata,
            "heuristic_top_score": top_score,
        }
        
        return QueryAnalysisResult(
            intent=best.name,
            query_type=query_type,
            confidence=min(best.score, 1.0),
            confidence_band=confidence_band,
            reasoning="；".join(reasoning_parts),
            candidates=fused_candidates,
            open_intent=open_intent,
            routing_target=routing_target,
            metadata=metadata,
        )
    
    def _extract_global_features(self, query: str) -> Dict[str, Any]:
        """提取全局特征（一次性，多处复用）"""
        normalized = query.lower()
        return {
            "length": len(query),
            "word_count": len(query.split()),
            "contains_question_mark": "?" in query or "?" in query,
            "contains_wh_word": bool(re.search(r"(why|what|how|when|where|谁|什么|如何|为什么)", normalized)),
            "contains_imperative": bool(re.search(r"(请|帮我|需要你|希望你)", query)),
            "contains_future": bool(re.search(r"(以后|未来|之后)", query)),
            "contains_profile": bool(re.search(r"(我喜欢|我不喜欢|我的|请记住)", query)),
            "professional_terms": self._count_professional_terms(query),
            "complexity_score": self._assess_query_complexity(query),
        }
    
    def _count_professional_terms(self, query: str) -> int:
        """统计专业术语数量"""
        count = 0
        for word in query.split():
            if len(word) > 3 and any(char in word for char in '学理论概念原理机制'):
                count += 1
        return count
    
    def _assess_query_complexity(self, query: str) -> float:
        """评估查询复杂度"""
        length_score = min(len(query) / 50, 1.0)
        term_score = min(self._count_professional_terms(query) / 3, 1.0)
        
        question_complexity = 0
        complex_patterns = [r"为什么.*而不是", r".*和.*的区别", r".*的优缺点", r".*的影响因素"]
        for pattern in complex_patterns:
            if re.search(pattern, query):
                question_complexity += 0.3
        
        return (length_score * 0.3 + term_score * 0.4 + min(question_complexity, 1.0) * 0.3)
    
    def _run_heuristics(
        self, query: str, global_features: Dict[str, Any]
    ) -> List[IntentCandidate]:
        """启发式意图识别"""
        normalized = query.lower()
        candidates: List[IntentCandidate] = []
        
        for intent, payload in self.intent_config.items():
            score, signals = self._score_intent(intent, payload, normalized, query, global_features)
            if score <= 0:
                continue
            candidates.append(
                IntentCandidate(
                    name=intent,
                    score=min(score, 1.0),
                    source="heuristic",
                    rationale=self._build_rationale(intent, signals),
                    signals=signals,
                )
            )
        
        candidates.sort(key=lambda c: c.score, reverse=True)
        return candidates
    
    def _score_intent(
        self,
        intent: str,
        payload: Dict[str, Any],
        normalized: str,
        raw_query: str,
        features: Dict[str, Any],
    ) -> Tuple[float, Dict[str, Any]]:
        """为意图打分"""
        keywords = payload.get("keywords", [])
        patterns = payload.get("patterns", [])
        weight = payload.get("weight", 1.0)
        
        # 关键词匹配
        keyword_hits = [kw for kw in keywords if kw.lower() in normalized]
        keyword_score = min(len(keyword_hits) * 0.25, 0.75)
        
        # 模式匹配
        pattern_hits = [pat for pat in patterns if re.search(pat, raw_query, re.IGNORECASE)]
        pattern_score = min(len(pattern_hits) * 0.3, 0.6)
        
        # 结构特征加成
        structural_bonus = 0.0
        if intent in {"concept_explanation", "knowledge_retrieval"} and features["contains_question_mark"]:
            structural_bonus += 0.1
        if intent == "learning_guidance" and features["contains_imperative"]:
            structural_bonus += 0.1
        if intent == "profile_update" and features["contains_profile"]:
            structural_bonus += 0.2
        if intent == "socratic_dialogue" and features["contains_wh_word"]:
            structural_bonus += 0.1
        
        raw_score = (keyword_score + pattern_score + structural_bonus) * weight
        raw_score = max(0.0, min(raw_score, 1.2))
        
        signals = {
            "keyword_hits": keyword_hits,
            "pattern_hits": pattern_hits,
            "structural_bonus": round(structural_bonus, 3),
            "weight": weight,
        }
        
        return raw_score, signals
    
    def _build_rationale(self, intent: str, signals: Dict[str, Any]) -> str:
        """构建推理说明"""
        fragments = []
        hits = signals.get("keyword_hits")
        if hits:
            fragments.append(f"命中关键词 {hits}")
        pats = signals.get("pattern_hits")
        if pats:
            fragments.append(f"匹配模式 {len(pats)} 个")
        bonus = signals.get("structural_bonus", 0)
        if bonus:
            fragments.append(f"结构特征额外加分 {bonus}")
        if not fragments:
            fragments.append("基础匹配得分")
        return "；".join(fragments)
    
    async def _invoke_llm(
        self, query: str, heuristic_candidates: Sequence[IntentCandidate]
    ) -> Tuple[Optional[IntentCandidate], Dict[str, Any]]:
        """调用 LLM 精修意图"""
        if not self.llm_manager:
            return None, {"disabled": True}
        
        system_prompt = build_intent_recognition_system_prompt()
        
        intent_catalog = [
            {
                "name": name,
                "description": self._intent_description(name),
            }
            for name in self.intent_config.keys()
        ]
        
        json_template = {
            "intent": "concept_explanation",
            "confidence": 0.68,
            "reasoning": "关键词匹配 + 用户想要解释",
            "unknown": False,
        }
        
        heuristic_summary = [c.to_dict() for c in heuristic_candidates]
        
        payload = {
            "intents": intent_catalog,
            "heuristic_candidates": heuristic_summary,
            "instruction": "请判断用户输入最有可能的意图，如不确定请将 unknown 设为 true。",
            "template": json_template,
            "user_query": query,
        }
        
        try:
            response = await self.llm_manager.async_generate_response(  # type: ignore[union-attr]
                json.dumps(payload, ensure_ascii=False),
                client_name=self.llm_client_name,
                system_prompt=system_prompt,
            )
        except LLMClientError as exc:
            self.logger.warning("LLM 调用失败：%s", exc)
            return None, {"error": str(exc)}
        
        parsed = self._safe_json_parse(response)
        if not parsed:
            self.logger.debug("LLM 返回无法解析：%s", response)
            return None, {"raw_response": response, "parse_success": False}
        
        intent_name = parsed.get("intent") or "open_intent"
        confidence = float(parsed.get("confidence", 0))
        reasoning = parsed.get("reasoning", "LLM 认为最优匹配")
        
        candidate = IntentCandidate(
            name=intent_name,
            score=max(0.0, min(confidence, 1.0)),
            source="llm",
            rationale=reasoning,
            signals={"raw": parsed},
        )
        
        return candidate, {"raw": parsed, "response": response, "parse_success": True}
    
    def _intent_description(self, name: str) -> str:
        """意图描述"""
        mapping = {
            "concept_explanation": "用户希望理解概念、原理或定义",
            "knowledge_retrieval": "用户请求检索或列举资料",
            "learning_guidance": "用户需要学习路径、规划或提升建议",
            "socratic_dialogue": "用户希望被提问引导深入思考",
            "direct_answer": "用户只要简洁回答或事实性结论",
            "profile_update": "用户在更新个人画像或偏好",
            "smalltalk": "寒暄、小聊天、非任务型对话",
            "meta_question": "询问系统能力或工作方式",
            "open_intent": "未知或全新意图",
        }
        return mapping.get(name, "")
    
    def _safe_json_parse(self, payload: str) -> Optional[Dict[str, Any]]:
        """安全解析 JSON"""
        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", payload, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    return None
        return None
    
    def _fuse_candidates(
        self,
        heuristic_candidates: Sequence[IntentCandidate],
        llm_candidate: Optional[IntentCandidate],
    ) -> List[IntentCandidate]:
        """融合启发式和 LLM 候选意图"""
        combined: Dict[str, IntentCandidate] = {}
        
        for candidate in heuristic_candidates:
            combined[candidate.name] = candidate
        
        if llm_candidate:
            existing = combined.get(llm_candidate.name)
            if existing:
                # 融合分数：取最大值
                fused_score = max(existing.score, llm_candidate.score)
                rationale = f"{existing.rationale}；LLM:{llm_candidate.rationale}"
                merged_signals = dict(existing.signals)
                merged_signals["llm"] = llm_candidate.signals.get("raw")
                combined[llm_candidate.name] = IntentCandidate(
                    name=llm_candidate.name,
                    score=fused_score,
                    source="hybrid",
                    rationale=rationale,
                    signals=merged_signals,
                )
            else:
                combined[llm_candidate.name] = llm_candidate
        
        fused_list = list(combined.values())
        fused_list.sort(key=lambda c: c.score, reverse=True)
        return fused_list
    
    def _confidence_band(self, score: float) -> str:
        """置信度区间"""
        for threshold, band in self.CONFIDENCE_BANDS:
            if score >= threshold:
                return band
        return "very_low"
    
    # ------------------------------------------------------------------
    # 阶段二：检索决策
    # ------------------------------------------------------------------
    
    def _should_consider_retrieval(self, intent_result: QueryAnalysisResult) -> bool:
        """判断是否应该考虑检索"""
        # 某些意图明确不需要检索
        no_retrieval_intents = {"smalltalk", "meta_question", "profile_update"}
        return intent_result.intent not in no_retrieval_intents
    
    def _plan_retrieval(
        self,
        query: str,
        intent_result: QueryAnalysisResult,
        global_features: Dict[str, Any],
    ) -> RetrievalPlan:
        """制定检索计划"""
        normalized = query.lower()
        
        # 1. 检查明确不需要检索的模式
        for pattern in self.NO_RETRIEVAL_PATTERNS:
            if re.search(pattern, normalized):
                return RetrievalPlan(
                    need_retrieval=False,
                    confidence=0.9,
                    reason=f"匹配无检索模式: {pattern}",
                )
        
        # 2. 基于意图获取检索倾向分数
        intent_payload = self.intent_config.get(intent_result.intent, {})
        intent_retrieval_score = intent_payload.get("need_retrieval_score", 0.5)
        
        # 3. 基于查询复杂度
        complexity_score = global_features["complexity_score"]
        
        # 4. 综合决策
        total_score = (
            intent_retrieval_score * 0.6 +
            complexity_score * 0.3 +
            intent_result.confidence * 0.1
        )
        
        need_retrieval = total_score > self.retrieval_threshold
        
        # 5. 如果需要检索，进行查询优化
        core_concepts: List[str] = []
        related_queries: List[str] = []
        optimized_queries: List[Dict[str, Any]] = []
        query_strategy: Dict[str, Any] = {}
        
        if need_retrieval:
            core_concepts = self._extract_core_concepts(query)
            related_queries = self._generate_related_queries(query, core_concepts)
            query_strategy = self._build_query_strategy(core_concepts, related_queries)
            optimized_queries = self._generate_optimized_queries(query, query_strategy)
        
        return RetrievalPlan(
            need_retrieval=need_retrieval,
            confidence=min(total_score, 1.0),
            reason=f"意图分数:{intent_retrieval_score:.2f}, 复杂度:{complexity_score:.2f}",
            core_concepts=core_concepts,
            related_queries=related_queries,
            optimized_queries=optimized_queries,
            query_strategy=query_strategy,
        )
    
    def _extract_core_concepts(self, query: str) -> List[str]:
        """提取核心概念（增强版：更精准的中文概念提取）"""
        concepts = []
        
        # 1. 使用正则模式提取
        for pattern in self.CONCEPT_PATTERNS:
            matches = re.findall(pattern, query)
            # 处理元组结果（如 "(\w+)和(\w+)" 会返回元组）
            for match in matches:
                if isinstance(match, tuple):
                    # 过滤掉属性词（如"概念"、"定义"等）
                    concepts.extend([m for m in match if m and len(m) > 1 and m not in {'概念', '定义', '含义', '特点', '历史', '作用', '原理', '意义', '内容', '过程', '什么', '哪些'}])
                elif match:
                    concepts.append(match)
        
        # 2. 去重和过滤
        concepts = list(set([c for c in concepts if len(c) > 1]))
        
        # 3. 如果没有提取到概念，使用备用方法
        if not concepts:
            concepts = self._extract_nouns_from_query(query)
        
        # 4. 按长度排序（优先保留更长的概念，通常更具体）
        concepts.sort(key=len, reverse=True)
        
        return concepts[:5]  # 增加到5个，提高召回率
    
    def _extract_nouns_from_query(self, query: str) -> List[str]:
        """从查询中提取名词（优化版：更好的中文分词）"""
        # 扩展停用词表
        stop_words = {
            '什么', '是', '的', '了', '在', '有', '和', '与', '或', '但', '而', '因为', '所以',
            '如何', '怎么', '怎样', '请', '一下', '吗', '呢', '吧', '啊',
            '这个', '那个', '哪些', '哪个', '为什么', '能不能', '可以',
            '解释', '说明', '介绍', '讲一讲', '详细',
        }
        
        # 尝试提取连续的中文字符串（可能是概念）
        chinese_segments = re.findall(r'[\u4e00-\u9fa5]{2,}', query)
        nouns = []
        
        for segment in chinese_segments:
            if segment not in stop_words and len(segment) >= 2:
                nouns.append(segment)
        
        # 如果没有找到，回退到按词分割
        if not nouns:
            words = query.split()
            for word in words:
                clean_word = re.sub(r'[^\w]', '', word)
                if len(clean_word) > 1 and clean_word not in stop_words:
                    nouns.append(clean_word)
        
        return nouns[:5]
    
    def _generate_related_queries(self, original_query: str, core_concepts: List[str]) -> List[str]:
        """生成相关查询"""
        related_queries = []
        
        for concept in core_concepts:
            concept_queries = [
                f"{concept}的定义",
                f"{concept}的概念",
                f"{concept}是什么",
                f"{concept}的特点",
                f"{concept}的作用",
                f"{concept}的原理",
            ]
            related_queries.extend(concept_queries)
        
        return list(set(related_queries))[:10]
    
    def _build_query_strategy(self, core_concepts: List[str], related_queries: List[str]) -> Dict[str, Any]:
        """构建查询策略"""
        return {
            'primary_strategy': 'concept_matching',
            'secondary_strategy': 'semantic_expansion',
            'fallback_strategy': 'keyword_search',
            'priority_order': [
                'exact_concept_match',
                'partial_concept_match',
                'related_concept_match',
                'keyword_match',
            ],
            'concept_weights': {concept: 1.0 - i * 0.1 for i, concept in enumerate(core_concepts)},
        }
    
    def _generate_optimized_queries(self, original_query: str, query_strategy: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成优化查询列表"""
        optimized_queries = []
        
        # 1. 原始查询
        optimized_queries.append({
            'query': original_query,
            'type': 'original',
            'priority': 1.0,
            'strategy': 'exact_match',
        })
        
        # 2. 核心概念查询
        for concept, weight in query_strategy.get('concept_weights', {}).items():
            optimized_queries.append({
                'query': concept,
                'type': 'core_concept',
                'priority': weight * 0.9,
                'strategy': 'concept_match',
            })
        
        # 3. 组合概念查询
        concepts = list(query_strategy.get('concept_weights', {}).keys())
        if len(concepts) > 1:
            for i in range(len(concepts)):
                for j in range(i + 1, len(concepts)):
                    combined_query = f"{concepts[i]} {concepts[j]}"
                    optimized_queries.append({
                        'query': combined_query,
                        'type': 'combined_concept',
                        'priority': 0.7,
                        'strategy': 'multi_concept_match',
                    })
        
        optimized_queries.sort(key=lambda x: x['priority'], reverse=True)
        return optimized_queries[:5]
    
    # ------------------------------------------------------------------
    # 阶段三：路由建议
    # ------------------------------------------------------------------
    
    def _suggest_next_agents(
        self,
        intent_result: QueryAnalysisResult,
        retrieval_plan: Optional[RetrievalPlan],
    ) -> List[str]:
        """建议下一步应该调用的 agents"""
        agents = []
        
        # 如果需要检索，优先调用知识检索器
        if retrieval_plan and retrieval_plan.need_retrieval:
            agents.append("knowledge_manager")
        
        # 基于意图添加路由目标
        routing_target = intent_result.routing_target
        if routing_target and routing_target not in agents:
            agents.append(routing_target)
        
        # 默认至少要有 executor
        if "executor" not in agents:
            agents.append("executor")
        
        return agents
    
    # ------------------------------------------------------------------
    # 写回状态
    # ------------------------------------------------------------------
    
    def _write_back_to_state(self, state: AgentState, result: QueryAnalysisResult) -> None:
        """将分析结果写回状态（优化版：添加关键词传递）"""
        # 写入查询类型
        state.query_type = result.query_type
        
        # 提取核心概念关键词供下游使用
        keywords = []
        if result.retrieval_plan:
            keywords = result.retrieval_plan.core_concepts
        if not keywords:
            # 后备方案：从查询中提取
            keywords = self._extract_core_concepts(state.user_query)
        
        # 写入意图识别结果（保持兼容性，增加 keywords）
        state.interpretation = {
            "intent": result.intent,
            "confidence": result.confidence,
            "confidence_band": result.confidence_band,
            "reasoning": result.reasoning,
            "open_intent": result.open_intent,
            "candidates": [c.to_dict() for c in result.candidates],
            "keywords": keywords,  # 🔑 关键：为 KnowledgeManager 提供关键词
        }
        
        # 写入检索决策（保持兼容性）
        if result.retrieval_plan:
            state.retrieval_decision = result.retrieval_plan.to_dict()
        else:
            state.retrieval_decision = {
                "need_retrieval": False,
                "confidence": 1.0,
                "reason": "意图不需要检索",
            }
        
        # 写入完整的查询分析结果
        state.metadata.setdefault("query_analysis", {}).update(result.to_dict())
        
        # 为后续代理提供简易标签
        state.metadata["intent_label"] = result.intent
        state.metadata["intent_confidence"] = result.confidence
        state.metadata["routing_target"] = result.routing_target
        state.metadata["next_agents"] = result.next_agents
        
        if result.open_intent:
            state.metadata["query_analysis"]["note"] = "低置信度，建议人工审阅或添加新意图"


__all__ = [
    "QueryAnalyzerAgent",
    "QueryAnalysisResult",
    "IntentCandidate",
    "RetrievalPlan",
]

