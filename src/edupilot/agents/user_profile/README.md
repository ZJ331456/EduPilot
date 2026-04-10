# user_profile 智能体

## 作用

根据会话摘要与图谱摘要生成结构化用户画像，写入 `data/users/<用户ID>/profile.json`。

## 输出 JSON 键

`learning_style`、`strengths`、`gaps`、`interests`、`recommended_focus`、`risk_notes` 等，具体以 `prompts/zh/prompts.yaml` 为准。

## 调用方式

HTTP `POST /api/v1/profile/analyze`，请求体可带 `session_id` 以自动拼接近期会话。
