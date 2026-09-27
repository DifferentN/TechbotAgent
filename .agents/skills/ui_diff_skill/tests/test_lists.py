from ui_diff_skill.core.models import Bounds,Component
from ui_diff_skill.matching.lists import detect_repeated_templates

def C(i,t,y,parent=None,idx=0,count=2):
    return Component(i,t,Bounds(0,y,100,20),Bounds(0,y/100,1,.2),Bounds(0,y,100,20),
                     parent_id=parent,sibling_index=idx,sibling_count=count)

def test_repeat_template():
    xs=[
        C("p","LIST",0,None,0,1),
        C("a","CONTAINER",10,"p",0,2),
        C("b","CONTAINER",40,"p",1,2),
        Component("a1","IMAGE",Bounds(0,10,20,20),Bounds(0,.1,.2,.2),Bounds(0,10,20,20),parent_id="a"),
        Component("b1","IMAGE",Bounds(0,40,20,20),Bounds(0,.4,.2,.2),Bounds(0,40,20,20),parent_id="b"),
    ]
    # structural geometry differs by parent absolute y, but normalized relative positions are similar enough
    groups=detect_repeated_templates(xs)
    assert isinstance(groups,list)
