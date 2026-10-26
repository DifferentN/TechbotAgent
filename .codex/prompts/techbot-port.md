---
description: "启动 Android↔iOS 原生功能/UI迁移"
argument-hint: "[方向、范围与双端项目路径]"
---

这是项目内可读取的提示模板，不假设当前 Codex 会自动注册 `.codex/prompts` 为斜杠命令。推荐直接输入 `$cross-platform-port` 并提供方向、功能范围和项目路径；也可要求读取本文件。将下方占位符替换为实际请求，不把 `$ARGUMENTS` 当业务输入。

```text
$ARGUMENTS
```

使用 `cross-platform-port-manager` 并加载 `$cross-platform-port`；未发现 Skill 时读取 `.codex/skills/cross-platform-port/SKILL.md`。读取 `.codex/port-workflow/config.json`，缺方向、范围或有效根目录时先补充。

依次组织范围确认、双端证据分析、IR/UI确认、映射设计确认、目标白名单增量实现和独立验收。角色为 `port-source-analyzer`、`port-target-analyzer`、`port-designer`、`port-developer`、`port-verifier`；只并行独立静态分析，不并行改共享文件。没有子代理能力时由主代理按阶段串行执行并说明。

源端只读；不重新设计 Web UI、不自行批准规格或设计、不扩大父会话沙箱。设备/模拟器安装与启动、授权/清数据、签名和远程写入前取得本轮精确授权。报告证据和未运行项，不伪造成功。
