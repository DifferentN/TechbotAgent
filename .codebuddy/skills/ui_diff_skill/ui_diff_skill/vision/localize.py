import cv2,math
from .common import crop
from ..core.models import Bounds

def _ratio(a,b):
    return min(a,b)/max(a,b) if a>0 and b>0 else 0

def locate(image,expected:Bounds):
    search=Bounds(
        expected.x-expected.width*.3,expected.y-expected.height*.3,
        expected.width*1.6,expected.height*1.6
    )
    roi=crop(image,search)
    if roi.size==0:return []
    g=cv2.cvtColor(roi,cv2.COLOR_BGR2GRAY)
    g=cv2.GaussianBlur(g,(5,5),0)
    e=cv2.Canny(g,50,150)
    cs,_=cv2.findContours(e,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    out=[]
    for c in cs:
        x,y,w,h=cv2.boundingRect(c)
        if w<3 or h<3:continue
        cx=search.x+x+w/2;cy=search.y+y+h/2
        dist=math.hypot(cx-expected.cx,cy-expected.cy)/max(expected.width,expected.height,1)
        pos=math.exp(-dist)
        size=(_ratio(w,expected.width)+_ratio(h,expected.height))/2
        aspect=_ratio(w/max(h,1),expected.width/max(expected.height,1))
        shape=1.0
        score=.35*pos+.30*size+.20*aspect+.15*shape
        out.append({"bounds":Bounds(search.x+x,search.y+y,w,h),"score":score})
    return sorted(out,key=lambda x:x["score"],reverse=True)
