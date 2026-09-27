from ..core.models import Difference

def _status(v,p,w):
    a=abs(v)
    return "PASS" if a<=p else ("WARNING" if a<=w else "FAIL")

def compare_parent_margins(ds,rs,matches,config):
    dmap={x.id:x for x in ds.components};rmap={x.id:x for x in rs.components}
    pair={m.design_id:m.runtime_id for m in matches}
    score={m.design_id:m.score for m in matches}
    p=config["geometry"]["pass_tolerance"];w=config["geometry"]["warning_tolerance"]
    out=[]

    for did,rid in pair.items():
        d=dmap[did];r=rmap[rid]
        if not d.parent_id or d.parent_id not in pair:continue
        dp=dmap.get(d.parent_id);rp=rmap.get(pair[d.parent_id])
        if not dp or not rp:continue
        dm={
            "left":d.normalized.x-dp.normalized.x,
            "top":d.normalized.y-dp.normalized.y,
            "right":dp.normalized.right-d.normalized.right,
            "bottom":dp.normalized.bottom-d.normalized.bottom,
        }
        rm={
            "left":r.normalized.x-rp.normalized.x,
            "top":r.normalized.y-rp.normalized.y,
            "right":rp.normalized.right-r.normalized.right,
            "bottom":rp.normalized.bottom-r.normalized.bottom,
        }
        for side in dm:
            scale=ds.width if side in {"left","right"} else ds.height
            expected=dm[side]*scale;actual=rm[side]*scale;delta=actual-expected
            out.append(Difference(
                component=d.name or d.id,property=f"margin_{side}",
                expected=round(expected,3),actual=round(actual,3),delta=round(delta,3),
                tolerance={"pass":p,"warning":w},status=_status(delta,p,w),
                source="relative-geometry",confidence=score[did]
            ))
    return out

def compare_sibling_gaps(ds,rs,matches,config):
    dmap={x.id:x for x in ds.components};rmap={x.id:x for x in rs.components}
    pair={m.design_id:m.runtime_id for m in matches}
    mscore={m.design_id:m.score for m in matches}
    p=config["geometry"]["pass_tolerance"];w=config["geometry"]["warning_tolerance"]
    out=[]

    by_parent={}
    for d in ds.components:
        if d.id in pair:
            by_parent.setdefault(d.parent_id,[]).append(d)

    for parent,items in by_parent.items():
        items=sorted(items,key=lambda x:x.sibling_index)
        for a,b in zip(items,items[1:]):
            ra=rmap.get(pair[a.id]);rb=rmap.get(pair[b.id])
            if not ra or not rb:continue

            # choose axis by dominant design separation
            dx=abs(b.normalized.x-a.normalized.x)
            dy=abs(b.normalized.y-a.normalized.y)
            if dx>=dy:
                egap=(b.normalized.x-a.normalized.right)*ds.width
                agap=(rb.normalized.x-ra.normalized.right)*ds.width
                prop="gap_horizontal"
            else:
                egap=(b.normalized.y-a.normalized.bottom)*ds.height
                agap=(rb.normalized.y-ra.normalized.bottom)*ds.height
                prop="gap_vertical"

            delta=agap-egap
            out.append(Difference(
                component=f"{a.name or a.id} -> {b.name or b.id}",
                property=prop,expected=round(egap,3),actual=round(agap,3),delta=round(delta,3),
                tolerance={"pass":p,"warning":w},status=_status(delta,p,w),
                source="relative-geometry",confidence=min(mscore[a.id],mscore[b.id])
            ))
    return out
