import numpy as np
from .common import crop

def median_rgb(image,bounds,inset=.10):
    roi=crop(image,bounds)
    if roi.size==0:return None
    h,w=roi.shape[:2]
    ix=int(w*inset);iy=int(h*inset)
    inner=roi[iy:max(iy+1,h-iy),ix:max(ix+1,w-ix)]
    med=np.median(inner.reshape(-1,3),axis=0)
    b,g,r=[int(round(x)) for x in med]
    return (r,g,b)
