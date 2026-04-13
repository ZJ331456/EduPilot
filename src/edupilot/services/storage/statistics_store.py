"""统计存储：系统监控数据，位于 data/statistics。"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from collections import defaultdict

from edupilot.config.settings import get_settings


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _utc_now_ms() -> int:
    """获取当前 UTC 时间戳（毫秒）。"""
    return int(time.time() * 1000)


class StatisticsStore:
    """统计存储：记录系统运行期间的各类指标。"""

    def __init__(self) -> None:
        self._root = get_settings().data_dir / "statistics"
        self._root.mkdir(parents=True, exist_ok=True)
        self._init_files()

    def _init_files(self) -> None:
        """初始化所有统计数据文件。"""
        # 全局统计
        self._global_path.touch(exist_ok=True)
        if not self._global_path.read_text(encoding="utf-8").strip():
            self._write_global({
                "total_requests": 0,
                "total_errors": 0,
                "total_sessions_created": 0,
                "total_sessions_ended": 0,
                "total_users": 0,
                "total_agents_executed": 0,
                "start_time": _utc_now_iso(),
                "last_updated": _utc_now_iso()
            })

        # API 统计
        self._api_stats_path.touch(exist_ok=True)
        if not self._api_stats_path.read_text(encoding="utf-8").strip():
            self._write_api_stats({})

        # 响应时间统计
        self._response_times_path.touch(exist_ok=True)
        if not self._response_times_path.read_text(encoding="utf-8").strip():
            self._write_response_times({"buckets": {}})

        # 错误统计
        self._errors_path.touch(exist_ok=True)
        if not self._errors_path.read_text(encoding="utf-8").strip():
            self._write_errors({"errors": [], "error_counts": {}})

        # 用户活跃度
        self._user_activity_path.touch(exist_ok=True)
        if not self._user_activity_path.read_text(encoding="utf-8").strip():
            self._write_user_activity({"users": {}})

        # Agent 执行统计
        self._agent_stats_path.touch(exist_ok=True)
        if not self._agent_stats_path.read_text(encoding="utf-8").strip():
            self._write_agent_stats({"agents": {}})

    @property
    def _global_path(self) -> Path:
        return self._root / "global.json"

    @property
    def _api_stats_path(self) -> Path:
        return self._root / "api_stats.json"

    @property
    def _response_times_path(self) -> Path:
        return self._root / "response_times.json"

    @property
    def _errors_path(self) -> Path:
        return self._root / "errors.json"

    @property
    def _user_activity_path(self) -> Path:
        return self._root / "user_activity.json"

    @property
    def _agent_stats_path(self) -> Path:
        return self._root / "agent_stats.json"

    def _write_global(self, data: Dict[str, Any]) -> None:
        data["last_updated"] = _utc_now_iso()
        self._global_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _write_api_stats(self, data: Dict[str, Any]) -> None:
        self._api_stats_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _write_response_times(self, data: Dict[str, Any]) -> None:
        self._response_times_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _write_errors(self, data: Dict[str, Any]) -> None:
        self._errors_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _write_user_activity(self, data: Dict[str, Any]) -> None:
        self._user_activity_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _write_agent_stats(self, data: Dict[str, Any]) -> None:
        self._agent_stats_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    # ==================== 全局统计 ====================

    def increment_request(self) -> None:
        """增加请求计数。"""
        data = json.loads(self._global_path.read_text(encoding="utf-8"))
        data["total_requests"] = data.get("total_requests", 0) + 1
        self._write_global(data)

    def increment_error(self) -> None:
        """增加错误计数。"""
        data = json.loads(self._global_path.read_text(encoding="utf-8"))
        data["total_errors"] = data.get("total_errors", 0) + 1
        self._write_global(data)

    def increment_session_created(self) -> None:
        """增加会话创建计数。"""
        data = json.loads(self._global_path.read_text(encoding="utf-8"))
        data["total_sessions_created"] = data.get("total_sessions_created", 0) + 1
        self._write_global(data)

    def increment_session_ended(self) -> None:
        """增加会话结束计数。"""
        data = json.loads(self._global_path.read_text(encoding="utf-8"))
        data["total_sessions_ended"] = data.get("total_sessions_ended", 0) + 1
        self._write_global(data)

    def add_user(self, user_id: str) -> None:
        """添加用户（如果不存在）。"""
        data = json.loads(self._global_path.read_text(encoding="utf-8"))
        known_users = set(data.get("known_users", []))
        if user_id not in known_users:
            known_users.add(user_id)
            data["known_users"] = list(known_users)
            data["total_users"] = len(known_users)
            self._write_global(data)

    def increment_agent_execution(self, agent_name: str) -> None:
        """增加 Agent 执行计数。"""
        data = json.loads(self._global_path.read_text(encoding="utf-8"))
        data["total_agents_executed"] = data.get("total_agents_executed", 0) + 1
        self._write_global(data)

    def get_global_stats(self) -> Dict[str, Any]:
        """获取全局统计。"""
        return json.loads(self._global_path.read_text(encoding="utf-8"))

    # ==================== API 统计 ====================

    def record_api_call(self, endpoint: str, method: str, status_code: int, 
                        response_time_ms: int) -> None:
        """记录 API 调用。"""
        data = json.loads(self._api_stats_path.read_text(encoding="utf-8"))
        
        # 初始化端点统计
        if endpoint not in data:
            data[endpoint] = {
                "total_calls": 0,
                "total_errors": 0,
                "total_response_time_ms": 0,
                "min_response_time_ms": float("inf"),
                "max_response_time_ms": 0,
                "methods": defaultdict(lambda: {"count": 0, "errors": 0}),
                "status_codes": defaultdict(int)
            }
        
        endpoint_stats = data[endpoint]
        endpoint_stats["total_calls"] += 1
        endpoint_stats["total_response_time_ms"] += response_time_ms
        endpoint_stats["min_response_time_ms"] = min(
            endpoint_stats["min_response_time_ms"], response_time_ms
        )
        endpoint_stats["max_response_time_ms"] = max(
            endpoint_stats["max_response_time_ms"], response_time_ms
        )
        
        # 记录方法统计
        if method not in endpoint_stats["methods"]:
            endpoint_stats["methods"][method] = {"count": 0, "errors": 0}
        endpoint_stats["methods"][method]["count"] += 1
        
        # 记录状态码
        endpoint_stats["status_codes"][str(status_code)] += 1
        
        # 记录错误
        if status_code >= 400:
            endpoint_stats["total_errors"] += 1
            endpoint_stats["methods"][method]["errors"] += 1
        
        # 转换为普通字典
        data[endpoint]["methods"] = dict(endpoint_stats["methods"])
        endpoint_stats["status_codes"] = dict(endpoint_stats["status_codes"])
        
        self._write_api_stats(data)

    def get_api_stats(self) -> Dict[str, Any]:
        """获取 API 统计。"""
        data = json.loads(self._api_stats_path.read_text(encoding="utf-8"))
        result = {}
        for endpoint, stats in data.items():
            result[endpoint] = {
                "total_calls": stats.get("total_calls", 0),
                "total_errors": stats.get("total_errors", 0),
                "total_response_time_ms": stats.get("total_response_time_ms", 0),
                "min_response_time_ms": stats.get("min_response_time_ms", 0),
                "max_response_time_ms": stats.get("max_response_time_ms", 0),
                "avg_response_time_ms": (
                    stats["total_response_time_ms"] / stats["total_calls"] 
                    if stats.get("total_calls", 0) > 0 else 0
                ),
                "methods": stats.get("methods", {}),
                "status_codes": stats.get("status_codes", {})
            }
        return result

    # ==================== 响应时间统计 ====================

    def record_response_time(self, endpoint: str, response_time_ms: int) -> None:
        """记录响应时间（用于直方图统计）。"""
        data = json.loads(self._response_times_path.read_text(encoding="utf-8"))
        
        if "buckets" not in data:
            data["buckets"] = {}
        
        if endpoint not in data["buckets"]:
            data["buckets"][endpoint] = {
                "times": [],
                "buckets": {
                    "0-100ms": 0,
                    "100-300ms": 0,
                    "300-500ms": 0,
                    "500-1000ms": 0,
                    "1-3s": 0,
                    "3-5s": 0,
                    ">5s": 0
                }
            }
        
        bucket_data = data["buckets"][endpoint]
        
        # 保存原始数据（限制数量）
        bucket_data["times"].append(response_time_ms)
        if len(bucket_data["times"]) > 1000:
            bucket_data["times"] = bucket_data["times"][-1000:]
        
        # 更新直方图
        if response_time_ms < 100:
            bucket_data["buckets"]["0-100ms"] += 1
        elif response_time_ms < 300:
            bucket_data["buckets"]["100-300ms"] += 1
        elif response_time_ms < 500:
            bucket_data["buckets"]["300-500ms"] += 1
        elif response_time_ms < 1000:
            bucket_data["buckets"]["500-1000ms"] += 1
        elif response_time_ms < 3000:
            bucket_data["buckets"]["1-3s"] += 1
        elif response_time_ms < 5000:
            bucket_data["buckets"]["3-5s"] += 1
        else:
            bucket_data["buckets"][">5s"] += 1
        
        self._write_response_times(data)

    def get_response_time_stats(self) -> Dict[str, Any]:
        """获取响应时间统计。"""
        return json.loads(self._response_times_path.read_text(encoding="utf-8"))

    # ==================== 错误统计 ====================

    def record_error(self, error_type: str, error_message: str, 
                     endpoint: Optional[str] = None, user_id: Optional[str] = None) -> None:
        """记录错误。"""
        data = json.loads(self._errors_path.read_text(encoding="utf-8"))
        
        # 添加错误记录
        error_record = {
            "timestamp": _utc_now_iso(),
            "error_type": error_type,
            "message": error_message[:500],  # 截断过长消息
            "endpoint": endpoint,
            "user_id": user_id
        }
        
        data["errors"].append(error_record)
        
        # 限制错误记录数量
        if len(data["errors"]) > 500:
            data["errors"] = data["errors"][-500:]
        
        # 更新错误计数
        if error_type not in data["error_counts"]:
            data["error_counts"][error_type] = 0
        data["error_counts"][error_type] += 1
        
        self._write_errors(data)

    def get_error_stats(self) -> Dict[str, Any]:
        """获取错误统计。"""
        return json.loads(self._errors_path.read_text(encoding="utf-8"))

    # ==================== 用户活跃度 ====================

    def record_user_activity(self, user_id: str, action: str) -> None:
        """记录用户活动。"""
        data = json.loads(self._user_activity_path.read_text(encoding="utf-8"))
        
        if user_id not in data["users"]:
            data["users"][user_id] = {
                "first_seen": _utc_now_iso(),
                "last_active": _utc_now_iso(),
                "total_actions": 0,
                "actions": defaultdict(int)
            }
        
        user_data = data["users"][user_id]
        user_data["last_active"] = _utc_now_iso()
        user_data["total_actions"] += 1
        user_data["actions"][action] = user_data["actions"].get(action, 0) + 1
        
        # 转换为普通字典
        data["users"][user_id]["actions"] = dict(user_data["actions"])
        
        self._write_user_activity(data)

    def get_user_activity(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """获取用户活跃度（可选指定用户）。"""
        data = json.loads(self._user_activity_path.read_text(encoding="utf-8"))
        
        if user_id:
            return data["users"].get(user_id, {})
        
        return data["users"]

    def get_active_users(self, hours: int = 24) -> List[str]:
        """获取最近 N 小时活跃的用户列表。"""
        data = json.loads(self._user_activity_path.read_text(encoding="utf-8"))
        
        cutoff = datetime.now(timezone.utc).timestamp() - (hours * 3600)
        active_users = []
        
        for user_id, user_data in data["users"].items():
            last_active = datetime.fromisoformat(
                user_data["last_active"].replace("Z", "+00:00")
            ).timestamp()
            if last_active >= cutoff:
                active_users.append(user_id)
        
        return active_users

    # ==================== Agent 执行统计 ====================

    def record_agent_execution(self, agent_name: str, execution_time_ms: int,
                               success: bool, mode: Optional[str] = None) -> None:
        """记录 Agent 执行。"""
        data = json.loads(self._agent_stats_path.read_text(encoding="utf-8"))
        
        if agent_name not in data["agents"]:
            data["agents"][agent_name] = {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "total_execution_time_ms": 0,
                "min_execution_time_ms": float("inf"),
                "max_execution_time_ms": 0,
                "modes": defaultdict(lambda: {"count": 0, "success": 0})
            }
        
        agent_data = data["agents"][agent_name]
        agent_data["total_executions"] += 1
        
        if success:
            agent_data["successful_executions"] += 1
        else:
            agent_data["failed_executions"] += 1
        
        agent_data["total_execution_time_ms"] += execution_time_ms
        agent_data["min_execution_time_ms"] = min(
            agent_data["min_execution_time_ms"], execution_time_ms
        )
        agent_data["max_execution_time_ms"] = max(
            agent_data["max_execution_time_ms"], execution_time_ms
        )
        
        # 记录模式统计
        if mode:
            if mode not in agent_data["modes"]:
                agent_data["modes"][mode] = {"count": 0, "success": 0}
            agent_data["modes"][mode]["count"] += 1
            if success:
                agent_data["modes"][mode]["success"] += 1
        
        # 转换为普通字典
        data["agents"][agent_name]["modes"] = dict(agent_data["modes"])
        
        self._write_agent_stats(data)

    def get_agent_stats(self) -> Dict[str, Any]:
        """获取 Agent 统计。"""
        data = json.loads(self._agent_stats_path.read_text(encoding="utf-8"))
        
        result = {}
        for agent_name, stats in data["agents"].items():
            total = stats.get("total_executions", 0)
            result[agent_name] = {
                "total_executions": total,
                "successful_executions": stats.get("successful_executions", 0),
                "failed_executions": stats.get("failed_executions", 0),
                "success_rate": (
                    stats["successful_executions"] / total * 100 
                    if total > 0 else 0
                ),
                "total_execution_time_ms": stats.get("total_execution_time_ms", 0),
                "min_execution_time_ms": stats.get("min_execution_time_ms", 0),
                "max_execution_time_ms": stats.get("max_execution_time_ms", 0),
                "avg_execution_time_ms": (
                    stats["total_execution_time_ms"] / total 
                    if total > 0 else 0
                ),
                "modes": stats.get("modes", {})
            }
        return result

    # ==================== 综合统计 ====================

    def get_full_statistics(self) -> Dict[str, Any]:
        """获取完整统计数据（所有子模块汇总）。"""
        return {
            "global": self.get_global_stats(),
            "api": self.get_api_stats(),
            "response_times": self.get_response_time_stats(),
            "errors": self.get_error_stats(),
            "user_activity": self.get_user_activity(),
            "agents": self.get_agent_stats(),
            "active_users_24h": self.get_active_users(hours=24),
            "active_users_7d": self.get_active_users(hours=24*7)
        }

    def reset_statistics(self) -> None:
        """重置所有统计数据（谨慎使用）。"""
        self._init_files()


# 全局单例
_statistics_store: Optional[StatisticsStore] = None


def get_statistics_store() -> StatisticsStore:
    """获取统计存储单例。"""
    global _statistics_store
    if _statistics_store is None:
        _statistics_store = StatisticsStore()
    return _statistics_store
