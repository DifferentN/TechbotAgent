---
name: bug-fix
description: 此 Skill 用于诊断和修复 Android 或后台 Bug：结合用户描述、ADB logcat 和经 SSH 获取的只读 Docker 日志，实施最小修复，并在逐轮确认后发布和验证。
---

# Bug Fix

## 配置与安全边界

读取 `.codex/demand-workflow/bug-fix.config.json`。校验 Android/后台根目录、SSH 私钥路径、单一 SSH 目标、只读 Docker 日志命令、发布/启动命令、设备序列号、验证方式和最大轮次。

- 私钥路径仅用于 `ssh -i`，绝不读取、显示、复制、提交或写入私钥内容。
- `dockerLogsCommand` 只能是单条 `docker logs` 或 `docker container logs`，拒绝换行、重定向、管道、命令替换和 Shell 拼接。
- 将日志、截图保存在系统临时目录，不写进仓库或外部服务，除非用户明确要求。

## 流程

1. 收集现象、预期、复现步骤、影响范围和时间信息。
2. 采集 ADB 日志：`adb logcat -d -v threadtime > logcat.txt`；设置 `adbSerial` 时指定对应设备。
3. 用非交互 SSH 和已校验的只读 Docker 日志命令采集服务端日志。
4. 关联用户描述、两端日志、时间线、请求标识、异常栈与源码调用链；区分事实、假设与证据缺口。
5. 根因有证据后，仅在配置的项目根目录实施最小修复，补充必要测试并执行不包含发布、安装或启动的本地检查。
6. 展示本轮变更、检查结果、将执行的发布/运行命令、目标环境、风险、回滚与验证方案；仅在用户明确确认后发布服务、安装/运行 App。
7. 根据 `verificationMode` 获取 ADB 截图、日志或两者。未修复时记录新证据并返回步骤 4；每次再次发布或运行 App 前重新确认。达到 `maxRepairAttempts` 时停止并汇总。

## 输出

每轮报告 Bug 现象、可用/缺失证据、根因结论、相关代码、修复、本地检查、确认状态、验证结果、后续计划与风险。
