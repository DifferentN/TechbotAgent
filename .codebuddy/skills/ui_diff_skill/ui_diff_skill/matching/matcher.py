import numpy as np
from scipy.optimize import linear_sum_assignment
from ..core.models import Match
from ..core.types import compatibility
from ..core.utils import norm_id
from .scoring import pair_score
from .lists import detect_repeated_templates

def confidence(v):
    if v>=.80:return "HIGH"
    if v>=.65:return "MEDIUM"
    if v>=.50:return "LOW"
    return "UNMATCHED"

def _children_by_parent(items):
    out={}
    for c in items:
        out.setdefault(c.parent_id,[]).append(c)
    for k in out:
        out[k]=sorted(out[k], key=lambda x:x.sibling_index)
    return out

def _stable_matches(design, runtime, used_d, used_r, matches):
    rid={}
    for j,r in enumerate(runtime):
        k=norm_id(r.semantic_id or r.name)
        if k: rid.setdefault(k,[]).append(j)
    for i,d in enumerate(design):
        if i in used_d: continue
        k=norm_id(d.semantic_id or d.name)
        if not k or len(rid.get(k,[]))!=1: continue
        j=rid[k][0]
        if j in used_r: continue
        if compatibility(d.type,runtime[j].type)<=0: continue
        matches.append(Match(d.id,runtime[j].id,1.0,"HIGH",{"semantic_id":1.0}))
        used_d.add(i);used_r.add(j)

def _hungarian_group(dgroup, rgroup, design_index, runtime_index, used_d, used_r, matches, hierarchy_bonus=0.15):
    if not dgroup or not rgroup: return
    scores=np.zeros((len(dgroup),len(rgroup)),dtype=float)
    evidence={}
    for ii,d in enumerate(dgroup):
        for jj,r in enumerate(rgroup):
            s,ev=pair_score(d,r)
            if s>0:
                s=min(1.0, s + hierarchy_bonus)
                ev=dict(ev)
                ev["hierarchy"]=1.0
            scores[ii,jj]=s
            evidence[(ii,jj)]=ev
    if scores.size==0:return
    rows,cols=linear_sum_assignment(1-scores)
    for ii,jj in zip(rows,cols):
        s=float(scores[ii,jj])
        if s<.50: continue
        d=dgroup[ii]; r=rgroup[jj]
        di=design_index[d.id]; ri=runtime_index[r.id]
        if di in used_d or ri in used_r: continue
        matches.append(Match(d.id,r.id,s,confidence(s),evidence[(ii,jj)]))
        used_d.add(di);used_r.add(ri)

def _match_hierarchically(design, runtime, used_d, used_r, matches):
    dindex={c.id:i for i,c in enumerate(design)}
    rindex={c.id:i for i,c in enumerate(runtime)}
    dchildren=_children_by_parent(design)
    rchildren=_children_by_parent(runtime)
    matched_parent={m.design_id:m.runtime_id for m in matches}

    # Start from roots, then expand layer by layer.
    pending=[(None,None)]
    seen=set()
    while pending:
        dp,rp=pending.pop(0)
        if (dp,rp) in seen: continue
        seen.add((dp,rp))
        dg=[c for c in dchildren.get(dp,[]) if dindex[c.id] not in used_d]
        rg=[c for c in rchildren.get(rp,[]) if rindex[c.id] not in used_r]
        _hungarian_group(dg,rg,dindex,rindex,used_d,used_r,matches,hierarchy_bonus=0.15)

        # refresh parent map and descend only through matched parents
        matched_parent={m.design_id:m.runtime_id for m in matches}
        for dc in dchildren.get(dp,[]):
            rr=matched_parent.get(dc.id)
            if rr:
                pending.append((dc.id,rr))

def _fallback_global(design, runtime, used_d, used_r, matches):
    di=[i for i in range(len(design)) if i not in used_d]
    rj=[j for j in range(len(runtime)) if j not in used_r]
    if not di or not rj: return
    scores=np.zeros((len(di),len(rj)),dtype=float);evidence={}
    for ii,i in enumerate(di):
        for jj,j in enumerate(rj):
            s,ev=pair_score(design[i],runtime[j])
            scores[ii,jj]=s;evidence[(ii,jj)]=ev
    rows,cols=linear_sum_assignment(1-scores)
    for ii,jj in zip(rows,cols):
        s=float(scores[ii,jj])
        if s<.55: continue
        i=di[ii];j=rj[jj]
        matches.append(Match(design[i].id,runtime[j].id,s,confidence(s),evidence[(ii,jj)]))
        used_d.add(i);used_r.add(j)

def _list_template_matches(design, runtime, used_d, used_r, matches):
    """
    Repeated design structures become templates. Runtime repeated structures with
    the same structural fingerprint are matched item-by-item by order, then their
    children are left to the hierarchical matcher.
    """
    dgroups=detect_repeated_templates(design)
    rgroups=detect_repeated_templates(runtime)
    dmap={x.id:x for x in design}; rmap={x.id:x for x in runtime}
    dindex={x.id:i for i,x in enumerate(design)}; rindex={x.id:i for i,x in enumerate(runtime)}

    rbyfp={}
    for g in rgroups:
        rbyfp.setdefault(g["fingerprint"],[]).append(g)

    for dg in dgroups:
        candidates=rbyfp.get(dg["fingerprint"],[])
        if not candidates: continue
        rg=max(candidates,key=lambda x:len(x["item_ids"]))
        dids=dg["item_ids"]; rids=rg["item_ids"]
        for did,rid in zip(dids,rids):
            di=dindex[did];ri=rindex[rid]
            if di in used_d or ri in used_r: continue
            d=dmap[did];r=rmap[rid]
            s,ev=pair_score(d,r)
            if s<.45: continue
            ev=dict(ev);ev["list_template"]=1.0
            s=min(1.0,max(.75,s+.10))
            matches.append(Match(did,rid,s,confidence(s),ev))
            used_d.add(di);used_r.add(ri)

def match_components(design,runtime):
    used_d=set();used_r=set();matches=[]

    # 1. strongest signal
    _stable_matches(design,runtime,used_d,used_r,matches)

    # 2. repeated/list templates
    _list_template_matches(design,runtime,used_d,used_r,matches)

    # 3. parent-constrained Hungarian, top-down
    _match_hierarchically(design,runtime,used_d,used_r,matches)

    # 4. orphan/global fallback
    _fallback_global(design,runtime,used_d,used_r,matches)

    return (
        matches,
        [design[i].id for i in range(len(design)) if i not in used_d],
        [runtime[j].id for j in range(len(runtime)) if j not in used_r]
    )
