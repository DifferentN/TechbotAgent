import xml.etree.ElementTree as ET
from pathlib import Path
from io import BytesIO
from PIL import Image
from ..core.models import Bounds, Component, Snapshot
from ..core.types import normalize_type
from ..core.utils import parse_android_bounds
from ..core.coordinate import CoordinateMapper

class AppiumAdapter:
    def __init__(self,url,capabilities,platform):
        self.url=url;self.capabilities=capabilities;self.platform=platform.lower()

    def collect(self,outdir):
        from appium import webdriver
        from appium.options.common.base import AppiumOptions
        opts=AppiumOptions();opts.load_capabilities(self.capabilities)
        try:
            driver=webdriver.Remote(self.url,options=opts)
        except Exception as e:
            raise RuntimeError(f"APPIUM_CONNECTION_FAILED: {e}")
        try:
            png=driver.get_screenshot_as_png()
            xml=driver.page_source
            try:
                rect=driver.get_window_rect()
            except Exception:
                rect=None
        finally:
            driver.quit()

        out=Path(outdir);out.mkdir(parents=True,exist_ok=True)
        img=out/"runtime.png";img.write_bytes(png)
        (out/"runtime.xml").write_text(xml,encoding="utf-8")
        with Image.open(BytesIO(png)) as im: sw,sh=im.size

        logical_w=(rect or {}).get("width",sw)
        logical_h=(rect or {}).get("height",sh)
        mapper=CoordinateMapper(logical_w,logical_h,sw,sh)

        root=ET.fromstring(xml)
        comps=[];counter=0

        def get_bounds(n):
            if n.attrib.get("bounds"):
                return parse_android_bounds(n.attrib["bounds"])
            try:
                return Bounds(float(n.attrib["x"]),float(n.attrib["y"]),float(n.attrib["width"]),float(n.attrib["height"]))
            except:return None

        def walk(n,parent=None,index=0,count=1):
            nonlocal counter
            b=get_bounds(n);current_parent=parent
            if b and b.width>0 and b.height>0:
                cid=f"{self.platform}-{counter}";counter+=1
                raw=n.attrib.get("class") or n.attrib.get("type") or n.tag
                sem=n.attrib.get("resource-id") or n.attrib.get("name") or n.attrib.get("label") or n.attrib.get("content-desc")
                txt=n.attrib.get("text") or n.attrib.get("value") or n.attrib.get("label")
                sb=mapper.logical_to_screenshot(b)
                comps.append(Component(
                    id=cid,type=normalize_type(raw),bounds=b,
                    normalized=Bounds(
                        b.x/max(logical_w,1e-9),b.y/max(logical_h,1e-9),
                        b.width/max(logical_w,1e-9),b.height/max(logical_h,1e-9)
                    ),
                    screenshot_bounds=sb,parent_id=parent,sibling_index=index,sibling_count=count,
                    name=sem,semantic_id=sem,text=txt,metadata=dict(n.attrib)
                ))
                current_parent=cid
            ch=list(n)
            for i,v in enumerate(ch):
                walk(v,current_parent,i,len(ch))
        walk(root)

        return Snapshot(
            width=logical_w,height=logical_h,
            screenshot_width=sw,screenshot_height=sh,
            components=comps,screenshot_path=str(img),
            source=f"appium-{self.platform}",
            metadata={"window_rect":rect or {}}
        )
