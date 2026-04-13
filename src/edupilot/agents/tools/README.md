# Builtin Tools - 内置工具集

内置工具集，提供 RAG 检索、头脑风暴、推理、摘要、代码解释等通用能力。

## 工具概览

| 工具类 | 工具名 | 功能 |
|--------|--------|------|
| `RAGTool` | `rag_retrieve` | GraphRAG 混合检索 |
| `BrainstormTool` | `brainstorm` | 头脑风暴 |
| `ReasonTool` | `reason` | 深度推理 |
| `SummaryTool` | `summarize` | 长文本摘要 |
| `CodeExplainTool` | `explain_code` | 代码功能解释 |

## 工具注册表

```python
# agents/tools/builtin.py
TOOL_REGISTRY: Dict[str, BaseTool] = {}

def register_builtin_tools() -> Dict[str, BaseTool]
def get_tool(name: str) -> Optional[BaseTool]
def get_all_tools() -> Dict[str, BaseTool]
def get_tools_schema() -> List[Dict[str, Any]]  # OpenAI Function Schema
```

## 基础接口

### BaseTool 抽象类

所有工具的基类：

```python
class BaseTool(ABC):
    @abstractmethod
    def get_definition(self) -> ToolDefinition:
        """返回工具定义"""

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """执行工具"""

    def validate_params(self, params: Dict) -> bool:
        """验证参数"""
```

### ToolDefinition

```python
@dataclass
class ToolDefinition:
    name: str              # 工具名称
    description: str       # 工具描述
    parameters: Dict       # 参数定义 (JSON Schema)
    returns: Dict          # 返回值定义
```

### ToolResult

```python
@dataclass
class ToolResult:
    success: bool         # 是否成功
    data: Any             # 返回数据
    error: Optional[str]  # 错误信息
    metadata: Dict        # 附加元数据
```

## 工具详解

### RAGTool - 知识检索

基于 GraphRAG 的混合检索工具，支持 local/global/naive 三种检索模式。

```python
class RAGTool(BaseTool):
    async def execute(
        self,
        query: str,
        kb_id: str = "default",
        mode: str = "hybrid",  # hybrid/local/naive
        top_k: int = 5
    ) -> ToolResult:
        """
        执行知识检索

        Args:
            query: 检索查询
            kb_id: 知识库 ID
            mode: 检索模式
                - hybrid: 混合检索（语义+关键词）
                - local: 本地检索（聚焦相关实体）
                - naive: 朴素检索（直接相似度）
            top_k: 返回结果数量

        Returns:
            ToolResult: 检索结果
        """
```

#### 检索模式对比

| 模式 | 适用场景 | 特点 |
|------|----------|------|
| `naive` | 简单问答 | 直接语义相似度匹配 |
| `local` | 实体关系查询 | 聚焦相关实体和邻居 |
| `hybrid` | 复杂推理 | 结合前两者优势 |

#### 使用示例

```python
from edupilot.agents.tools.builtin import RAGTool

tool = RAGTool()

# 混合检索
result = await tool.execute(
    query="什么是神经网络？",
    kb_id="ml_knowledge",
    mode="hybrid",
    top_k=5
)

print(result.data)
# [{'content': '...', 'score': 0.95, 'source': '...'}]
```

### BrainstormTool - 头脑风暴

生成相关概念和联想，帮助拓展思路。

```python
class BrainstormTool(BaseTool):
    async def execute(
        self,
        topic: str,
        count: int = 10,
        direction: str = "related"  # related/extended/contrast
    ) -> ToolResult:
        """
        执行头脑风暴

        Args:
            topic: 主题
            count: 生成数量
            direction: 方向
                - related: 相关概念
                - extended: 延伸扩展
                - contrast: 对比相反

        Returns:
            ToolResult: 头脑风暴结果
        """
```

#### 使用示例

```python
from edupilot.agents.tools.builtin import BrainstormTool

tool = BrainstormTool()

# 相关概念
result = await tool.execute(
    topic="机器学习",
    count=10,
    direction="related"
)

print(result.data)
# ['监督学习', '无监督学习', '深度学习', '强化学习', ...]
```

### ReasonTool - 深度推理

提供 chain/tree/contrast 三种推理方法。

```python
class ReasonTool(BaseTool):
    async def execute(
        self,
        problem: str,
        method: str = "chain",  # chain/tree/contrast
        context: Optional[str] = None
    ) -> ToolResult:
        """
        执行推理

        Args:
            problem: 问题描述
            method: 推理方法
                - chain: 链式推理（逐步推导）
                - tree: 树状推理（多路径探索）
                - contrast: 对比推理（正反分析）
            context: 上下文信息

        Returns:
            ToolResult: 推理结果
        """
```

#### 推理方法对比

| 方法 | 适用场景 | 特点 |
|------|----------|------|
| `chain` | 简单逻辑推导 | 线性步骤，清晰易理解 |
| `tree` | 复杂问题分解 | 分支探索，全面分析 |
| `contrast` | 决策分析 | 正反对比，利弊权衡 |

#### 使用示例

```python
from edupilot.agents.tools.builtin import ReasonTool

tool = ReasonTool()

# 链式推理
result = await tool.execute(
    problem="为什么深度学习需要大量数据？",
    method="chain"
)

print(result.data)
# [
#   "深度学习模型参数量大...",
#   "大量数据能有效防止过拟合...",
#   "数据量不足会导致模型泛化能力差..."
# ]
```

### SummaryTool - 文本摘要

对长文本进行智能摘要。

```python
class SummaryTool(BaseTool):
    async def execute(
        self,
        text: str,
        max_length: int = 200,
        style: str = "concise"  # concise/detailed/bullet
    ) -> ToolResult:
        """
        生成摘要

        Args:
            text: 原始文本
            max_length: 最大长度（字符）
            style: 摘要风格
                - concise: 简洁摘要
                - detailed: 详细摘要
                - bullet: 要点列表

        Returns:
            ToolResult: 摘要结果
        """
```

#### 使用示例

```python
from edupilot.agents.tools.builtin import SummaryTool

tool = SummaryTool()

# 生成要点列表式摘要
result = await tool.execute(
    text="长篇技术文章内容...",
    max_length=300,
    style="bullet"
)

print(result.data)
# • 要点1
# • 要点2
# • 要点3
```

### CodeExplainTool - 代码解释

解释代码的功能和工作原理。

```python
class CodeExplainTool(BaseTool):
    async def execute(
        self,
        code: str,
        language: Optional[str] = None,
        level: str = "intermediate"  # beginner/intermediate/advanced
    ) -> ToolResult:
        """
        解释代码

        Args:
            code: 代码内容
            language: 编程语言（自动检测可省略）
            level: 解释深度
                - beginner: 入门级解释
                - intermediate: 中级解释
                - advanced: 高级原理

        Returns:
            ToolResult: 解释结果
        """
```

#### 使用示例

```python
from edupilot.agents.tools.builtin import CodeExplainTool

tool = CodeExplainTool()

# 解释 Python 代码
result = await tool.execute(
    code="""
    def quicksort(arr):
        if len(arr) <= 1:
            return arr
        pivot = arr[len(arr) // 2]
        left = [x for x in arr if x < pivot]
        middle = [x for x in arr if x == pivot]
        right = [x for x in arr if x > pivot]
        return quicksort(left) + middle + quicksort(right)
    """,
    language="python",
    level="intermediate"
)

print(result.data)
# 解释内容...
```

## 工具注册

### 注册所有内置工具

```python
from edupilot.agents.tools.builtin import register_builtin_tools

tools = register_builtin_tools()
# {'rag_retrieve': RAGTool, 'brainstorm': BrainstormTool, ...}
```

### 获取工具定义

```python
# 获取 OpenAI Function Schema
from edupilot.agents.tools.builtin import get_tools_schema

schemas = get_tools_schema()
print(schemas)
# [
#   {
#     "type": "function",
#     "function": {
#       "name": "rag_retrieve",
#       "description": "...",
#       "parameters": {...}
#     }
#   },
#   ...
# ]
```

### 在 Agent 中使用

```python
from edupilot.agents.tools.builtin import get_all_tools, get_tool

# 获取所有工具
tools = get_all_tools()

# 在 Agent 中注册工具
agent.register_tool(tools['rag_retrieve'])

# 调用工具
result = await agent.call_tool('rag_retrieve', query="什么是机器学习")
```

## OpenAI Function Schema

工具定义遵循 OpenAI Function Calling 规范：

```json
{
  "type": "function",
  "function": {
    "name": "rag_retrieve",
    "description": "基于 GraphRAG 的知识检索工具...",
    "parameters": {
      "type": "object",
      "properties": {
        "query": {
          "type": "string",
          "description": "检索查询"
        },
        "kb_id": {
          "type": "string",
          "description": "知识库 ID"
        },
        "mode": {
          "type": "string",
          "enum": ["hybrid", "local", "naive"],
          "description": "检索模式"
        },
        "top_k": {
          "type": "integer",
          "description": "返回结果数量"
        }
      },
      "required": ["query"]
    }
  }
}
```

## 扩展开发

### 添加新工具

1. 继承 `BaseTool` 类
2. 实现 `get_definition()` 和 `execute()` 方法
3. 在 `register_builtin_tools()` 中注册

```python
class MyCustomTool(BaseTool):
    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="my_tool",
            description="我的自定义工具",
            parameters={...},
            returns={...}
        )

    async def execute(self, **kwargs) -> ToolResult:
        # 实现工具逻辑
        return ToolResult(success=True, data={...})

# 注册工具
TOOL_REGISTRY["my_tool"] = MyCustomTool()
```

## 相关模块

- [ChatAgent](../chat/README.md) - 对话智能体
- [BaseAgent](../base/agent.py) - Agent 基类
