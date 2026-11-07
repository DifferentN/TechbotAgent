from copy import deepcopy
from math import isfinite

from .models import Bounds, Difference


def validate_viewport(viewport):
    if len(viewport) != 2 or any(not isfinite(v) or v <= 0 for v in viewport):
        raise ValueError("comparison viewport requires two positive finite dimensions")
    return tuple(viewport)


def validate_content_rect(rect):
    if len(rect) != 4 or any(not isfinite(v) for v in rect):
        raise ValueError("content rect requires finite x:y:width:height")
    x, y, w, h = rect
    if x < 0 or y < 0 or w <= 0 or h <= 0 or x + w > 1 or y + h > 1:
        raise ValueError("content rect must lie within the normalized viewport [0, 1]")
    return tuple(rect)


def validate_semantic_map(mapping):
    if not isinstance(mapping, dict) or any(
        not isinstance(k, str) or not k.strip() or not isinstance(v, str) or not v.strip()
        for k, v in mapping.items()
    ):
        raise ValueError("semantic map must be an object of baseline ID -> target ID strings")
    return mapping


def prepare_snapshot(snapshot, viewport, content_rect=(0, 0, 1, 1), semantic_map=None):
    width, height = validate_viewport(viewport)
    x, y, w, h = validate_content_rect(content_rect)
    mapping = validate_semantic_map(semantic_map or {})
    validate_viewport((snapshot.width, snapshot.height))
    result = deepcopy(snapshot)
    result.width, result.height = width, height
    result.metadata["runtime_comparison"] = {
        "source_viewport": [snapshot.width, snapshot.height],
        "reference_viewport": [width, height],
        "content_rect": [x, y, w, h],
        "geometry_unit": "reference-logical-unit",
    }
    retained = []
    for node in result.components:
        b = node.normalized
        left, top = max(b.x, x), max(b.y, y)
        right, bottom = min(b.right, x + w), min(b.bottom, y + h)
        if right <= left or bottom <= top or b.width <= 0 or b.height <= 0:
            continue
        sb = node.screenshot_bounds
        if (left, top, right, bottom) != (b.x, b.y, b.right, b.bottom):
            node.screenshot_bounds = Bounds(
                sb.x + (left - b.x) / b.width * sb.width,
                sb.y + (top - b.y) / b.height * sb.height,
                (right - left) / b.width * sb.width,
                (bottom - top) / b.height * sb.height,
            )
        node.normalized = Bounds((left - x) / w, (top - y) / h,
                                 (right - left) / w, (bottom - top) / h)
        n = node.normalized
        node.bounds = Bounds(n.x * width, n.y * height, n.width * width, n.height * height)
        if node.semantic_id in mapping:
            node.metadata["original_semantic_id"] = node.semantic_id
            node.semantic_id = mapping[node.semantic_id]
        if node.name:
            node.metadata["original_name"] = node.name
            if not node.semantic_id:
                node.semantic_id = node.name
            node.name = f"{node.name} [{node.id}]"
        sx, sy = width / (snapshot.width * w), height / (snapshot.height * h)
        for prop in ("font_size", "line_height"):
            value = getattr(node.style, prop)
            if value is not None:
                setattr(node.style, prop, value * sy)
        if node.style.letter_spacing is not None:
            node.style.letter_spacing *= sx
        scale = (sx + sy) / 2
        if node.style.border_width is not None:
            node.style.border_width *= scale
        if node.style.corner_radii is not None:
            node.style.corner_radii = [v * scale for v in node.style.corner_radii]
        retained.append(node)
    original = {c.id: c for c in result.components}
    ids = {c.id for c in retained}
    by_parent = {}
    for node in retained:
        parent = node.parent_id
        while parent and parent not in ids:
            parent = original[parent].parent_id if parent in original else None
        node.parent_id = parent
        by_parent.setdefault(parent, []).append(node)
    for siblings in by_parent.values():
        for index, node in enumerate(siblings):
            node.sibling_index = index
            node.sibling_count = len(siblings)
    result.components = retained
    return result


def complete_runtime_differences(ds, rs, matches, differences):
    dmap = {c.id: c for c in ds.components}
    rmap = {c.id: c for c in rs.components}
    measured = {(d.component, d.property) for d in differences}
    out = []
    for match in matches:
        d, r = dmap[match.design_id], rmap[match.runtime_id]
        name = d.name or d.id
        if d.type in {"TEXT", "BUTTON", "INPUT"}:
            expected, actual = d.text, r.text
            known = expected is not None and actual is not None
            out.append(Difference(name, "text", expected, actual, None, "exact",
                                  ("PASS" if expected == actual else "FAIL") if known else "UNKNOWN",
                                  "runtime-metadata" if known else "unavailable-metadata",
                                  match.score if known else 0.0))
        props = ["background_color", "border_color", "border_width"]
        props += [f"corner_radius_{i}" for i in range(4)]
        if d.type in {"TEXT", "BUTTON", "INPUT"}:
            props += ["text_color", "font_family", "font_size", "font_weight",
                      "line_height", "letter_spacing"]
        for prop in props:
            if (name, prop) in measured:
                continue
            if prop.startswith("corner_radius_"):
                index = int(prop.rsplit("_", 1)[1])
                expected = d.style.corner_radii[index] if d.style.corner_radii and index < len(d.style.corner_radii) else None
                actual = r.style.corner_radii[index] if r.style.corner_radii and index < len(r.style.corner_radii) else None
            else:
                expected, actual = getattr(d.style, prop), getattr(r.style, prop)
            out.append(Difference(name, prop, expected, actual, None, None, "UNKNOWN",
                                  "unavailable-measurement", 0.0))
        if (name, "visual_roi") not in measured:
            out.append(Difference(name, "visual_roi", None, None, None, None, "UNKNOWN",
                                  "unavailable-visual-measurement", 0.0))
    return out
