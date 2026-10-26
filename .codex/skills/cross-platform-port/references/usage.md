# 使用与维护

## 安装位置

- CodeBuddy Agents：`.codebuddy/agents/cross-platform-port-manager.md` 和五个 `port-*.md`。
- CodeBuddy Skill：`.codebuddy/skills/cross-platform-port/`；命令模板 `.codebuddy/commands/port.md`。
- Codex Agents：`.codex/agents/cross-platform-port-manager.toml` 和五个 `port-*.toml`；沿用项目 `[agents]` 配置。
- Codex Skill 本体：`.codex/skills/cross-platform-port/`；当前官方发现目录通过 `.agents/skills/cross-platform-port` 相对符号链接接入。
- Codex 提示模板：`.codex/prompts/techbot-port.md`，不是保证自动注册的 slash command。

角色没有硬编码模型、MCP、设备或 SDK；Codex 不在角色中覆盖父会话沙箱/审批策略，CodeBuddy 关闭 Auto Run。文件格式基于当前官方文档和本仓库已有约定；本机版本不识别角色时按 Skill 串行执行。重新加载工作区/新会话以发现新增内容。

## 首次配置

分别填写 `.codebuddy/port-workflow/config.json` 或 `.codex/port-workflow/config.json`：

1. `android_root`、`ios_root`：真实且存在的绝对工程根目录；必须分离，不能相同、嵌套或符号链接等价。
2. `artifact_root`：协调仓库内的产物目录，默认 `porting`，禁止指向双端代码根、`.codebuddy`、`.codex`、`.agents`、`.git` 或通过链接越界。
3. `allowed_write_roots`：允许迁移写入的工程根目录数组，初始为空；至少显式加入本次目标根。配置不是外部目录权限授权，仍受会话沙箱和工具审批限制。
4. `default_ui_policy`：mixed/native/visual；只是推荐，仍需具体任务确认。
5. `validation`：双端 `build_argv/test_argv` 数组，留空后由目标分析器发现实际候选命令。禁止填写凭据；脚本不执行这些命令。执行前人工检查工作目录、参数与副作用，设备/签名/上传单独审批。

两个配置独立维护，避免一个平台路径失效时隐式使用另一个平台的旧配置。不会自动读取现有 Android/后台配置，也不会继承其中的远程凭据。

## 启动

CodeBuddy 可尝试 `/port android-to-ios 迁移商品列表页，保留分页、错误重试和详情导航`，或直接要求使用 `cross-platform-port-manager` 和 `cross-platform-port` Skill，并提供双端路径。

Codex 输入 `$cross-platform-port 将 Android 商品列表页迁移到 iOS，源/目标根目录见配置，只迁移列表、分页和详情导航`；反向指定 `ios-to-android`。新角色是否即时进入选择器取决于当前客户端，必要时开启新会话。

缺信息时会停在范围确认；确认后只读分析，IR/UI 和设计分别确认后才写目标业务代码。配置默认空路径和写入许可，不能直接运行迁移，这是有意的安全默认值。

## 校验

Python 3.11+，无需 pip 安装；默认只读。把 `<skill>` 替换为当前 Skill 绝对路径，`<workspace>` 替换为协调仓库根：

- 配置：`python3 <skill>/scripts/validate_port.py --workspace-root <workspace> --config <config.json>`。
- 规格草稿：追加 `--ir <porting/task/ir.json>`。
- 开发前：追加 `--ir <ir.json> --design <design.json> --stage ready`。
- 批准摘要：`python3 <skill>/scripts/validate_port.py --digest <ir或design.json>`；只输出摘要，不设置批准。
- 自测试：`python3 -B -m unittest discover -s <skill>/tests -v`。

样例为合成列表场景，含非真实 `/example/...` 路径和 pending 批准，不能用作真实工程证明。脚本返回 0 只说明静态规则通过，不能替代用户确认或 SDK/设备验收。默认配置校验失败属于预期，因为未填写真实路径。

## 双副本维护

两个 Skill 初始内容一致。修改时更新 `.codebuddy/skills/cross-platform-port` 与 `.codex/skills/cross-platform-port` 两个副本，并运行各自测试和内容差异检查；`.agents` 链接跟随 Codex 副本。不要把两个配置同步成不经确认的真实路径。复制到其他仓库时一并复制 Agents、Skill、配置模板与发现链接；不能只复制 Agent 文件而遗漏参考资源。

打包的 `dist/cross-platform-port/codebuddy/cross-platform-port.zip` 与 `dist/cross-platform-port/codex/cross-platform-port.zip` 是 Skill 包，不包含角色与项目配置；完整使用仍需要上述目录。重新打包前运行测试并排除缓存/凭据。

## 文档依据与限制

核对日期：2026-10-26。

- CodeBuddy：`https://www.codebuddy.ai/docs/zh/ide/User-guide/Overview`、`https://www.codebuddy.ai/docs/zh/ide/Features/Subagents`、`https://www.codebuddy.ai/docs/zh/ide/User-guide/Slash-Commands`。
- Codex：`https://developers.openai.com/codex/multi-agent`、`https://developers.openai.com/codex/skills`（当前返回文档使用 `.codex/agents` 与 `.agents/skills`，支持技能目录链接）。

CodeBuddy commands 的参数文件格式沿用本仓库约定，官方 IDE 页面未完整说明文件字段；保留直接请求总控的备用入口。不宣称本次已实际启动 SDK、调用新子代理或完成真实 Android/iOS 功能迁移。
