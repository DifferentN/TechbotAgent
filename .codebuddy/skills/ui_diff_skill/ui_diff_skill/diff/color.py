import cv2, numpy as np
from ..core.models import Difference

def _hex_rgb(v):
    if not v:return None
    v=v.strip()
    if v.startswith("#") and len(v)>=7:
        try:return tuple(int(v[i:i+2],16) for i in (1,3,5))
        except:return None
    if v.startswith("rgb"):
        import re
        n=re.findall(r"[\d.]+",v)
        if len(n)>=3:return tuple(int(float(x)) for x in n[:3])
    return None

def delta_e(a,b):
    if a is None or b is None:return None
    arr=np.uint8([[list(a),list(b)]])
    lab=cv2.cvtColor(arr,cv2.COLOR_RGB2LAB)[0].astype(float)
    return float(np.linalg.norm(lab[0]-lab[1]))

def compare(ds,rs,matches,config):
    dmap={x.id:x for x in ds.components};rmap={x.id:x for x in rs.components}
    p=config["color"]["pass_delta_e"];w=config["color"]["warning_delta_e"]
    out=[]
    for m in matches:
        d=dmap[m.design_id];r=rmap[m.runtime_id]
        for prop,e,a in [
            ("background_color",d.style.background_color,r.style.background_color),
            ("text_color",d.style.text_color,r.style.text_color),
            ("border_color",d.style.border_color,r.style.border_color),
        ]:
            er=_hex_rgb(e);ar=_hex_rgb(a)
            de=delta_e(er,ar)
            if de is None:continue
            status="PASS" if de<=p else ("WARNING" if de<=w else "FAIL")
            out.append(Difference(
                component=d.name or d.id,property=prop,expected=e,actual=a,
                delta=round(de,3),tolerance={"pass_delta_e":p,"warning_delta_e":w},
                status=status,source="metadata-color",confidence=m.score
            ))
    return out
