from ..core.models import Difference

def compare(ds,rs,matches):
    dmap={x.id:x for x in ds.components};rmap={x.id:x for x in rs.components}
    out=[]
    for m in matches:
        d=dmap[m.design_id];r=rmap[m.runtime_id]
        if d.style.border_width is not None and r.style.border_width is not None:
            delta=r.style.border_width-d.style.border_width
            out.append(Difference(
                component=d.name or d.id,property="border_width",
                expected=d.style.border_width,actual=r.style.border_width,delta=delta,
                tolerance=1.0,status="PASS" if abs(delta)<=1 else "FAIL",
                source="metadata",confidence=m.score
            ))
        if d.style.corner_radii and r.style.corner_radii:
            for i,(e,a) in enumerate(zip(d.style.corner_radii,r.style.corner_radii)):
                delta=a-e
                out.append(Difference(
                    component=d.name or d.id,property=f"corner_radius_{i}",
                    expected=e,actual=a,delta=delta,tolerance=1.0,
                    status="PASS" if abs(delta)<=1 else "FAIL",
                    source="metadata",confidence=m.score
                ))
    return out
