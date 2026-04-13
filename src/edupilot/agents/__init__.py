"""Agent 模块初始化。"""

from edupilot.agents.chat.agent import ChatAgent, ChatMode
from edupilot.agents.tools.builtin import (
    RAGTool,
    BrainstormTool,
    ReasonTool,
    SummaryTool,
    CodeExplainTool,
    register_builtin_tools,
    get_tool,
    get_all_tools,
    get_tools_schema
)

__all__ = [
    # Chat Agent
    "ChatAgent",
    "ChatMode",
    # 工具
    "RAGTool",
    "BrainstormTool",
    "ReasonTool",
    "SummaryTool",
    "CodeExplainTool",
    "register_builtin_tools",
    "get_tool",
    "get_all_tools",
    "get_tools_schema"
]
