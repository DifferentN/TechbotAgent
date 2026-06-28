---
description: "启动需求分析、拆分、架构设计与开发工作流"
argument-hint: "[需求描述]"
---

请启动需求交付工作流。用户输入的原始需求描述如下：

```text
$ARGUMENTS
```

## 总体原则

- 全程使用简体中文与用户沟通。
- 如果命令后没有需求描述，先询问用户补充需求描述，不要开始创建需求文档。
- 如果存在多个可行方案，必须先向用户说明方案差异并等待用户确认后再继续。
- 不要在用户确认完整架构方案前启动开发 Agent。
- 所有输出文件路径中的“当前需求名称”必须使用从需求中提炼出的短名称，建议使用中文短名；如存在文件系统兼容风险，使用 kebab-case 英文或拼音短名。
- 如需读取后台或 Android 代码，必须先读取对应配置文件中的代码根目录；配置为空或目录不存在时，提示用户先补充配置。

## 工作流

1. 唤醒并委派给 `demand-manager`，由它先执行 `demand-process` Skill，基于原始需求进行：
   - 需求分析、拆分与补充；
   - 业务目标、用户角色、核心流程、验收标准梳理；
   - 边界情况、异常场景、遗漏场景检查；
   - 如果需求单提及 UI 描述，调用 `web-ui-generater` 检查 UI 描述完整性，执行 `web-ui` Skill 生成 Web UI，与用户确认到同意后保存到 `ui/<当前需求名称>/`；
   - 判断是否需要拆分后台需求和前端/Android 需求；
   - 管理从需求到开发、验证、验收的完整流程。

2. 需求确认后，将最终需求文档保存到：
   - 后台需求：`demand/<当前需求名称>/后台需求/requirements.md`
   - 前端/Android 需求：`demand/<当前需求名称>/前端需求/requirements.md`
   - 如果某一端无需开发，也要在对应文档中明确“本端暂无开发需求”及原因。

3. 调用或委派给 `server-code-analyzer`：
   - 读取 `.codebuddy/demand-workflow/server-code-analyzer.config.json`；
   - 基于其中 `codeRoot` 分析后台代码结构、编码规范、关键模块、可复用能力、风险点；
   - 分析结果供后续后台架构设计与开发使用。

4. 调用或委派给 `android-code-analyzer`：
   - 读取 `.codebuddy/demand-workflow/android-code-analyzer.config.json`；
   - 基于其中 `codeRoot` 分析 Android 端代码结构、编码规范、关键模块、可复用能力、风险点；
   - 分析结果供后续客户端架构设计与开发使用。

5. 调用或委派给 `server-code-designer` 和 `android-code-designer` 分别进行开发前架构设计：
   - 必须基于需求文档和代码分析结果；
   - 如产生多个方案，先输出方案对比、影响范围、风险和推荐意见，交由用户确认；
   - 用户未明确同意全部方案前，不要保存最终架构文档，也不要进入开发。

6. 用户确认全部架构方案后，将最终架构设计分别保存到：
   - 后台：`architecture/<当前需求名称>/server/architecture.md`
   - Android/客户端：`architecture/<当前需求名称>/client/architecture.md`

7. 用户确认可以开发后，调用或委派给：
   - `server-code-developer`：负责后台代码开发；
   - `android-code-developer`：负责 Android 端代码开发。

8. 开发必须遵守：
   - 已确认的需求文档；
   - 已确认的架构设计；
   - 如有新增 UI，已确认的 Web UI 和 `android-ui` Skill 输出；
   - 对应 code-analyzer 的代码分析结果；
   - 当前仓库已有编码规范、目录结构、命名风格和测试习惯。

## 最终汇报

完成后简要汇报：

- 需求文档路径；
- 架构文档路径；
- 涉及的后台和 Android 代码变更；
- 未完成项、风险或需要用户继续确认的问题。
