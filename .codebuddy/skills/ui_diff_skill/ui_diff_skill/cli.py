import argparse,json,os
from pathlib import Path
from .core.config import load_config
from .adapters.figma import FigmaAdapter
from .adapters.web import WebAdapter
from .adapters.android_adb import AndroidADBAdapter
from .adapters.appium import AppiumAdapter
from .engine import UIDiffEngine

def _viewport(value):
    from .core.runtime_comparison import validate_viewport
    try:
        return validate_viewport(tuple(map(int, value.lower().split("x"))))
    except (ValueError, TypeError) as exc:
        raise argparse.ArgumentTypeError("viewport must be positive WIDTHxHEIGHT") from exc


def _content_rect(value):
    from .core.runtime_comparison import validate_content_rect
    try:
        return validate_content_rect(tuple(map(float, value.split(":"))))
    except (ValueError, TypeError) as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def _runtime_adapter(parser, kind, serial, platform, url, capabilities, region_y=None):
    if kind == "android-adb":
        return AndroidADBAdapter(serial, region_y=region_y)
    if not platform or not capabilities:
        parser.error("Appium requires platform and capabilities for each Appium side")
    try:
        caps = json.loads(Path(capabilities).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        parser.error(f"Cannot read capabilities {capabilities}: {exc}")
    if not isinstance(caps, dict):
        parser.error("Capabilities must be a JSON object")
    if str(caps.get("platformName", platform)).lower() != platform:
        parser.error("Capabilities platformName does not match the selected platform")
    return AppiumAdapter(url, caps, platform)


def main():
    p=argparse.ArgumentParser(description="Figma/Web or Android/iOS runtime UI diff")
    source=p.add_mutually_exclusive_group(required=True)
    source.add_argument("--design-type",choices=["figma","web"])
    source.add_argument("--baseline-runtime",choices=["android-adb","appium"])
    p.add_argument("--design-url")
    p.add_argument("--figma-token",default=os.getenv("FIGMA_TOKEN"))
    p.add_argument("--viewport",default="390x844")
    p.add_argument("--web-scroll-selector")
    p.add_argument("--web-target-y",type=int,default=260)
    p.add_argument("--web-click-selector")
    p.add_argument("--web-scope-selector")
    p.add_argument("--web-scroll-padding",type=int,default=0)
    p.add_argument("--runtime-region-y")

    p.add_argument("--runtime",choices=["android-adb","appium"],required=True)
    p.add_argument("--serial")
    p.add_argument("--platform",choices=["android","ios"])
    p.add_argument("--appium-url",default="http://127.0.0.1:4723")
    p.add_argument("--capabilities")
    p.add_argument("--baseline-serial")
    p.add_argument("--baseline-platform",choices=["android","ios"])
    p.add_argument("--baseline-appium-url",default="http://127.0.0.1:4723")
    p.add_argument("--baseline-capabilities")
    p.add_argument("--comparison-viewport",type=_viewport,default=(390,844))
    p.add_argument("--baseline-content-rect",type=_content_rect,default=(0,0,1,1))
    p.add_argument("--runtime-content-rect",type=_content_rect,default=(0,0,1,1))
    p.add_argument("--semantic-map",help="JSON object mapping baseline semantic IDs to target IDs")
    p.add_argument("--config")
    p.add_argument("--output",default="./ui-diff-out")
    a=p.parse_args()

    cfg=load_config(a.config)
    comparison=None
    if a.baseline_runtime:
        if a.design_url:
            p.error("--design-url cannot be used with --baseline-runtime")
        baseline_platform="android" if a.baseline_runtime=="android-adb" else a.baseline_platform
        target_platform="android" if a.runtime=="android-adb" else a.platform
        if {baseline_platform,target_platform}!={"android","ios"}:
            p.error("Runtime comparison requires one Android side and one iOS side")
        if a.runtime_region_y:
            p.error("Use --runtime-content-rect instead of --runtime-region-y in runtime comparison")
        semantic_map={}
        if a.semantic_map:
            from .core.runtime_comparison import validate_semantic_map
            try:
                semantic_map=validate_semantic_map(json.loads(Path(a.semantic_map).read_text(encoding="utf-8")))
            except (OSError,ValueError) as exc:
                p.error(str(exc))
        comparison={
            "viewport":a.comparison_viewport,
            "baseline_content_rect":a.baseline_content_rect,
            "target_content_rect":a.runtime_content_rect,
            "semantic_map":semantic_map,
        }
        design=_runtime_adapter(p,a.baseline_runtime,a.baseline_serial,a.baseline_platform,
                                a.baseline_appium_url,a.baseline_capabilities)
    else:
        if not a.design_url:
            p.error("Design comparison requires --design-url")
        if a.design_type=="figma":
            if not a.figma_token:
                p.error("Figma requires FIGMA_TOKEN or --figma-token")
            design=FigmaAdapter(a.figma_token,url=a.design_url)
        else:
            try:
                w,h=_viewport(a.viewport)
            except argparse.ArgumentTypeError as exc:
                p.error(str(exc))
            design=WebAdapter(a.design_url,w,h,
                              scroll_selector=a.web_scroll_selector,
                              target_y=a.web_target_y,
                              click_selector=a.web_click_selector,
                              scope_selector=a.web_scope_selector,
                              scroll_padding=a.web_scroll_padding)
    region_y=None
    if a.runtime_region_y:
        try:
            region_y=tuple(map(float,a.runtime_region_y.split(":")))
            if len(region_y)!=2 or not 0<=region_y[0]<region_y[1]<=1:
                raise ValueError("invalid region")
        except ValueError:
            p.error("--runtime-region-y requires normalized START:END within [0,1]")
    runtime=_runtime_adapter(p,a.runtime,a.serial,a.platform,a.appium_url,a.capabilities,region_y)
    engine=UIDiffEngine(cfg)
    if comparison is None:
        data=engine.run(design,runtime,a.output)
    else:
        data=engine.run(design,runtime,a.output,runtime_comparison=comparison)
    print(json.dumps(data["summary"],ensure_ascii=False,indent=2))
    print("report:",Path(a.output)/"report.html")

if __name__=="__main__":
    main()
