import subprocess, xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image
from ..core.models import Bounds, Component, Snapshot
from ..core.types import normalize_type
from ..core.utils import parse_android_bounds

class AndroidADBAdapter:
    def __init__(self,serial=None):
        self.serial=serial

    def devices(self):
        try:
            out=subprocess.check_output(["adb","devices"],text=True,stderr=subprocess.STDOUT)
        except FileNotFoundError:
            raise RuntimeError("ADB_NOT_FOUND")
        return [x.split()[0] for x in out.splitlines()[1:] if len(x.split())>=2 and x.split()[1]=="device"]

    def _adb(self,*args,binary=False):
        cmd=["adb"]
        if self.serial:cmd+=["-s",self.serial]
        cmd+=list(args)
        return subprocess.check_output(cmd,stderr=subprocess.STDOUT) if binary else subprocess.check_output(cmd,text=True,stderr=subprocess.STDOUT)

    def collect(self,outdir):
        ds=self.devices()
        if not ds: raise RuntimeError("NO_ANDROID_DEVICE")
        if not self.serial:
            if len(ds)>1: raise RuntimeError("MULTIPLE_ANDROID_DEVICES: "+", ".join(ds))
            self.serial=ds[0]

        out=Path(outdir);out.mkdir(parents=True,exist_ok=True)
        img=out/"runtime.png"
        img.write_bytes(self._adb("exec-out","screencap","-p",binary=True))
        self._adb("shell","uiautomator","dump","/sdcard/window_dump.xml")
        xml=self._adb("shell","cat","/sdcard/window_dump.xml")
        (out/"runtime.xml").write_text(xml,encoding="utf-8")

        with Image.open(img) as im:
            sw,sh=im.size

        root=ET.fromstring(xml)
        comps=[];counter=0

        def walk(n,parent=None,index=0,count=1):
            nonlocal counter
            b=parse_android_bounds(n.attrib.get("bounds"))
            current_parent=parent
            if b and b.width>0 and b.height>0:
                cid=f"android-{counter}";counter+=1
                semantic=n.attrib.get("resource-id") or n.attrib.get("content-desc") or None
                c=Component(
                    id=cid,type=normalize_type(n.attrib.get("class","")),
                    bounds=b,normalized=Bounds(b.x/sw,b.y/sh,b.width/sw,b.height/sh),
                    screenshot_bounds=b,parent_id=parent,sibling_index=index,sibling_count=count,
                    name=semantic,semantic_id=semantic,text=n.attrib.get("text") or None,
                    metadata=dict(n.attrib)
                )
                comps.append(c);current_parent=cid
            ch=list(n)
            for i,v in enumerate(ch):
                walk(v,current_parent,i,len(ch))
        walk(root)

        return Snapshot(
            width=sw,height=sh,screenshot_width=sw,screenshot_height=sh,
            components=comps,screenshot_path=str(img),source="android-adb",
            metadata={"serial":self.serial}
        )
