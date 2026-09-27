def _children(component_id, items):
    return sorted([c for c in items if c.parent_id==component_id], key=lambda x:x.sibling_index)

def structural_fingerprint(component, components):
    ch=_children(component.id,components)
    types=",".join(x.type for x in ch)
    geom=[]
    for c in ch[:6]:
        geom.append(
            f"{c.type}:{round(c.normalized.x-component.normalized.x,2)}:"
            f"{round(c.normalized.y-component.normalized.y,2)}:"
            f"{round(c.normalized.width,2)}:{round(c.normalized.height,2)}"
        )
    return component.type+"("+types+")|"+";".join(geom)

def detect_repeated_templates(components):
    by_parent={}
    for c in components:
        by_parent.setdefault(c.parent_id,[]).append(c)

    groups=[]
    for parent,items in by_parent.items():
        fps={}
        for c in items:
            fp=structural_fingerprint(c,components)
            fps.setdefault(fp,[]).append(c.id)
        for fp,ids in fps.items():
            if len(ids)>=2 and "(" in fp and not fp.startswith("TEXT(") and not fp.startswith("IMAGE("):
                groups.append({
                    "parent_id":parent,
                    "fingerprint":fp,
                    "item_ids":ids
                })
    return groups
