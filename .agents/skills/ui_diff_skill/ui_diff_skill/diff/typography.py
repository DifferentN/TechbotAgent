from ..core.models import Difference

def compare(ds,rs,matches):
    dmap={x.id:x for x in ds.components};rmap={x.id:x for x in rs.components}
    out=[]
    for m in matches:
        d=dmap[m.design_id];r=rmap[m.runtime_id]
        if d.type!="TEXT":continue
        pairs=[
            ("font_family",d.style.font_family,r.style.font_family,0),
            ("font_size",d.style.font_size,r.style.font_size,1.0),
            ("font_weight",d.style.font_weight,r.style.font_weight,100),
            ("line_height",d.style.line_height,r.style.line_height,1.0),
            ("letter_spacing",d.style.letter_spacing,r.style.letter_spacing,0.5),
        ]
        for prop,e,a,tol in pairs:
            if e is None or a is None:continue
            if isinstance(e,(int,float)) and isinstance(a,(int,float)):
                delta=a-e;status="PASS" if abs(delta)<=tol else "FAIL"
            else:
                delta=None;status="PASS" if str(e).lower()==str(a).lower() else "WARNING"
            out.append(Difference(
                component=d.name or d.id,property=prop,expected=e,actual=a,delta=delta,
                tolerance=tol,status=status,source="metadata",confidence=m.score
            ))
    return out
