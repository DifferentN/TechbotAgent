def normalize_type(raw="", tag="", has_text=False):
    x=(raw or "").lower()
    t=(tag or "").lower()

    if t=="img" or "imageview" in x or "xc uielementtypeimage".replace(" ","") in x.replace(" ",""):
        return "IMAGE"
    if t=="button" or "button" in x:
        return "BUTTON"
    if t in {"input","textarea"} or "edittext" in x or "textfield" in x:
        return "INPUT"
    if "textview" in x or "statictext" in x or t in {"span","p","label","h1","h2","h3","h4"}:
        return "TEXT"
    if "recyclerview" in x or "collectionview" in x or "tableview" in x or x.endswith("list"):
        return "LIST"
    if t in {"div","section","main","body"} or "viewgroup" in x or "frame" in x or "other" in x:
        return "CONTAINER"
    if has_text:
        return "TEXT"
    return "UNKNOWN"

def compatibility(a,b):
    if a==b:
        return 1.0
    if {a,b}=={"BUTTON","CONTAINER"}:
        return 0.7
    if {a,b}=={"ICON","IMAGE"}:
        return 0.7
    if "UNKNOWN" in {a,b}:
        return 0.3
    return 0.0
