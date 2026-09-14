import argparse,json,os
from pathlib import Path
from .core.config import load_config
from .adapters.figma import FigmaAdapter
from .adapters.web import WebAdapter
from .adapters.android_adb import AndroidADBAdapter
from .adapters.appium import AppiumAdapter
from .engine import UIDiffEngine

def main():
    p=argparse.ArgumentParser(description="UI Diff Skill")
    p.add_argument("--design-type",choices=["figma","web"],required=True)
    p.add_argument("--design-url",required=True)
    p.add_argument("--figma-token",default=os.getenv("FIGMA_TOKEN"))
    p.add_argument("--viewport",default="390x844")

    p.add_argument("--runtime",choices=["android-adb","appium"],required=True)
    p.add_argument("--serial")
    p.add_argument("--platform",choices=["android","ios"])
    p.add_argument("--appium-url",default="http://127.0.0.1:4723")
    p.add_argument("--capabilities")
    p.add_argument("--config")
    p.add_argument("--output",default="./ui-diff-out")
    a=p.parse_args()

    cfg=load_config(a.config)

    if a.design_type=="figma":
        if not a.figma_token:
            raise SystemExit("Figma requires FIGMA_TOKEN or --figma-token")
        design=FigmaAdapter(a.figma_token,url=a.design_url)
    else:
        w,h=map(int,a.viewport.lower().split("x"))
        design=WebAdapter(a.design_url,w,h)

    if a.runtime=="android-adb":
        runtime=AndroidADBAdapter(a.serial)
    else:
        if not a.platform or not a.capabilities:
            raise SystemExit("Appium requires --platform and --capabilities")
        caps=json.loads(Path(a.capabilities).read_text(encoding="utf-8"))
        runtime=AppiumAdapter(a.appium_url,caps,a.platform)

    data=UIDiffEngine(cfg).run(design,runtime,a.output)
    print(json.dumps(data["summary"],ensure_ascii=False,indent=2))
    print("report:",Path(a.output)/"report.html")

if __name__=="__main__":
    main()
