import json,html,os
from pathlib import Path
from urllib.parse import quote
from ..core.models import serializable


def _screenshot_panel(out, snapshot, label):
    relative=os.path.relpath(Path(snapshot.screenshot_path).resolve(),out.resolve())
    src=html.escape(quote(Path(relative).as_posix()),quote=True)
    return (f'<figure><figcaption>{html.escape(label)}: {html.escape(snapshot.source)}</figcaption>'
            f'<a href="{src}"><img src="{src}" alt="{html.escape(label)} screenshot"></a></figure>')


def write(outdir,ds,rs,matches,missing,unexpected,diffs,comparison=None,extra=None):
    out=Path(outdir);out.mkdir(parents=True,exist_ok=True)
    summary={
        "matched":len(matches),"missing":len(missing),"unexpected":len(unexpected),
        "fail":sum(d.status=="FAIL" for d in diffs),
        "warning":sum(d.status=="WARNING" for d in diffs),
        "unknown":sum(d.status=="UNKNOWN" for d in diffs)
    }
    if comparison is not None:
        summary["status"]=("FAIL" if summary["fail"] or missing or unexpected else
                           "UNKNOWN" if summary["unknown"] or not matches else
                           "WARNING" if summary["warning"] else "PASS")
    data={
        "summary":summary,
        "design_source":ds.source,"runtime_source":rs.source,
        "matches":[serializable(m) for m in matches],
        "missing":missing,"unexpected":unexpected,
        "differences":[serializable(d) for d in diffs]
    }
    if comparison is not None:
        data["comparison"]=comparison
        data["coverage"]={
            "scope":"matched component property checks only; not whole-screen equivalence",
            "measured":len(diffs)-summary["unknown"],"unknown":summary["unknown"],
            "baseline_components":len(ds.components),"target_components":len(rs.components),
        }
    if extra:
        data.update(extra)
    (out/"report.json").write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
    labels=("Baseline","Target") if comparison is not None else ("Design","Runtime")
    screenshots=_screenshot_panel(out,ds,labels[0])+_screenshot_panel(out,rs,labels[1])
    context=("<h2>Comparison</h2><pre>"+html.escape(json.dumps(comparison,ensure_ascii=False,indent=2))+"</pre>"
             if comparison is not None else "")

    rows=[]
    for d in diffs:
        if d.status=="PASS":continue
        rows.append("<tr>"+
            "".join(f"<td>{html.escape(str(v))}</td>" for v in
                [d.component,d.property,d.expected,d.actual,d.delta,d.tolerance,d.status,d.source,f"{d.confidence:.3f}"])
            +"</tr>")
    page=f"""<!doctype html><html><head><meta charset="utf-8"><title>UI Diff Report</title>
<style>body{{font-family:Arial;margin:28px}}table{{border-collapse:collapse;width:100%}}
th,td{{border:1px solid #ddd;padding:8px;text-align:left}}th{{background:#f5f5f5}}
.screenshots{{display:flex;gap:24px;flex-wrap:wrap}}figure{{margin:0;flex:1;min-width:240px}}
figure img{{max-width:100%;max-height:720px;object-fit:contain}}pre{{white-space:pre-wrap}}</style></head>
<body><h1>UI Diff Report</h1>
<p>Matched {summary['matched']} | Missing {summary['missing']} | Unexpected {summary['unexpected']} |
FAIL {summary['fail']} | WARNING {summary['warning']} | UNKNOWN {summary['unknown']}</p>
{context}<div class="screenshots">{screenshots}</div>
<table><tr><th>Component</th><th>Property</th><th>Expected</th><th>Actual</th>
<th>Delta</th><th>Tolerance</th><th>Status</th><th>Source</th><th>Confidence</th></tr>{''.join(rows)}</table>
<h2>Missing</h2><pre>{html.escape(json.dumps(missing,ensure_ascii=False,indent=2))}</pre>
<h2>Unexpected</h2><pre>{html.escape(json.dumps(unexpected,ensure_ascii=False,indent=2))}</pre>
</body></html>"""
    (out/"report.html").write_text(page,encoding="utf-8")
    return data
