import cv2, numpy as np, math
from .common import crop
from ..core.models import Bounds

def _dominant_edge_transition(line):
    if line.ndim==2:
        vals=line.astype(float)
    else:
        vals=cv2.cvtColor(line,cv2.COLOR_BGR2GRAY).astype(float)
    if vals.ndim>1:
        vals=vals.reshape(-1)
    if len(vals)<4:return None
    grad=np.abs(np.diff(vals))
    idx=int(np.argmax(grad))
    strength=float(grad[idx])
    return idx+1,strength

def measure_border(image,bounds:Bounds):
    roi=crop(image,bounds)
    if roi.size==0:return None
    h,w=roi.shape[:2]
    if min(h,w)<8:return None
    samples=[]
    # center lines from each side inward
    samples.append(_dominant_edge_transition(roi[h//2, :max(4,w//3)]))
    samples.append(_dominant_edge_transition(roi[h//2, max(0,w-w//3):][::-1]))
    samples.append(_dominant_edge_transition(roi[:max(4,h//3), w//2]))
    samples.append(_dominant_edge_transition(roi[max(0,h-h//3):, w//2][::-1]))
    samples=[x for x in samples if x and x[1]>=8]
    if len(samples)<2:return None
    width=float(np.median([x[0] for x in samples]))
    conf=min(1.0, np.mean([x[1] for x in samples])/64.0)
    return {"width_px":width,"confidence":conf}

def _corner_radius_single(gray, corner):
    h,w=gray.shape[:2]
    size=max(8,int(min(h,w)*.35))
    if corner=="tl":
        sub=gray[:size,:size]
        origin=(0,0)
    elif corner=="tr":
        sub=gray[:size,w-size:]
        origin=(w-size,0)
    elif corner=="br":
        sub=gray[h-size:,w-size:]
        origin=(w-size,h-size)
    else:
        sub=gray[h-size:,:size]
        origin=(0,h-size)

    blur=cv2.GaussianBlur(sub,(5,5),0)
    edges=cv2.Canny(blur,40,120)
    ys,xs=np.where(edges>0)
    if len(xs)<8:return None
    # Estimate radius from nearest edge point to the geometric corner.
    if corner=="tl":
        d=np.sqrt(xs**2+ys**2)
    elif corner=="tr":
        d=np.sqrt((size-1-xs)**2+ys**2)
    elif corner=="br":
        d=np.sqrt((size-1-xs)**2+(size-1-ys)**2)
    else:
        d=np.sqrt(xs**2+(size-1-ys)**2)
    # Robust lower percentile approximates arc distance from corner.
    r=float(np.percentile(d,20))
    spread=float(np.std(d[d <= np.percentile(d,50)])) if len(d)>3 else 999
    conf=max(0.0,min(1.0,1.0-spread/max(r,1)))
    if r<1 or r>size*1.5:return None
    return {"radius_px":r,"confidence":conf}

def measure_corner_radii(image,bounds:Bounds):
    roi=crop(image,bounds)
    if roi.size==0:return None
    gray=cv2.cvtColor(roi,cv2.COLOR_BGR2GRAY)
    vals=[]
    for c in ["tl","tr","br","bl"]:
        vals.append(_corner_radius_single(gray,c))
    valid=[v for v in vals if v and v["confidence"]>=.15]
    if len(valid)<2:return None
    return {
        "radii_px":[None if v is None else v["radius_px"] for v in vals],
        "confidence":float(np.mean([v["confidence"] for v in valid]))
    }

def median_background_rgb(image,bounds:Bounds,inset=.12):
    roi=crop(image,bounds)
    if roi.size==0:return None
    h,w=roi.shape[:2]
    ix=int(w*inset);iy=int(h*inset)
    inner=roi[iy:max(iy+1,h-iy), ix:max(ix+1,w-ix)]
    if inner.size==0:return None
    med=np.median(inner.reshape(-1,3),axis=0)
    b,g,r=[int(round(v)) for v in med]
    return (r,g,b)
