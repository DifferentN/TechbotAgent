import json,html
from pathlib import Path
from ..core.models import serializable

def write(outdir,ds,rs,matches,missing,unexpected,diffs):
    out=Path(outdir);out.mkdir(parents=True,exist_ok=True)
    summary={
        "matched":len(matches),"missing":len(missing),"unexpected":len(unexpected),
        "fail":sum(d.status=="FAIL" for d in diffs),
        "warning":sum(d.status=="WARNING" for d in diffs)
    }
    data={
        "summary":summary,
        "design_source":ds.source,"runtime_source":rs.source,
        "matches":[serializable(m) for m in matches],
        "missing":missing,"unexpected":unexpected,
        "differences":[serializable(d) for d in diffs]
    }
    (out/"report.json").write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")

    rows=[]
    for d in diffs:
        if d.status=="PASS":continue
        rows.append("<tr>"+
            "".join(f"<td>{html.escape(str(v))}</td>" for v in
                [d.component,d.property,d.expected,d.actual,d.delta,d.status,d.source,f"{d.confidence:.3f}"])
            +"</tr>")
    page=f"""<!doctype html><html><head><meta charset="utf-8"><title>UI Diff Report</title>
<style>body{{font-family:Arial;margin:28px}}table{{border-collapse:collapse;width:100%}}
th,td{{border:1px solid #ddd;padding:8px;text-align:left}}th{{background:#f5f5f5}}</style></head>
<body><h1>UI Diff Report</h1>
<p>Matched {summary['matched']} | Missing {summary['missing']} | Unexpected {summary['unexpected']} |
FAIL {summary['fail']} | WARNING {summary['warning']}</p>
<table><tr><th>Component</th><th>Property</th><th>Expected</th><th>Actual</th>
<th>Delta</th><th>Status</th><th>Source</th><th>Confidence</th></tr>{''.join(rows)}</table>
<h2>Missing</h2><pre>{html.escape(json.dumps(missing,ensure_ascii=False,indent=2))}</pre>
<h2>Unexpected</h2><pre>{html.escape(json.dumps(unexpected,ensure_ascii=False,indent=2))}</pre>
</body></html>"""
    (out/"report.html").write_text(page,encoding="utf-8")
    return data
