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
            <span class="option-label">检索策略:</span>
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
            <div class="result-stats">
              <el-tag type="success" effect="light" size="small">
                <el-icon><Timer /></el-icon>
                {{ retrievalTime }}ms
              </el-tag>
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
                type="primary"
                size="small" 
                plain
                @click="loadKnowledgeBases"
                :loading="loadingBases"
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
import api from '../api'
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
    const data = await api.knowledgeRetriever.retrieve({
      query,
      top_k: topK.value,
      retrieval_strategy: searchStrategy.value
    })

    searchResults.value = data.results || []
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

async function viewConcept(conceptName) {
  try {
    const data = await api.knowledgeRetriever.getConcept(conceptName)
    selectedConcept.value = {
      name: conceptName,
      definition: safeGet(data, 'data.definition', '暂无定义')
    }
    const relatedData = await api.knowledgeRetriever.getRelated(conceptName, { limit: 10 })
    relatedConcepts.value = safeGet(relatedData, 'data.related_concepts', [])
  } catch (error) {
    console.error('获取概念详情失败:', error)
    showError(error, '获取概念详情失败')
  }
}

async function loadKnowledgeBases() {
  loadingBases.value = true
  try {
    const data = await api.knowledgeRetriever.listBases()
    knowledgeBases.value = safeGet(data, 'data.knowledge_bases', [])
  } catch (error) {
    console.error('加载知识库失败:', error)
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

/* 搜索英雄区域 */
.search-hero {
  background: linear-gradient(180deg, #f9fafb 0%, #ffffff 100%);
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  padding: 48px 32px;
  margin-bottom: 32px;
  text-align: center;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

.hero-title {
  font-size: 32px;
  font-weight: 700;
  color: #111827;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.hero-icon {
  color: #4f46e5;
}

.hero-subtitle {
  color: #6b7280;
  font-size: 16px;
  margin-bottom: 32px;
}

.search-box-container {
  max-width: 700px;
  margin: 0 auto 24px;
  display: flex;
  gap: 12px;
}

.hero-search-input {
  flex: 1;
}

.hero-search-input :deep(.el-input__wrapper) {
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  border-radius: 8px;
}

.hero-search-btn {
  border-radius: 8px;
  padding: 0 32px;
  background-color: #4f46e5;
  border-color: #4f46e5;
}

.search-options {
  display: flex;
  justify-content: center;
  gap: 24px;
  align-items: center;
  flex-wrap: wrap;
}

.option-group {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #4b5563;
  font-size: 14px;
}

/* 卡片通用样式 */
.clean-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  transition: all 0.3s ease;
}

.clean-card:hover {
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  border-color: #d1d5db;
}

.clean-card :deep(.el-card__header) {
  padding: 16px 24px;
  border-bottom: 1px solid #f3f4f6;
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
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.results-icon { background: #eff6ff; color: #3b82f6; }
.kb-icon { background: #ecfdf5; color: #10b981; }
.concept-icon { background: #f5f3ff; color: #8b5cf6; }
.hot-icon { background: #fff7ed; color: #f97316; }

.header-icon { font-size: 20px; }

.card-title {
  font-size: 16px;
  font-weight: 700;
  color: #111827;
  margin: 0;
}

.card-subtitle {
  font-size: 12px;
  color: #6b7280;
  margin: 2px 0 0 0;
}

/* 搜索结果 */
.results-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.result-item {
  display: flex;
  gap: 16px;
  padding: 20px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: #f9fafb;
  transition: all 0.2s;
}

.result-item:hover {
  background: #ffffff;
  border-color: #4f46e5;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.result-number {
  width: 28px;
  height: 28px;
  background: #4f46e5;
  color: white;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
  flex-shrink: 0;
}

.result-content-wrapper {
  flex: 1;
}

.result-title {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  display: flex;
  align-items: center;
  gap: 8px;
}

.result-content {
  font-size: 14px;
  color: #4b5563;
  line-height: 1.6;
  margin-bottom: 12px;
}

.result-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px solid #e5e7eb;
  padding-top: 12px;
}

/* 知识库 */
.kb-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.kb-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.kb-item:hover {
  background: #ffffff;
  border-color: #10b981;
  transform: translateY(-2px);
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.kb-item-icon {
  color: #10b981;
  font-size: 20px;
}

.kb-item-content {
  flex: 1;
}

.kb-item-name {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
  margin: 0 0 4px 0;
}

.kb-arrow {
  color: #9ca3af;
  font-size: 14px;
}

/* 概念区域 */
.concept-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.concept-name {
  font-size: 20px;
  font-weight: 700;
  color: #111827;
}

.definition-text {
  color: #4b5563;
  line-height: 1.6;
  background: #f9fafb;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.related-section {
  margin-top: 20px;
}

.related-title, .recommended-title {
  font-size: 14px;
  font-weight: 600;
  color: #6b7280;
  margin-bottom: 12px;
}

.related-concepts-grid, .recommended-concepts-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.concept-tag {
  padding: 6px 12px;
  background: #f3f4f6;
  color: #4b5563;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.concept-tag:hover {
  background: #eef2ff;
  color: #4f46e5;
}

.recommended-concept-card {
  flex: 1 0 45%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.recommended-concept-card:hover {
  border-color: #8b5cf6;
  background: #ffffff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.concept-card-name {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
  margin: 0;
}

.concept-category {
  font-size: 12px;
  color: #9ca3af;
}

.concept-arrow {
  color: #9ca3af;
}

/* 热门搜索 */
.hot-searches {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.hot-tag {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 20px;
  color: #4b5563;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.hot-tag:hover {
  background: #fff7ed;
  border-color: #fdba74;
  color: #ea580c;
}

/* 响应式 */
@media (max-width: 768px) {
  .search-hero {
    padding: 32px 16px;
  }
  
  .hero-title {
    font-size: 24px;
  }
  
  .search-box-container {
    flex-direction: column;
  }
  
  .hero-search-btn {
    width: 100%;
  }
}
</style>
