"""基于 nano_graphrag 的本地知识库构建与图谱导出。"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import networkx as nx

from edupilot.config.settings import get_settings
from edupilot.services.llm import build_graphrag_functions, get_llm_client
from edupilot.services.graphrag import GraphRAG, QueryParam


def _graphml_path(working_dir: Path) -> Path:
    return working_dir / "graph_chunk_entity_relation.graphml"


def nx_to_echarts(G: nx.Graph) -> Dict[str, Any]:
    """将无向图转为 ECharts graph 所需 nodes / links。"""
    nodes = []
    for n in G.nodes():
        nodes.append({"id": str(n), "name": str(n), "category": 0})
    links = []
    for u, v, data in G.edges(data=True):
        links.append(
            {
                "source": str(u),
                "target": str(v),
                "value": str(data.get("weight", data.get("description", "")))[:80],
            }
        )
    return {"nodes": nodes, "links": links}


class KnowledgeGraphService:
    """每个知识库使用独立 working_dir，位于 data/knowledge_bases/<kb_id>/rag_workspace。"""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._instances: Dict[str, GraphRAG] = {}

    def kb_paths(self, kb_id: str) -> Tuple[Path, Path]:
        root = self._settings.data_dir / "knowledge_bases" / kb_id
        root.mkdir(parents=True, exist_ok=True)
        knowledge_file = root / "knowledge.txt"
        workspace = root / "rag_workspace"
        workspace.mkdir(parents=True, exist_ok=True)
        return knowledge_file, workspace

    def _build_graphrag(self, workspace: Path) -> GraphRAG:
        client = get_llm_client()
        best_fn, embed_fn = build_graphrag_functions(client.settings, client.async_client)
        s = self._settings
        return GraphRAG(
            working_dir=str(workspace),
            best_model_func=best_fn,
            cheap_model_func=best_fn,
            embedding_func=embed_fn,
            enable_local=True,
            enable_naive_rag=False,
            best_model_max_async=s.graphrag_llm_max_async,
            cheap_model_max_async=s.graphrag_llm_max_async,
            embedding_func_max_async=s.graphrag_embedding_max_async,
            embedding_batch_num=s.graphrag_embedding_batch_num,
        )

    def _metadata_source_for_kb(self, kb_id: str) -> Path:
        """用户放置的原始建库文本：data/metadata/<知识库ID>/knowledge.txt"""
        return self._settings.data_dir / "metadata" / kb_id / "knowledge.txt"

    async def ensure_index(self, kb_id: str, source_text_path: Optional[Path] = None) -> Dict[str, Any]:
        """若 knowledge_bases 下尚无 knowledge.txt，则依次从：显式路径、data/metadata 拷贝。"""
        knowledge_file, workspace = self.kb_paths(kb_id)
        if source_text_path and source_text_path.exists() and not knowledge_file.exists():
            knowledge_file.write_text(source_text_path.read_text(encoding="utf-8"), encoding="utf-8")

        if not knowledge_file.exists():
            meta_src = self._metadata_source_for_kb(kb_id)
            if meta_src.exists():
                knowledge_file.write_text(meta_src.read_text(encoding="utf-8"), encoding="utf-8")

        if not knowledge_file.exists():
            return {
                "ok": False,
                "error": (
                    "未找到建库文本。请将原始文件放在 data/metadata/<知识库ID>/knowledge.txt，"
                    "或通过 API 传入 source_path / use_sample。"
                ),
            }

        if _graphml_path(workspace).exists():
            self._instances[kb_id] = self._build_graphrag(workspace)
            return {"ok": True, "kb_id": kb_id, "working_dir": str(workspace), "indexed": False}

        loop = asyncio.get_event_loop()
        graphrag = self._build_graphrag(workspace)

        def _insert() -> None:
            content = knowledge_file.read_text(encoding="utf-8")
            graphrag.insert(content)

        await loop.run_in_executor(None, _insert)
        self._instances[kb_id] = graphrag

        return {"ok": True, "kb_id": kb_id, "working_dir": str(workspace), "indexed": True}

    async def query(self, kb_id: str, question: str, mode: str = "local") -> str:
        if kb_id not in self._instances:
            _, workspace = self.kb_paths(kb_id)
            if not _graphml_path(workspace).exists():
                res = await self.ensure_index(kb_id)
                if not res.get("ok"):
                    return "无法查询：" + str(res.get("error", "未知错误"))
            if kb_id not in self._instances:
                self._instances[kb_id] = self._build_graphrag(workspace)
        gr = self._instances[kb_id]
        qp = QueryParam(mode=mode, top_k=10, only_need_context=False)
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: gr.query(question, param=qp))

    def export_visual_graph(self, kb_id: str) -> Dict[str, Any]:
        _, workspace = self.kb_paths(kb_id)
        gp = _graphml_path(workspace)
        if not gp.exists():
            return {"nodes": [], "links": [], "error": "图谱尚未构建，请先执行索引"}
        G = nx.read_graphml(gp)
        return nx_to_echarts(G)
