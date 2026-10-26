---
description: "启动 Android↔iOS 原生功能/UI迁移：分析、规格、确认、实现和等价验收"
argument-hint: "[android-to-ios|ios-to-android] [功能范围与双端项目路径]"
---

启动 `cross-platform-port-manager`，先加载 `.codebuddy/skills/cross-platform-port/SKILL.md`，使用 `.codebuddy/port-workflow/config.json`。用户迁移请求：

```text
$ARGUMENTS
```

若参数未替换、为空或缺方向/范围/有效根目录，先要求必要补充，不创建假规格或修改业务代码。沿用项目命令文件格式；当前 IDE 若未加载命令，可直接将真实请求交给迁移总控。

按范围确认→双端只读分析→带证据IR/UI确认→差异/设计确认→目标白名单增量开发→独立验收推进。使用 `port-source-analyzer`、`port-target-analyzer`、`port-designer`、`port-developer`、`port-verifier`；独立静态分析可并行，缺委派能力时按同一角色串行执行并说明。

不得调用普通需求流程自动重新生成 Web UI；不要迁移整个项目、覆盖源端或绕过用户批准。安装/启动/设备改动/签名/上传/发布操作本轮单独展示精确命令、风险、回滚和验证并确认。最终区分实际通过、失败、阻塞与未验证，不以编译成功声称迁移完成。
