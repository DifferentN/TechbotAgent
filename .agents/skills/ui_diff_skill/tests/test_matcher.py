from ui_diff_skill.core.models import Bounds,Component
from ui_diff_skill.matching.matcher import match_components

def C(i,t,x,y,w,h,s=None):
    return Component(i,t,Bounds(x,y,w,h),Bounds(x/100,y/100,w/100,h/100),Bounds(x,y,w,h),semantic_id=s)

def test_semantic_match():
    d=[C("d","IMAGE",10,10,20,20,"product_image")]
    r=[C("r","IMAGE",10,10,20,20,"product_image")]
    m,missing,unexpected=match_components(d,r)
    assert len(m)==1 and not missing and not unexpected
