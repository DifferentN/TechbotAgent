---
name: bug-fix
description: This skill should be used when diagnosing and fixing an Android or backend bug with a user report, ADB logcat, and remote Docker logs, including confirmation-gated deployment and device verification.
---

# Bug Fix

## Overview

执行 Android 与后台联动 Bug 的证据驱动修复闭环：收集用户描述、ADB 日志和远程 Docker 日志，定位根因，实施最小修复，在用户确认后发布服务和运行 App，并使用截图或日志验证结果。

## Required Configuration

读取 `.codebuddy/demand-workflow/remote-publish-log.config.json`。开始前校验以下字段：

- `androidProjectRoot` 与 `backendProjectRoot`：存在的项目根目录；
- `sshPrivateKeyPath`：仅供 SSH 使用的现有私钥路径，绝不读取或显示密钥内容；
- `sshTarget`：唯一的 `用户名@服务器IP/主机名`；
- `dockerLogsCommand`：只读 Docker 日志命令；
- `serviceDeployCommand` 与 `androidRunCommand`：发布和启动所需命令；
- `adbSerial`、`verificationMode` 与 `maxRepairAttempts`：设备与验证策略。

拒绝不安全或不完整的配置。不要将日志、截图、私钥或认证信息写进仓库。

## Workflow

### 1. 收集证据

1. 获取用户 Bug 描述、预期结果、复现步骤、影响范围和时间信息。
2. 创建系统临时目录保存本轮诊断产物。
3. 使用 `adb logcat -d -v threadtime > logcat.txt` 采集 Android 日志；设置 `adbSerial` 时为命令指定对应设备。
4. 使用非交互 SSH 和配置中的只读 `dockerLogsCommand` 采集远程 Docker 日志。
5. 将用户描述、两端日志与源码调用链、时间线、请求标识和异常栈关联，区分事实、假设和缺失证据。

### 2. 实施最小修复

1. 明确根因与影响范围后，只修改 `androidProjectRoot` 或 `backendProjectRoot` 中的相关文件。
2. 补充或调整覆盖根因的测试，并执行不包含发布、安装或启动 App 的本地检查。
3. 汇报修改、检查结果、风险、回滚线索和验证计划。

### 3. 确认后发布与运行

发布或运行前，展示本轮将执行的远程发布命令、本地 Android 运行命令、目标环境和风险。

仅在用户对本轮明确确认后执行：

1. 远程 `serviceDeployCommand`；
2. 本地 `androidRunCommand`；
3. 后续设备验证。

不要把任意历史确认用于下一轮、不同命令或不同目标。

### 4. 验证与重试

按 `verificationMode` 执行以下一种或多种方式：

- `screenshot`：通过 `adb exec-out screencap -p` 获取当前页面截图；
- `logcat`：重新采集 ADB 日志；
- `both`：同时获取截图和日志。

判断是否满足预期。未修复时，带着新增证据回到“收集证据”，重新分析和修复；再次发布或运行前必须再次取得用户确认。达到 `maxRepairAttempts` 时停止自动重试并汇总待决问题。

## Guardrails

- 仅允许 `docker logs` 或 `docker container logs` 用于远程诊断；拒绝包含 Shell 拼接、重定向或命令替换的日志命令。
- 不执行配置外的远程命令，不读取私钥内容，不将凭据写入代码或报告。
- 不在未确认时发布服务、重启远程容器、安装 APK 或运行 App。
- 不以无关重构替代 Bug 修复；每项修改均需能关联到证据和根因。

## Output Requirements

每轮输出 Bug 现象、证据来源、根因结论、代码修改、本地验证、确认状态、设备验证结果和后续动作。未修复时，说明新证据、剩余假设和下一轮计划。
