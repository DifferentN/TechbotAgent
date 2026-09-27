import math,re
from ..core.types import compatibility
from ..core.utils import norm_id

def _ratio(a,b):
    if a<=0 or b<=0:return 0.0
    return min(a,b)/max(a,b)

def _lev(a,b):
    prev=list(range(len(b)+1))
    for i,ca in enumerate(a,1):
        cur=[i]
        for j,cb in enumerate(b,1):
            cur.append(min(cur[-1]+1,prev[j]+1,prev[j-1]+(ca!=cb)))
        prev=cur
    return prev[-1]

def text_score(a,b):
    a=(a or "").strip().lower();b=(b or "").strip().lower()
    if not a and not b:return 0.5
    if not a or not b:return 0.0
    a=re.sub(r"\d+(?:\.\d+)?","${NUMBER}",a)
    b=re.sub(r"\d+(?:\.\d+)?","${NUMBER}",b)
    if a==b:return 1.0
    return 1-_lev(a,b)/max(len(a),len(b))

def pair_score(d,r):
    ts=compatibility(d.type,r.type)
    if ts<=0:return 0.0,{}
    dist=math.hypot(d.normalized.cx-r.normalized.cx,d.normalized.cy-r.normalized.cy)
    if dist>0.35:return 0.0,{}
    wr=d.normalized.width/max(r.normalized.width,1e-9)
    hr=d.normalized.height/max(r.normalized.height,1e-9)
    if wr>3 or wr<1/3 or hr>3 or hr<1/3:return 0.0,{}

    ps=math.exp(-dist/0.10)
    ss=(_ratio(d.normalized.width,r.normalized.width)+_ratio(d.normalized.height,r.normalized.height))/2
    do=d.sibling_index/max(d.sibling_count-1,1)
    ro=r.sibling_index/max(r.sibling_count-1,1)
    os=max(0,1-abs(do-ro))
    dn=norm_id(d.semantic_id or d.name);rn=norm_id(r.semantic_id or r.name)
    sem=1.0 if dn and rn and dn==rn else text_score(d.text,r.text)
    total=.30*ts+.25*ps+.20*ss+.10*os+.15*sem
    return total,{"type":ts,"position":ps,"size":ss,"order":os,"semantic":sem}
