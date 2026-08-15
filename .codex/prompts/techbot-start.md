---
description: "启动 Techbot 的需求分析、拆分、设计、开发与验收工作流"
argument-hint: "[需求描述]"
---

请启动需求交付工作流。用户输入的原始需求描述如下：

```text
$ARGUMENTS
```

1. 如果需求为空，先要求用户补充需求描述；不要创建文档或修改代码。
2. 使用 `demand-manager` 子代理并显式加载 `$demand-process` Skill。
3. 全程使用简体中文。需求涉及 UI 时，使用 `web-ui-generater` 和 `$web-ui` 在 `ui/<需求名>/` 生成可预览 UI，再让用户确认是否调整。
4. 需求确认后，将后台和 Android/前端需求分别保存至 `demand/<需求名>/后台需求/requirements.md` 和 `demand/<需求名>/前端需求/requirements.md`；不涉及的一端也要说明原因。
5. 按需求涉及端并行委派只读的 `server-code-analyzer` 和 `android-code-analyzer`，它们必须先读取 `.codex/demand-workflow/` 的对应配置；代码根目录为空或不可用时停止对应端流程。
6. 使用 `server-code-designer` 和 `android-code-designer` 提出可执行设计。存在多个方案或关键取舍时，比较影响、风险和推荐项并等待用户明确确认。
7. 仅在需求、UI（如有）和全部架构均确认后，才使用 `server-code-developer`、`android-code-developer` 实施。新增 Android UI 时加载 `$android-ui`。
8. 完成后汇报需求/架构产物路径、涉及文件、验证结果、未完成项和风险。
