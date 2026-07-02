---
name: demand-process
description: This skill should be used by demand-manager after receiving a new demand from `/start`, or whenever a demand must be analyzed, supplemented, boundary-checked, checked for UI completeness, split into backend and Android/frontend requirements, documented, designed, developed, and tracked through acceptance.
---

# Demand Process

## Overview

执行需求研发全流程管理，从原始需求进入、需求分析、需求补充、UI 描述完整性检查、边界检查、需求文档输出，到代码分析、架构设计、开发协同和验收闭环。

继承 `demand-manager` 的需求分析能力：分析需求、补充需求、检查需求边界、发现遗漏场景、输出标准需求文档。

## Trigger

在以下场景使用此 Skill：

- 通过 `/start [需求描述]` 启动新需求。
- `demand-manager` 收到用户的新需求描述。
- 用户要求进行需求分析、需求拆分、研发流程推进或验收管理。
- 已有需求需要补充边界情况、异常场景、验收标准或前后端拆分。
- 需求中提及 UI、页面、样式、风格、交互、原型或视觉呈现。

## Core Workflow

### 1. 接收需求

- 读取用户输入的原始需求。
- 如果需求为空或过于模糊，先收集必要澄清问题。
- 如果存在多个产品方案、技术方案、UI 方案或关键口径，先列出方案差异并等待用户确认。
- 提炼当前需求名称，用于目录路径：`demand/<当前需求名称>/`、`ui/<当前需求名称>/` 和 `architecture/<当前需求名称>/`。

### 2. 分析与补充需求

输出并确认以下内容：

1. 需求背景与业务目标
2. 用户角色与使用场景
3. 核心功能范围
4. 非功能要求
5. 主流程与分支流程
6. 权限、状态、数据、时序约束
7. 边界情况与异常场景
8. 遗漏场景与待确认问题
9. 验收标准
10. UI 描述完整性检查结论
11. 后台需求与前端/Android 需求拆分结论

### 3. UI 描述处理

如果需求单中提及 UI 描述，在需求分析阶段调用 `web-ui-generater`：

1. 检查 UI 描述完整性，例如页面目标、布局、信息层级、交互、状态、风格样式、颜色、字体、间距、适配等。
2. 对缺失的 UI 细节直接做出合理假设，不向用户提问。
3. 调用 `web-ui` Skill 直接生成并保存 Web UI 到 `ui/<当前需求名称>/`，无需在创建前征求用户同意。
4. Web UI 文件创建完成后，由 `demand-manager` 向用户展示生成结果，并询问 UI 是否需要调整。
5. 如需调整，收集意见后再次调用 `web-ui-generater` 迭代并重新展示；如不需要调整，视为 UI 确认通过。
6. 在前端/Android 需求文档中记录最终 UI 路径和确认结论。

UI 未确认无需调整前，不进入客户端架构设计和 Android UI 开发。

### 4. 输出需求文档

在需求确认后保存：

- 后台需求：`demand/<当前需求名称>/后台需求/requirements.md`
- 前端/Android 需求：`demand/<当前需求名称>/前端需求/requirements.md`

如果某一端暂无开发需求，仍创建对应文档并说明原因。

### 5. 协同代码分析 Agent

需求文档完成后，按需求涉及范围调用：

- `server-code-analyzer`：读取后台代码，分析后台工程结构、编码规范、复用能力、风险点。
- `android-code-analyzer`：读取 Android 代码，分析客户端工程结构、UI 架构、网络/数据层、编码规范、风险点。

代码分析 Agent 必须先读取各自配置：

- `.codebuddy/demand-workflow/server-code-analyzer.config.json`
- `.codebuddy/demand-workflow/android-code-analyzer.config.json`

如果 `codeRoot` 为空或不可用，停止对应端分析并提示用户补充配置。

### 6. 协同架构设计 Agent

代码分析完成后，按需求涉及范围调用：

- `server-code-designer`
- `android-code-designer`

设计必须基于：

- 已确认需求文档
- 已确认 Web UI（如有）
- 对应代码分析结果
- 当前工程编码规范和模块结构

如出现多个可行方案，必须先输出方案对比，包含复杂度、影响范围、风险、可维护性和推荐方案，并等待用户确认。

用户确认全部方案后保存：

- 后台架构：`architecture/<当前需求名称>/server/architecture.md`
- Android/客户端架构：`architecture/<当前需求名称>/client/architecture.md`

### 7. 协同开发 Agent

仅在用户确认需求和架构方案后，按需求涉及范围调用：

- `server-code-developer`
- `android-code-developer`

开发必须遵守：

- 已确认需求文档
- 已确认架构设计
- 已确认 Web UI 和 `android-ui` Skill 输出（如有新增 UI）
- 对应代码分析结果
- 当前工程已有编码规范、目录结构、命名风格和测试习惯

如开发中发现架构或 UI 方案需调整，先停止并请求用户确认变更方案。

### 8. 验收闭环

开发完成后整理验收信息：

- 已完成的功能点
- 修改文件清单
- 需求文档、Web UI 与架构设计对应关系
- 建议验证步骤
- 未完成项、风险和回归范围
- 是否满足需求文档中的验收标准

## Output Requirements

每次阶段性输出保持清晰、可追踪：

- 当前阶段
- 已完成内容
- 产物路径
- 待确认问题
- 下一步建议

不要跳过用户确认直接进入存在方案分歧的下一阶段。
