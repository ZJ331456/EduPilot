#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EduPilot API 客户端使用示例
演示如何使用各个API接口
"""

import requests
import json
from typing import Dict, Any


class EduPilotAPIClient:
    """EduPilot API 客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_prefix = "/api/agent/v1"
        self.session = requests.Session()
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """发送HTTP请求"""
        url = f"{self.base_url}{self.api_prefix}{endpoint}"
        response = self.session.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()
    
    # ========================================================================
    # 基础接口
    # ========================================================================
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return self._make_request("GET", "/health")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取系统统计"""
        return self._make_request("GET", "/stats")
    
    # ========================================================================
    # 工作流接口
    # ========================================================================
    
    def start_session(
        self,
        user_id: str,
        query: str,
        session_id: str = None,
        workflow_config: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """启动学习会话"""
        return self._make_request(
            "POST",
            "/workflow/session/start",
            json={
                "user_id": user_id,
                "query": query,
                "session_id": session_id,
                "workflow_config": workflow_config or {},
            }
        )
    
    def continue_session(
        self,
        session_id: str,
        user_id: str,
        user_response: str,
    ) -> Dict[str, Any]:
        """继续学习会话"""
        return self._make_request(
            "POST",
            "/workflow/session/continue",
            json={
                "session_id": session_id,
                "user_id": user_id,
                "user_response": user_response,
            }
        )
    
    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """获取会话信息"""
        return self._make_request("GET", f"/workflow/session/{session_id}")
    
    def end_session(self, session_id: str) -> Dict[str, Any]:
        """结束会话"""
        return self._make_request("DELETE", f"/workflow/session/{session_id}")
    
    def get_active_sessions(self) -> Dict[str, Any]:
        """获取活跃会话"""
        return self._make_request("GET", "/workflow/sessions/active")
    
    # ========================================================================
    # 智能体接口
    # ========================================================================
    
    def analyze_query(
        self,
        query: str,
        user_id: str = None,
        session_id: str = None,
        use_llm_refinement: bool = True,
    ) -> Dict[str, Any]:
        """查询分析"""
        return self._make_request(
            "POST",
            "/agents/query-analyzer",
            json={
                "query": query,
                "user_id": user_id,
                "session_id": session_id,
                "use_llm_refinement": use_llm_refinement,
            }
        )
    
    def create_plan(
        self,
        query: str,
        query_type: str = None,
        retrieved_knowledge: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """创建学习计划"""
        return self._make_request(
            "POST",
            "/agents/planner",
            json={
                "query": query,
                "query_type": query_type,
                "retrieved_knowledge": retrieved_knowledge,
            }
        )
    
    def execute_plan(
        self,
        query: str,
        plan: Dict[str, Any],
        retrieved_knowledge: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """执行计划"""
        return self._make_request(
            "POST",
            "/agents/executor",
            json={
                "query": query,
                "plan": plan,
                "retrieved_knowledge": retrieved_knowledge,
            }
        )
    
    def get_socratic_guidance(
        self,
        user_query: str,
        user_response: str = None,
        knowledge_context: Dict[str, Any] = None,
        guidance_level: str = "moderate",
    ) -> Dict[str, Any]:
        """获取苏格拉底引导"""
        return self._make_request(
            "POST",
            "/agents/socratic-guide",
            json={
                "user_query": user_query,
                "user_response": user_response,
                "knowledge_context": knowledge_context,
                "guidance_level": guidance_level,
            }
        )
    
    # ========================================================================
    # 记忆管理接口
    # ========================================================================
    
    def get_user_profile(
        self,
        user_id: str,
        include_triples: bool = False,
        include_emotions: bool = False,
        include_patterns: bool = False,
    ) -> Dict[str, Any]:
        """获取用户画像"""
        return self._make_request(
            "GET",
            f"/memory/profile/{user_id}",
            params={
                "include_triples": include_triples,
                "include_emotions": include_emotions,
                "include_patterns": include_patterns,
            }
        )
    
    def get_session_memory(self, session_id: str, user_id: str = None) -> Dict[str, Any]:
        """获取会话记忆"""
        params = {"user_id": user_id} if user_id else {}
        return self._make_request("GET", f"/memory/session/{session_id}", params=params)
    
    def get_knowledge_graph(self, user_id: str) -> Dict[str, Any]:
        """获取知识图谱"""
        return self._make_request("GET", f"/memory/knowledge-graph/{user_id}")
    
    # ========================================================================
    # 知识检索接口
    # ========================================================================
    
    def retrieve_knowledge(
        self,
        query: str,
        top_k: int = 5,
        retrieval_strategy: str = "hybrid",
    ) -> Dict[str, Any]:
        """检索知识"""
        return self._make_request(
            "POST",
            "/knowledge/retrieve",
            json={
                "query": query,
                "top_k": top_k,
                "retrieval_strategy": retrieval_strategy,
            }
        )
    
    def get_concept_details(self, concept_name: str) -> Dict[str, Any]:
        """获取概念详情"""
        return self._make_request("GET", f"/knowledge/concept/{concept_name}")
    
    def get_related_concepts(self, concept_name: str, limit: int = 10) -> Dict[str, Any]:
        """获取相关概念"""
        return self._make_request(
            "GET",
            f"/knowledge/related/{concept_name}",
            params={"limit": limit}
        )
    
    def list_knowledge_bases(self) -> Dict[str, Any]:
        """获取知识库列表"""
        return self._make_request("GET", "/knowledge/bases")
    
    def get_search_suggestions(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """获取搜索建议"""
        return self._make_request(
            "GET",
            "/knowledge/suggestions",
            params={"query": query, "limit": limit}
        )


# ============================================================================
# 使用示例
# ============================================================================

def print_response(title: str, response: Dict[str, Any]):
    """打印响应"""
    print(f"\n{'='*60}")
    print(f"📌 {title}")
    print('='*60)
    print(json.dumps(response, indent=2, ensure_ascii=False))


def example_complete_workflow():
    """示例: 完整学习会话工作流"""
    print("\n🎯 示例 1: 完整学习会话工作流")
    print("-" * 60)
    
    client = EduPilotAPIClient()
    
    # 1. 健康检查
    health = client.health_check()
    print_response("健康检查", health)
    
    # 2. 启动学习会话
    session = client.start_session(
        user_id="demo_user",
        query="什么是大化改新？",
        workflow_config={
            "enable_socratic": True,
            "enable_learning": True,
        }
    )
    print_response("启动学习会话", session)
    
    session_id = session["session_id"]
    
    # 3. 继续会话
    continued = client.continue_session(
        session_id=session_id,
        user_id="demo_user",
        user_response="可以详细解释一下背景吗？"
    )
    print_response("继续会话", continued)
    
    # 4. 结束会话
    ended = client.end_session(session_id)
    print_response("结束会话", ended)


def example_individual_agents():
    """示例: 单独调用各个智能体"""
    print("\n🎯 示例 2: 单独调用智能体")
    print("-" * 60)
    
    client = EduPilotAPIClient()
    
    # 1. 查询分析
    analysis = client.analyze_query(
        query="大化改新的历史意义是什么？",
        user_id="demo_user"
    )
    print_response("查询分析", analysis)
    
    # 2. 创建计划
    plan = client.create_plan(
        query="大化改新的历史意义是什么？",
        query_type="concept_explanation"
    )
    print_response("创建学习计划", plan)
    
    # 3. 苏格拉底引导
    guidance = client.get_socratic_guidance(
        user_query="什么是大化改新？",
        guidance_level="moderate"
    )
    print_response("苏格拉底引导", guidance)


def example_knowledge_retrieval():
    """示例: 知识检索"""
    print("\n🎯 示例 3: 知识检索")
    print("-" * 60)
    
    client = EduPilotAPIClient()
    
    # 1. 检索知识
    results = client.retrieve_knowledge(
        query="大化改新",
        top_k=3,
        retrieval_strategy="hybrid"
    )
    print_response("知识检索", results)
    
    # 2. 获取概念详情
    concept = client.get_concept_details("大化改新")
    print_response("概念详情", concept)
    
    # 3. 获取相关概念
    related = client.get_related_concepts("大化改新", limit=5)
    print_response("相关概念", related)
    
    # 4. 搜索建议
    suggestions = client.get_search_suggestions("大化", limit=5)
    print_response("搜索建议", suggestions)


def example_memory_management():
    """示例: 记忆管理"""
    print("\n🎯 示例 4: 记忆管理")
    print("-" * 60)
    
    client = EduPilotAPIClient()
    
    # 1. 获取用户画像
    profile = client.get_user_profile(
        user_id="demo_user",
        include_triples=True,
        include_emotions=True,
        include_patterns=True
    )
    print_response("用户画像", profile)
    
    # 2. 获取知识图谱
    graph = client.get_knowledge_graph("demo_user")
    print_response("知识图谱", graph)


def main():
    """主函数"""
    print("=" * 60)
    print("🚀 EduPilot API 客户端使用示例")
    print("=" * 60)
    print("\n请确保API服务器已启动: python run_api_server.py")
    print("默认地址: http://localhost:8000")
    
    try:
        # 运行各个示例
        example_complete_workflow()
        # example_individual_agents()
        # example_knowledge_retrieval()
        # example_memory_management()
        
    except requests.exceptions.ConnectionError:
        print("\n❌ 错误: 无法连接到API服务器")
        print("请先启动服务器: python run_api_server.py")
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

