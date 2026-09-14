from dataclasses import dataclass
from .models import Bounds

@dataclass
class CoordinateMapper:
    logical_width: float
    logical_height: float
    screenshot_width: float
    screenshot_height: float

    @property
    def scale_x(self):
        return self.screenshot_width / max(self.logical_width, 1e-9)

    @property
    def scale_y(self):
        return self.screenshot_height / max(self.logical_height, 1e-9)

    def logical_to_screenshot(self, b: Bounds) -> Bounds:
        return Bounds(
            b.x * self.scale_x,
            b.y * self.scale_y,
            b.width * self.scale_x,
            b.height * self.scale_y,
        )

    def screenshot_to_logical(self, b: Bounds) -> Bounds:
        return Bounds(
            b.x / max(self.scale_x, 1e-9),
            b.y / max(self.scale_y, 1e-9),
            b.width / max(self.scale_x, 1e-9),
            b.height / max(self.scale_y, 1e-9),
        )

    def normalized_to_screenshot(self, b: Bounds) -> Bounds:
        return Bounds(
            b.x * self.screenshot_width,
            b.y * self.screenshot_height,
            b.width * self.screenshot_width,
            b.height * self.screenshot_height,
        )
