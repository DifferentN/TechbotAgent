from pathlib import Path
from ..core.models import Bounds, Style, Component, Snapshot
from ..core.types import normalize_type

class WebAdapter:
    def __init__(self,url,width=390,height=844):
        self.url=url;self.width=width;self.height=height

    @staticmethod
    def _px(v):
        try:return float(str(v).replace("px",""))
        except:return None

    def collect(self,outdir):
        from playwright.sync_api import sync_playwright
        out=Path(outdir);out.mkdir(parents=True,exist_ok=True)
        img=out/"design.png"

        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True)
            page=browser.new_page(viewport={"width":self.width,"height":self.height})
            page.goto(self.url,wait_until="networkidle")
            rows=page.evaluate(r"""
            () => [...document.body.querySelectorAll("*")].map((el,i) => {
              const r=el.getBoundingClientRect(), s=getComputedStyle(el);
              if(s.display==="none"||s.visibility==="hidden"||r.width<=0||r.height<=0) return null;
              const direct=[...el.childNodes].filter(n=>n.nodeType===Node.TEXT_NODE)
                .map(n=>n.textContent||"").join(" ").trim();
              const parent=el.parentElement;
              const siblings=parent ? [...parent.children] : [el];
              return {
                id:"web-"+i, tag:el.tagName.toLowerCase(),
                semantic:el.getAttribute("data-testid")||el.getAttribute("aria-label")||el.id||null,
                text:direct,
                x:r.left,y:r.top,w:r.width,h:r.height,
                siblingIndex:siblings.indexOf(el), siblingCount:siblings.length,
                bg:s.backgroundColor,color:s.color,borderColor:s.borderColor,
                borderWidth:s.borderWidth,borderRadius:s.borderRadius,
                fontFamily:s.fontFamily,fontSize:s.fontSize,fontWeight:s.fontWeight,
                lineHeight:s.lineHeight,letterSpacing:s.letterSpacing,opacity:s.opacity
              }
            }).filter(Boolean)
            """)
            page.screenshot(path=str(img),full_page=False)
            browser.close()

        comps=[]
        for r in rows:
            cr=self._px(r["borderRadius"])
            comps.append(Component(
                id=r["id"],type=normalize_type(tag=r["tag"],has_text=bool(r["text"])),
                bounds=Bounds(r["x"],r["y"],r["w"],r["h"]),
                normalized=Bounds(r["x"]/self.width,r["y"]/self.height,r["w"]/self.width,r["h"]/self.height),
                screenshot_bounds=Bounds(r["x"],r["y"],r["w"],r["h"]),
                sibling_index=r["siblingIndex"],sibling_count=max(r["siblingCount"],1),
                name=r["semantic"],semantic_id=r["semantic"],text=r["text"] or None,
                style=Style(
                    background_color=r["bg"],text_color=r["color"],
                    border_color=r["borderColor"],border_width=self._px(r["borderWidth"]),
                    corner_radii=[cr]*4 if cr is not None else None,
                    font_family=r["fontFamily"],font_size=self._px(r["fontSize"]),
                    font_weight=int(r["fontWeight"]) if str(r["fontWeight"]).isdigit() else None,
                    line_height=self._px(r["lineHeight"]),letter_spacing=self._px(r["letterSpacing"]),
                    opacity=float(r["opacity"]) if r["opacity"] else None
                )
            ))
        return Snapshot(
            width=self.width,height=self.height,
            screenshot_width=self.width,screenshot_height=self.height,
            components=comps,screenshot_path=str(img),source="web"
        )
