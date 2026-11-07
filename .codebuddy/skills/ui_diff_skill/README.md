# UI Diff Skill Pro

这是正式模块化版本，不再把所有逻辑塞进一个 Python 文件。

## 安装

```bash
python3 scripts/setup_ui_diff.py
```

脚本会在当前 Skill 下创建 `.venv`、安装 Python 依赖与匹配版本的
Playwright Chromium，并验证依赖、无头浏览器和 ADB。仅检查现有环境：

```bash
python3 scripts/setup_ui_diff.py --check-only
```

Android 还需要：

```bash
adb devices
```

iOS 需要 Appium + XCUITest。

## Figma -> Android

```bash
export FIGMA_TOKEN='...'

python scripts/run_ui_diff.py \
  --design-type figma \
  --design-url 'https://www.figma.com/design/FILE_KEY/NAME?node-id=123-456' \
  --runtime android-adb \
  --output ./out
```

## Web -> Android

```bash
python scripts/run_ui_diff.py \
  --design-type web \
  --design-url 'https://example.com' \
  --viewport 390x844 \
  --runtime android-adb \
  --output ./out
```

## Figma -> iOS

```bash
python scripts/run_ui_diff.py \
  --design-type figma \
  --design-url 'https://www.figma.com/design/...' \
  --runtime appium \
  --platform ios \
  --capabilities examples/ios_caps.json \
  --output ./out
```

## Android ↔ iOS 运行时对比

先把两端置于相同页面、数据、登录态、语言、主题、方向和滚动位置。
将 `examples/ios_caps.json` 中的 UDID 和 bundle ID 替换为实际值；模板默认
不自动启动、重置或终止 App。执行设备命令或建立 Appium 会话前应确认目标、
精确命令与可能的设备状态影响。

Android 作为基准，iOS 作为目标：

```bash
python scripts/run_ui_diff.py \
  --baseline-runtime android-adb \
  --baseline-serial ANDROID_SERIAL \
  --runtime appium \
  --platform ios \
  --appium-url http://127.0.0.1:4723 \
  --capabilities examples/ios_caps.json \
  --comparison-viewport 390x844 \
  --output ./android-ios-out
```

iOS 作为基准，Android 作为目标：

```bash
python scripts/run_ui_diff.py \
  --baseline-runtime appium \
  --baseline-platform ios \
  --baseline-appium-url http://127.0.0.1:4723 \
  --baseline-capabilities examples/ios_caps.json \
  --runtime android-adb \
  --serial ANDROID_SERIAL \
  --output ./ios-android-out
```

Android 也可使用 Appium：分别提供基准侧和目标侧的 platform、capabilities
及 Appium URL。双端模式不能同时传 `--design-type` 或 `--design-url`。

- 双端布局归一化到统一参照视口，默认 `390x844`；容差 `2/4` 表示参照逻辑单位，
  不是 Android 原始 px，也不意味着直接判定 dp/pt 等价。
- 用 `--baseline-content-rect x:y:width:height` 和
  `--runtime-content-rect x:y:width:height` 明确排除系统栏/安全区域；值为各端全视口
  的归一化比例，未传时比较全视口。不自动猜测安全区域，不使用 `--runtime-region-y`。
- 用 `--semantic-map /path/to/map.json` 传入基准 ID 到目标 ID 的 JSON 字典，
  例如 `{"com.example:id/title":"screen_title"}`；不改原始快照。
- 对比组件几何、有效父子/兄弟间距、文本、已有样式元数据和高置信截图 ROI；
  动态图片只比较外环。无法测量的字体、颜色、圆角、边框等输出 `UNKNOWN`。
- 采集顺序执行，不保证同步快照。原生树包装差异可能影响匹配，需检查置信度及
  missing/unexpected，不能仅凭没有 `FAIL` 宣称两端完全一致。

产物继续使用 `design/`（基准）和 `runtime/`（目标），保存原始快照、截图/XML
及 `comparison_snapshot.json`。`report.json` 增加比较角色、参照单位、内容区域、
覆盖范围及未知统计；`report.html` 并排展示双端截图。无 FAIL 但存在未知测量时，
整体状态为 `UNKNOWN`，不视为 PASS。

## 配置

默认配置见：

```text
examples/config.json
```

可调整：
- geometry 容差
- DeltaE 阈值
- visual diff 阈值
- ignore patterns
- 是否开启 OpenCV fallback


## V2 新增

V2 已把以下能力真正接入执行链路：

- top-down hierarchical matcher
- matched-parent constrained Hungarian assignment
- repeated list template matching
- sibling gap comparison
- explicit logical/screenshot coordinate mapper
- iOS Appium window-rect -> screenshot pixel mapping
- OpenCV corner radius fallback
- OpenCV border-width fallback
- OpenCV background-color fallback
- Figma render size -> screenshot bounds mapping
- `list_templates.json`

推荐生产顺序：

```text
Stable ID
→ List Template
→ Hierarchical Hungarian
→ Global orphan fallback
→ Geometry/Spacing/Metadata Diff
→ OpenCV property fallback
→ ROI visual diff
```
