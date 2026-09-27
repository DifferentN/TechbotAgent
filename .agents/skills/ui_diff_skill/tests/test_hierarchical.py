from ui_diff_skill.core.models import Bounds,Component
from ui_diff_skill.matching.matcher import match_components

def C(i,t,x,y,w,h,parent=None,idx=0,count=1,name=None):
    return Component(
        i,t,Bounds(x,y,w,h),Bounds(x/100,y/100,w/100,h/100),Bounds(x,y,w,h),
        parent_id=parent,sibling_index=idx,sibling_count=count,name=name,semantic_id=name
    )

def test_parent_constrained_children():
    d=[
        C("dp","CONTAINER",0,0,100,100,None,0,1,"card"),
        C("d1","TEXT",10,10,20,10,"dp",0,2),
        C("d2","IMAGE",10,30,20,20,"dp",1,2),
    ]
    r=[
        C("rp","CONTAINER",0,0,100,100,None,0,1,"card"),
        C("r1","TEXT",11,10,20,10,"rp",0,2),
        C("r2","IMAGE",10,31,20,20,"rp",1,2),
    ]
    m,missing,unexpected=match_components(d,r)
    pairs={(x.design_id,x.runtime_id) for x in m}
    assert ("dp","rp") in pairs
    assert ("d1","r1") in pairs
    assert ("d2","r2") in pairs
    assert not missing and not unexpected
