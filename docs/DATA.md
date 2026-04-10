# 数据目录说明

所有运行时数据默认位于项目根目录下的 `data` 文件夹（可通过环境变量扩展，当前实现以 `edupilot.config.settings.Settings.data_dir` 为准，默认等于 `<项目根>/data`）。

## 目录结构

- `data/metadata/`
  - 存放**构建索引用的原始文本**（不要直接堆在 `data/` 根目录）。
  - 推荐：`data/metadata/<知识库ID>/knowledge.txt`，建库时会自动复制到 `data/knowledge_bases/<知识库ID>/knowledge.txt`（若后者尚不存在）。
  - 示例：`data/metadata/sanguo_sample.txt`，供接口 `use_sample=true` 时作为《三国演义》样例来源。

- `data/knowledge_bases/<知识库ID>/`
  - `knowledge.txt`：实际参与 GraphRAG 的文本副本（可由 metadata 自动拷贝或接口写入）。
  - `rag_workspace/`：nano_graphrag 工作目录，内含向量库、实体关系图 GraphML 等，可整体删除后重建索引。

- `data/sessions/<会话ID>.json`
  - 短期存储：单会话消息列表、本会话对话图谱（节点与边）、元数据。

- `data/users/<用户ID>/`
  - `long_term_graph.json`：长期合并后的用户图谱（来自多轮对话抽取结果的合并）。
  - `profile.json`：用户画像智能体输出。
  - `learning_plan.json`：学习计划智能体输出。

## 清理与备份

- 重建某一知识库索引：删除对应 `knowledge_bases/<ID>/rag_workspace` 后再调用索引接口。
- 备份：直接打包整个 `data` 目录即可。

## 安全

请勿将包含真实 API 密钥的 `.env` 或含隐私会话的 `data` 提交到公共仓库。
