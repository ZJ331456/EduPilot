"""知识库图谱与对话图谱查询。"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from edupilot.config.settings import get_settings
from edupilot.services.graphrag import KnowledgeGraphService
from edupilot.services.storage import SessionStore, UserGraphStore

router = APIRouter(prefix="/graph", tags=["graph"])
_kg = KnowledgeGraphService()


@router.get("/knowledge/{kb_id}")
async def knowledge_graph(kb_id: str):
    return _kg.export_visual_graph(kb_id)


class IndexBody(BaseModel):
    source_path: Optional[str] = Field(
        default=None,
        description="可选：原始 txt 绝对路径，将拷贝为 knowledge_bases/<kb>/knowledge.txt",
    )
    use_sample: bool = Field(
        default=False,
        description="为 True 时使用 data/metadata/sanguo_sample.txt 作为来源（若存在）",
    )


@router.post("/knowledge/{kb_id}/index")
async def index_knowledge(kb_id: str, body: IndexBody):
    src: Optional[Path] = None
    if body.source_path:
        src = Path(body.source_path)
    elif body.use_sample:
        sample = get_settings().data_dir / "metadata" / "sanguo_sample.txt"
        if sample.exists():
            src = sample
    return await _kg.ensure_index(kb_id, source_text_path=src)


@router.get("/knowledge/{kb_id}/query")
async def query_knowledge(kb_id: str, q: str, mode: str = "local"):
    text = await _kg.query(kb_id, q, mode=mode)
    return {"answer": text}


@router.get("/session/{session_id}")
async def dialogue_graph(session_id: str):
    store = SessionStore()
    try:
        doc = store.load(session_id)
    except FileNotFoundError:
        return {"nodes": [], "links": [], "error": "session_not_found"}
    g = doc.get("dialogue_graph") or {}
    nodes = g.get("nodes") or []
    edges = g.get("edges") or []
    links = [{"source": e.get("source"), "target": e.get("target"), "value": e.get("relation", "")} for e in edges]
    out_nodes = [{"id": n.get("id"), "name": n.get("label", n.get("id"))} for n in nodes]
    return {"nodes": out_nodes, "links": links}


@router.get("/user/{user_id}/long_term")
async def user_long_graph(user_id: str):
    ug = UserGraphStore()
    g = ug.load_graph(user_id)
    nodes = g.get("nodes") or []
    edges = g.get("edges") or []
    links = [{"source": e.get("source"), "target": e.get("target"), "value": e.get("relation", "")} for e in edges]
    out_nodes = [{"id": n.get("id"), "name": n.get("label", n.get("id"))} for n in nodes]
    return {"nodes": out_nodes, "links": links}
