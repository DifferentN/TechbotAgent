# UI Diff Skill Pro

这是正式模块化版本，不再把所有逻辑塞进一个 Python 文件。

## 安装

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
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
