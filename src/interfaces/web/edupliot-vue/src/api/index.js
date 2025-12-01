/**
 * EduPilot API 主入口
 * 严格对齐后端 API 结构 (@routers)
 * 
 * 架构对齐说明：
 * ============
 * Frontend API              Backend Router              Core Module
 * ─────────────────────────────────────────────────────────────────
 * api/workflow              /workflow/                  core.workflow
 * api/query-analyzer        /query-analyzer/            core.agents.query_analyzer
 * api/orchestrator          /orchestrator/              core.agents.orchestrator
 * api/draft-writer          /draft-writer/              core.agents.draft_writer
 * api/reviewer              /reviewer/                  core.agents.reviewer
 * api/curriculum-designer   /curriculum-designer/       core.agents.curriculum_designer
 * api/quiz-master           /quiz-master/               core.agents.quiz_master
 * api/tool-specialist       /tool-specialist/          core.agents.tool_specialist
 * api/knowledge-retriever   /knowledge-manager/         core.agents.knowledge_manager
 * api/socratic-guide        /socratic-guide/            core.agents.socratic_guide
 * api/memory-manager        /memory-manager/            core.agents.memory_manager
 * api/system                /                          系统接口
 * 
 * 使用建议：
 * =========
 * ✅ 生产环境：优先使用 workflow API
 * ⚠️ 数据查询：使用 knowledgeRetriever 和 memoryManager API
 * 🔧 开发调试：使用独立的 agent API
 */

// 导入所有 API 模块（与后端 routers 完全对齐）
import workflow from './workflow'
import queryAnalyzer from './query-analyzer'
import orchestrator from './orchestrator'
import draftWriter from './draft-writer'
import reviewer from './reviewer'
import curriculumDesigner from './curriculum-designer'
import quizMaster from './quiz-master'
import toolSpecialist from './tool-specialist'
import knowledgeRetriever from './knowledge-retriever'
import socraticGuide from './socratic-guide'
import memoryManager from './memory-manager'
import system from './system'

// 导出统一的 API 对象（与后端 routers 完全对齐）
export const api = {
  // 主流程接口（推荐使用）
  workflow,
  
  // 独立 Agent 接口（调试用，与后端 routers 对齐）
  queryAnalyzer,
  orchestrator,
  draftWriter,
  reviewer,
  curriculumDesigner,
  quizMaster,
  toolSpecialist,
  knowledgeRetriever,
  socraticGuide,
  memoryManager,
  
  // 系统接口
  system,
  
  // 常用系统方法快捷访问
  health: system.health,
  stats: system.stats,
  performanceStats: system.performanceStats,
  cacheStats: system.cacheStats,
  clearCache: system.clearCache
}

// 默认导出
export default api
