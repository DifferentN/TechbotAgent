import json
from copy import deepcopy

DEFAULT_CONFIG = {
    "geometry": {"pass_tolerance": 2.0, "warning_tolerance": 4.0},
    "color": {"pass_delta_e": 3.0, "warning_delta_e": 6.0},
    "visual": {
        "enabled": True,
        "ssim_diff_threshold": 0.15,
        "warning_diff_ratio": 0.20
    },
    "vision_localization": {"enabled": True, "minimum_score": 0.75},
    "ignore": {"runtime_semantic_patterns": []}
}

def _merge(a,b):
    out=deepcopy(a)
    for k,v in b.items():
        if isinstance(v,dict) and isinstance(out.get(k),dict):
            out[k]=_merge(out[k],v)
        else:
            out[k]=v
    return out

def load_config(path=None):
    if not path:
        return deepcopy(DEFAULT_CONFIG)
    with open(path,"r",encoding="utf-8") as f:
        return _merge(DEFAULT_CONFIG,json.load(f))
