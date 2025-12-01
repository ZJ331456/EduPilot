#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 路由模块
严格对齐 core 模块结构

架构层次说明：
==============

1. 主流程接口（推荐使用）
   - workflow: 完整的学习工作流编排，包含所有10个agent
   路径: /api/agent/v1/workflow/
   
   包含的10个agent：
   - query_analyzer: 查询分析器
   - orchestrator: 编排器/规划器
   - draft_writer: 初稿撰写器
   - reviewer: 审核器
   - curriculum_designer: 课程设计器
   - quiz_master: 测验大师
   - tool_specialist: 工具专家
   - knowledge_manager: 知识管理器
   - socratic_guide: 苏格拉底引导
   - memory_manager: 记忆管理器
   
2. 工具接口（按需使用）
   - memory_manager: 用户画像和学习记录管理
   - knowledge_manager: 知识库检索和管理
   路径: /api/agent/v1/memory-manager/, /api/agent/v1/knowledge-manager/
   
3. 调试接口（开发测试用）- 所有10个agent都有独立路由
   - query_analyzer: 查询分析
   - orchestrator: 学习规划（编排器）
   - draft_writer: 内容撰写
   - reviewer: 内容审核
   - curriculum_designer: 课程设计
   - quiz_master: 测试题生成
   - tool_specialist: 工具调用
   - socratic_guide: 苏格拉底引导
   路径: /api/agent/v1/{agent-name}/
   ⚠️ 不建议在生产环境直接使用，建议使用 workflow 接口

结构对齐说明：
============
api/routers/                    ↔ core/
  ├── query_analyzer.py        ↔ agents/query_analyzer/
  ├── orchestrator.py          ↔ agents/orchestrator/
  ├── draft_writer.py          ↔ agents/draft_writer/
  ├── reviewer.py              ↔ agents/reviewer/
  ├── curriculum_designer.py   ↔ agents/curriculum_designer/
  ├── quiz_master.py           ↔ agents/quiz_master/
  ├── tool_specialist.py       ↔ agents/tool_specialist/
  ├── knowledge_manager.py     ↔ agents/knowledge_manager/
  ├── socratic_guide.py       ↔ agents/socratic_guide/
  ├── memory_manager.py        ↔ agents/memory_manager/
  └── workflow.py              ↔ workflow/ (包含所有10个agent)

使用建议：
=========
✅ 生产环境：使用 workflow 接口
⚠️ 数据查询：使用 memory_manager/knowledge_manager 接口
🔧 调试测试：使用独立 agent 接口

示例：
=====
# 推荐：完整工作流
POST /api/agent/v1/workflow/session/start
{
    "user_id": "user123",
    "query": "什么是大化改新？"
}

# 查询用户数据
GET /api/agent/v1/memory-manager/profile/user123

# 调试：测试查询分析器
POST /api/agent/v1/query-analyzer/analyze
{
    "query": "什么是大化改新？"
}
"""

# 工作流路由（主流程接口）
from . import workflow

# Agent 路由（所有10个agent，与 core.agents 严格对齐）
from . import (
    query_analyzer,
    orchestrator,
    draft_writer,
    reviewer,
    curriculum_designer,
    quiz_master,
    tool_specialist,
    knowledge_manager,
    socratic_guide,
    memory_manager,
)

__all__ = [
    # 主流程接口
    "workflow",
    
    # 独立 Agent 接口（所有10个agent，与 core.agents 对齐）
    "query_analyzer",
    "orchestrator",
    "draft_writer",
    "reviewer",
    "curriculum_designer",
    "quiz_master",
    "tool_specialist",
    "knowledge_manager",
    "socratic_guide",
    "memory_manager",
]
