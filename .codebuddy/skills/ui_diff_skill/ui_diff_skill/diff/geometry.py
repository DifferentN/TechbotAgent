from ..core.models import Difference

def _status(delta,pass_tol,warn_tol):
    a=abs(delta)
    if a<=pass_tol:return "PASS"
    if a<=warn_tol:return "WARNING"
    return "FAIL"

def compare(design_snapshot,runtime_snapshot,matches,config):
    dmap={x.id:x for x in design_snapshot.components};rmap={x.id:x for x in runtime_snapshot.components}
    p=config["geometry"]["pass_tolerance"];w=config["geometry"]["warning_tolerance"]
    out=[]
    for m in matches:
        d=dmap[m.design_id];r=rmap[m.runtime_id]
        for prop,dv,rv,scale in [
            ("x",d.normalized.x,r.normalized.x,design_snapshot.width),
            ("y",d.normalized.y,r.normalized.y,design_snapshot.height),
            ("width",d.normalized.width,r.normalized.width,design_snapshot.width),
            ("height",d.normalized.height,r.normalized.height,design_snapshot.height),
        ]:
            expected=dv*scale;actual=rv*scale;delta=actual-expected
            out.append(Difference(
                component=d.name or d.id,property=prop,
                expected=round(expected,3),actual=round(actual,3),delta=round(delta,3),
                tolerance={"pass":p,"warning":w},status=_status(delta,p,w),
                source="geometry",confidence=m.score
            ))
    return out
