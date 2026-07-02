---
name: web-ui
description: This skill should be used by web-ui-generater to generate, refine, and document a Web UI from confirmed UI requirements, including layout, style, interactions, component states, and final files under the demand-specific ui directory.
---

# Web UI

## Overview

生成需求对应的 Web UI，用于让用户在研发前确认页面结构、视觉风格、交互流程和关键状态，并作为后续 Android UI 生成的参考输入。

## Input Requirements

生成时参考以下信息：

1. 页面目标和用户角色
2. 页面信息架构和核心内容
3. 主要操作和交互流程
4. 页面状态：默认态、加载态、空态、错误态、禁用态、成功/失败反馈
5. 视觉风格：色彩、字体、圆角、间距、阴影、图标、品牌倾向
6. 适配要求：移动端、桌面端、响应式、深色模式等
7. 需要复用或对齐的现有 UI 风格

如关键信息缺失，直接基于需求上下文和常见最佳实践做出合理假设并继续生成，不向用户提问；在 `ui-spec.md` 中记录这些默认假设。

## Generation Workflow

1. 梳理 UI 需求，形成 `ui-spec`。
2. 设计页面结构、组件层级和交互状态。
3. 直接生成可预览的 Web UI，优先使用单文件 `index.html`，包含 HTML、CSS 和必要的轻量 JavaScript。
4. 直接保存产物到 `ui/<当前需求名称>/`，无需在生成前征求用户同意。
5. 记录关键默认假设，供后续向用户展示时说明。

## Output Files

最终至少输出：

- `ui/<当前需求名称>/index.html`
- `ui/<当前需求名称>/ui-spec.md`

`ui-spec.md` 必须包含：

- UI 目标
- 页面结构
- 组件说明
- 交互说明
- 状态说明
- 视觉风格
- 关键默认假设
- 给 `android-ui` Skill 的实现参考

## Quality Bar

- 页面层级清晰，主操作突出。
- 风格与需求描述一致。
- 覆盖关键状态和异常场景。
- 文案可读，布局适合移动端转换。
- 不引入外部不可控依赖；如使用 CDN，需说明替代方案。
