# dialogue_graph 智能体

## 作用

从一段中文多轮对话中抽取实体与有向关系，输出 JSON，供会话级图谱与长期用户图谱合并。

## 实现说明

抽取逻辑在 `edupilot.services.graph.dialogue_graph_service` 中调用本目录下的中文提示词；本目录仅保留 `prompts/zh/prompts.yaml` 便于与 DeepTutor 风格一致地独立维护。

## 输出格式

模型需输出包含 `nodes` 与 `edges` 的 JSON，字段约定见 YAML 内说明。
