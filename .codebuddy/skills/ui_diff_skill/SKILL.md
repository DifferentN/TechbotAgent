---
name: ui-diff-skill
description: Install, verify, and run deterministic UI comparisons between Figma/Web designs and Android/iOS runtime screens, or directly between Android and iOS runtime UIs. Use when checking cross-platform layout, text, spacing, missing components, or visual drift; report unavailable typography and style measurements as UNKNOWN.
---

# UI Diff Skill

## Purpose

Compare a Figma/Web design against an Android/iOS runtime UI, or compare Android and iOS runtime screens directly. Preserve the existing design-vs-runtime entry point; use `--baseline-runtime` for cross-platform runtime comparison.

Supported design sources:
- Figma
- Web UI

Supported runtime sources:
- Android via ADB + UIAutomator
- Android via Appium
- iOS via Appium + XCUITest

Primary checks:
- x/y position
- width/height
- relative position
- parent margins
- sibling gaps
- alignment
- text
- font size / weight / family / line-height / letter-spacing when metadata exists
- text/background/border color
- border width
- corner radius
- image container geometry
- missing components
- unexpected components

Dynamic IMAGE content is ignored by default.

---

## Entry point

```bash
python scripts/run_ui_diff.py ...
```

## Android ↔ iOS runtime comparison

Choose one runtime as the baseline (`expected`) and the other as the target (`actual`).
Require one Android side and one iOS side. Use ADB or Appium for Android and Appium +
XCUITest for iOS. Do not pass `--design-type` or `--design-url` in this mode.

Align both apps to the same page, data, login state, locale, theme, orientation and
scroll position before capture. Capture sequentially; do not infer synchronized
state. Obtain explicit confirmation before device commands or Appium sessions;
sessions can launch/reset/terminate apps depending on capabilities. Do not install
or start apps implicitly. Edit `examples/ios_caps.json` with the actual device UDID
and installed bundle ID; its defaults disable app auto-launch and reset.

From the skill directory, compare Android baseline to iOS target:

```bash
python scripts/run_ui_diff.py \
  --baseline-runtime android-adb \
  --baseline-serial ANDROID_SERIAL \
  --runtime appium --platform ios \
  --appium-url http://127.0.0.1:4723 \
  --capabilities examples/ios_caps.json \
  --comparison-viewport 390x844 \
  --output ./android-ios-out
```

Reverse the roles with `--baseline-runtime appium --baseline-platform ios
--baseline-capabilities examples/ios_caps.json --runtime android-adb --serial
ANDROID_SERIAL`. Set `--baseline-appium-url` independently when both sides use
Appium; pass independent `--baseline-capabilities` and `--capabilities` files.

Normalize both sides into the same reference viewport (default `390x844`). Compute
geometry and spacing deltas in reference logical units, not Android screenshot px
or physical dp/pt equality. Preserve raw snapshots and screenshot pixel bounds.
Use `--baseline-content-rect x:y:width:height` and `--runtime-content-rect
x:y:width:height` to explicitly exclude differing system/safe-area regions; each
rect uses normalized `[0,1]` coordinates in that side's full viewport. Intersect
components with the chosen content rect and rebase the visible layout to `[0,1]`.
Do not guess safe-area insets. Do not use `--runtime-region-y` in this mode.

Supply `--semantic-map /path/to/map.json` when platform identifiers differ. Use a
JSON object mapping exact baseline IDs to target IDs, for example
`{"com.example:id/title": "screen_title"}`. Apply mapping to comparison copies
only. Reuse stable ID → list templates → hierarchical Hungarian → orphan matching.
Compare parent margins/sibling gaps only when the target parent relation agrees.
Do not claim native wrapper/accessibility-tree differences are business defects.

Compare captured text for TEXT/BUTTON/INPUT nodes and mark unequal text as FAIL.
Keep IMAGE center content excluded from visual checks. Report unavailable fonts,
colors, borders, radii, or visual ROI measurements as UNKNOWN; never turn absence
of measurements into PASS. Treat ROI SSIM as supporting raster evidence, not font
metadata or whole-screen semantic equivalence. Review matching confidence and
missing/unexpected nodes, even when no geometry FAIL exists.

Retain `design/` and `runtime/` artifact names for compatibility; in this mode they
mean baseline and target. Save original `*_snapshot.json`, normalized
`comparison_snapshot.json`, PNG/XML, `list_templates.json`, and JSON/HTML reports.
Include actual source roles, reference units, chosen content rects, limitations and
matched-property coverage. Show both screenshots side by side in HTML.

## Setup

From this skill directory, run the bundled installer. It keeps dependencies in
`.venv`, installs the matching Playwright Chromium runtime, and verifies Python,
Chromium, and ADB:

```bash
python3 scripts/setup_ui_diff.py
```

Recheck an existing installation without reinstalling:

```bash
python3 scripts/setup_ui_diff.py --check-only
```

If macOS sandboxing prevents the Chromium smoke test, rerun outside the sandbox
or use `--skip-browser-smoke-test`; this skips only the launch check.

---

## Required behavior

1. Resolve the design source.
2. Collect structured design metadata and a screenshot.
3. Collect structured runtime metadata and a screenshot.
4. Convert both sides into the same component schema.
5. Normalize coordinates into:
   - source logical bounds
   - normalized [0..1] bounds
   - screenshot-pixel bounds
6. Match semantic components before diffing.
7. Compare deterministic metadata first.
8. Use OpenCV only for missing visual measurements or screenshot-only fallback.
9. For IMAGE nodes, never use center image pixels for semantic matching.
10. Produce JSON + HTML reports with expected/actual/delta/source/confidence.
11. If a fact cannot be measured reliably, return UNKNOWN rather than inventing a result.

---

## Figma acquisition

Input:
- Figma URL, or file key + node id
- FIGMA_TOKEN

Calculation:
- Parse `file_key` from `/design/<file_key>/...` or `/file/<file_key>/...`.
- Parse `node-id`, replacing `-` with `:`.
- Retrieve the target node tree from the Figma REST API.
- Extract `absoluteBoundingBox`, fills, strokes, radii, text style, children.
- Use target frame `(fx, fy, fw, fh)` as the design-local coordinate system.
- For node `(nx, ny, nw, nh)`:

```text
local_x = nx - fx
local_y = ny - fy

normalized_x = local_x / fw
normalized_y = local_y / fh
normalized_w = nw / fw
normalized_h = nh / fh
```

- Render the target node to PNG through the Figma image endpoint.

Output:
- `Snapshot`
- screenshot
- component tree

---

## Web acquisition

Input:
- URL
- viewport, default 390x844

Calculation:
- Open with Playwright Chromium.
- Traverse visible DOM nodes.
- Read `getBoundingClientRect()` and `getComputedStyle()`.
- Extract semantic identifiers from `data-testid`, `aria-label`, `id`.
- Build component types:
  - img -> IMAGE
  - button -> BUTTON
  - input/textarea -> INPUT
  - direct text elements -> TEXT
  - structural elements -> CONTAINER
- Normalize bounds by viewport width/height.
- Save screenshot.

---

## Android acquisition

Preferred direct mode: ADB.

Commands:
```bash
adb devices
adb -s SERIAL exec-out screencap -p
adb -s SERIAL shell uiautomator dump /sdcard/window_dump.xml
adb -s SERIAL shell cat /sdcard/window_dump.xml
```

Bounds:
```text
[x1,y1][x2,y2]

x=x1
y=y1
w=x2-x1
h=y2-y1
```

Normalized:
```text
nx=x/screenshot_width
ny=y/screenshot_height
nw=w/screenshot_width
nh=h/screenshot_height
```

If only one device is attached, auto-select it.
If multiple devices exist and no serial is provided, fail explicitly with the available serial list.

---

## iOS acquisition

Use Appium + XCUITest.

Read:
- `driver.page_source`
- `driver.get_screenshot_as_png()`

Use node attributes:
- x/y/width/height
- type
- name
- label
- value

Read `driver.get_window_rect()` and normalize node bounds against its logical
width/height after subtracting its x/y origin. Map logical bounds to screenshot
pixels with `CoordinateMapper`; never divide iOS pt bounds directly by Retina
screenshot pixels. Fail explicitly when a valid logical viewport is unavailable.

---

## Matching algorithm

### Stable semantic ID

Normalize IDs:
```text
lowercase
remove spaces
remove `_ - : /`
```

If design and runtime IDs are uniquely equal and type-compatible:
```text
score=1.0
confidence=HIGH
```

### Candidate filtering

Reject candidate if:
```text
type_compatibility == 0
normalized center distance > 0.35
width ratio outside [1/3, 3]
height ratio outside [1/3, 3]
```

### Pair score

```text
position_score = exp(-center_distance / 0.10)

width_score = min(dw,rw)/max(dw,rw)
height_score = min(dh,rh)/max(dh,rh)
size_score = (width_score+height_score)/2

order_score =
1 - abs(
 design_index/max(design_count-1,1)
 -
 runtime_index/max(runtime_count-1,1)
)

semantic_score:
- exact semantic id => 1.0
- otherwise normalized text Levenshtein similarity
```

Final score:
```text
0.30 * type
+ 0.25 * position
+ 0.20 * size
+ 0.10 * sibling_order
+ 0.15 * semantic
```

Then build a score matrix and run Hungarian assignment:
```python
scipy.optimize.linear_sum_assignment(1 - score_matrix)
```

Confidence:
```text
>=0.80 HIGH
>=0.65 MEDIUM
>=0.50 LOW
<0.50 UNMATCHED
```

---

## Geometry diff

Always compare normalized layout first, then convert delta into design logical units:

```text
delta_x =
(runtime.normalized_x-design.normalized_x)
* design_viewport_width

delta_y =
(runtime.normalized_y-design.normalized_y)
* design_viewport_height
```

Same for width/height.

Default thresholds:
```text
|delta| <= 2    PASS
2 < |delta| <=4 WARNING
|delta| > 4     FAIL
```

Configurable in YAML.

---

## Spacing diff

Parent margins:
```text
left = child.x-parent.x
right = parent.right-child.right
top = child.y-parent.y
bottom = parent.bottom-child.bottom
```

Sibling horizontal gap:
```text
gap = B.left-A.right
```

Sibling vertical gap:
```text
gap = B.top-A.bottom
```

Calculate in normalized space, then convert to design logical units.

---

## Typography diff

Compare metadata when available:
- font family
- font size
- font weight
- line height
- letter spacing
- text color

Normalize common font weights:
```text
Regular 400
Medium 500
Semibold 600
Bold 700
```

Do not use rasterized glyph pixels as the primary typography truth.

---

## Color diff

Prefer structured metadata.

When screenshot measurement is required:
1. Crop ROI.
2. Inset by 10%.
3. Exclude child regions if available.
4. Use median RGB, not mean.
5. Convert RGB -> Lab.
6. Compare with DeltaE CIE76.

Default:
```text
DeltaE <= 3 PASS
3 < DeltaE <= 6 WARNING
DeltaE > 6 FAIL
```

---

## Corner radius

Prefer metadata.

If metadata is unavailable, OpenCV fallback:
1. Crop ROI.
2. Analyze four corner sub-ROIs sized `min(w,h)*0.35`.
3. Gray -> blur -> Canny.
4. Find contour points near the expected corner boundary.
5. Estimate radius from edge transition / fitted quarter-circle.
6. Convert screenshot pixels to source logical units using component-scale.
7. Return confidence.
8. Low confidence -> UNKNOWN.

---

## Border

Prefer metadata.

Fallback:
- sample lines from the outside edge inward;
- detect a stable transition from edge color to interior background;
- estimate width and border color;
- low contrast -> UNKNOWN.

---

## Dynamic image rule

IMAGE defaults:
```text
compare_content=false
```

Compare:
- x/y
- width/height
- aspect ratio
- radius
- border
- edge clipping

Never use center content for component matching.

Visual check uses a ring mask:
```text
ring_width=max(2, round(min(w,h)*0.08))
```

Only pixels in the outer ring participate in SSIM/absdiff.

---

## Vision localization fallback

Use only when runtime UI tree is missing a component.

1. Map design normalized bounds to expected runtime screenshot bounds.
2. Expand the search region by 30%.
3. Gray -> blur -> Canny -> contours -> bounding rectangles.
4. Candidate score:

```text
0.35 position
+0.30 size
+0.20 aspect
+0.15 shape
```

5. Candidate >= 0.75 may be returned to matching.
6. OpenCV does not independently declare semantic identity.

---

## Lists / repeated structures

Detect repeated siblings using structural fingerprints:
```text
CONTAINER(IMAGE,TEXT,TEXT)
```

Repeated siblings with the same fingerprint and similar child relative geometry are treated as a list-item template.

Runtime list items are validated against the template rather than against dynamic content snapshots.

---

## Output

```text
output/
├── design/
│   ├── design.png
│   └── design_snapshot.json
├── runtime/
│   ├── runtime.png
│   ├── runtime.xml
│   └── runtime_snapshot.json
├── report.json
└── report.html
```

Every difference must include:
```text
component
property
expected
actual
delta
tolerance
status
source
confidence
```


---

## V2 matching order

The implementation MUST use this order:

```text
Stable semantic ID
↓
Repeated list/template matching
↓
Top-down hierarchical Hungarian matching
↓
Global orphan fallback
```

For hierarchical matching, once a design parent is matched to a runtime parent,
their unmatched children are compared only inside that sibling group before any
global fallback occurs.

---

## V2 automatic property fallback

When design metadata contains a property but runtime metadata does not:

```text
corner radius
→ vision.style_measure.measure_corner_radii()

border width
→ vision.style_measure.measure_border()

background color
→ vision.style_measure.median_background_rgb()
→ RGB/Lab
→ DeltaE
```

OpenCV results MUST include confidence and MUST NOT override structured metadata.

---

## V2 coordinate requirement

For Appium, do not normalize logical node bounds against screenshot pixels directly.

Use:

```python
driver.get_window_rect()
```

to get the logical viewport and map:

```text
logical bounds
→ screenshot bounds
```

through `CoordinateMapper`.
