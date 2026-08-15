---
name: android-ui
description: 此 Skill 用于当前需求存在已确认 Web UI 时，将其映射为符合现有 Android 工程技术栈、组件体系和视觉规范的 Android UI 实现方案。存在未决 UI 选择时必须先确认。
---

# Android UI

## 前置输入

读取：

1. `ui/<需求名>/index.html` 或 `ui-spec.md`；
2. `demand/<需求名>/前端需求/requirements.md`；
3. `architecture/<需求名>/client/architecture.md`；
4. Android 代码分析结论；
5. 工程中相似页面、主题、组件、资源命名和布局写法。

Web UI 不存在或未确认时停止。

## 流程

1. 提取 Web UI 页面结构、组件、视觉、交互和状态。
2. 分析工程现有主题色、字体、间距、圆角、组件封装和页面架构。
3. 映射为 Android 页面和组件、状态、资源、文案、适配和交互方案。
4. 对组件选型、动效、适配或既有风格冲突等未决问题，先向用户说明并等待确认。
5. 确认后再指导或实施 Android UI 代码。

## 输出

给出 Web UI 对应关系、页面/组件拆分、复用与新增资源、状态/交互、适配/兼容性、待确认问题、实现建议和风险。不得绕过用户确认自行决定存在分歧的 UI 方案。
