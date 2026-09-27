import cv2
from ..core.models import Difference
from ..vision.style_measure import measure_corner_radii, measure_border, median_background_rgb
from .color import delta_e, _hex_rgb

def _logical_scale(component):
    sx=component.screenshot_bounds.width/max(component.bounds.width,1e-9)
    sy=component.screenshot_bounds.height/max(component.bounds.height,1e-9)
    return (sx+sy)/2

def compare(ds,rs,matches,config):
    """
    Only fills gaps where runtime structured metadata is missing.
    Figma/Web metadata remains the source of expected values.
    """
    ri=cv2.imread(rs.screenshot_path)
    if ri is None:return []
    dmap={x.id:x for x in ds.components};rmap={x.id:x for x in rs.components}
    out=[]

    for m in matches:
        d=dmap[m.design_id];r=rmap[m.runtime_id]
        scale=_logical_scale(r)

        # Corner radius fallback
        if d.style.corner_radii and not r.style.corner_radii:
            meas=measure_corner_radii(ri,r.screenshot_bounds)
            if meas and meas["confidence"]>=.25:
                for i,e in enumerate(d.style.corner_radii):
                    px=meas["radii_px"][i] if i < len(meas["radii_px"]) else None
                    if px is None: continue
                    a=px/max(scale,1e-9)
                    delta=a-e
                    out.append(Difference(
                        component=d.name or d.id,property=f"corner_radius_{i}",
                        expected=round(float(e),3),actual=round(float(a),3),delta=round(float(delta),3),
                        tolerance=1.5,status="PASS" if abs(delta)<=1.5 else "FAIL",
                        source="opencv-corner-radius",confidence=min(m.score,meas["confidence"])
                    ))

        # Border width fallback
        if d.style.border_width is not None and r.style.border_width is None:
            meas=measure_border(ri,r.screenshot_bounds)
            if meas and meas["confidence"]>=.25:
                a=meas["width_px"]/max(scale,1e-9)
                delta=a-d.style.border_width
                out.append(Difference(
                    component=d.name or d.id,property="border_width",
                    expected=d.style.border_width,actual=round(float(a),3),delta=round(float(delta),3),
                    tolerance=1.0,status="PASS" if abs(delta)<=1 else "FAIL",
                    source="opencv-border",confidence=min(m.score,meas["confidence"])
                ))

        # Background color fallback
        if d.style.background_color and not r.style.background_color:
            rgb=median_background_rgb(ri,r.screenshot_bounds)
            exp=_hex_rgb(d.style.background_color)
            de=delta_e(exp,rgb) if exp and rgb else None
            if de is not None:
                p=config["color"]["pass_delta_e"];w=config["color"]["warning_delta_e"]
                status="PASS" if de<=p else ("WARNING" if de<=w else "FAIL")
                out.append(Difference(
                    component=d.name or d.id,property="background_color",
                    expected=d.style.background_color,
                    actual="#%02X%02X%02X"%rgb,delta=round(float(de),3),
                    tolerance={"pass_delta_e":p,"warning_delta_e":w},
                    status=status,source="opencv-median-color",
                    confidence=min(m.score,.75)
                ))
    return out
