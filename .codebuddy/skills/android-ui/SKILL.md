---
name: android-ui
description: This skill should be used by android-code-developer when the current demand has newly confirmed Web UI under the demand-specific ui directory. It reads the Web UI and current Android UI style, then generates an Android UI implementation plan and code-aligned UI design, asking the user before unresolved UI decisions.
---

# Android UI

## Overview

将已确认的 Web UI 转换为符合当前 Android 工程风格和技术栈的 Android UI 方案，并指导 `android-code-developer` 进行实现。

## Trigger

在以下场景使用：

- 当前需求存在新增 UI。
- `ui/<当前需求名称>/` 下存在已确认的 Web UI。
- Android 开发需要根据 Web UI 还原页面结构、视觉风格、组件状态或交互。

## Required Inputs

必须先读取：

1. `ui/<当前需求名称>/index.html` 或 `ui/<当前需求名称>/ui-spec.md`
2. `demand/<当前需求名称>/前端需求/requirements.md`
3. `architecture/<当前需求名称>/client/architecture.md`
4. `android-code-analyzer` 对当前 Android UI 风格、组件体系和编码规范的分析结果
5. 当前 Android 工程中相似页面、主题、组件、资源命名和布局写法

如果 Web UI 不存在或未确认，停止并提示先完成 Web UI 确认。

## Workflow

1. 解析 Web UI 的页面结构、组件、视觉风格、交互和状态。
2. 读取当前 Android 工程 UI 风格，包括主题色、字体、间距、圆角、资源命名、组件封装和页面架构。
3. 将 Web UI 映射为 Android UI 方案：页面结构、组件拆分、状态管理、资源、文案、适配和交互。
4. 如果存在不确定点，如组件选型、动效、适配策略、与现有风格冲突，先向用户确认。
5. 用户确认后，再指导或执行 Android UI 代码实现。

## Output Requirements

输出 Android UI 方案时包含：

- Web UI 对应关系
- Android 页面/组件拆分
- 复用的现有组件和资源
- 新增资源清单
- 状态与交互处理
- 适配和兼容性说明
- 待用户确认的问题
- 实现建议和风险

不要绕过用户确认直接决定存在分歧的 UI 方案。
