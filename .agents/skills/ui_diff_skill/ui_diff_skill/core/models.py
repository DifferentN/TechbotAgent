from dataclasses import dataclass, field, asdict
from typing import Any, Optional

@dataclass
class Bounds:
    x: float
    y: float
    width: float
    height: float

    @property
    def right(self): return self.x + self.width
    @property
    def bottom(self): return self.y + self.height
    @property
    def cx(self): return self.x + self.width / 2
    @property
    def cy(self): return self.y + self.height / 2

@dataclass
class Style:
    background_color: Optional[str] = None
    text_color: Optional[str] = None
    border_color: Optional[str] = None
    border_width: Optional[float] = None
    corner_radii: Optional[list[float]] = None
    font_family: Optional[str] = None
    font_size: Optional[float] = None
    font_weight: Optional[int] = None
    line_height: Optional[float] = None
    letter_spacing: Optional[float] = None
    opacity: Optional[float] = None

@dataclass
class Component:
    id: str
    type: str
    bounds: Bounds
    normalized: Bounds
    screenshot_bounds: Bounds
    parent_id: Optional[str] = None
    sibling_index: int = 0
    sibling_count: int = 1
    name: Optional[str] = None
    semantic_id: Optional[str] = None
    text: Optional[str] = None
    style: Style = field(default_factory=Style)
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class Snapshot:
    width: float
    height: float
    screenshot_width: float
    screenshot_height: float
    components: list[Component]
    screenshot_path: str
    source: str
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class Match:
    design_id: str
    runtime_id: str
    score: float
    confidence: str
    evidence: dict[str, float]

@dataclass
class Difference:
    component: str
    property: str
    expected: Any
    actual: Any
    delta: Any
    tolerance: Any
    status: str
    source: str
    confidence: float = 1.0

def serializable(v):
    return asdict(v)
