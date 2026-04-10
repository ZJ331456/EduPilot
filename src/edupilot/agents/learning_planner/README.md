# learning_planner 智能体

## 作用

读取用户画像与可选学习目标说明，生成周粒度学习计划 JSON，保存为 `data/users/<用户ID>/learning_plan.json`。

## 输入

画像对象与 `goal_hint` 字符串。

## 提示词

`prompts/zh/prompts.yaml` 中约束了周计划与可检验检查点，可按培训场景改写。
