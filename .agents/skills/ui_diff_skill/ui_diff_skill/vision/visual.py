import cv2,numpy as np
from skimage.metrics import structural_similarity
from .common import crop,resize_to
from ..core.models import Difference

def compare(ds,rs,matches,config):
    if not config["visual"]["enabled"]:return []
    di=cv2.imread(ds.screenshot_path);ri=cv2.imread(rs.screenshot_path)
    if di is None or ri is None:return []
    dmap={x.id:x for x in ds.components};rmap={x.id:x for x in rs.components}
    th=config["visual"]["ssim_diff_threshold"]
    wr=config["visual"]["warning_diff_ratio"]
    out=[]
    for m in matches:
        if m.score<.80:continue
        d=dmap[m.design_id];r=rmap[m.runtime_id]
        a=crop(di,d.screenshot_bounds);b=crop(ri,r.screenshot_bounds)
        if a.size==0 or b.size==0:continue
        b=resize_to(b,a)
        ag=cv2.cvtColor(a,cv2.COLOR_BGR2GRAY);bg=cv2.cvtColor(b,cv2.COLOR_BGR2GRAY)
        score,sm=structural_similarity(ag,bg,full=True,data_range=255)
        mask=((1-sm)>th).astype(np.uint8)*255
        if d.type=="IMAGE":
            h,w=a.shape[:2];ring=max(2,round(min(w,h)*.08))
            if w>2*ring and h>2*ring:
                mask[ring:h-ring,ring:w-ring]=0
        k=np.ones((3,3),np.uint8)
        mask=cv2.morphologyEx(mask,cv2.MORPH_OPEN,k)
        mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,k)
        ratio=float(np.count_nonzero(mask)/mask.size)
        out.append(Difference(
            component=d.name or d.id,property="visual_roi",
            expected="design_roi",actual={"ssim":round(float(score),4),"diffRatio":round(ratio,4)},
            delta=round(ratio,4),tolerance={"warning_diff_ratio":wr},
            status="WARNING" if ratio>wr else "PASS",
            source="opencv-ring-ssim" if d.type=="IMAGE" else "opencv-ssim",
            confidence=m.score
        ))
    return out
