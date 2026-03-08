#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EduPilot v4 — KnowledgeEngine Service

职责（合并 v3 KnowledgeManager + ToolSpecialist）：
- GraphRAG 知识库语义检索
- 多概念并发检索 + 结果聚合去重
- 工具调用（网络搜索、数学计算、代码执行等）
- 统一输出 knowledge_context 字典

设计要点：
1. 服务而非 Agent — 不调用 LLM 做决策，只执行检索和工具
2. 并发执行 — asyncio.gather 多源检索
3. 优雅降级 — 任何检索器失败时降级到关键词匹配
4. 超时保护 — 每个检索源独立超时（15s）
"""

import asyncio
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

_RETRIEVAL_TIMEOUT = 15.0    # 单个检索源超时
_MAX_CHUNKS = 8               # 最多返回 chunk 数
_SCORE_THRESHOLD = 0.3        # 最低相关性分数


class KnowledgeEngineService:
    """EduPilot v4 知识引擎服务

    聚合 GraphRAG + 工具调用，统一输出 knowledge_context。
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._knowledge_bases: Dict[str, Any] = {}
        self._initialized = False
        self._init_lock = asyncio.Lock()
        self._call_count = 0
        self._error_count = 0

    async def _ensure_initialized(self):
        """延迟初始化知识库（避免启动时阻塞）"""
        if self._initialized:
            return
        async with self._init_lock:
            if self._initialized:
                return
            await self._load_knowledge_bases()
            self._initialized = True

    async def _load_knowledge_bases(self):
        """扫描并加载所有知识库"""
        try:
            kb_root = Path("data/concept_knowledge_bases")
            if not kb_root.exists():
                self.logger.info("知识库目录不存在，跳过加载")
                return

            for concept_dir in kb_root.iterdir():
                if not concept_dir.is_dir():
                    continue
                knowledge_file = concept_dir / "knowledge.txt"
                if knowledge_file.exists():
                    self._knowledge_bases[concept_dir.name] = {
                        "path": str(knowledge_file),
                        "content": knowledge_file.read_text(encoding="utf-8"),
                        "graphrag": None,  # 懒加载 GraphRAG 实例
                    }

            self.logger.info(f"加载知识库: {list(self._knowledge_bases.keys())}")
        except Exception as e:
            self.logger.warning(f"知识库加载失败: {e}")

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """执行知识检索，返回 state 更新片段"""
        start_ts = time.time()
        await self._ensure_initialized()

        task_plan: Dict[str, Any] = state.get("task_plan") or {}
        user_query: str = state.get("user_query", "")
        core_concepts: List[str] = task_plan.get("core_concepts", [])
        strategy: str = task_plan.get("strategy", "explain")
        intent: str = task_plan.get("intent", "")

        # 构建检索查询列表
        queries = self._build_queries(user_query, core_concepts)

        # 并发执行多源检索
        retrieval_tasks = [
            self._retrieve_from_knowledge_base(q, task_plan) for q in queries[:3]
        ]

        # 工具调用（仅对特定意图）
        tool_tasks = []
        if intent in ("knowledge_retrieval",) and self._needs_tool_call(user_query, task_plan):
            tool_tasks.append(self._call_tools(user_query, task_plan))

        # 并发执行
        all_tasks = retrieval_tasks + tool_tasks
        results = await asyncio.gather(*all_tasks, return_exceptions=True)

        # 聚合结果
        all_chunks: List[Dict[str, Any]] = []
        tool_results: Dict[str, Any] = {}
        sources: List[str] = []

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.warning(f"检索任务 {i} 失败: {result}")
                continue

            if i < len(retrieval_tasks):
                # 知识库检索结果
                chunks = result or []
                all_chunks.extend(chunks)
                for c in chunks:
                    src = c.get("source", "")
                    if src and src not in sources:
                        sources.append(src)
            else:
                # 工具调用结果
                tool_results.update(result or {})

        # 去重 + 排序 + 截断
        deduplicated = self._deduplicate_chunks(all_chunks)
        top_chunks = sorted(
            deduplicated,
            key=lambda x: x.get("relevance_score", 0),
            reverse=True
        )[:_MAX_CHUNKS]

        self._call_count += 1
        elapsed_ms = (time.time() - start_ts) * 1000

        self.logger.info(
            f"[KnowledgeEngine] queries={len(queries)} chunks={len(top_chunks)} "
            f"tools={bool(tool_results)} ({elapsed_ms:.0f}ms)"
        )

        knowledge_context = {
            "retrieved_chunks": top_chunks,
            "tool_results": tool_results,
            "sources": sources,
            "retrieval_strategy": task_plan.get("strategy", "semantic"),
            "total_tokens": sum(len(c.get("content", "")) for c in top_chunks),
            "query_count": len(queries),
        }

        # 同步 v3 兼容字段
        from src.core.workflow.state import sync_compat_fields
        partial_state = {**state, "knowledge_context": knowledge_context}
        sync_compat_fields(partial_state)

        return {
            "knowledge_context": knowledge_context,
            "retrieved_docs": partial_state.get("retrieved_docs", []),
            "validated_docs": partial_state.get("validated_docs", []),
            "evidence_used": partial_state.get("evidence_used", []),
            "tool_outputs": partial_state.get("tool_outputs", {}),
            "knowledge_sources": sources,
            "next_step": "teaching",
            "performance_data": {
                **state.get("performance_data", {}),
                "knowledge_engine_ms": elapsed_ms,
            },
        }

    def _build_queries(self, user_query: str, core_concepts: List[str]) -> List[str]:
        """构建检索查询列表"""
        queries = [user_query]
        for concept in core_concepts[:2]:
            if concept not in user_query:
                queries.append(concept)
        return queries

    def _needs_tool_call(self, user_query: str, task_plan: Dict[str, Any]) -> bool:
        """判断是否需要外部工具调用"""
        tool_indicators = ["最新", "现在", "今天", "搜索", "查找", "计算", "代码"]
        return any(kw in user_query for kw in tool_indicators)

    async def _retrieve_from_knowledge_base(
        self, query: str, task_plan: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """从知识库检索相关内容"""
        try:
            return await asyncio.wait_for(
                self._do_retrieval(query, task_plan),
                timeout=_RETRIEVAL_TIMEOUT,
            )
        except asyncio.TimeoutError:
            self.logger.warning(f"知识库检索超时: {query[:50]}")
            return []
        except Exception as e:
            self._error_count += 1
            self.logger.warning(f"知识库检索失败: {e}")
            return []

    async def _do_retrieval(
        self, query: str, task_plan: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """执行实际检索逻辑（GraphRAG 或关键词）"""
        if not self._knowledge_bases:
            return []

        results = []

        # 识别目标知识库
        target_kbs = self._identify_target_kbs(query, task_plan)
        if not target_kbs:
            target_kbs = list(self._knowledge_bases.keys())[:2]

        for kb_name in target_kbs[:2]:
            kb = self._knowledge_bases.get(kb_name)
            if not kb:
                continue

            # 优先使用 GraphRAG 实例
            graphrag_instance = kb.get("graphrag")
            if graphrag_instance:
                chunks = await self._graphrag_search(graphrag_instance, query, task_plan)
            else:
                # 兜底：尝试初始化 GraphRAG，否则用关键词检索
                graphrag_instance = await self._try_init_graphrag(kb_name, kb)
                if graphrag_instance:
                    kb["graphrag"] = graphrag_instance
                    chunks = await self._graphrag_search(graphrag_instance, query, task_plan)
                else:
                    chunks = self._keyword_search(kb["content"], query, kb_name)

            results.extend(chunks)

        return results

    def _identify_target_kbs(
        self, query: str, task_plan: Dict[str, Any]
    ) -> List[str]:
        """识别最相关的知识库"""
        candidates = []
        core_concepts = task_plan.get("core_concepts", [])
        query_lower = query.lower()

        for kb_name in self._knowledge_bases:
            kb_lower = kb_name.lower()
            # 直接名称匹配
            if kb_lower in query_lower:
                candidates.insert(0, kb_name)
                continue
            # 核心概念匹配
            for concept in core_concepts:
                if kb_lower in concept.lower() or concept.lower() in kb_lower:
                    candidates.append(kb_name)
                    break

        return candidates[:3]

    async def _try_init_graphrag(
        self, kb_name: str, kb: Dict[str, Any]
    ) -> Optional[Any]:
        """尝试初始化 GraphRAG 实例（懒加载）"""
        try:
            from src.infrastructure.llm.manager import get_llm_manager

            llm_manager = get_llm_manager()
            llm_fn = llm_manager.get_llm_function()
            embed_fn = llm_manager.get_embedding_function()

            from nano_graphrag import GraphRAG, QueryParam
            graphrag = GraphRAG(
                working_dir=str(Path(kb["path"]).parent),
                enable_llm_cache=True,
                best_model_func=llm_fn,
                cheap_model_func=llm_fn,
                embedding_func=embed_fn,
            )
            return graphrag
        except ImportError:
            return None
        except Exception as e:
            self.logger.debug(f"GraphRAG 初始化失败 ({kb_name}): {e}")
            return None

    async def _graphrag_search(
        self, graphrag: Any, query: str, task_plan: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """执行 GraphRAG 检索"""
        try:
            from nano_graphrag import QueryParam
            strategy = task_plan.get("strategy", "explain")
            mode_map = {
                "explain": "hybrid",
                "socratic": "local",
                "curriculum": "global",
                "direct": "naive",
            }
            mode = mode_map.get(strategy, "hybrid")

            result = await graphrag.aquery(
                query,
                param=QueryParam(mode=mode, top_k=5),
            )

            if isinstance(result, str):
                return [{
                    "content": result,
                    "source": "graphrag",
                    "relevance_score": 0.8,
                }]
            return []
        except Exception as e:
            self.logger.debug(f"GraphRAG 检索失败: {e}")
            return []

    def _keyword_search(
        self, content: str, query: str, source: str
    ) -> List[Dict[str, Any]]:
        """基于关键词的简单文本检索（兜底方案）"""
        if not content:
            return []

        query_words = set(query.lower().split())
        paragraphs = content.split("\n\n")
        scored = []

        for para in paragraphs:
            if len(para.strip()) < 20:
                continue
            para_lower = para.lower()
            score = sum(1 for w in query_words if w in para_lower) / max(len(query_words), 1)
            if score >= _SCORE_THRESHOLD:
                scored.append({
                    "content": para.strip()[:500],
                    "source": source,
                    "relevance_score": score,
                })

        return sorted(scored, key=lambda x: x["relevance_score"], reverse=True)[:3]

    async def _call_tools(
        self, user_query: str, task_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """调用外部工具（网络搜索 / 计算等）"""
        results = {}
        try:
            # 数学计算
            if any(kw in user_query for kw in ["计算", "求", "等于", "=", "+"]):
                results["math"] = await self._math_tool(user_query)

            # 未来可扩展：web_search, code_execution 等
        except Exception as e:
            self.logger.warning(f"工具调用失败: {e}")

        return results

    async def _math_tool(self, query: str) -> str:
        """简单数学计算工具"""
        import re
        expr = re.search(r'[\d\s\+\-\*\/\(\)\.]+', query)
        if expr:
            try:
                result = eval(expr.group().strip())  # noqa: S307
                return str(result)
            except Exception:
                pass
        return ""

    def _deduplicate_chunks(
        self, chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """基于内容指纹去重"""
        seen = set()
        unique = []
        for chunk in chunks:
            key = chunk.get("content", "")[:150]
            if key not in seen:
                seen.add(key)
                unique.append(chunk)
        return unique

    def get_stats(self) -> Dict[str, Any]:
        return {
            "service": "KnowledgeEngine",
            "call_count": self._call_count,
            "error_count": self._error_count,
            "kb_count": len(self._knowledge_bases),
        }
