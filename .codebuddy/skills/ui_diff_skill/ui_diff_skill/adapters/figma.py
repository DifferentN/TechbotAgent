import re, requests
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from ..core.models import Bounds, Style, Component, Snapshot
from ..core.utils import write_json

class FigmaAdapter:
    def __init__(self, token, url=None, file_key=None, node_id=None):
        self.token=token
        self.file_key=file_key
        self.node_id=node_id
        if url:
            self._parse(url)

    def _parse(self,url):
        m=re.search(r"/(?:design|file)/([^/]+)",url)
        if m and not self.file_key:
            self.file_key=m.group(1)
        q=parse_qs(urlparse(url).query)
        if not self.node_id and q.get("node-id"):
            self.node_id=q["node-id"][0].replace("-",":")

    @property
    def headers(self):
        return {"X-Figma-Token":self.token}

    def _target(self):
        if not self.file_key:
            raise RuntimeError("FIGMA_FILE_KEY_MISSING")
        if self.node_id:
            r=requests.get(
                f"https://api.figma.com/v1/files/{self.file_key}/nodes",
                headers=self.headers,params={"ids":self.node_id},timeout=30
            )
            r.raise_for_status()
            return r.json()["nodes"][self.node_id]["document"]
        r=requests.get(f"https://api.figma.com/v1/files/{self.file_key}",headers=self.headers,timeout=30)
        r.raise_for_status()
        q=[r.json()["document"]]
        while q:
            n=q.pop(0)
            if n.get("absoluteBoundingBox") and n.get("type") in {"FRAME","COMPONENT","INSTANCE"}:
                self.node_id=n.get("id")
                return n
            q.extend(n.get("children",[]))
        raise RuntimeError("FIGMA_TARGET_NOT_FOUND")

    def _paint(self,p):
        if not isinstance(p,dict) or not p.get("visible",True):
            return None
        c=p.get("color")
        if not c:return None
        r=round(c.get("r",0)*255);g=round(c.get("g",0)*255);b=round(c.get("b",0)*255)
        return f"#{r:02X}{g:02X}{b:02X}"

    def collect(self,outdir):
        root=self._target()
        rb=root.get("absoluteBoundingBox")
        if not rb:
            raise RuntimeError("FIGMA_TARGET_HAS_NO_BOUNDS")
        fx,fy=float(rb["x"]),float(rb["y"])
        fw,fh=float(rb["width"]),float(rb["height"])
        comps=[]

        def infer_type(n):
            if n.get("type")=="TEXT": return "TEXT"
            fills=n.get("fills") or []
            if any(isinstance(p,dict) and p.get("type")=="IMAGE" for p in fills):
                return "IMAGE"
            if n.get("type") in {"FRAME","GROUP","COMPONENT","INSTANCE","SECTION"}:
                return "BUTTON" if "button" in (n.get("name") or "").lower() else "CONTAINER"
            return "UNKNOWN"

        def walk(n,parent=None,index=0,count=1):
            b=n.get("absoluteBoundingBox")
            current_parent=parent
            if b and b.get("width",0)>0 and b.get("height",0)>0:
                x=float(b["x"])-fx;y=float(b["y"])-fy
                w=float(b["width"]);h=float(b["height"])
                fills=n.get("fills") or []
                strokes=n.get("strokes") or []
                radii=n.get("rectangleCornerRadii")
                if radii is None and n.get("cornerRadius") is not None:
                    radii=[float(n["cornerRadius"])]*4
                st=n.get("style") or {}
                c=Component(
                    id=n.get("id",""),
                    type=infer_type(n),
                    bounds=Bounds(x,y,w,h),
                    normalized=Bounds(x/fw,y/fh,w/fw,h/fh),
                    screenshot_bounds=Bounds(x,y,w,h),
                    parent_id=parent,
                    sibling_index=index,sibling_count=count,
                    name=n.get("name"),semantic_id=n.get("name"),
                    text=n.get("characters"),
                    style=Style(
                        background_color=next((self._paint(p) for p in fills if self._paint(p)),None),
                        text_color=self._paint(fills[0]) if n.get("type")=="TEXT" and fills else None,
                        border_color=next((self._paint(p) for p in strokes if self._paint(p)),None),
                        border_width=n.get("strokeWeight"),
                        corner_radii=radii,
                        font_family=st.get("fontFamily"),
                        font_size=st.get("fontSize"),
                        font_weight=int(st["fontWeight"]) if str(st.get("fontWeight","")).isdigit() else None,
                        line_height=st.get("lineHeightPx"),
                        letter_spacing=st.get("letterSpacing"),
                        opacity=n.get("opacity"),
                    ),
                    metadata={"figma_type":n.get("type")}
                )
                comps.append(c)
                current_parent=c.id
            ch=n.get("children") or []
            for i,v in enumerate(ch):
                walk(v,current_parent,i,len(ch))
        walk(root)

        out=Path(outdir);out.mkdir(parents=True,exist_ok=True)
        img_path=out/"design.png"
        rr=requests.get(
            f"https://api.figma.com/v1/images/{self.file_key}",
            headers=self.headers,
            params={"ids":self.node_id,"format":"png","scale":1},
            timeout=30
        )
        rr.raise_for_status()
        image_url=rr.json().get("images",{}).get(self.node_id)
        if not image_url:
            raise RuntimeError("FIGMA_RENDER_FAILED")
        ir=requests.get(image_url,timeout=30)
        ir.raise_for_status()
        img_path.write_bytes(ir.content)

        from PIL import Image
        with Image.open(img_path) as im:
            sw,sh=im.size
        sx=sw/max(fw,1e-9); sy=sh/max(fh,1e-9)
        for c in comps:
            c.screenshot_bounds=Bounds(
                c.bounds.x*sx,c.bounds.y*sy,c.bounds.width*sx,c.bounds.height*sy
            )
        snap=Snapshot(
            width=fw,height=fh,screenshot_width=sw,screenshot_height=sh,
            components=comps,screenshot_path=str(img_path),source="figma"
        )
        write_json(out/"design_snapshot.json",{
            "width":fw,"height":fh,
            "components":[{"id":c.id,"type":c.type,"name":c.name} for c in comps]
        })
        return snap
