<template>
  <div class="knowledge-view">
    <!-- 🔍 搜索区域 - 白色清爽风格 -->
    <div class="search-hero">
      <div class="hero-content">
        <h1 class="hero-title">
          <el-icon class="hero-icon"><Search /></el-icon>
          探索知识海洋
        </h1>
        <p class="hero-subtitle">基于 GraphRAG 的智能知识检索系统</p>
        
        <!-- 主搜索框 -->
        <div class="search-box-container">
          <el-input
            v-model="searchQuery"
            size="large"
            placeholder="输入关键词，开始探索..."
            clearable
            @keyup.enter="searchKnowledge"
            class="hero-search-input"
          >
            <template #prefix>
              <el-icon class="search-prefix-icon"><Search /></el-icon>
            </template>
          </el-input>
          <el-button 
            type="primary" 
            size="large"
            @click="searchKnowledge"
            :loading="searching"
            class="hero-search-btn"
          >
            <el-icon v-if="!searching"><Search /></el-icon>
            {{ searching ? '搜索中...' : '搜索' }}
          </el-button>
        </div>

        <!-- 搜索选项 -->
        <div class="search-options">
          <div class="option-group">
            <el-icon><Filter /></el-icon>
            <span class="option-label">检索策略</span>
            <el-radio-group v-model="searchStrategy" size="small" class="strategy-radio">
              <el-radio-button value="hybrid">混合检索</el-radio-button>
              <el-radio-button value="semantic">语义检索</el-radio-button>
              <el-radio-button value="keyword">关键词</el-radio-button>
            </el-radio-group>
          </div>
          <el-select v-model="topK" size="small" class="top-k-select" style="width: 120px">
            <el-option label="5条结果" :value="5" />
            <el-option label="10条结果" :value="10" />
            <el-option label="15条结果" :value="15" />
            <el-option label="20条结果" :value="20" />
          </el-select>
        </div>
      </div>
    </div>

    <!-- 📊 搜索结果 -->
    <div class="content-section" v-if="searchResults.length > 0">
      <el-card class="clean-card results-card">
        <template #header>
          <div class="card-header-enhanced">
            <div class="header-left">
              <div class="header-icon-wrapper results-icon">
                <el-icon class="header-icon"><Document /></el-icon>
              </div>
              <div>
                <h3 class="card-title">搜索结果</h3>
                <p class="card-subtitle">找到 {{ searchResults.length }} 条相关内容</p>
              </div>
            </div>
            <div class="result-actions">
              <el-tag type="success" effect="light" size="small">
                <el-icon><Timer /></el-icon>
                {{ retrievalTime }}ms
              </el-tag>
              <el-button 
                size="small" 
                circle 
                @click="clearSearchResults"
                :icon="Refresh"
                title="清空结果"
              >
                <el-icon><Refresh /></el-icon>
              </el-button>
            </div>
          </div>
        </template>

        <div class="results-list">
          <div 
            v-for="(result, index) in searchResults" 
            :key="index"
            class="result-item"
          >
            <div class="result-number">{{ index + 1 }}</div>
            <div class="result-content-wrapper">
              <div class="result-header">
                <h3 class="result-title">
                  <el-icon><Reading /></el-icon>
                  {{ result.title || result.concept || '知识片段' }}
                </h3>
                <el-tag v-if="result.score" type="success" effect="plain" size="small">
                  {{ formatPercentage(result.score, 0) }}
                </el-tag>
              </div>
              
              <div class="result-content">
                {{ result.content || result.text }}
              </div>

              <div class="result-footer">
                <div class="footer-tags">
                  <el-tag size="small" type="info" effect="plain" v-if="result.source">
                    <el-icon><Files /></el-icon>
                    {{ result.source }}
                  </el-tag>
                </div>
                <el-button 
                  v-if="result.concept" 
                  size="small" 
                  type="primary"
                  text
                  @click="viewConcept(result.concept)"
                  class="view-detail-btn"
                >
                  查看详情
                  <el-icon><ArrowRight /></el-icon>
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 📚 知识库和相关概念 -->
    <el-row :gutter="24" class="content-section">
      <!-- 知识库列表 -->
      <el-col :xs="24" :lg="12">
        <el-card class="clean-card kb-card">
          <template #header>
            <div class="card-header-enhanced">
              <div class="header-left">
                <div class="header-icon-wrapper kb-icon">
                  <el-icon class="header-icon"><FolderOpened /></el-icon>
                </div>
                <div>
                  <h3 class="card-title">知识库</h3>
                  <p class="card-subtitle">{{ knowledgeBases.length }} 个可用知识库</p>
                </div>
              </div>
              <el-button 
                type="default"
                size="small" 
                circle
                @click="loadKnowledgeBases"
                :loading="loadingBases"
                class="refresh-btn"
                title="刷新知识库"
              >
                <el-icon><Refresh /></el-icon>
              </el-button>
            </div>
          </template>

          <div v-if="knowledgeBases.length > 0">
            <div class="kb-grid">
              <div
                v-for="(kb, index) in displayedKnowledgeBases"
                :key="index"
                class="kb-item"
                @click="toggleKB(kb.name)"
              >
                <div class="kb-item-icon">
                  <el-icon><Folder /></el-icon>
                </div>
                <div class="kb-item-content">
                  <h4 class="kb-item-name">{{ kb.name }}</h4>
                  <el-tag size="small" effect="plain" type="info">
                    {{ kb.size || '未知' }}
                  </el-tag>
                </div>
                <el-icon class="kb-arrow"><ArrowRight /></el-icon>
              </div>
            </div>
            
            <div v-if="knowledgeBases.length > kbDisplayLimit" class="kb-toggle-section">
              <el-button 
                @click="toggleShowAll" 
                class="toggle-all-btn"
                type="primary"
                link
              >
                {{ showAllKB ? '收起' : '查看全部' }}
              </el-button>
            </div>
          </div>
          <el-empty v-else description="暂无知识库" />
        </el-card>
      </el-col>

      <!-- 相关概念 -->
      <el-col :xs="24" :lg="12">
        <el-card class="clean-card concept-card">
          <template #header>
            <div class="card-header-enhanced">
              <div class="header-icon-wrapper concept-icon">
                <el-icon class="header-icon"><Connection /></el-icon>
              </div>
              <div>
                <h3 class="card-title">相关概念</h3>
                <p class="card-subtitle">概念关联与扩展</p>
              </div>
            </div>
          </template>

          <div v-if="selectedConcept" class="concept-content">
            <div class="concept-main">
              <div class="concept-header">
                <h3 class="concept-name">{{ selectedConcept.name }}</h3>
                <el-button size="small" circle @click="selectedConcept = null"><el-icon><Close /></el-icon></el-button>
              </div>
              
              <div class="concept-definition">
                <p class="definition-text">{{ selectedConcept.definition }}</p>
              </div>
            </div>

            <div v-if="relatedConcepts.length > 0" class="related-section">
              <h4 class="related-title">关联概念</h4>
              <div class="related-concepts-grid">
                <div
                  v-for="concept in relatedConcepts"
                  :key="concept.name"
                  @click="viewConcept(concept.name)"
                  class="concept-tag"
                >
                  {{ concept.name }}
                </div>
              </div>
            </div>
          </div>
          
          <!-- 推荐概念 -->
          <div v-else class="recommended-concepts-state">
            <h4 class="recommended-title">推荐概念</h4>
            <div class="recommended-concepts-grid">
              <div
                v-for="concept in recommendedConcepts"
                :key="concept.name"
                @click="viewConcept(concept.name)"
                class="recommended-concept-card"
              >
                <div class="concept-card-content">
                  <h5 class="concept-card-name">{{ concept.name }}</h5>
                  <span class="concept-category">{{ concept.category }}</span>
                </div>
                <el-icon class="concept-arrow"><ArrowRight /></el-icon>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 🔥 热门搜索 -->
    <el-row :gutter="24" class="content-section">
      <el-col :span="24">
        <el-card class="clean-card hot-search-card">
          <template #header>
            <div class="card-header-enhanced">
              <div class="header-left">
                <div class="header-icon-wrapper hot-icon">
                  <el-icon class="header-icon"><TrendCharts /></el-icon>
                </div>
                <div>
                  <h3 class="card-title">热门搜索</h3>
                </div>
              </div>
            </div>
          </template>
          <div class="hot-searches">
            <div
              v-for="(term, index) in hotSearches"
              :key="term"
              @click="searchWithTerm(term)"
              class="hot-tag"
            >
              <el-icon><Search /></el-icon>
              {{ term }}
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import {
  Search, Document, Reading, FolderOpened, Folder, Connection, TrendCharts,
  Filter, Promotion, Key, Timer, Files, ArrowRight, Refresh, ArrowDown, ArrowUp,
  Collection, Clock, Star, Link, View, Close
} from '@element-plus/icons-vue'
import { queryKnowledgeGraph } from '../api/edupilot'
import { showError, showSuccess, showWarning, showInfo, formatPercentage, safeGet } from '../utils'

const searchQuery = ref('')
const searchStrategy = ref('hybrid')
const topK = ref(10)
const searching = ref(false)
const searchResults = ref([])
const retrievalTime = ref(0)
const knowledgeBases = ref([])
const loadingBases = ref(false)
const expandedKB = ref(null)
const showAllKB = ref(false)
const kbDisplayLimit = 5
const selectedConcept = ref(null)
const relatedConcepts = ref([])

const recommendedConcepts = ref([
  { name: '大化改新', category: '政治改革' },
  { name: '律令制度', category: '制度' },
  { name: '幕府政治', category: '政权形式' },
  { name: '摄关政治', category: '政治制度' },
  { name: '古坟时代', category: '历史时期' },
  { name: '平安时代', category: '历史时期' },
  { name: '战国大名', category: '封建领主' },
  { name: '德川幕府', category: '政权' }
])

const displayedKnowledgeBases = computed(() => {
  if (showAllKB.value) {
    return knowledgeBases.value
  }
  return knowledgeBases.value.slice(0, kbDisplayLimit)
})

function toggleKB(kbName) {
  expandedKB.value = expandedKB.value === kbName ? null : kbName
}

function toggleShowAll() {
  showAllKB.value = !showAllKB.value
}

const hotSearches = [
  '大化改新', '古坟时代', '奈良时代', '平安时代', '镰仓幕府', '德川幕府', '明治维新'
]

async function searchKnowledge() {
  const query = searchQuery.value.trim()
  if (!query) {
    showWarning('请输入搜索关键词')
    return
  }
  if (searching.value) return

  searching.value = true
  const startTime = Date.now()

  try {
    const mode = searchStrategy.value === 'global' ? 'global' : searchStrategy.value === 'naive' ? 'naive' : 'local'
    const data = await queryKnowledgeGraph('sanguo', query, mode)

    searchResults.value = data.answer ? [{ content: data.answer, score: 1, source: 'GraphRAG' }] : []
    retrievalTime.value = Date.now() - startTime

    if (searchResults.value.length === 0) {
      showInfo('未找到相关结果')
    } else {
      showSuccess(`找到 ${searchResults.value.length} 条结果`)
    }
  } catch (error) {
    console.error('搜索失败:', error)
    showError(error, '搜索失败')
    searchResults.value = []
  } finally {
    searching.value = false
  }
}

function searchWithTerm(term) {
  searchQuery.value = term
  nextTick(() => searchKnowledge())
}

function clearSearchResults() {
  searchResults.value = []
  searchQuery.value = ''
  retrievalTime.value = 0
}

async function viewConcept(conceptName) {
  try {
    const data = await queryKnowledgeGraph('sanguo', `请简要解释概念：${conceptName}`, 'local')
    selectedConcept.value = {
      name: conceptName,
      definition: data.answer || '暂无定义'
    }
    relatedConcepts.value = []
  } catch (error) {
    console.error('获取概念详情失败:', error)
    showError(error, '获取概念详情失败')
  }
}

async function loadKnowledgeBases() {
  loadingBases.value = true
  try {
    knowledgeBases.value = [
      { id: 'sanguo', name: '三国演义（示例）', description: '原始文本见 data/metadata，索引见 data/knowledge_bases/sanguo' }
    ]
  } catch (error) {
    console.error('加载知识库失败', error)
    knowledgeBases.value = []
  } finally {
    loadingBases.value = false
  }
}

onMounted(() => {
  loadKnowledgeBases()
})
</script>

<style scoped>
.knowledge-view {
  max-width: 1400px;
  margin: 0 auto;
}

.content-section {
  margin-bottom: 24px;
}

/* 搜索区域 */
.search-hero {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-xl);
  padding: 48px 40px;
  margin-bottom: 28px;
  text-align: center;
}

.hero-title {
  font-size: 36px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
  letter-spacing: -0.5px;
}

.hero-icon {
  color: var(--text-secondary);
  font-size: 32px;
}

.hero-subtitle {
  color: var(--text-secondary);
  font-size: 15px;
  margin-bottom: 36px;
  font-weight: 400;
}

.search-box-container {
  max-width: 680px;
  margin: 0 auto 28px;
  display: flex;
  gap: 10px;
}

.hero-search-input {
  flex: 1;
}

.hero-search-btn {
  border-radius: var(--radius-md);
  padding: 0 32px;
  background: var(--text-primary);
  border: none;
  color: var(--bg-base);
  font-weight: 600;
  transition: all var(--transition-normal);
}

.hero-search-btn:hover {
  transform: translateY(-2px);
}

.search-options {
  display: flex;
  justify-content: center;
  gap: 20px;
  align-items: center;
  flex-wrap: wrap;
}

.option-group {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--text-secondary);
  font-size: 13px;
}

/* 卡片通用样式 */
.clean-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-xl);
  transition: all var(--transition-normal);
}

.clean-card:hover {
  border-color: var(--border-hover);
}

.clean-card :deep(.el-card__header) {
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
}

.card-header-enhanced {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-icon-wrapper {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-secondary);
  color: var(--text-secondary);
}

.results-icon, .kb-icon, .concept-icon, .hot-icon {
  background: var(--bg-secondary);
  color: var(--text-secondary);
}

.header-icon { font-size: 18px; }

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.card-subtitle {
  font-size: 12px;
  color: var(--text-muted);
  margin: 4px 0 0 0;
}

/* 搜索结果 */
.results-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.result-item {
  display: flex;
  gap: 14px;
  padding: 18px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  transition: all var(--transition-normal);
}

.result-item:hover {
  border-color: var(--border-hover);
}

.result-number {
  width: 28px;
  height: 28px;
  background: var(--text-primary);
  color: var(--bg-base);
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 13px;
  flex-shrink: 0;
}

.result-content-wrapper {
  flex: 1;
}

.result-title {
  margin: 0 0 8px 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 6px;
}

.result-content {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
  margin-bottom: 12px;
}

.result-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 10px;
  border-top: 1px solid var(--border-color);
}

.result-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* 知识库 */
.kb-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 10px;
  margin-bottom: 14px;
}

.kb-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all var(--transition-normal);
}

.kb-item:hover {
  border-color: var(--border-hover);
}

.kb-item-icon {
  color: var(--text-secondary);
  font-size: 18px;
}

.kb-item-content {
  flex: 1;
}

.kb-item-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 2px 0;
}

.kb-arrow {
  color: var(--text-ghost);
  font-size: 12px;
  transition: all var(--transition-fast);
}

.kb-item:hover .kb-arrow {
  transform: translateX(3px);
  color: var(--text-secondary);
}

.kb-toggle-section {
  text-align: center;
  padding-top: 6px;
}

.toggle-all-btn {
  font-size: 12px;
  color: var(--text-secondary);
}

/* 刷新按钮样式 */
.refresh-btn {
  background: var(--bg-secondary) !important;
  border: 1px solid var(--border-color) !important;
  color: var(--text-secondary) !important;
  transition: all var(--transition-fast);
}

.refresh-btn:hover:not(:disabled) {
  background: var(--text-primary) !important;
  border-color: var(--text-primary) !important;
  color: var(--bg-base) !important;
}

.refresh-btn.is-loading {
  background: var(--bg-secondary) !important;
  border-color: var(--border-color) !important;
  color: var(--text-secondary) !important;
}

/* 概念区域 */
.concept-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.concept-name {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
}

.definition-text {
  color: var(--text-secondary);
  line-height: 1.7;
  background: var(--bg-secondary);
  padding: 18px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
  font-size: 13px;
}

.related-section {
  margin-top: 20px;
}

.related-title, .recommended-title {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-muted);
  margin-bottom: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.related-concepts-grid, .recommended-concepts-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.concept-tag {
  padding: 6px 14px;
  background: var(--bg-secondary);
  color: var(--text-secondary);
  border-radius: var(--radius-sm);
  font-size: 12px;
  cursor: pointer;
  transition: all var(--transition-fast);
  border: 1px solid var(--border-color);
}

.concept-tag:hover {
  background: var(--text-primary);
  color: var(--bg-base);
  border-color: var(--text-primary);
}

.recommended-concept-card {
  flex: 1 0 45%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all var(--transition-normal);
}

.recommended-concept-card:hover {
  border-color: var(--border-hover);
}

.concept-card-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.concept-category {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 2px;
}

.concept-arrow {
  color: var(--text-ghost);
  transition: all var(--transition-fast);
}

.recommended-concept-card:hover .concept-arrow {
  color: var(--text-secondary);
  transform: translateX(3px);
}

/* 热门搜索 */
.hot-searches {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.hot-tag {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 8px 16px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-full);
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all var(--transition-normal);
}

.hot-tag:hover {
  background: var(--text-primary);
  color: var(--bg-base);
  border-color: var(--text-primary);
}

/* 响应式 */
@media (max-width: 768px) {
  .search-hero {
    padding: 36px 20px;
    border-radius: var(--radius-lg);
  }
  
  .hero-title {
    font-size: 26px;
  }
  
  .search-box-container {
    flex-direction: column;
  }
  
  .hero-search-btn {
    width: 100%;
  }
}
</style>