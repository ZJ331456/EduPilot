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
                找到 {{ searchResults.length }} 条相关内容</p>
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

/* 搜索区域 - 黑白极简 */
.search-hero {
  background: #ffffff;
  border: 1px solid #e5e5e5;
  border-radius: 24px;
  padding: 60px 40px;
  margin-bottom: 32px;
  text-align: center;
}

.hero-title {
  font-size: 42px;
  font-weight: 800;
  color: #000000;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  letter-spacing: -1px;
}

.hero-icon {
  color: #000000;
  font-size: 36px;
}

.hero-subtitle {
  color: #666666;
  font-size: 16px;
  margin-bottom: 40px;
  font-weight: 400;
}

.search-box-container {
  max-width: 700px;
  margin: 0 auto 32px;
  display: flex;
  gap: 12px;
}

.hero-search-input {
  flex: 1;
}

.hero-search-input :deep(.el-input__wrapper) {
  border-radius: 14px;
  padding: 8px 12px;
  border: 2px solid #e5e5e5;
  box-shadow: none;
  transition: all 0.2s ease;
}

.hero-search-input :deep(.el-input__wrapper):hover {
  border-color: #cccccc;
}

.hero-search-input :deep(.el-input__wrapper.is-focus) {
  border-color: #000000;
  box-shadow: none;
}

.hero-search-btn {
  border-radius: 14px;
  padding: 0 40px;
  background: #000000;
  border: none;
  font-weight: 600;
  transition: all 0.2s ease;
}

.hero-search-btn:hover {
  background: #1a1a1a;
  transform: translateY(-1px);
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
  color: #666666;
  font-size: 14px;
}

.strategy-radio :deep(.el-radio-button__inner) {
  border-radius: 8px;
  border: 1px solid #e5e5e5;
  background: #fafafa;
  color: #666666;
}

.strategy-radio :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: #000000;
  border-color: #000000;
  color: #ffffff;
}

/* 卡片通用样式 - 极简风 */
.clean-card {
  background: #ffffff;
  border: 1px solid #e5e5e5;
  border-radius: 20px;
  transition: all 0.25s ease;
}

.clean-card:hover {
  border-color: #cccccc;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.06);
}

.clean-card :deep(.el-card__header) {
  padding: 20px 24px;
  border-bottom: 1px solid #f0f0f0;
}

.card-header-enhanced {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.header-icon-wrapper {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f5;
  color: #333333;
}

.results-icon, .kb-icon, .concept-icon, .hot-icon {
  background: #f5f5f5;
  color: #333333;
}

.header-icon { font-size: 20px; }

.card-title {
  font-size: 16px;
  font-weight: 700;
  color: #000000;
  margin: 0;
}

.card-subtitle {
  font-size: 13px;
  color: #888888;
  margin: 4px 0 0 0;
}

/* 搜索结果 */
.results-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.result-item {
  display: flex;
  gap: 16px;
  padding: 20px;
  border: 1px solid #f0f0f0;
  border-radius: 16px;
  background: #fafafa;
  transition: all 0.2s ease;
}

.result-item:hover {
  background: #ffffff;
  border-color: #000000;
}

.result-number {
  width: 32px;
  height: 32px;
  background: #000000;
  color: #ffffff;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
  flex-shrink: 0;
}

.result-content-wrapper {
  flex: 1;
}

.result-title {
  margin: 0 0 10px 0;
  font-size: 15px;
  font-weight: 600;
  color: #000000;
  display: flex;
  align-items: center;
  gap: 8px;
}

.result-content {
  font-size: 14px;
  color: #666666;
  line-height: 1.7;
  margin-bottom: 14px;
}

.result-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 14px;
  border-top: 1px solid #f0f0f0;
}

/* 知识库 */
.kb-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.kb-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: #fafafa;
  border: 1px solid #f0f0f0;
  border-radius: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.kb-item:hover {
  background: #ffffff;
  border-color: #000000;
}

.kb-item-icon {
  color: #333333;
  font-size: 20px;
}

.kb-item-content {
  flex: 1;
}

.kb-item-name {
  font-size: 14px;
  font-weight: 600;
  color: #000000;
  margin: 0 0 4px 0;
}

.kb-arrow {
  color: #cccccc;
  font-size: 14px;
  transition: all 0.2s ease;
}

.kb-item:hover .kb-arrow {
  transform: translateX(4px);
  color: #000000;
}

.kb-toggle-section {
  text-align: center;
  padding-top: 8px;
}

.toggle-all-btn {
  font-size: 13px;
  color: #666666;
}

/* 概念区域 */
.concept-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.concept-name {
  font-size: 22px;
  font-weight: 800;
  color: #000000;
}

.definition-text {
  color: #555555;
  line-height: 1.8;
  background: #fafafa;
  padding: 20px;
  border-radius: 14px;
  border: 1px solid #f0f0f0;
  font-size: 14px;
}

.related-section {
  margin-top: 24px;
}

.related-title, .recommended-title {
  font-size: 12px;
  font-weight: 700;
  color: #888888;
  margin-bottom: 14px;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.related-concepts-grid, .recommended-concepts-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.concept-tag {
  padding: 8px 16px;
  background: #f5f5f5;
  color: #555555;
  border-radius: 8px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.concept-tag:hover {
  background: #000000;
  color: #ffffff;
}

.recommended-concept-card {
  flex: 1 0 45%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  background: #fafafa;
  border: 1px solid #f0f0f0;
  border-radius: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.recommended-concept-card:hover {
  border-color: #000000;
  background: #ffffff;
}

.concept-card-name {
  font-size: 14px;
  font-weight: 600;
  color: #000000;
  margin: 0;
}

.concept-category {
  font-size: 12px;
  color: #999999;
  margin-top: 2px;
}

.concept-arrow {
  color: #cccccc;
  transition: all 0.2s ease;
}

.recommended-concept-card:hover .concept-arrow {
  color: #000000;
  transform: translateX(4px);
}

/* 热门搜索 */
.hot-searches {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.hot-tag {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 18px;
  background: #fafafa;
  border: 1px solid #f0f0f0;
  border-radius: 24px;
  color: #666666;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.hot-tag:hover {
  background: #000000;
  border-color: #000000;
  color: #ffffff;
}

/* 响应式 */
@media (max-width: 768px) {
  .search-hero {
    padding: 40px 20px;
    border-radius: 20px;
  }
  
  .hero-title {
    font-size: 28px;
  }
  
  .search-box-container {
    flex-direction: column;
  }
  
  .hero-search-btn {
    width: 100%;
  }
}
</style>