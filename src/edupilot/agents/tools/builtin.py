"""内置工具：RAG检索、网页搜索、代码执行、头脑风暴等。"""

from __future__ import annotations

import asyncio
import json
import re
from abc import ABC
from typing import Any, Dict, List, Optional

from edupilot.core.protocol import BaseTool, ToolDefinition, ToolResult
from edupilot.services.llm import get_llm_client
from edupilot.services.graph import KnowledgeGraphService


class RAGTool(BaseTool):
    """知识库检索工具：基于 GraphRAG 的混合检索。"""

    def __init__(self, kb_id: str = "default") -> None:
        self._kb_id = kb_id
        self._kg = KnowledgeGraphService()
        self._llm = get_llm_client()

    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="rag_retrieve",
            description="从知识库中检索相关信息，支持 local/global/naive 三种模式。",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "检索查询文本"
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["local", "global", "naive"],
                        "description": "检索模式：local(社区局部)、global(全局总结)、naive(直接相似度)",
                        "default": "local"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "返回结果数量",
                        "default": 5
                    }
                },
                "required": ["query"]
            },
            is_async=True
        )

    async def execute(self, query: str, mode: str = "local", top_k: int = 5, **kwargs) -> ToolResult:
        """执行 RAG 检索。"""
        import time
        start = time.time()
        try:
            result = await self._kg.query(self._kb_id, query, mode=mode)
            return ToolResult(
                tool_name=self.get_definition().name,
                success=True,
                output=result[:2000],
                duration_ms=(time.time() - start) * 1000
            )
        except Exception as e:
            return ToolResult(
                tool_name=self.get_definition().name,
                success=False,
                error=str(e),
                duration_ms=(time.time() - start) * 1000
            )


class BrainstormTool(BaseTool):
    """头脑风暴工具：生成相关概念和联想。"""

    def __init__(self) -> None:
        self._llm = get_llm_client()

    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="brainstorm",
            description="对给定主题进行头脑风暴，生成相关概念、问题和学习方向的联想。",
            parameters={
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "头脑风暴的主题"
                    },
                    "count": {
                        "type": "integer",
                        "description": "生成联想数量",
                        "default": 5
                    }
                },
                "required": ["topic"]
            },
            is_async=True
        )

    async def execute(self, topic: str, count: int = 5, **kwargs) -> ToolResult:
        """执行头脑风暴。"""
        import time
        start = time.time()
        try:
            prompt = f"""围绕主题「{topic}」进行头脑风暴，生成 {count} 个相关的联想：
1. 相关概念
2. 延伸问题
3. 学习方向

请以 JSON 格式返回：
{{"concepts": [...], "questions": [...], "directions": [...]}}"""
            result = await self._llm.chat(
                [{"role": "user", "content": prompt}],
                temperature=0.9,
                max_tokens=1000
            )
            # 尝试解析 JSON
            m = re.search(r'\{[\s\S]*\}', result)
            if m:
                data = json.loads(m.group(0))
                result = json.dumps(data, ensure_ascii=False, indent=2)
            return ToolResult(
                tool_name=self.get_definition().name,
                success=True,
                output=result,
                duration_ms=(time.time() - start) * 1000
            )
        except Exception as e:
            return ToolResult(
                tool_name=self.get_definition().name,
                success=False,
                error=str(e),
                duration_ms=(time.time() - start) * 1000
            )


class ReasonTool(BaseTool):
    """深度推理工具：专用 LLM 进行结构化推理。"""

    def __init__(self) -> None:
        self._llm = get_llm_client()

    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="reason",
            description="对给定问题进行深度结构化推理，逐步分析并给出结论。",
            parameters={
                "type": "object",
                "properties": {
                    "problem": {
                        "type": "string",
                        "description": "需要推理的问题"
                    },
                    "method": {
                        "type": "string",
                        "enum": ["chain", "tree", "contrast"],
                        "description": "推理方法",
                        "default": "chain"
                    }
                },
                "required": ["problem"]
            },
            is_async=True
        )

    async def execute(self, problem: str, method: str = "chain", **kwargs) -> ToolResult:
        """执行深度推理。"""
        import time
        start = time.time()
        try:
            prompts = {
                "chain": f"请逐步推理分析以下问题：\n{problem}\n\n推理过程：",
                "tree": f"请从多个角度分析以下问题，列出所有可能性：\n{problem}\n\n分析：",
                "contrast": f"请对比分析以下问题的正反两面：\n{problem}\n\n对比分析："
            }
            prompt = prompts.get(method, prompts["chain"])
            result = await self._llm.chat(
                [{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=1500
            )
            return ToolResult(
                tool_name=self.get_definition().name,
                success=True,
                output=result,
                duration_ms=(time.time() - start) * 1000
            )
        except Exception as e:
            return ToolResult(
                tool_name=self.get_definition().name,
                success=False,
                error=str(e),
                duration_ms=(time.time() - start) * 1000
            )


class SummaryTool(BaseTool):
    """摘要工具：对长文本进行摘要。"""

    def __init__(self) -> None:
        self._llm = get_llm_client()

    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="summarize",
            description="对长文本进行摘要，提取关键信息和要点。",
            parameters={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "需要摘要的文本"
                    },
                    "max_length": {
                        "type": "integer",
                        "description": "摘要最大长度（字符）",
                        "default": 500
                    }
                },
                "required": ["text"]
            },
            is_async=True
        )

    async def execute(self, text: str, max_length: int = 500, **kwargs) -> ToolResult:
        """执行摘要。"""
        import time
        start = time.time()
        try:
            if len(text) <= max_length:
                return ToolResult(
                    tool_name=self.get_definition().name,
                    success=True,
                    output=text,
                    duration_ms=(time.time() - start) * 1000
                )
            prompt = f"请简要摘要以下内容，控制在 {max_length} 字以内：\n\n{text[:3000]}"
            result = await self._llm.chat(
                [{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=int(max_length * 2)
            )
            return ToolResult(
                tool_name=self.get_definition().name,
                success=True,
                output=result,
                duration_ms=(time.time() - start) * 1000
            )
        except Exception as e:
            return ToolResult(
                tool_name=self.get_definition().name,
                success=False,
                error=str(e),
                duration_ms=(time.time() - start) * 1000
            )


class CodeExplainTool(BaseTool):
    """代码解释工具：解释代码逻辑和功能。"""

    def __init__(self) -> None:
        self._llm = get_llm_client()

    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="explain_code",
            description="解释代码的功能、逻辑和实现细节。",
            parameters={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "需要解释的代码"
                    },
                    "language": {
                        "type": "string",
                        "description": "编程语言"
                    }
                },
                "required": ["code"]
            },
            is_async=True
        )

    async def execute(self, code: str, language: str = "", **kwargs) -> ToolResult:
        """执行代码解释。"""
        import time
        start = time.time()
        try:
            prompt = f"请解释以下{language}代码的功能和实现逻辑：\n\n```{language}\n{code}\n```\n\n解释："
            result = await self._llm.chat(
                [{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=2000
            )
            return ToolResult(
                tool_name=self.get_definition().name,
                success=True,
                output=result,
                duration_ms=(time.time() - start) * 1000
            )
        except Exception as e:
            return ToolResult(
                tool_name=self.get_definition().name,
                success=False,
                error=str(e),
                duration_ms=(time.time() - start) * 1000
            )


# 工具注册表
TOOL_REGISTRY: Dict[str, BaseTool] = {}


def register_builtin_tools() -> Dict[str, BaseTool]:
    """注册所有内置工具。"""
    global TOOL_REGISTRY
    tools = [
        RAGTool(),
        BrainstormTool(),
        ReasonTool(),
        SummaryTool(),
        CodeExplainTool()
    ]
    for tool in tools:
        TOOL_REGISTRY[tool.get_definition().name] = tool
    return TOOL_REGISTRY


def get_tool(name: str) -> Optional[BaseTool]:
    """获取工具实例。"""
    if not TOOL_REGISTRY:
        register_builtin_tools()
    return TOOL_REGISTRY.get(name)


def get_all_tools() -> Dict[str, BaseTool]:
    """获取所有已注册工具。"""
    if not TOOL_REGISTRY:
        register_builtin_tools()
    return TOOL_REGISTRY.copy()


def get_tools_schema() -> List[Dict[str, Any]]:
    """获取所有工具的 OpenAI Function Schema。"""
    tools = get_all_tools()
    return [
        {
            "type": "function",
            "function": {
                "name": t.get_definition().name,
                "description": t.get_definition().description,
                "parameters": t.get_definition().parameters
            }
        }
        for t in tools.values()
    ]
