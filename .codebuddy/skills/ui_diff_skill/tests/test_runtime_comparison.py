import json
from copy import deepcopy
from unittest.mock import Mock

import pytest
from PIL import Image

from ui_diff_skill import cli
from ui_diff_skill.core.config import load_config
from ui_diff_skill.core.models import Bounds, Component, Match, Snapshot
from ui_diff_skill.engine import UIDiffEngine


def snapshot(tmp_path, source, scale=1, text="Hello", offset=0):
    path = tmp_path / (source + ".png")
    Image.new("RGB", (390 * scale, 844 * scale), "white").save(path)
    b = Bounds(39 * scale + offset, 84 * scale, 78 * scale, 42 * scale)
    component = Component("title", "TEXT", b,
                          Bounds(b.x / (390 * scale), b.y / (844 * scale), .2, 42 / 844),
                          deepcopy(b), semantic_id="title", text=text)
    return Snapshot(390 * scale, 844 * scale, 390 * scale, 844 * scale,
                    [component], str(path), source)


def adapter(value):
    return Mock(collect=Mock(return_value=value))


def test_runtime_geometry_uses_reference_units_not_android_pixels(tmp_path):
    left = snapshot(tmp_path, "android-adb", 3)
    right = snapshot(tmp_path, "appium-ios", offset=3)
    cfg = load_config()
    cfg["visual"]["enabled"] = False
    data = UIDiffEngine(cfg).run(adapter(left), adapter(right), tmp_path / "report",
                                runtime_comparison={"viewport": (390, 844)})
    x = next(d for d in data["differences"] if d["property"] == "x")
    assert x["delta"] == 3
    assert x["status"] == "WARNING"
    assert left.width == 1170
    assert left.components[0].bounds.x == 117
    raw = json.loads((tmp_path / "report/design/design_snapshot.json").read_text())
    assert raw["width"] == 1170
    assert data["comparison"]["baseline_source"] == "android-adb"
    assert data["comparison"]["target_source"] == "appium-ios"
    assert data["comparison"]["geometry_unit"] == "reference-logical-unit"
    assert data == json.loads((tmp_path / "report/report.json").read_text())
    page = (tmp_path / "report/report.html").read_text()
    assert "Baseline" in page and "Target" in page and "<img" in page


def test_runtime_text_changes_fail_and_unmeasurable_fonts_are_unknown(tmp_path):
    left = snapshot(tmp_path, "android-adb")
    right = snapshot(tmp_path, "appium-ios", text="Goodbye")
    data = UIDiffEngine(load_config()).run(adapter(left), adapter(right), tmp_path / "out",
                                           runtime_comparison={"viewport": (390, 844)})
    props = {d["property"]: d for d in data["differences"]}
    assert props["text"]["status"] == "FAIL"
    assert props["font_size"]["status"] == "UNKNOWN"
    assert props["background_color"]["status"] == "UNKNOWN"
    assert data["summary"]["unknown"] > 0


def test_content_rect_and_semantic_mapping_preserve_raw_evidence(tmp_path):
    from ui_diff_skill.core.runtime_comparison import prepare_snapshot
    raw = snapshot(tmp_path, "android-adb", 3)
    raw.components[0].semantic_id = "android_title"
    prepared = prepare_snapshot(raw, (390, 844), (.1, .05, .8, .9),
                                {"android_title": "ios_title"})
    node = prepared.components[0]
    assert node.normalized.x == pytest.approx(0)
    assert node.normalized.width == pytest.approx(.25)
    assert node.bounds.width == pytest.approx(97.5)
    assert node.screenshot_bounds == raw.components[0].screenshot_bounds
    assert node.semantic_id == "ios_title"
    assert raw.components[0].semantic_id == "android_title"


@pytest.mark.parametrize("rect", [(0, 0, 0, 1), (-.1, 0, 1, 1), (0, .5, 1, 1)])
def test_invalid_content_rect_is_rejected(tmp_path, rect):
    from ui_diff_skill.core.runtime_comparison import prepare_snapshot
    with pytest.raises(ValueError, match="content rect"):
        prepare_snapshot(snapshot(tmp_path, "android-adb"), (390, 844), rect)


def test_runtime_spacing_does_not_compare_unrelated_target_parents():
    from ui_diff_skill.diff.spacing import compare_parent_margins, compare_sibling_gaps
    b = Bounds(0, 0, 10, 10)
    n = Bounds(0, 0, .1, .1)
    nodes = [Component("p", "CONTAINER", b, n, b),
             Component("a", "TEXT", b, n, b, parent_id="p"),
             Component("b", "TEXT", b, n, b, parent_id="p", sibling_index=1)]
    left = Snapshot(100, 100, 100, 100, nodes, "", "android-adb")
    right = deepcopy(left)
    right.components[1].parent_id = "other"
    matches = [Match(i, i, 1, "HIGH", {}) for i in ("p", "a", "b")]
    cfg = load_config()
    cfg["runtime_comparison"] = True
    margins = compare_parent_margins(left, right, matches, cfg)
    assert all(d.status == "UNKNOWN" for d in margins if d.component == "a")
    gaps = compare_sibling_gaps(left, right, matches, cfg)
    assert len(gaps) == 1
    assert gaps[0].status == "UNKNOWN"


def test_cli_collects_android_and_ios_with_independent_connections(tmp_path, monkeypatch):
    caps = tmp_path / "ios.json"
    caps.write_text('{"platformName":"iOS"}')
    android = Mock()
    ios = Mock()
    engine = Mock()
    engine.run.return_value = {"summary": {}}
    monkeypatch.setattr(cli, "AndroidADBAdapter", android)
    monkeypatch.setattr(cli, "AppiumAdapter", ios)
    monkeypatch.setattr(cli, "UIDiffEngine", Mock(return_value=engine))
    monkeypatch.setattr("sys.argv", ["ui-diff", "--baseline-runtime", "android-adb",
                                    "--baseline-serial", "android-device", "--runtime", "appium",
                                    "--platform", "ios", "--capabilities", str(caps),
                                    "--appium-url", "http://ios-host:4725", "--output", str(tmp_path)])
    cli.main()
    android.assert_called_once_with("android-device", region_y=None)
    ios.assert_called_once_with("http://ios-host:4725", {"platformName": "iOS"}, "ios")
    assert engine.run.call_args.kwargs["runtime_comparison"]["viewport"] == (390, 844)


def test_cli_rejects_same_platform_before_collecting(monkeypatch):
    collect = Mock()
    monkeypatch.setattr(cli, "AndroidADBAdapter", collect)
    monkeypatch.setattr("sys.argv", ["ui-diff", "--baseline-runtime", "android-adb",
                                    "--runtime", "android-adb"])
    with pytest.raises(SystemExit):
        cli.main()
    collect.assert_not_called()


def test_cli_preserves_web_android_entry(monkeypatch):
    engine = Mock()
    engine.run.return_value = {"summary": {}}
    monkeypatch.setattr(cli, "UIDiffEngine", Mock(return_value=engine))
    monkeypatch.setattr(cli, "WebAdapter", Mock())
    monkeypatch.setattr(cli, "AndroidADBAdapter", Mock())
    monkeypatch.setattr("sys.argv", ["ui-diff", "--design-type", "web", "--design-url",
                                    "http://localhost:8000", "--runtime", "android-adb"])
    cli.main()
    assert not engine.run.call_args.kwargs


def test_small_visual_components_do_not_crash(tmp_path):
    from ui_diff_skill.vision.visual import compare
    left = snapshot(tmp_path, "android-adb")
    right = snapshot(tmp_path, "appium-ios")
    for value in (left, right):
        value.components[0].screenshot_bounds = Bounds(0, 0, 3, 3)
    diffs = compare(left, right, [Match("title", "title", 1, "HIGH", {})], load_config())
    assert diffs[0].status == "UNKNOWN"
