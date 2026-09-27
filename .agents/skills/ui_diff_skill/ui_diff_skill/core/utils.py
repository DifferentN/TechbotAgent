import re
from pathlib import Path
from PIL import Image

def norm_id(v):
    return re.sub(r"[\s_\-:/]+","",(v or "").lower())

def parse_android_bounds(v):
    m=re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]",v or "")
    if not m:
        return None
    x1,y1,x2,y2=map(float,m.groups())
    from .models import Bounds
    return Bounds(x1,y1,x2-x1,y2-y1)

def image_size(path):
    with Image.open(path) as im:
        return im.size

def write_json(path,data):
    import json
    Path(path).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
